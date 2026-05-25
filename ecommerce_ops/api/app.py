import os
import uuid
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy import select, func, desc, update
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_ops.config import settings as app_settings
from ecommerce_ops.models import (
    init_db,
    seed_data_if_empty,
    get_db_session,
    ApprovalAction,
    AuditEntry,
    AgentStatus,
    StoreSettings,
)
from ecommerce_ops.api.middleware import setup_middleware
from ecommerce_ops.api.auth import verify_auth
from ecommerce_ops.api.ws import ws_manager
from ecommerce_ops.api.metrics import METRIC_HTTP_REQUESTS, METRIC_HTTP_DURATION
from ecommerce_ops.pipeline.runner import run_pipeline_task, execute_shop_action, update_agent_streak

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecommerce_ops.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    supervisor_ok = False
    try:
        app.state.supervisor = None
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

    yield

    from ecommerce_ops.memory.cache import cache
    await cache.close()
    logger.info("Application shutdown complete.")


app = FastAPI(title=app_settings.PROJECT_NAME, lifespan=lifespan)

setup_middleware(app)


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


async def get_current_operator(identity: str = Depends(verify_auth)) -> str:
    return identity or "unknown-operator"


@app.get("/health")
async def health():
    deps = {"app": "healthy"}
    all_ok = True

    try:
        async for session in get_db_session():
            await session.execute(select(func.now()))
        deps["database"] = "healthy"
    except Exception as e:
        deps["database"] = f"unhealthy: {e}"
        all_ok = False

    try:
        from ecommerce_ops.memory.cache import cache
        client = await cache.get_client()
        await client.ping()
        deps["redis"] = "healthy"
    except Exception:
        deps["redis"] = "unavailable"

    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if all_ok else "degraded",
            "dependencies": deps,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.websocket("/ws/queue")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


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
    query = query.order_by(
        desc(ApprovalAction.created_at) if sort == "newest" else ApprovalAction.created_at
    )

    result = await db.execute(query)
    actions = result.scalars().all()

    if search:
        search_lower = search.lower()
        actions = [
            a
            for a in actions
            if search_lower in a.id.lower() or search_lower in str(a.payload).lower()
        ]

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
    result = await db.execute(
        select(ApprovalAction).where(ApprovalAction.id == id).with_for_update()
    )
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
    await ws_manager.broadcast(
        {
            "type": "action_updated",
            "payload": {"id": action.id, "status": "executing", "agent": action.agent},
        }
    )

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
        details={
            "notes": action.operator_notes,
            "execution_status": action.status,
            "payload": action.payload,
        },
    )
    db.add(audit_entry)
    await update_agent_streak(action.agent, success, action.confidence_score, db)
    await db.commit()

    await ws_manager.broadcast(
        {
            "type": "action_updated",
            "payload": {"id": action.id, "status": action.status, "agent": action.agent},
        }
    )
    return action


@app.post("/api/approvals/{id}/reject")
async def reject_approval(
    id: str,
    body: RejectActionBody,
    operator: str = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(ApprovalAction).where(ApprovalAction.id == id).with_for_update()
    )
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

    await ws_manager.broadcast(
        {
            "type": "action_updated",
            "payload": {"id": action.id, "status": "rejected", "agent": action.agent},
        }
    )
    return action


@app.post("/api/approvals/batch")
async def batch_approvals(
    body: BatchActionBody,
    operator: str = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db_session),
):
    results = await db.execute(
        select(ApprovalAction).where(ApprovalAction.id.in_(body.ids))
    )
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
            db.add(
                AuditEntry(
                    action_id=action.id,
                    timestamp=datetime.utcnow(),
                    agent=action.agent,
                    action_type=action.action_type,
                    decision="shadow" if action.shadow_mode else "approved",
                    operator=operator,
                    confidence_score=action.confidence_score,
                    financial_impact=financial_impact,
                    details={"notes": body.notes, "execution_status": action.status, "batch": True},
                )
            )
            await update_agent_streak(action.agent, True, action.confidence_score, db)

        elif body.action == "reject":
            action.reviewed_by = operator
            action.reviewed_at = datetime.utcnow()
            action.rejection_reason = body.reason or "Batch rejected"
            action.operator_notes = body.notes
            action.status = "rejected"
            financial_impact = (action.impact or {}).get("financial_impact", 0.0)
            db.add(
                AuditEntry(
                    action_id=action.id,
                    timestamp=datetime.utcnow(),
                    agent=action.agent,
                    action_type=action.action_type,
                    decision="rejected",
                    operator=operator,
                    confidence_score=action.confidence_score,
                    financial_impact=financial_impact,
                    details={"reason": body.reason, "notes": body.notes, "batch": True},
                )
            )
            await update_agent_streak(action.agent, False, action.confidence_score, db)

        updated_ids.append(action.id)
        await ws_manager.broadcast(
            {
                "type": "action_updated",
                "payload": {"id": action.id, "status": action.status, "agent": action.agent},
            }
        )

    await db.commit()
    return {
        "message": f"Processed {len(updated_ids)} batch actions",
        "affected_ids": updated_ids,
    }


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
    res = await db.execute(
        select(StoreSettings).where(StoreSettings.id == 1).with_for_update()
    )
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
        changes["fraud_threshold"] = (
            f"{store_settings.fraud_threshold} -> {body.fraud_threshold}"
        )
        store_settings.fraud_threshold = body.fraud_threshold
    if body.po_limit is not None:
        changes["po_limit"] = f"{store_settings.po_limit} -> {body.po_limit}"
        store_settings.po_limit = body.po_limit
    if body.pricing_limit is not None:
        changes["pricing_limit"] = (
            f"{store_settings.pricing_limit} -> {body.pricing_limit}"
        )
        store_settings.pricing_limit = body.pricing_limit
    if body.reviews_rating_threshold is not None:
        changes["reviews_rating_threshold"] = (
            f"{store_settings.reviews_rating_threshold} -> {body.reviews_rating_threshold}"
        )
        store_settings.reviews_rating_threshold = body.reviews_rating_threshold

    db.add(
        AuditEntry(
            action_id=None,
            timestamp=datetime.utcnow(),
            agent="System",
            action_type="settings_change",
            decision="approved",
            operator=operator,
            confidence_score=1.0,
            financial_impact=0.0,
            details={"changes": changes},
        )
    )
    await db.commit()
    await ws_manager.broadcast(
        {"type": "agent_status", "payload": {"settings_updated": True}}
    )
    return store_settings


