import os
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, update
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

from ecommerce_ops.config import settings as app_settings
from ecommerce_ops.graph.supervisor import Supervisor
from ecommerce_ops.models import (
    init_db,
    seed_data_if_empty,
    get_db_session,
    async_session_factory,
    ApprovalAction,
    AuditEntry,
    AgentStatus,
    StoreSettings,
)
from ecommerce_ops.safety.safety_rules import evaluate_action_safety
from ecommerce_ops.api.middleware import setup_middleware
from ecommerce_ops.api.auth import verify_auth
from sqlalchemy.ext.asyncio import AsyncSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecommerce_ops.api")

app = FastAPI(title=app_settings.PROJECT_NAME)

setup_middleware(app)

METRIC_HTTP_REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
METRIC_HTTP_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)
METRIC_DECISIONS_CREATED = Counter(
    "agent_decisions_total", "Total agent decisions created", ["agent", "action_type"]
)
METRIC_DECISIONS_APPROVED = Counter(
    "agent_decisions_approved_total", "Total decisions approved", ["agent"]
)
METRIC_DECISIONS_REJECTED = Counter(
    "agent_decisions_rejected_total", "Total decisions rejected", ["agent"]
)
METRIC_PIPELINE_RUNS = Counter(
    "pipeline_runs_total", "Total pipeline runs", ["status"]
)
METRIC_LLM_CALL_DURATION = Histogram(
    "llm_call_duration_seconds", "LLM call duration", ["agent"]
)
from ecommerce_ops.api.auth import verify_auth

# ── Thread-Safe WebSocket Manager ──────────────────────────
MAX_WS_CONNECTIONS = 1000


class ConnectionManager:
    def __init__(self):
        self._connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if len(self._connections) >= MAX_WS_CONNECTIONS:
                await websocket.close(code=1013, reason="Too many connections")
                return
            self._connections.append(websocket)
            logger.info("WS client connected. Total: %d", len(self._connections))

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
                logger.info("WS client disconnected. Total: %d", len(self._connections))

    async def broadcast(self, message: dict):
        async with self._lock:
            dead: List[WebSocket] = []
            for conn in self._connections:
                try:
                    await conn.send_json(message)
                except Exception:
                    dead.append(conn)
            for conn in dead:
                self._connections.remove(conn)


ws_manager = ConnectionManager()

# ── Request Models ─────────────────────────────────────────


class DecisionActionBody(BaseModel):
    notes: Optional[str] = None
    draft_response: Optional[str] = None


class RejectActionBody(BaseModel):
    reason: str
    notes: Optional[str] = None


class BatchActionBody(BaseModel):
    ids: List[str]
    action: str
    reason: Optional[str] = None
    notes: Optional[str] = None


class SettingsUpdateBody(BaseModel):
    shadow_mode: Optional[bool] = None
    fraud_threshold: Optional[int] = None
    po_limit: Optional[float] = None
    pricing_limit: Optional[float] = None
    reviews_rating_threshold: Optional[int] = None


# ── Startup / Shutdown ────────────────────────────────────


@app.on_event("startup")
async def startup_event():
    supervisor_ok = False
    try:
        app.state.supervisor = Supervisor()
        supervisor_ok = True
    except Exception as e:
        logger.critical("Failed to initialize Supervisor: %s", e)

    try:
        await init_db()
        await seed_data_if_empty()
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.critical("Database initialization failed: %s", e)
        if app_settings.ENV == "production":
            raise

    if supervisor_ok:
        logger.info("Application fully initialized and ready.")
    else:
        logger.warning("Application started without Supervisor — /api/run will fail.")


@app.on_event("shutdown")
async def shutdown_event():
    from ecommerce_ops.memory.cache import cache
    await cache.close()
    logger.info("Application shutdown complete.")


