import os
import uuid
import time
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy import select, func, desc, update, text
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
from ecommerce_ops.api.auth import verify_auth, verify_auth_optional
from ecommerce_ops.api.ws import ws_manager
from ecommerce_ops.api.metrics import (
    METRIC_HTTP_REQUESTS,
    METRIC_HTTP_DURATION,
    METRIC_DECISIONS_APPROVED,
    METRIC_DECISIONS_REJECTED,
    METRIC_DECISIONS_AUTO_APPROVED,
    METRIC_AGENT_CONFIDENCE_AVG,
)
from ecommerce_ops.pipeline.runner import run_pipeline_task, execute_shop_action, update_agent_streak
from ecommerce_ops.infra.task_queue import TaskQueue
from ecommerce_ops.infra.browser_pool import browser_pool
from ecommerce_ops.api.shopify import router as shopify_router
from ecommerce_ops.api.cart_recovery import router as cart_recovery_router
from ecommerce_ops.api.customer_support import router as customer_support_router
from ecommerce_ops.api.observability import router as observability_router
from ecommerce_ops.api.memory import router as memory_router
from ecommerce_ops.api.security import router as security_router
from ecommerce_ops.api.demo import router as demo_router
from ecommerce_ops.security.auth import AuthenticationMiddleware
from ecommerce_ops.security.role_manager import role_manager
from ecommerce_ops.observability.tracing_otel import init_tracing, instrument_app
from ecommerce_ops.api.versioning import APIVersionMiddleware, create_v1_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecommerce_ops.api")


task_queue = TaskQueue(num_workers=2, max_queue_size=100)
SERVER_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await task_queue.start()
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

    try:
        await browser_pool.start()
        logger.info("Browser pool initialized.")
    except Exception as e:
        logger.warning("Browser pool initialization failed (scraping will fall back): %s", e)

    if supervisor_ok:
        logger.info("Application fully initialized and ready.")
    else:
        logger.warning("Application started without Supervisor — /api/run will fail.")

    yield

    await task_queue.stop(wait=True)
    await browser_pool.stop()
    from ecommerce_ops.memory.cache import cache
    await cache.close()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="OpsIQ — Autonomous Ecommerce Operations Engine",
    description="""
## OpsIQ — AI-Powered Ecommerce Operations

OpsIQ is an autonomous multi-agent system that manages ecommerce operations including:

- **Fraud Detection** — LLM-powered risk assessment with rule-based fallback
- **Inventory Management** — Demand forecasting and automated reorder
- **Price Optimization** — Competitor price monitoring and dynamic pricing
- **Review Moderation** — Sentiment analysis and response drafting
- **Marketing Automation** — Campaign creation and audience segmentation

### Architecture
- **7 AI Agents** with LLM-first, rule-based fallback
- **PostgreSQL** for persistent storage (RBAC, audit, vector memory)
- **Redis** for caching, rate limiting, and session management
- **LangGraph** for agent orchestration and supervisor pattern
- **Prometheus + Grafana** for monitoring and alerting

### Security
- Role-Based Access Control (RBAC) with 5 roles
- API key authentication with SHA-256 hashing
- Audit logging for all security events
- Rate limiting with Redis sliding window
- Input sanitization and security headers
    """,
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "Health", "description": "Health checks and readiness probes"},
        {"name": "Pipeline", "description": "Pipeline trigger and task management"},
        {"name": "Approvals", "description": "Human-in-the-loop approval queue"},
        {"name": "Audit", "description": "Audit log queries and export"},
        {"name": "Analytics", "description": "Analytics and reporting"},
        {"name": "Agents", "description": "Agent status and configuration"},
        {"name": "Settings", "description": "Store settings management"},
        {"name": "Observability", "description": "Traces, evaluations, and metrics"},
        {"name": "Memory", "description": "Vector memory and session management"},
        {"name": "Security", "description": "RBAC, API keys, and security management"},
        {"name": "Shopify", "description": "Shopify integration and webhooks"},
        {"name": "Cart Recovery", "description": "Abandoned cart recovery automation"},
        {"name": "Customer Support", "description": "AI-powered customer support"},
    ],
)