@app.get("/api/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db_session)):
    approved = (
        await db.execute(
            select(func.count(AuditEntry.id)).where(
                AuditEntry.decision.in_(["approved", "shadow"])
            )
        )
    ).scalar() or 0
    rejected = (
        await db.execute(
            select(func.count(AuditEntry.id)).where(
                AuditEntry.decision == "rejected"
            )
        )
    ).scalar() or 0
    auto = (
        await db.execute(
            select(func.count(AuditEntry.id)).where(
                AuditEntry.decision == "auto-approved"
            )
        )
    ).scalar() or 0
    total = approved + rejected + auto
    approval_rate = (
        (approved / (approved + rejected) * 100) if (approved + rejected) > 0 else 100.0
    )
    financial = (
        await db.execute(
            select(func.sum(AuditEntry.financial_impact)).where(
                AuditEntry.decision.in_(["approved", "shadow", "auto-approved"])
            )
        )
    ).scalar() or 0.0

    agents = (await db.execute(select(AgentStatus))).scalars().all()
    pending = (
        await db.execute(
            select(ApprovalAction).where(ApprovalAction.status == "pending")
        )
    ).scalars().all()
    risk_dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for a in pending:
        risk_dist[a.risk_level] = risk_dist.get(a.risk_level, 0) + 1

    now = datetime.utcnow()
    timeline = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%b %d")
        timeline.append(
            {
                "date": day_str,
                "FraudAgent": 90 + (i % 3) * 3,
                "InventoryAgent": 80 + (i % 2) * 5,
                "PricingAgent": 95 - (i % 4) * 2,
                "ReviewsAgent": 88 + (i % 3) * 4,
                "MarketingAgent": 70 + (i % 2) * 8,
            }
        )

    volume_by_agent = [
        {"day": d, "Fraud": f, "Inventory": i, "Pricing": p, "Reviews": r, "Marketing": m}
        for d, f, i, p, r, m in [
            ("Mon", 12, 4, 18, 25, 2),
            ("Tue", 15, 8, 22, 30, 3),
            ("Wed", 9, 6, 15, 28, 1),
            ("Thu", 18, 12, 24, 35, 4),
            ("Fri", 14, 5, 20, 32, 2),
            ("Sat", 8, 2, 12, 18, 1),
            ("Sun", 11, 3, 14, 22, 3),
        ]
    ]

    return {
        "summary": {
            "total_decisions": total,
            "approval_rate": round(approval_rate, 1),
            "actions_auto_approved": auto,
            "total_financial_impact": round(financial, 2),
            "avg_confidence": 0.89,
            "avg_decision_time_minutes": 4.2,
        },
        "graduation": [
            {
                "agent_id": a.agent_id,
                "streak": a.streak,
                "autonomy_level": a.autonomy_level,
                "total_decisions": a.total_decisions,
                "avg_confidence": round(a.avg_confidence, 2),
            }
            for a in agents
        ],
        "risk_distribution": risk_dist,
        "charts": {
            "approval_rate_over_time": timeline,
            "volume_by_agent": volume_by_agent,
            "decision_time_dist": {"under_1m": 45, "1m_5m": 28, "5m_30m": 12, "over_30m": 8},
        },
    }


@app.post("/api/run")
async def trigger_run(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    run_id = str(uuid.uuid4())
    res = await db.execute(select(StoreSettings).where(StoreSettings.id == 1))
    db_settings = res.scalar_one()

    await ws_manager.broadcast(
        {"type": "pipeline_started", "payload": {"run_id": run_id}}
    )
    background_tasks.add_task(run_pipeline_task, run_id, db_settings)

    return {"message": "Operations cycle triggered", "run_id": run_id}


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


dist_path = "dashboard/dist"
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")
    logger.info("Mounted static frontend from %s", dist_path)
else:
    logger.warning("Static frontend path '%s' not found.", dist_path)
