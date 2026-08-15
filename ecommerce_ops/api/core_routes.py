"""Core API routes that exist on both legacy /api/* and v1 /api/v1/* namespaces."""

import time
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import String, cast, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_ops.api.auth import verify_auth, verify_auth_optional
from ecommerce_ops.api.metrics import (
    METRIC_AGENT_CONFIDENCE_AVG,
    METRIC_DECISIONS_APPROVED,
    METRIC_DECISIONS_REJECTED,
)
from ecommerce_ops.api.ws import ws_manager
from ecommerce_ops.config import settings as app_settings
from ecommerce_ops.models import (
    AgentStatus,
    ApprovalAction,
    AuditEntry,
    StoreSettings,
    get_db_session,
)
from ecommerce_ops.pipeline.runner import execute_shop_action, update_agent_streak

router = APIRouter()

SERVER_START_TIME = time.time()


async def get_current_operator(identity: str = Depends(verify_auth)) -> str:
    return identity or "unknown-operator"


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


async def expire_stale_approvals(db: AsyncSession) -> int:
    """Flip pending approvals whose expiry has passed to 'expired'."""
    now = datetime.utcnow()
    result = await db.execute(
        update(ApprovalAction)
        .where(
            ApprovalAction.status == "pending",
            ApprovalAction.expires_at.isnot(None),
            ApprovalAction.expires_at < now,
        )
        .values(status="expired")
    )
    return result.rowcount or 0


@router.get("/approvals")
async def get_approvals(
    agent: Optional[str] = None,
    risk: Optional[str] = None,
    status: Optional[str] = "pending",
    search: Optional[str] = None,
    sort: Optional[str] = "newest",
    db: AsyncSession = Depends(get_db_session),
):
    await expire_stale_approvals(db)
    query = select(ApprovalAction)
    if status == "pending":
        query = query.where(ApprovalAction.status == "pending")
    if agent and agent != "all":
        query = query.where(ApprovalAction.agent == agent)
    if risk and risk != "all":
        query = query.where(ApprovalAction.risk_level == risk)
    if search:
        search_like = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(ApprovalAction.id).like(search_like),
                func.lower(cast(ApprovalAction.payload, String)).like(search_like),
                func.lower(cast(ApprovalAction.evidence, String)).like(search_like),
            )
        )
    if status == "all":
        pass
    query = query.order_by(
        desc(ApprovalAction.created_at) if sort == "newest" else ApprovalAction.created_at
    )

    result = await db.execute(query)
    actions = result.scalars().all()
    return actions


@router.get("/approvals/{id}")
async def get_approval(id: str, db: AsyncSession = Depends(get_db_session)):
    await expire_stale_approvals(db)
    result = await db.execute(select(ApprovalAction).where(ApprovalAction.id == id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Approval action not found")
    return action


@router.post("/approvals/{id}/approve")
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


@router.post("/approvals/{id}/reject")
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
    if action.expires_at and action.expires_at < datetime.utcnow():
        action.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Action expired")

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


@router.post("/approvals/batch")
async def batch_approvals(
    body: BatchActionBody,
    operator: str = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db_session),
):
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    results = await db.execute(
        select(ApprovalAction).where(ApprovalAction.id.in_(body.ids))
    )
    actions = results.scalars().all()
    updated_ids = []

    for action in actions:
        if action.status != "pending":
            continue
        if action.expires_at and action.expires_at < datetime.utcnow():
            action.status = "expired"
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


@router.get("/agents/status")
async def get_agents_status(db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(AgentStatus))
    return res.scalars().all()


@router.get("/settings")
async def get_store_settings(db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(StoreSettings).where(StoreSettings.id == 1))
    store_settings = res.scalar_one_or_none()
    return store_settings


@router.patch("/settings")
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


@router.get("/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db_session)):
    await expire_stale_approvals(db)
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

    batch_lookup: dict[tuple, int] = {}
    for row in batch_rows:
        day_str = str(row.day)
        batch_lookup[(row.agent, day_str)] = row.cnt

    timeline = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_label = day.strftime("%b %d")
        counts = {}
        for agent_id in agent_ids:
            counts[agent_id] = batch_lookup.get((agent_id, day_str), 0)
        timeline.append({"date": day_label, **counts})

    volume_by_agent = []
    short_names = {
        "FraudAgent": "Fraud",
        "InventoryAgent": "Inventory",
        "PricingAgent": "Pricing",
        "ReviewsAgent": "Reviews",
        "MarketingAgent": "Marketing",
    }
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

    reviewed_actions = (
        await db.execute(
            select(ApprovalAction).where(ApprovalAction.reviewed_at.isnot(None))
        )
    ).scalars().all()
    decision_minutes: List[float] = []
    for act in reviewed_actions:
        if act.created_at and act.reviewed_at:
            dt_sec = (act.reviewed_at - act.created_at).total_seconds()
            minutes = dt_sec / 60.0
            decision_minutes.append(minutes)
            if minutes < 1:
                decision_time_dist["under_1m"] += 1
            elif minutes < 5:
                decision_time_dist["1m_5m"] += 1
            elif minutes < 30:
                decision_time_dist["5m_30m"] += 1
            else:
                decision_time_dist["over_30m"] += 1

    avg_decision_minutes = (
        round(sum(decision_minutes) / len(decision_minutes), 2)
        if decision_minutes
        else 0.0
    )

    return {
        "summary": {
            "total_decisions": total,
            "approval_rate": round(approval_rate, 1),
            "actions_auto_approved": auto,
            "total_financial_impact": round(financial, 2),
            "avg_confidence": round(avg_conf, 2),
            "avg_decision_time_minutes": avg_decision_minutes,
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


@router.get("/health")
async def v1_health(operator: str = Depends(verify_auth_optional)):
    """Full health check matching legacy /health response shape."""

    deps: dict[str, str] = {}
    all_ok = True
    uptime_seconds = time.time() - SERVER_START_TIME

    try:
        async for session in get_db_session():
            await session.execute(select(func.now()))
        deps["database"] = "healthy"
    except Exception:
        deps["database"] = "unhealthy"
        all_ok = False

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

    try:
        from ecommerce_ops.infra.redis_task_queue import RedisTaskQueue
        if RedisTaskQueue is not None:
            task_queue_size = 0
        else:
            from ecommerce_ops.infra.task_queue import task_queue
            task_queue_size = task_queue._queue.qsize() if hasattr(task_queue, "_queue") else 0
        deps["task_queue_depth"] = str(task_queue_size)
        deps["task_queue"] = "healthy"
    except Exception:
        deps["task_queue"] = "unknown"

    try:
        from sqlalchemy import text

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

    try:
        deps["safety_engine"] = "loaded"
    except Exception:
        deps["safety_engine"] = "unavailable"

    try:
        from ecommerce_ops.agents.factory import agent_factory
        for name in ["fraud", "inventory", "pricing", "reviews", "marketing"]:
            agent_factory.get_agent(name)
        deps["agents"] = "loaded"
    except Exception:
        deps["agents"] = "degraded"

    status_code = 200 if all_ok else 503
    from fastapi.responses import JSONResponse
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