setup_middleware(app)

# Instrument FastAPI with OpenTelemetry (before auth middleware)
otel_provider = init_tracing()
instrument_app(app)

# Authentication middleware (after all other middleware)
app.add_middleware(AuthenticationMiddleware)

# Include Shopify routes
app.include_router(shopify_router)

# Include Cart Recovery routes
app.include_router(cart_recovery_router)

# Include Customer Support routes
app.include_router(customer_support_router)

# Include Observability routes
app.include_router(observability_router)

# Include Memory routes
app.include_router(memory_router)

# Include Security routes
app.include_router(security_router)

# Include Demo routes
app.include_router(demo_router)

# ── API Versioning: /api/v1/ routes + deprecation headers ──
v1_router = create_v1_router(
    shopify_router, cart_recovery_router, customer_support_router,
    observability_router, memory_router, security_router, demo_router,
)
app.include_router(v1_router)
app.add_middleware(APIVersionMiddleware)


class LoginBody(BaseModel):
    api_key: str
    operator_id: Optional[str] = None


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
    slack_channel: Optional[str] = None
    notify_on_failure: Optional[bool] = None
    notify_on_hitl: Optional[bool] = None
    notify_on_graduation: Optional[bool] = None


async def get_current_operator(identity: str = Depends(verify_auth)) -> str:
    return identity or "unknown-operator"


@app.post("/api/auth/login")
async def login(body: LoginBody):
    import hmac
    api_key_setting = app_settings.API_KEY
    valid_key = api_key_setting.get_secret_value() if api_key_setting else ""

    if not valid_key or not body.api_key or not hmac.compare_digest(body.api_key, valid_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {
        "status": "ok",
        "operator": body.operator_id or "api-operator",
    }


@app.get("/health")
async def health(operator: str = Depends(verify_auth_optional)):
    deps: dict[str, str] = {}
    all_ok = True
    uptime_seconds = time.time() - SERVER_START_TIME

    # Database check
    try:
        async for session in get_db_session():
            await session.execute(select(func.now()))
        deps["database"] = "healthy"
    except Exception as e:
        deps["database"] = "unhealthy"
        all_ok = False

    # Redis check
    try:
        from ecommerce_ops.memory.cache import cache
        client = await cache.get_client()
        if client:
            await client.ping()
            deps["redis"] = "healthy"
        else:
            deps["redis"] = "unavailable"
            all_ok = False
    except Exception:
        deps["redis"] = "unavailable"
        all_ok = False

    # Task queue check
    try:
        task_queue_size = task_queue._queue.qsize() if hasattr(task_queue, "_queue") else 0
        deps["task_queue_depth"] = str(task_queue_size)
        deps["task_queue"] = "healthy"
    except Exception:
        deps["task_queue"] = "unknown"

    # pgvector check
    try:
        from ecommerce_ops.memory.vector.persistent_store import PersistentVectorStore
        from ecommerce_ops.models import async_session_factory
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            if result.fetchone():
                deps["pgvector"] = "healthy"
            else:
                deps["pgvector"] = "not installed"
    except Exception:
        deps["pgvector"] = "unavailable"

    # Safety engine check
    try:
        from ecommerce_ops.safety.safety_rules import evaluate_action_safety
        deps["safety_engine"] = "loaded"
    except Exception:
        deps["safety_engine"] = "unavailable"

    # Agent status check
    try:
        from ecommerce_ops.agents.factory import agent_factory
        for name in ["fraud", "inventory", "pricing", "reviews", "marketing"]:
            agent_factory.get_agent(name)
        deps["agents"] = "loaded"
    except Exception:
        deps["agents"] = "degraded"

    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if all_ok else "degraded",
            "dependencies": deps,
            "uptime_seconds": uptime_seconds,
            "version": app_settings.PROJECT_NAME,
            "version_number": "0.2.0",
            "environment": app_settings.ENV.value if hasattr(app_settings.ENV, "value") else str(app_settings.ENV),
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": deps.get("database", "unknown"),
                "redis": deps.get("redis", "unknown"),
                "pgvector": deps.get("pgvector", "unknown"),
                "task_queue": deps.get("task_queue", "unknown"),
                "agents": deps.get("agents", "unknown"),
            },
        },
    )