# ── Health ─────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Liveness + readiness probe. Returns 503 if dependencies are down."""
    deps = {"app": "healthy"}
    all_ok = True

    # Check database
    try:
        async for session in get_db_session():
            await session.execute(select(func.now()))
        deps["database"] = "healthy"
    except Exception as e:
        deps["database"] = f"unhealthy: {e}"
        all_ok = False

    # Check Redis (best-effort)
    try:
        from ecommerce_ops.memory.cache import cache
        client = await cache.get_client()
        await client.ping()
        deps["redis"] = "healthy"
    except Exception:
        deps["redis"] = "unavailable"

    status_code = 200 if all_ok else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if all_ok else "degraded", "dependencies": deps, "timestamp": datetime.utcnow().isoformat()},
    )


# ── WebSocket ──────────────────────────────────────────────


@app.websocket("/ws/queue")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


# ── Shared Helper ──────────────────────────────────────────


async def get_current_operator(identity: str = Depends(verify_auth)) -> str:
    """Extract the operator identity from auth."""
    return identity or "unknown-operator"


async def execute_shop_action(action: ApprovalAction) -> tuple[bool, str]:
    if action.shadow_mode:
        logger.info("[SHADOW] Simulating %s for %s", action.action_type, action.id)
        return True, "Shadow mode simulation"

    try:
        logger.info("[LIVE] Executing %s for %s", action.action_type, action.id)
        return True, f"Executed {action.action_type}"
    except Exception as e:
        logger.error("Shop action failed: %s", e)
        return False, str(e)


async def update_agent_streak(agent_name: str, approved: bool, confidence: float, db: AsyncSession):
    res = await db.execute(select(AgentStatus).where(AgentStatus.agent_id == agent_name).with_for_update())
    status = res.scalar_one_or_none()
    if not status:
        return
    status.total_decisions += 1
    if approved:
        status.total_approvals += 1
        if confidence >= 0.95:
            status.streak += 1
            if status.streak >= 50 and status.autonomy_level != "autonomous":
                status.autonomy_level = "autonomous"
                logger.info("Agent %s graduated to AUTONOMOUS!", agent_name)
    else:
        status.total_rejections += 1
        status.streak = 0
        status.autonomy_level = "supervised"
    n = status.total_decisions
    status.avg_confidence = ((status.avg_confidence * (n - 1)) + confidence) / n
    db.add(status)


# ── Endpoints ──────────────────────────────────────────────


@app.get("/api/approvals")
async def get_approvals(
    agent: Optional[str] = None,
    risk: Optional[str] = None,
    status: Optional[str] = "pending",
    search: Optional[str] = None,
    sort: Optional[str] = "newest",
    db: AsyncSession = Depends(get_db_session),
):
    query = select(ApprovalAction)
    if status == "pending":
        query = query.where(ApprovalAction.status == "pending")
    if agent and agent != "all":
        query = query.where(ApprovalAction.agent == agent)
    if risk and risk != "all":
        query = query.where(ApprovalAction.risk_level == risk)
    query = query.order_by(desc(ApprovalAction.created_at) if sort == "newest" else ApprovalAction.created_at)

    result = await db.execute(query)
    actions = result.scalars().all()

    if search:
        search_lower = search.lower()
        actions = [a for a in actions if search_lower in a.id.lower() or search_lower in str(a.payload).lower()]

    return actions


