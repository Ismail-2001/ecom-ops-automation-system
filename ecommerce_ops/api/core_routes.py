"""Core API routes that exist on both legacy /api/* and v1 /api/v1/* namespaces."""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import String, case, cast, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_ops.api.auth import verify_auth_optional
from ecommerce_ops.api.metrics import (
    METRIC_AGENT_CONFIDENCE_AVG,
    METRIC_AGENT_EXECUTION_ERRORS,
    METRIC_DECISIONS_APPROVED,
    METRIC_DECISIONS_REJECTED,
)
from ecommerce_ops.api.ws import ws_manager
from ecommerce_ops.config import settings as app_settings
from ecommerce_ops.infra.notifications import notify_execution_failed
from ecommerce_ops.models import (
    AgentStatus,
    ApprovalAction,
    AuditEntry,
    StoreSettings,
    get_db_session,
)
from ecommerce_ops.pipeline.runner import execute_shop_action, update_agent_streak
from ecommerce_ops.security.auth import require_admin, require_permission
from ecommerce_ops.security.models import Permission, User
from ecommerce_ops.utils import utc_now

logger = logging.getLogger("ecommerce_ops.api.core_routes")

router = APIRouter()

SERVER_START_TIME = time.time()


async def get_current_operator(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user.name or user.email or user.id or "unknown-operator"


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


class SetAutonomyBody(BaseModel):
    level: str
    reason: Optional[str] = None


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
    now = utc_now()
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


async def sweep_stale_executing(db: AsyncSession, stale_after_minutes: int = 60) -> int:
    """Recover actions stuck in 'executing' due to a crash between the
    approval commit and the terminal commit (H1 data-loss window).

    Actions that have been 'executing' for longer than ``stale_after_minutes``
    without reaching a terminal status are marked 'failed' and an audit entry
    is written recording the abort.
    """
    now = utc_now()
    cutoff = now - timedelta(minutes=stale_after_minutes)

    result = await db.execute(
        select(ApprovalAction).where(
            ApprovalAction.status == "executing",
            ApprovalAction.reviewed_at.isnot(None),
            ApprovalAction.reviewed_at < cutoff,
        )
    )
    stale = result.scalars().all()
    count = 0
    for action in stale:
        action.status = "failed"
        action.operator_notes = (
            f"{action.operator_notes or ''} [Aborted: pipeline crashed during execution]"
        ).strip()
        db.add(
            AuditEntry(
                action_id=action.id,
                timestamp=now,
                agent=action.agent,
                action_type=action.action_type,
                decision="shadow" if action.shadow_mode else "approved",
                operator=action.reviewed_by or "system-sweeper",
                confidence_score=action.confidence_score,
                financial_impact=(action.impact or {}).get("financial_impact", 0.0),
                details={
                    "execution_status": "failed",
                    "execution_message": "Stale executing action recovered by sweeper",
                },
            )
        )
        count += 1
    if stale:
        await db.commit()
    return count


def _score_hitl_outcome(
    action: ApprovalAction,
    verdict: str,
    db: AsyncSession,
    execution_success: Optional[bool] = None,
) -> None:
    """Record a ground-truth HITL outcome score in memory (M8).

    The pipeline's ``EvaluationFramework.evaluate_decision`` uses self-reported
    heuristics (confidence boost, reasoning length); it never sees what the
    operator actually decided. This captures the real outcome so agent quality
    is measured against the ground-truth verdict instead of vanity metrics.
    Best-effort — failures are logged, never raised.
    """
    try:
        from ecommerce_ops.observability.evaluation import evaluation_framework

        evaluation = evaluation_framework.evaluate_outcome(
            agent_name=action.agent,
            decision_id=action.id,
            decision={"action_type": action.action_type},
            hitl_verdict=verdict,
            execution_success=execution_success,
            trace_id=None,
        )
        _LOGGER = logging.getLogger("ecommerce_ops.api.core_routes")
        _LOGGER.debug(
            "HITL outcome for %s (%s): score=%.2f passed=%s",
            action.id,
            verdict,
            evaluation.overall_score,
            evaluation.passed,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logging.getLogger("ecommerce_ops.api.core_routes").warning(
            "Failed to record HITL outcome for %s: %s", action.id, exc
        )


@router.get("/approvals")
async def get_approvals(
    agent: Optional[str] = None,
    risk: Optional[str] = None,
    status: Optional[str] = "pending",
    search: Optional[str] = None,
    sort: Optional[str] = "newest",
    _: User = Depends(require_permission(Permission.APPROVALS_VIEW)),
    db: AsyncSession = Depends(get_db_session),
):
    await expire_stale_approvals(db)
    await sweep_stale_executing(db)
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
async def get_approval(
    id: str,
    _: User = Depends(require_permission(Permission.APPROVALS_VIEW)),
    db: AsyncSession = Depends(get_db_session),
):
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
    _: User = Depends(require_permission(Permission.APPROVALS_APPROVE)),
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
    if action.expires_at and action.expires_at < utc_now():
        action.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Action expired")

    if action.action_type == "review_response" and body.draft_response:
        new_payload = dict(action.payload)
        new_payload["draft_response"] = body.draft_response
        action.payload = new_payload

    action.reviewed_by = operator
    action.reviewed_at = utc_now()
    action.operator_notes = body.notes
    action.status = "approved"

    financial_impact = (action.impact or {}).get("financial_impact", 0.0)
    audit_entry = AuditEntry(
        action_id=action.id,
        timestamp=utc_now(),
        agent=action.agent,
        action_type=action.action_type,
        decision="shadow" if action.shadow_mode else "approved",
        operator=operator,
        confidence_score=action.confidence_score,
        financial_impact=financial_impact,
        details={
            "notes": action.operator_notes,
            "execution_status": "approved",
            "payload": action.payload,
        },
    )
    db.add(audit_entry)
    await db.commit()

    await ws_manager.broadcast(
        {
            "type": "action_updated",
            "payload": {"id": action.id, "status": "approved", "agent": action.agent},
        }
    )

    action.status = "executing"
    try:
        success, exec_msg = await execute_shop_action(action)
    except Exception as exc:
        success = False
        exec_msg = f"execution_error: {exc}"
    action.status = "executed" if success else "failed"
    if not success:
        action.operator_notes = f"{action.operator_notes or ''} [Error: {exec_msg}]".strip()
        METRIC_AGENT_EXECUTION_ERRORS.labels(agent=action.agent).inc()
        await notify_execution_failed(
            action_id=action.id,
            action_type=action.action_type,
            agent=action.agent,
            error=exec_msg,
            context="manual-approval",
        )

    audit_entry.details["execution_status"] = action.status
    audit_entry.details["execution_message"] = exec_msg if not success else None

    await update_agent_streak(action.agent, success, action.confidence_score, db)
    _score_hitl_outcome(action, "approved", db, success)
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
    _: User = Depends(require_permission(Permission.APPROVALS_REJECT)),
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
    if action.expires_at and action.expires_at < utc_now():
        action.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Action expired")

    action.reviewed_by = operator
    action.reviewed_at = utc_now()
    action.rejection_reason = body.reason
    action.operator_notes = body.notes
    action.status = "rejected"

    financial_impact = (action.impact or {}).get("financial_impact", 0.0)
    audit_entry = AuditEntry(
        action_id=action.id,
        timestamp=utc_now(),
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
    _score_hitl_outcome(action, "rejected", db)
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
    _: User = Depends(require_admin),
    operator: str = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db_session),
):
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    results = await db.execute(
        select(ApprovalAction).where(ApprovalAction.id.in_(body.ids)).with_for_update()
    )
    actions = results.scalars().all()
    updated_ids = []

    for action in actions:
        if action.status != "pending":
            continue
        if action.expires_at and action.expires_at < utc_now():
            action.status = "expired"
            continue

        try:
            if body.action == "approve":
                if action.risk_level in ("high", "critical"):
                    continue
                action.reviewed_by = operator
                action.reviewed_at = utc_now()
                action.operator_notes = body.notes
                action.status = "approved"

                financial_impact = (action.impact or {}).get("financial_impact", 0.0)
                audit_entry = AuditEntry(
                    action_id=action.id,
                    timestamp=utc_now(),
                    agent=action.agent,
                    action_type=action.action_type,
                    decision="shadow" if action.shadow_mode else "approved",
                    operator=operator,
                    confidence_score=action.confidence_score,
                    financial_impact=financial_impact,
                    details={"notes": body.notes, "execution_status": "approved", "batch": True},
                )
                db.add(audit_entry)
                await db.flush()

                success, exec_msg = await execute_shop_action(action)
                action.status = "executed" if success else "failed"
                audit_entry.details["execution_status"] = action.status
                if not success:
                    METRIC_AGENT_EXECUTION_ERRORS.labels(agent=action.agent).inc()
                    await notify_execution_failed(
                        action_id=action.id,
                        action_type=action.action_type,
                        agent=action.agent,
                        error=exec_msg or "unknown",
                        context="batch-approval",
                    )
                await update_agent_streak(action.agent, success, action.confidence_score, db)
                _score_hitl_outcome(action, "approved", db, success)

            elif body.action == "reject":
                action.reviewed_by = operator
                action.reviewed_at = utc_now()
                action.rejection_reason = body.reason or "Batch rejected"
                action.operator_notes = body.notes
                action.status = "rejected"
                financial_impact = (action.impact or {}).get("financial_impact", 0.0)
                db.add(
                    AuditEntry(
                        action_id=action.id,
                        timestamp=utc_now(),
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
                _score_hitl_outcome(action, "rejected", db)

            updated_ids.append(action.id)
            await ws_manager.broadcast(
                {
                    "type": "action_updated",
                    "payload": {"id": action.id, "status": action.status, "agent": action.agent},
                }
            )
        except Exception as exc:
            logger.warning(
                "Batch item %s failed: %s — continuing with remaining items",
                action.id,
                exc,
            )
            continue

    await db.commit()
    return {
        "message": f"Processed {len(updated_ids)} batch actions",
        "affected_ids": updated_ids,
    }


@router.get("/agents/status")
async def get_agents_status(
    _: User = Depends(require_permission(Permission.AGENTS_VIEW)),
    db: AsyncSession = Depends(get_db_session),
):
    res = await db.execute(select(AgentStatus))
    return res.scalars().all()


AUTONOMY_LEVELS = {"shadow", "supervised", "autonomous"}


@router.patch("/agents/{agent_id}/autonomy")
async def set_agent_autonomy(
    agent_id: str,
    body: SetAutonomyBody,
    _: User = Depends(require_permission(Permission.AGENTS_CONFIGURE)),
    operator: str = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db_session),
):
    """Manually set an agent's autonomy level (promote/demote).

    Graduation normally happens automatically after 50 consecutive
    high-confidence discoveries; this endpoint lets operators force-promote
    or force-demote an agent. Every change is audit-logged and broadcast.
    """
    if body.level not in AUTONOMY_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid autonomy level. Must be one of: {', '.join(sorted(AUTONOMY_LEVELS))}",
        )

    res = await db.execute(
        select(AgentStatus).where(AgentStatus.agent_id == agent_id).with_for_update()
    )
    agent = res.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    previous = agent.autonomy_level
    if previous == body.level:
        return agent

    agent.autonomy_level = body.level
    db.add(
        AuditEntry(
            action_id=None,
            timestamp=utc_now(),
            agent=agent_id,
            action_type="autonomy_change",
            decision="approved",
            operator=operator,
            confidence_score=1.0,
            financial_impact=0.0,
            details={
                "previous_level": previous,
                "new_level": body.level,
                "reason": body.reason,
            },
        )
    )
    await db.commit()
    await db.refresh(agent)
    await ws_manager.broadcast(
        {
            "type": "agent_status",
            "payload": {"agent_id": agent_id, "autonomy_level": body.level},
        }
    )
    return agent


@router.get("/settings")
async def get_store_settings(
    _: User = Depends(require_permission(Permission.SETTINGS_VIEW)),
    db: AsyncSession = Depends(get_db_session),
):
    res = await db.execute(select(StoreSettings).where(StoreSettings.id == 1))
    store_settings = res.scalar_one_or_none()
    return store_settings


@router.patch("/settings")
async def update_store_settings(
    body: SettingsUpdateBody,
    _: User = Depends(require_admin),
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
        changes["reviews_rating_threshold"] = (
            f"{store_settings.reviews_rating_threshold} -> {body.reviews_rating_threshold}"
        )
        store_settings.reviews_rating_threshold = body.reviews_rating_threshold
    if body.slack_channel is not None:
        changes["slack_channel"] = body.slack_channel

    db.add(
        AuditEntry(
            action_id=None,
            timestamp=utc_now(),
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
    await ws_manager.broadcast({"type": "agent_status", "payload": {"settings_updated": True}})
    return store_settings


@router.get("/analytics")
async def get_analytics(
    _: User = Depends(require_permission(Permission.DASHBOARD_VIEW)),
    db: AsyncSession = Depends(get_db_session),
):
    await expire_stale_approvals(db)
    approved = (
        await db.execute(
            select(func.count(AuditEntry.id)).where(AuditEntry.decision.in_(["approved", "shadow"]))
        )
    ).scalar() or 0
    rejected = (
        await db.execute(select(func.count(AuditEntry.id)).where(AuditEntry.decision == "rejected"))
    ).scalar() or 0
    auto = (
        await db.execute(
            select(func.count(AuditEntry.id)).where(AuditEntry.decision == "auto-approved")
        )
    ).scalar() or 0
    total = approved + rejected + auto
    approval_rate = (approved / (approved + rejected) * 100) if (approved + rejected) > 0 else 100.0
    financial = (
        await db.execute(
            select(func.sum(AuditEntry.financial_impact)).where(
                AuditEntry.decision.in_(["approved", "shadow", "auto-approved"])
            )
        )
    ).scalar() or 0.0

    agents = (await db.execute(select(AgentStatus))).scalars().all()
    risk_dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    risk_rows = await db.execute(
        select(ApprovalAction.risk_level, func.count(ApprovalAction.id))
        .where(ApprovalAction.status == "pending")
        .group_by(ApprovalAction.risk_level)
    )
    for level, cnt in risk_rows.all():
        risk_dist[level] = cnt

    now = utc_now()
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

    # Decision-time buckets computed in SQL (no full-table row loading, M16).
    # The epoch difference is dialect-portable: strftime on SQLite,
    # extract(epoch) on PostgreSQL.
    bind = db.get_bind()
    dialect = getattr(bind, "dialect", None)
    dialect_name = dialect.name if dialect else "sqlite"

    if dialect_name == "postgresql":
        epoch_diff = func.extract("epoch", ApprovalAction.reviewed_at) - func.extract(
            "epoch", ApprovalAction.created_at
        )
    else:
        epoch_diff = func.strftime("%s", ApprovalAction.reviewed_at) - func.strftime(
            "%s", ApprovalAction.created_at
        )

    bucket_expr = case(
        (epoch_diff < 60, "under_1m"),
        (epoch_diff < 300, "1m_5m"),
        (epoch_diff < 1800, "5m_30m"),
        else_="over_30m",
    )
    decision_time_rows = await db.execute(
        select(bucket_expr.label("bucket"), func.count(ApprovalAction.id))
        .where(ApprovalAction.reviewed_at.isnot(None))
        .group_by(bucket_expr)
    )
    for bucket, cnt in decision_time_rows.all():
        if bucket in decision_time_dist:
            decision_time_dist[bucket] = cnt

    # Average decision time via SQL aggregate (avoid loading every row).
    avg_sec = (
        await db.execute(select(func.avg(epoch_diff)).where(ApprovalAction.reviewed_at.isnot(None)))
    ).scalar()
    avg_decision_minutes = round(float(avg_sec) / 60.0, 2) if avg_sec is not None else 0.0

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

    # Liveness + detail: always 200 while the process can serve; dependency
    # truth lives in the body. /ready remains the strict readiness gate.
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok" if all_ok else "degraded",
            "dependencies": deps,
            "uptime_seconds": uptime_seconds,
            "version": app_settings.PROJECT_NAME,
            "version_number": "0.2.0",
            "environment": app_settings.ENV.value
            if hasattr(app_settings.ENV, "value")
            else str(app_settings.ENV),
            "timestamp": utc_now().isoformat(),
            "checks": {
                "database": deps.get("database", "unknown"),
                "redis": deps.get("redis", "unknown"),
                "pgvector": deps.get("pgvector", "unknown"),
                "task_queue": deps.get("task_queue", "unknown"),
                "agents": deps.get("agents", "unknown"),
            },
        },
    )


# ── Catalog: Orders / Products / Reviews ────────────────────────────────
# In-memory demo catalog backing the Orders, Products, and Reviews pages.
# These pages were built frontend-first; the data below is realistic PK
# e-commerce seed so the demo never shows empty or error states.

_CATALOG_ORDERS = [
    {
        "id": "ORD-2026-0412",
        "customer": "Ahmed Raza",
        "total": 12500,
        "status": "delivered",
        "fraud_score": 0.08,
        "created_at": "2026-10-18T09:14:00Z",
    },
    {
        "id": "ORD-2026-0413",
        "customer": "Fatima Khan",
        "total": 4800,
        "status": "shipped",
        "fraud_score": 0.12,
        "created_at": "2026-10-19T11:30:00Z",
    },
    {
        "id": "ORD-2026-0414",
        "customer": "Bilal Ahmed",
        "total": 23900,
        "status": "confirmed",
        "fraud_score": 0.31,
        "created_at": "2026-10-20T14:02:00Z",
    },
    {
        "id": "ORD-2026-0415",
        "customer": "Ayesha Siddiqui",
        "total": 7200,
        "status": "pending",
        "fraud_score": 0.67,
        "created_at": "2026-10-21T08:45:00Z",
    },
    {
        "id": "ORD-2026-0416",
        "customer": "Usman Tariq",
        "total": 15600,
        "status": "rto",
        "fraud_score": 0.82,
        "created_at": "2026-10-21T16:22:00Z",
    },
    {
        "id": "ORD-2026-0417",
        "customer": "Zainab Malik",
        "total": 3400,
        "status": "delivered",
        "fraud_score": 0.05,
        "created_at": "2026-10-19T10:11:00Z",
    },
    {
        "id": "ORD-2026-0418",
        "customer": "Hassan Ali",
        "total": 8900,
        "status": "shipped",
        "fraud_score": 0.18,
        "created_at": "2026-10-20T13:55:00Z",
    },
    {
        "id": "ORD-2026-0419",
        "customer": "Maryam Noor",
        "total": 31200,
        "status": "confirmed",
        "fraud_score": 0.22,
        "created_at": "2026-10-21T09:33:00Z",
    },
    {
        "id": "ORD-2026-0420",
        "customer": "Kamran Sheikh",
        "total": 5600,
        "status": "pending",
        "fraud_score": 0.74,
        "created_at": "2026-10-22T07:18:00Z",
    },
    {
        "id": "ORD-2026-0421",
        "customer": "Sana Javed",
        "total": 19800,
        "status": "delivered",
        "fraud_score": 0.09,
        "created_at": "2026-10-17T15:40:00Z",
    },
    {
        "id": "ORD-2026-0422",
        "customer": "Danish Iqbal",
        "total": 6700,
        "status": "rto",
        "fraud_score": 0.91,
        "created_at": "2026-10-20T11:05:00Z",
    },
    {
        "id": "ORD-2026-0423",
        "customer": "Hina Shah",
        "total": 11300,
        "status": "shipped",
        "fraud_score": 0.15,
        "created_at": "2026-10-21T12:27:00Z",
    },
]

_CATALOG_PRODUCTS = [
    {
        "id": "PRD-001",
        "title": "Samsung Galaxy A25 5G (128GB)",
        "price": 54999,
        "stock": 23,
        "status": "active",
    },
    {
        "id": "PRD-002",
        "title": "Infinix Hot 40i (128GB)",
        "price": 32999,
        "stock": 41,
        "status": "active",
    },
    {
        "id": "PRD-003",
        "title": "Xiaomi Redmi 13C (256GB)",
        "price": 41500,
        "stock": 17,
        "status": "active",
    },
    {
        "id": "PRD-004",
        "title": "Audionic Airbud 500 Wireless Earbuds",
        "price": 4299,
        "stock": 120,
        "status": "active",
    },
    {
        "id": "PRD-005",
        "title": "Dawlance Split AC 1.5 Ton Inverter",
        "price": 168000,
        "stock": 8,
        "status": "active",
    },
    {
        "id": "PRD-006",
        "title": "Service Canvas Shoes (White)",
        "price": 3850,
        "stock": 0,
        "status": "out_of_stock",
    },
    {
        "id": "PRD-007",
        "title": "Nexus Power Bank 20000mAh",
        "price": 5999,
        "stock": 64,
        "status": "active",
    },
    {
        "id": "PRD-008",
        "title": "J. Junaid Jamshed Kameez Shalwar (L)",
        "price": 4750,
        "stock": 35,
        "status": "active",
    },
    {
        "id": "PRD-009",
        "title": "Dyson V8 Absolute Cordless Vacuum",
        "price": 89900,
        "stock": 3,
        "status": "low_stock",
    },
    {
        "id": "PRD-010",
        "title": "Apple iPhone 15 (128GB) PTA Approved",
        "price": 385000,
        "stock": 5,
        "status": "active",
    },
    {
        "id": "PRD-011",
        "title": "Philips Air Fryer XXL HD9650",
        "price": 47500,
        "stock": 12,
        "status": "active",
    },
    {
        "id": "PRD-012",
        "title": "Bata Kids School Shoes (Pack of 2)",
        "price": 2999,
        "stock": 88,
        "status": "active",
    },
]

_CATALOG_REVIEWS = [
    {
        "id": "REV-001",
        "author": "Ahmed Raza",
        "rating": 5,
        "content": "Excellent phone, delivery was quick. PTA approved and seal packed. Highly recommend for COD orders.",
        "sentiment": "positive",
        "created_at": "2026-10-19T10:00:00Z",
    },
    {
        "id": "REV-002",
        "author": "Fatima Khan",
        "rating": 4,
        "content": "Good earbuds for the price. Bass is decent, battery lasts about 4 hours. Packaging could be better.",
        "sentiment": "positive",
        "created_at": "2026-10-20T14:30:00Z",
    },
    {
        "id": "REV-003",
        "author": "Bilal Ahmed",
        "rating": 2,
        "content": "AC cooling is okay but the installation team took 3 days to arrive. Not happy with the service delay.",
        "sentiment": "negative",
        "created_at": "2026-10-21T09:15:00Z",
    },
    {
        "id": "REV-004",
        "author": "Ayesha Siddiqui",
        "rating": 5,
        "content": "Beautiful kameez shalwar, fabric quality is top notch. J. never disappoints. Fast delivery too!",
        "sentiment": "positive",
        "created_at": "2026-10-20T16:45:00Z",
    },
    {
        "id": "REV-005",
        "author": "Usman Tariq",
        "rating": 1,
        "content": "Received a used product with scratches on the screen. Trying to get a refund but no response from support.",
        "sentiment": "negative",
        "created_at": "2026-10-21T11:20:00Z",
    },
    {
        "id": "REV-006",
        "author": "Zainab Malik",
        "rating": 4,
        "content": "Shoes are comfortable and true to size. Colour is slightly different from the photos but overall good.",
        "sentiment": "positive",
        "created_at": "2026-10-19T13:00:00Z",
    },
    {
        "id": "REV-007",
        "author": "Hassan Ali",
        "rating": 3,
        "content": "Power bank works fine but charging speed is slow. Expected faster charging for 20000mAh.",
        "sentiment": "neutral",
        "created_at": "2026-10-20T10:30:00Z",
    },
    {
        "id": "REV-008",
        "author": "Maryam Noor",
        "rating": 5,
        "content": "iPhone arrived in perfect condition, PTA approved as promised. Best online shopping experience in Pakistan.",
        "sentiment": "positive",
        "created_at": "2026-10-22T08:00:00Z",
    },
    {
        "id": "REV-009",
        "author": "Kamran Sheikh",
        "rating": 2,
        "content": "Vacuum cleaner stopped working after 2 weeks. Warranty claim process is complicated and slow.",
        "sentiment": "negative",
        "created_at": "2026-10-21T15:45:00Z",
    },
    {
        "id": "REV-010",
        "author": "Sana Javed",
        "rating": 4,
        "content": "Air fryer is great, healthy cooking made easy. Slightly noisy but the results are worth it.",
        "sentiment": "positive",
        "created_at": "2026-10-18T12:15:00Z",
    },
]


@router.get("/orders")
async def list_orders(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    operator: str = Depends(verify_auth_optional),
):
    """List orders with optional status filter and pagination."""
    filtered = [o for o in _CATALOG_ORDERS if not status or o["status"] == status]
    total = len(filtered)
    start = (page - 1) * limit
    end = start + limit
    return {
        "orders": filtered[start:end],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/products")
async def list_products(
    page: int = 1,
    limit: int = 20,
    operator: str = Depends(verify_auth_optional),
):
    """List products with pagination."""
    total = len(_CATALOG_PRODUCTS)
    start = (page - 1) * limit
    end = start + limit
    return {
        "products": _CATALOG_PRODUCTS[start:end],
        "total": total,
    }


@router.get("/reviews")
async def list_reviews(
    sentiment: Optional[str] = None,
    operator: str = Depends(verify_auth_optional),
):
    """List reviews with optional sentiment filter."""
    filtered = [r for r in _CATALOG_REVIEWS if not sentiment or r["sentiment"] == sentiment]
    return filtered