@app.websocket("/ws/queue")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """Authenticated WebSocket endpoint for real-time events.

    Auth: Pass API key as query param ?token=<api-key>
    Browser WS API cannot send custom headers, so query param is the standard approach.
    """
    from ecommerce_ops.api.ws import (
        CLOSE_AUTH_FAILED,
        CLOSE_RATE_LIMITED,
    )

    conn = await ws_manager.connect(websocket, token=token)
    if conn is None:
        # Connection was rejected (auth failed, rate limited, or at capacity)
        return

    try:
        while True:
            data = await websocket.receive_text()
            # Rate limit check
            if not conn.check_rate_limit():
                await websocket.send_json({"type": "error", "payload": {"code": "rate_limited"}})
                await websocket.close(code=CLOSE_RATE_LIMITED, reason="Rate limit exceeded")
                break
            # Respond to ping
            try:
                import json
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except (json.JSONDecodeError, ValueError):
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("WS error for %s: %s", conn.operator, e)
    finally:
        await ws_manager.disconnect(conn)


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

    METRIC_DECISIONS_APPROVED.labels(agent=action.agent).inc()
    METRIC_AGENT_CONFIDENCE_AVG.labels(agent=action.agent).set(action.confidence_score)

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

    METRIC_DECISIONS_REJECTED.labels(agent=action.agent).inc()
    METRIC_AGENT_CONFIDENCE_AVG.labels(agent=action.agent).set(action.confidence_score)

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
        if not (0 <= body.fraud_threshold <= 100):
            raise HTTPException(status_code=400, detail="fraud_threshold must be 0-100")
        changes["fraud_threshold"] = f"{store_settings.fraud_threshold} -> {body.fraud_threshold}"
        store_settings.fraud_threshold = body.fraud_threshold
    if body.po_limit is not None:
        if body.po_limit <= 0:
            raise HTTPException(status_code=400, detail="po_limit must be positive")
        changes["po_limit"] = f"{store_settings.po_limit} -> {body.po_limit}"
        store_settings.po_limit = body.po_limit
    if body.pricing_limit is not None:
        if not (0 < body.pricing_limit <= 100):
            raise HTTPException(status_code=400, detail="pricing_limit must be 0-100")
        changes["pricing_limit"] = f"{store_settings.pricing_limit} -> {body.pricing_limit}"
        store_settings.pricing_limit = body.pricing_limit
    if body.reviews_rating_threshold is not None:
        if not (1 <= body.reviews_rating_threshold <= 5):
            raise HTTPException(status_code=400, detail="reviews_rating_threshold must be 1-5")
        changes["reviews_rating_threshold"] = f"{store_settings.reviews_rating_threshold} -> {body.reviews_rating_threshold}"
        store_settings.reviews_rating_threshold = body.reviews_rating_threshold
    if body.slack_channel is not None:
        changes["slack_channel"] = body.slack_channel

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
    day_start_7d = datetime(now.year, now.month, now.day) - timedelta(days=6)

    agent_ids = ["FraudAgent", "InventoryAgent", "PricingAgent", "ReviewsAgent", "MarketingAgent"]

    # Batch query: counts per agent per day (single query instead of 35)
    batch_result = await db.execute(
        select(
            AuditEntry.agent,
            func.date(AuditEntry.timestamp).label("day"),
            func.count(AuditEntry.id).label("cnt"),
        )
        .where(
            AuditEntry.timestamp >= day_start_7d,
            AuditEntry.agent.in_(agent_ids),
        )
        .group_by(AuditEntry.agent, func.date(AuditEntry.timestamp))
    )
    batch_rows = batch_result.all()

    # Build lookup: {(agent, day_str): count}
    batch_lookup: dict[tuple, int] = {}
    for row in batch_rows:
        day_str = str(row.day)
        batch_lookup[(row.agent, day_str)] = row.cnt

    # Build timeline
    timeline = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_label = day.strftime("%b %d")
        counts = {}
        for agent_id in agent_ids:
            counts[agent_id] = batch_lookup.get((agent_id, day_str), 0)
        timeline.append({"date": day_label, **counts})

    # Build volume_by_agent
    volume_by_agent = []
    short_names = {"FraudAgent": "Fraud", "InventoryAgent": "Inventory", "PricingAgent": "Pricing", "ReviewsAgent": "Reviews", "MarketingAgent": "Marketing"}
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        vol = {"day": day.strftime("%a")}
        for agent_id, short in short_names.items():
            vol[short] = batch_lookup.get((agent_id, day_str), 0)
        volume_by_agent.append(vol)

    avg_conf = 0.0
    if agents:
        avg_conf = sum(a.avg_confidence for a in agents) / len(agents)

    decision_time_dist = {"under_1m": 0, "1m_5m": 0, "5m_30m": 0, "over_30m": 0}

    return {
        "summary": {
            "total_decisions": total,
            "approval_rate": round(approval_rate, 1),
            "actions_auto_approved": auto,
            "total_financial_impact": round(financial, 2),
            "avg_confidence": round(avg_conf, 2),
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
            "decision_time_dist": decision_time_dist,
        },
    }