@app.get("/api/approvals/{id}")
async def get_approval(id: str, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(ApprovalAction).where(ApprovalAction.id == id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Approval action not found")
    return action


@app.post("/api/approvals/{id}/approve")
async def approve_approval(
    id: str,
    body: DecisionActionBody,
    operator: str = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(ApprovalAction).where(ApprovalAction.id == id).with_for_update())
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Approval action not found")
    if action.status != "pending":
        raise HTTPException(status_code=400, detail="Action already decided")
    if action.expires_at and action.expires_at < datetime.utcnow():
        action.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Action expired")

    if action.action_type == "review_response" and body.draft_response:
        new_payload = dict(action.payload)
        new_payload["draft_response"] = body.draft_response
        action.payload = new_payload

    action.reviewed_by = operator
    action.reviewed_at = datetime.utcnow()
    action.operator_notes = body.notes
    action.status = "executing"
    await db.commit()
    await ws_manager.broadcast({"type": "action_updated", "payload": {"id": action.id, "status": "executing", "agent": action.agent}})

    success, exec_msg = await execute_shop_action(action)
    action.status = "executed" if success else "failed"
    if not success:
        action.operator_notes = f"{action.operator_notes or ''} [Error: {exec_msg}]".strip()

    financial_impact = (action.impact or {}).get("financial_impact", 0.0)
    audit_entry = AuditEntry(
        action_id=action.id,
        timestamp=datetime.utcnow(),
        agent=action.agent,
        action_type=action.action_type,
        decision="shadow" if action.shadow_mode else "approved",
        operator=operator,
        confidence_score=action.confidence_score,
        financial_impact=financial_impact,
        details={"notes": action.operator_notes, "execution_status": action.status, "payload": action.payload},
    )
    db.add(audit_entry)
    await update_agent_streak(action.agent, success, action.confidence_score, db)
    await db.commit()

    await ws_manager.broadcast({"type": "action_updated", "payload": {"id": action.id, "status": action.status, "agent": action.agent}})
    return action


@app.post("/api/approvals/{id}/reject")
async def reject_approval(
    id: str,
    body: RejectActionBody,
    operator: str = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(ApprovalAction).where(ApprovalAction.id == id).with_for_update())
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Approval action not found")
    if action.status != "pending":
        raise HTTPException(status_code=400, detail="Action already decided")

    action.reviewed_by = operator
    action.reviewed_at = datetime.utcnow()
    action.rejection_reason = body.reason
    action.operator_notes = body.notes
    action.status = "rejected"

    financial_impact = (action.impact or {}).get("financial_impact", 0.0)
    audit_entry = AuditEntry(
        action_id=action.id,
        timestamp=datetime.utcnow(),
        agent=action.agent,
        action_type=action.action_type,
        decision="rejected",
        operator=operator,
        confidence_score=action.confidence_score,
        financial_impact=financial_impact,
        details={"reason": body.reason, "notes": body.notes},
    )
    db.add(audit_entry)
    await update_agent_streak(action.agent, False, action.confidence_score, db)
    await db.commit()

    await ws_manager.broadcast({"type": "action_updated", "payload": {"id": action.id, "status": "rejected", "agent": action.agent}})
    return action


@app.post("/api/approvals/batch")
async def batch_approvals(
    body: BatchActionBody,
    operator: str = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db_session),
):
    results = await db.execute(select(ApprovalAction).where(ApprovalAction.id.in_(body.ids)))
    actions = results.scalars().all()
    updated_ids = []

    for action in actions:
        if action.status != "pending":
            continue

        if body.action == "approve":
            if action.risk_level in ("high", "critical"):
                continue
            action.reviewed_by = operator
            action.reviewed_at = datetime.utcnow()
            action.operator_notes = body.notes
            action.status = "executing"
            await db.flush()

            success, _ = await execute_shop_action(action)
            action.status = "executed" if success else "failed"
            financial_impact = (action.impact or {}).get("financial_impact", 0.0)
            db.add(AuditEntry(
                action_id=action.id, timestamp=datetime.utcnow(), agent=action.agent,
                action_type=action.action_type, decision="shadow" if action.shadow_mode else "approved",
                operator=operator, confidence_score=action.confidence_score, financial_impact=financial_impact,
                details={"notes": body.notes, "execution_status": action.status, "batch": True},
            ))
            await update_agent_streak(action.agent, True, action.confidence_score, db)

        elif body.action == "reject":
            action.reviewed_by = operator
            action.reviewed_at = datetime.utcnow()
            action.rejection_reason = body.reason or "Batch rejected"
            action.operator_notes = body.notes
            action.status = "rejected"
            financial_impact = (action.impact or {}).get("financial_impact", 0.0)
            db.add(AuditEntry(
                action_id=action.id, timestamp=datetime.utcnow(), agent=action.agent,
                action_type=action.action_type, decision="rejected", operator=operator,
                confidence_score=action.confidence_score, financial_impact=financial_impact,
                details={"reason": body.reason, "notes": body.notes, "batch": True},
            ))
            await update_agent_streak(action.agent, False, action.confidence_score, db)

        updated_ids.append(action.id)
        await ws_manager.broadcast({"type": "action_updated", "payload": {"id": action.id, "status": action.status, "agent": action.agent}})

    await db.commit()
    return {"message": f"Processed {len(updated_ids)} batch actions", "affected_ids": updated_ids}


@app.get("/api/audit")
async def get_audit_logs(
    agent: Optional[str] = None,
    decision: Optional[str] = None,
    operator: Optional[str] = None,
    action_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session),
):
    query = select(AuditEntry)
    if agent and agent != "all":
        query = query.where(AuditEntry.agent == agent)
    if decision and decision != "all":
        query = query.where(AuditEntry.decision == decision)
    if operator and operator != "all":
        query = query.where(AuditEntry.operator == operator)
    if action_type and action_type != "all":
        query = query.where(AuditEntry.action_type == action_type)
    query = query.order_by(desc(AuditEntry.timestamp))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    entries = (await db.execute(query)).scalars().all()

    return {"entries": entries, "total": total, "page": page, "limit": limit}


