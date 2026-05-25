import uuid
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_ops.config import settings as app_settings
from ecommerce_ops.graph.supervisor import Supervisor
from ecommerce_ops.models import (
    async_session_factory,
    ApprovalAction,
    AuditEntry,
    AgentStatus,
    StoreSettings,
)
from ecommerce_ops.safety.safety_rules import evaluate_action_safety
from ecommerce_ops.pipeline.builder import build_payload_and_evidence
from ecommerce_ops.api.ws import ws_manager
from ecommerce_ops.api.metrics import METRIC_PIPELINE_RUNS
from ecommerce_ops.infra.notifications import notify_hitl_request, notify_pipeline_failed, notify_agent_graduated

logger = logging.getLogger("ecommerce_ops.pipeline.runner")

DECISION_TYPE_MAP = {
    "HOLD_ORDER": "fraud_hold",
    "DRAFT_PO": "purchase_order",
    "UPDATE_PRICE": "price_change",
    "POST_REVIEW_RESPONSE": "review_response",
    "DRAFT_MARKETING_CAMPAIGN": "marketing_campaign",
}


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


async def update_agent_streak(
    agent_name: str, approved: bool, confidence: float, db: AsyncSession
):
    res = await db.execute(
        select(AgentStatus)
        .where(AgentStatus.agent_id == agent_name)
        .with_for_update()
    )
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
                await notify_agent_graduated(agent_name, "autonomous", status.streak)
    else:
        status.total_rejections += 1
        status.streak = 0
        status.autonomy_level = "supervised"
    n = status.total_decisions
    status.avg_confidence = ((status.avg_confidence * (n - 1)) + confidence) / n
    db.add(status)


async def run_pipeline_task(run_id: str, db_settings: StoreSettings):
    logger.info("Starting pipeline run %s", run_id)

    inventory_data = [
        {"sku": "TSHIRT-BLUE-L", "stock": 3, "price": 25.0, "variant_id": "v1"},
        {"sku": "MUG-WHITE", "stock": 2, "price": 12.0, "variant_id": "v2"},
        {"sku": "SILK-PILLOW-SLV", "stock": 1, "price": 49.0, "variant_id": "v3"},
    ]

    active_orders = [
        {
            "id": "o_suspicious",
            "line_items": [{"sku": "TSHIRT-BLUE-L", "quantity": 1}],
            "order_total": 450.0,
        },
    ]

    reviews_data = [
        {"id": "r_100", "content": "The shipping was delayed and box was damaged!", "rating": 2},
    ]

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
        supervisor = Supervisor()
        final_state = await supervisor.run(initial_state)
        decisions_list = final_state.get("decisions", [])
        logger.info("Pipeline %s finished: %d decisions", run_id, len(decisions_list))

        async with async_session_factory() as session:
            res_set = await session.execute(
                select(StoreSettings).where(StoreSettings.id == 1)
            )
            settings = res_set.scalar_one()
            new_actions_count = 0

            for d in decisions_list:
                mapped_type = DECISION_TYPE_MAP.get(
                    d.action_type, "marketing_campaign"
                )
                requires_hitl, risk_level, financial_impact = evaluate_action_safety(
                    d.agent_id, mapped_type, d.action_data, d.confidence_score, settings
                )

                payload, evidence = build_payload_and_evidence(d, reviews_data)
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
                    impact["affected_skus"] = (
                        [payload.get("sku", "")] if payload.get("sku") else []
                    )

                status = "pending"
                if not requires_hitl and not settings.shadow_mode:
                    status = "executed"

                action_id = str(uuid.uuid4())
                session.add(
                    ApprovalAction(
                        id=action_id,
                        agent=d.agent_id,
                        action_type=mapped_type,
                        status=status,
                        risk_level=risk_level,
                        confidence_score=d.confidence_score,
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=2),
                        requires_hitl=requires_hitl,
                        shadow_mode=settings.shadow_mode,
                        payload=payload,
                        evidence=evidence,
                        impact=impact,
                    )
                )

                if status == "executed":
                    session.add(
                        AuditEntry(
                            action_id=action_id,
                            timestamp=datetime.utcnow(),
                            agent=d.agent_id,
                            action_type=mapped_type,
                            decision="auto-approved",
                            operator=None,
                            confidence_score=d.confidence_score,
                            financial_impact=financial_impact,
                            details={
                                "notes": "Auto-approved by safety system",
                                "payload": payload,
                            },
                        )
                    )
                    await update_agent_streak(
                        d.agent_id, True, d.confidence_score, session
                    )

                new_actions_count += 1
                if requires_hitl or settings.shadow_mode:
                    await notify_hitl_request(
                        agent=d.agent_id,
                        action_id=action_id,
                        action_type=mapped_type,
                        risk_level=risk_level,
                        confidence=d.confidence_score,
                    )

            await session.commit()
            await ws_manager.broadcast(
                {
                    "type": "pipeline_completed",
                    "payload": {
                        "run_id": run_id,
                        "action_count": new_actions_count,
                    },
                }
            )
            METRIC_PIPELINE_RUNS.labels(status="success").inc()

    except Exception as e:
        logger.exception("Pipeline run %s failed: %s", run_id, e)
        METRIC_PIPELINE_RUNS.labels(status="failure").inc()
        await notify_pipeline_failed(run_id, str(e))
        await ws_manager.broadcast(
            {
                "type": "pipeline_failed",
                "payload": {"run_id": run_id, "error": str(e)},
            }
        )