@app.get("/api/audit/export")
async def export_audit_logs(
    format: str = "csv",
    db: AsyncSession = Depends(get_db_session),
):
    entries = (await db.execute(
        select(AuditEntry).order_by(desc(AuditEntry.timestamp)).limit(10000)
    )).scalars().all()

    if format == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Timestamp", "Agent", "Action Type", "Decision", "Operator", "Confidence", "Financial Impact", "Details"])
        for e in entries:
            writer.writerow([
                e.action_id, e.timestamp.isoformat(), e.agent, e.action_type,
                e.decision, e.operator, e.confidence_score, e.financial_impact, str(e.details),
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
        )

    return {"entries": [{
        "action_id": e.action_id, "timestamp": e.timestamp.isoformat(),
        "agent": e.agent, "action_type": e.action_type, "decision": e.decision,
        "operator": e.operator, "confidence": e.confidence_score,
        "financial_impact": e.financial_impact, "details": e.details,
    } for e in entries]}


@app.get("/ready")
async def readiness():
    """Kubernetes-style readiness probe — checks critical deps only."""
    try:
        async for session in get_db_session():
            await session.execute(select(func.now()))
        db_ok = True
    except Exception:
        db_ok = False

    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={"status": "ready" if db_ok else "not ready", "database": "ok" if db_ok else "down"},
    )


@app.get("/live")
async def liveness():
    """Kubernetes-style liveness probe."""
    return JSONResponse(status_code=200, content={"status": "alive"})


@app.get("/api/ws/stats")
async def ws_stats(
    operator: str = Depends(verify_auth),
):
    """WebSocket connection statistics (requires auth)."""
    return ws_manager.get_stats()


@app.post("/api/run")
async def trigger_run(
    db: AsyncSession = Depends(get_db_session),
):
    run_id = str(uuid.uuid4())
    res = await db.execute(select(StoreSettings).where(StoreSettings.id == 1))
    db_settings = res.scalar_one_or_none()
    if not db_settings:
        db_settings = StoreSettings(
            id=1, shadow_mode=True, fraud_threshold=70,
            po_limit=1000.0, pricing_limit=5.0, reviews_rating_threshold=4,
        )
        db.add(db_settings)
        await db.commit()

    await ws_manager.broadcast(
        {"type": "pipeline_started", "payload": {"run_id": run_id}}
    )
    await task_queue.enqueue("pipeline", run_pipeline_task, run_id, db_settings)

    return {"message": "Operations cycle triggered", "run_id": run_id}


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "name": task.name,
        "status": task.status.value,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


dist_path = "dashboard/dist"
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")
    logger.info("Mounted static frontend from %s", dist_path)
else:
    logger.warning("Static frontend path '%s' not found.", dist_path)