@app.get("/api/agents/status")
async def get_agents_status(db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(AgentStatus))
    return res.scalars().all()


@app.get("/api/settings")
async def get_store_settings(db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(StoreSettings).where(StoreSettings.id == 1))
    store_settings = res.scalar_one_or_none()
    return store_settings


@app.patch("/api/settings")
async def update_store_settings(
    body: SettingsUpdateBody,
    operator: str = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db_session),
):
    res = await db.execute(select(StoreSettings).where(StoreSettings.id == 1).with_for_update())
    store_settings = res.scalar_one_or_none()
    if not store_settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    changes = {}
    if body.shadow_mode is not None:
        changes["shadow_mode"] = f"{store_settings.shadow_mode} -> {body.shadow_mode}"
        store_settings.shadow_mode = body.shadow_mode
        autonomy = "shadow" if body.shadow_mode else "supervised"
        await db.execute(update(AgentStatus).values(autonomy_level=autonomy))
    if body.fraud_threshold is not None:
        changes["fraud_threshold"] = f"{store_settings.fraud_threshold} -> {body.fraud_threshold}"
        store_settings.fraud_threshold = body.fraud_threshold
    if body.po_limit is not None:
        changes["po_limit"] = f"{store_settings.po_limit} -> {body.po_limit}"
        store_settings.po_limit = body.po_limit
    if body.pricing_limit is not None:
        changes["pricing_limit"] = f"{store_settings.pricing_limit} -> {body.pricing_limit}"
        store_settings.pricing_limit = body.pricing_limit
    if body.reviews_rating_threshold is not None:
        changes["reviews_rating_threshold"] = f"{store_settings.reviews_rating_threshold} -> {body.reviews_rating_threshold}"
        store_settings.reviews_rating_threshold = body.reviews_rating_threshold

    db.add(AuditEntry(
        action_id=None, timestamp=datetime.utcnow(), agent="System",
        action_type="settings_change", decision="approved", operator=operator,
        confidence_score=1.0, financial_impact=0.0, details={"changes": changes},
    ))
    await db.commit()
    await ws_manager.broadcast({"type": "agent_status", "payload": {"settings_updated": True}})
    return store_settings


@app.get("/api/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db_session)):
    approved = (await db.execute(select(func.count(AuditEntry.id)).where(AuditEntry.decision.in_(["approved", "shadow"])))).scalar() or 0
    rejected = (await db.execute(select(func.count(AuditEntry.id)).where(AuditEntry.decision == "rejected"))).scalar() or 0
    auto = (await db.execute(select(func.count(AuditEntry.id)).where(AuditEntry.decision == "auto-approved"))).scalar() or 0
    total = approved + rejected + auto
    approval_rate = (approved / (approved + rejected) * 100) if (approved + rejected) > 0 else 100.0
    financial = (await db.execute(select(func.sum(AuditEntry.financial_impact)).where(AuditEntry.decision.in_(["approved", "shadow", "auto-approved"])))).scalar() or 0.0

    agents = (await db.execute(select(AgentStatus))).scalars().all()
    pending = (await db.execute(select(ApprovalAction).where(ApprovalAction.status == "pending"))).scalars().all()
    risk_dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for a in pending:
        risk_dist[a.risk_level] = risk_dist.get(a.risk_level, 0) + 1

    now = datetime.utcnow()
    timeline = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%b %d")
        timeline.append({
            "date": day_str, "FraudAgent": 90 + (i % 3) * 3,
            "InventoryAgent": 80 + (i % 2) * 5, "PricingAgent": 95 - (i % 4) * 2,
            "ReviewsAgent": 88 + (i % 3) * 4, "MarketingAgent": 70 + (i % 2) * 8,
        })

    volume_by_agent = [
        {"day": d, "Fraud": f, "Inventory": i, "Pricing": p, "Reviews": r, "Marketing": m}
        for d, f, i, p, r, m in [
            ("Mon", 12, 4, 18, 25, 2), ("Tue", 15, 8, 22, 30, 3),
            ("Wed", 9, 6, 15, 28, 1), ("Thu", 18, 12, 24, 35, 4),
            ("Fri", 14, 5, 20, 32, 2), ("Sat", 8, 2, 12, 18, 1),
            ("Sun", 11, 3, 14, 22, 3),
        ]
    ]

    return {
        "summary": {
            "total_decisions": total, "approval_rate": round(approval_rate, 1),
            "actions_auto_approved": auto, "total_financial_impact": round(financial, 2),
            "avg_confidence": 0.89, "avg_decision_time_minutes": 4.2,
        },
        "graduation": [
            {"agent_id": a.agent_id, "streak": a.streak, "autonomy_level": a.autonomy_level,
             "total_decisions": a.total_decisions, "avg_confidence": round(a.avg_confidence, 2)}
            for a in agents
        ],
        "risk_distribution": risk_dist,
        "charts": {
            "approval_rate_over_time": timeline,
            "volume_by_agent": volume_by_agent,
            "decision_time_dist": {"under_1m": 45, "1m_5m": 28, "5m_30m": 12, "over_30m": 8},
        },
    }


# ── Pipeline Runner ────────────────────────────────────────

DECISION_TYPE_MAP = {
    "HOLD_ORDER": "fraud_hold",
    "DRAFT_PO": "purchase_order",
    "UPDATE_PRICE": "price_change",
    "POST_REVIEW_RESPONSE": "review_response",
    "DRAFT_MARKETING_CAMPAIGN": "marketing_campaign",
}


async def run_pipeline_task(run_id: str, db_settings: StoreSettings):
    logger.info("Starting pipeline run %s", run_id)
    import random

    seed_choice = random.choice(["fraud", "inventory", "price", "review", "marketing", "all"])
    inventory_data = [
        {"sku": "TSHIRT-BLUE-L", "stock": random.randint(1, 15), "price": 25.0, "variant_id": "v1"},
        {"sku": "MUG-WHITE", "stock": random.randint(1, 8), "price": 12.0, "variant_id": "v2"},
    ]
    if seed_choice in ("inventory", "all"):
        inventory_data.append({"sku": "SILK-PILLOW-SLV", "stock": 1, "price": 49.0, "variant_id": "v3"})

    active_orders = []
    if seed_choice in ("fraud", "all"):
        active_orders.append({"id": "o_suspicious", "line_items": [{"sku": "TSHIRT-BLUE-L", "quantity": 1}], "order_total": 450.0})
    else:
        active_orders.append({"id": f"o_{random.randint(100, 999)}", "line_items": [{"sku": "MUG-WHITE", "quantity": 2}], "order_total": 24.0})

    reviews_data = []
    if seed_choice in ("review", "all"):
        reviews_data.append({"id": f"r_{random.randint(100, 999)}", "content": "The shipping was delayed and box was damaged!", "rating": 2})
    else:
        reviews_data.append({"id": f"r_{random.randint(100, 999)}", "content": "Good material, very soft.", "rating": 5})

    initial_state = {
        "inventory_data": inventory_data,
        "active_orders": active_orders,
        "reviews_data": reviews_data,
        "decisions": [],
        "hitl_queue": [],
        "messages": [],
        "errors": [],
        "run_id": run_id,
        "timestamp": datetime.utcnow(),
    }

    try:
        supervisor = getattr(app.state, "supervisor", None)
        if not supervisor:
            supervisor = Supervisor()
        final_state = await supervisor.run(initial_state)
        decisions_list = final_state.get("decisions", [])
        logger.info("Pipeline %s finished: %d decisions", run_id, len(decisions_list))

        async with async_session_factory() as session:
            res_set = await session.execute(select(StoreSettings).where(StoreSettings.id == 1))
            settings = res_set.scalar_one()
            new_actions_count = 0

            for d in decisions_list:
                mapped_type = DECISION_TYPE_MAP.get(d.action_type, "marketing_campaign")
                requires_hitl, risk_level, financial_impact = evaluate_action_safety(
                    d.agent_id, mapped_type, d.action_data, d.confidence_score, settings
                )

                payload, evidence = _build_payload_and_evidence(d, reviews_data)
                impact = {
                    "financial_impact": financial_impact,
                    "affected_skus": [],
                    "affected_orders": [],
                    "reversible": True,
                    "reversal_window_hours": 24,
                }
                if d.agent_id in ("FraudAgent",):
                    impact["affected_orders"] = [payload.get("order_id", "")]
                else:
                    impact["affected_skus"] = [payload.get("sku", "")] if payload.get("sku") else []

                status = "pending"
                if not requires_hitl and not settings.shadow_mode:
                    status = "executed"

                action_id = str(uuid.uuid4())
                session.add(ApprovalAction(
                    id=action_id, agent=d.agent_id, action_type=mapped_type, status=status,
                    risk_level=risk_level, confidence_score=d.confidence_score,
                    created_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(days=2),
                    requires_hitl=requires_hitl, shadow_mode=settings.shadow_mode,
                    payload=payload, evidence=evidence, impact=impact,
                ))

                if status == "executed":
                    session.add(AuditEntry(
                        action_id=action_id, timestamp=datetime.utcnow(), agent=d.agent_id,
                        action_type=mapped_type, decision="auto-approved",
                        operator=None, confidence_score=d.confidence_score,
                        financial_impact=financial_impact,
                        details={"notes": "Auto-approved by safety system", "payload": payload},
                    ))
                    await update_agent_streak(d.agent_id, True, d.confidence_score, session)

                new_actions_count += 1

            await session.commit()
            await ws_manager.broadcast({"type": "pipeline_completed", "payload": {"run_id": run_id, "action_count": new_actions_count}})
            METRIC_PIPELINE_RUNS.labels(status="success").inc()

    except Exception as e:
        logger.exception("Pipeline run %s failed: %s", run_id, e)
        METRIC_PIPELINE_RUNS.labels(status="failure").inc()
        await ws_manager.broadcast({"type": "pipeline_failed", "payload": {"run_id": run_id, "error": str(e)}})


def _build_payload_and_evidence(d, reviews_data):
    """Extract payload and evidence from a decision based on agent type."""
    if d.agent_id == "FraudAgent":
        payload = {
            "order_id": d.action_data.get("order_id", "ORD-UNKNOWN"),
            "customer_name": "Valued Customer", "customer_email": "customer@vpnmail.net",
            "order_total": d.action_data.get("risk_score", 85) * 10,
            "fraud_score": d.action_data.get("risk_score", 85),
            "risk_signals": d.action_data.get("risk_factors", ["IP/Shipping mismatch"]),
            "recommended_action": "hold",
        }
        evidence = [
            {"label": "Risk Score", "value": f"{payload['fraud_score']}/100", "weight": "primary", "source": "FraudHeuristics"},
            {"label": "Risk Signals", "value": ", ".join(payload["risk_signals"]), "weight": "supporting", "source": "FraudAgent"},
        ]
        return payload, evidence

    if d.agent_id == "InventoryAgent":
        qty = d.action_data.get("quantity_to_order", 75)
        payload = {
            "sku": d.action_data.get("sku", "TSHIRT-BLUE-L"),
            "product_name": f"Product ({d.action_data.get('sku')})",
            "current_stock": 5, "daily_velocity": 2.5, "days_of_supply": 2.0,
            "reorder_quantity": qty, "supplier_name": "Default Supplier",
            "unit_cost": 15.00, "total_po_value": qty * 15.00,
        }
        evidence = [
            {"label": "Reorder Qty", "value": str(qty), "weight": "primary", "source": "InventoryAgent"},
            {"label": "Stockout", "value": f"~{d.action_data.get('predicted_stockout_days', 2.0):.1f}d", "weight": "supporting", "source": "Forecaster"},
        ]
        return payload, evidence

    if d.agent_id == "PricingAgent":
        payload = {
            "sku": d.action_data.get("sku", "TSHIRT-BLUE-L"),
            "product_name": f"Product ({d.action_data.get('sku')})",
            "current_price": d.action_data.get("old_price", 25.00),
            "proposed_price": d.action_data.get("new_price", 22.50),
            "change_percent": -10.0, "reasoning": d.reasoning,
            "competitor_prices": [{"competitor": "Competitor", "price": 22.50}],
        }
        evidence = [
            {"label": "Old Price", "value": f"${payload['current_price']:.2f}", "weight": "supporting", "source": "Shopify"},
            {"label": "New Price", "value": f"${payload['proposed_price']:.2f}", "weight": "primary", "source": "PricingAgent"},
        ]
        return payload, evidence

    if d.agent_id == "ReviewsAgent":
        payload = {
            "review_id": d.action_data.get("review_id", "rev-99"),
            "product_name": "Product Premium",
            "rating": reviews_data[0]["rating"] if reviews_data else 3,
            "review_text": reviews_data[0]["content"] if reviews_data else "Okay.",
            "customer_name": "Customer",
            "sentiment": d.action_data.get("sentiment", "Negative"),
            "draft_response": d.action_data.get("response_content", "Draft..."),
            "key_issues": d.action_data.get("themes", ["Support"]),
        }
        evidence = [
            {"label": "Rating", "value": f"{payload['rating']}/5", "weight": "primary", "source": "Shopify"},
            {"label": "Response", "value": payload["draft_response"][:80], "weight": "supporting", "source": "ReviewsAgent"},
        ]
        return payload, evidence

    # MarketingAgent fallthrough
    payload = {
        "campaign_name": f"Campaign for {d.action_data.get('sku')}",
        "target_skus": [d.action_data.get("sku", "TSHIRT-BLUE-L")],
        "discount_percent": 15.0, "urgency_reason": d.reasoning,
        "estimated_reach": 3000, "draft_message": d.action_data.get("draft_copy", "Draft..."),
    }
    evidence = [
        {"label": "Message", "value": payload["draft_message"][:80], "weight": "primary", "source": "MarketingAgent"},
        {"label": "Reason", "value": d.reasoning[:80], "weight": "supporting", "source": "MarketingAgent"},
    ]
    return payload, evidence


@app.post("/api/run")
async def trigger_run(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    run_id = str(uuid.uuid4())
    res = await db.execute(select(StoreSettings).where(StoreSettings.id == 1))
    db_settings = res.scalar_one()

    await ws_manager.broadcast({"type": "pipeline_started", "payload": {"run_id": run_id}})
    background_tasks.add_task(run_pipeline_task, run_id, db_settings)

    return {"message": "Operations cycle triggered", "run_id": run_id}


# ── Static Files ───────────────────────────────────────────

dist_path = "dashboard/dist"
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")
    logger.info("Mounted static frontend from %s", dist_path)
else:
    logger.warning("Static frontend path '%s' not found.", dist_path)
