import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_ops.api.metrics import (
    METRIC_DECISIONS_AUTO_APPROVED,
    METRIC_DECISIONS_CREATED,
    METRIC_FINANCIAL_IMPACT,
    METRIC_PIPELINE_RUNS,
)
from ecommerce_ops.api.ws import ws_manager
from ecommerce_ops.config import Environment
from ecommerce_ops.config import settings as app_settings
from ecommerce_ops.graph.supervisor import Supervisor
from ecommerce_ops.infra.notifications import (
    notify_agent_graduated,
    notify_hitl_request,
    notify_pipeline_failed,
)
from ecommerce_ops.models import (
    AgentStatus,
    ApprovalAction,
    AuditEntry,
    OutboxMessage,
    PipelineRun,
    StoreSettings,
    async_session_factory,
)
from ecommerce_ops.observability.evaluation import evaluation_framework
from ecommerce_ops.observability.langfuse_client import langfuse_client
from ecommerce_ops.pipeline.builder import build_payload_and_evidence
from ecommerce_ops.safety.safety_rules import evaluate_action_safety

# ── Locked batch guard ─────────────────────────────────────────
# In-process asyncio lock per run_id (prevents concurrent runs in same process).
# For multi-worker deployments, add a Redis/distributed lock via backend.
_pipeline_locks: dict[str, asyncio.Lock] = {}


def _get_pipeline_lock(run_id: str) -> asyncio.Lock:
    """Get or create a lock for the given run_id."""
    if run_id not in _pipeline_locks:
        _pipeline_locks[run_id] = asyncio.Lock()
    return _pipeline_locks[run_id]


async def _try_register_pipeline_run(
    run_id: str, session: AsyncSession
) -> PipelineRun | None:
    """Attempt to register a pipeline run idempotently.

    Uses ``INSERT … ON CONFLICT DO NOTHING`` against the ``pipeline_runs``
    table.  Returns the new ``PipelineRun`` row if this call owns the run,
    or ``None`` if the ``run_id`` was already registered (another worker or
    a prior invocation beat us).
    """
    try:
        from ecommerce_ops.models.db import is_sqlite

        if is_sqlite:
            from sqlalchemy.dialects.sqlite import insert as dialect_insert
        else:
            from sqlalchemy.dialects.postgresql import insert as dialect_insert

        stmt = (
            dialect_insert(PipelineRun)
            .values(run_id=run_id, status="running", started_at=datetime.utcnow())
            .on_conflict_do_nothing(index_elements=[PipelineRun.run_id])
        )
        result = await session.execute(stmt)
        if result.rowcount == 0:
            return None
        # Fetch the row we just inserted to get the ORM object
        row = await session.execute(
            select(PipelineRun).where(PipelineRun.run_id == run_id)
        )
        return row.scalar_one()
    except Exception:
        return None


logger = logging.getLogger("ecommerce_ops.pipeline.runner")


async def fetch_shopify_data() -> Optional[Dict[str, Any]]:
    """Fetch real data from Shopify if credentials are configured."""
    from ecommerce_ops.connectors.shopify.client import ShopifyClient

    shop_domain = app_settings.SHOPIFY_SHOP_DOMAIN
    access_token = app_settings.SHOPIFY_ACCESS_TOKEN

    if not shop_domain or not access_token:
        logger.debug("Shopify credentials not configured, using mock data")
        return None

    try:
        client = ShopifyClient(
            shop_domain=shop_domain,
            access_token=access_token,
            api_version=app_settings.SHOPIFY_API_VERSION,
        )

        # Fetch inventory
        inventory_response = await client.get_products(limit=100)
        inventory_data = []
        for product in inventory_response.get("products", []):
            for variant in product.get("variants", []):
                inventory_data.append(
                    {
                        "sku": variant.get("sku", f"SKU-{variant['id']}"),
                        "stock": variant.get("inventory_quantity", 0),
                        "price": float(variant.get("price", 0)),
                        "variant_id": str(variant["id"]),
                    }
                )

        # Fetch recent orders (last 24h)
        orders_response = await client.get_orders(
            status="any",
            limit=50,
            created_at_min=(datetime.utcnow() - timedelta(hours=24)).isoformat(),
        )
        active_orders = []
        for order in orders_response.get("orders", []):
            if order.get("fulfillment_status") != "fulfilled":
                active_orders.append(
                    {
                        "id": str(order["id"]),
                        "line_items": [
                            {"sku": item.get("sku", ""), "quantity": item.get("quantity", 1)}
                            for item in order.get("line_items", [])
                        ],
                        "order_total": float(order.get("total_price", 0)),
                    }
                )

        # Fetch reviews (from order notes/comments - placeholder)
        reviews_data = []  # Reviews API not available in basic scope

        # Fetch abandoned carts (checkouts)
        checkouts_response = await client.get_checkouts(limit=50)
        abandoned_carts = []
        for checkout in checkouts_response.get("checkouts", []):
            # Check if checkout is abandoned (no completed order)
            if checkout.get("order") is None:
                items = []
                for item in checkout.get("line_items", []):
                    items.append(
                        {
                            "product_id": item.get("product_id", 0),
                            "variant_id": item.get("variant_id", 0),
                            "title": item.get("title", "Unknown"),
                            "sku": item.get("sku"),
                            "quantity": item.get("quantity", 1),
                            "price": float(item.get("price", 0)),
                            "total": float(item.get("line_price", 0)),
                        }
                    )

                abandoned_carts.append(
                    {
                        "id": str(checkout.get("id", f"cart-{len(abandoned_carts)}")),
                        "shop_domain": shop_domain,
                        "checkout_token": checkout.get("token"),
                        "items": items,
                        "total_value": float(checkout.get("total_price", 0)),
                        "currency": checkout.get("currency", "USD"),
                        "items_count": len(items),
                        "status": "abandoned",
                        "checkout_url": checkout.get("abandoned_checkout_url"),
                        "created_at": checkout.get("created_at"),
                        "abandoned_at": checkout.get("updated_at"),
                        "customer": {
                            "email": checkout.get("email"),
                            "first_name": checkout.get("billing_address", {}).get("first_name"),
                            "last_name": checkout.get("billing_address", {}).get("last_name"),
                        }
                        if checkout.get("email")
                        else None,
                    }
                )

        await client.close()

        return {
            "inventory_data": inventory_data,
            "active_orders": active_orders,
            "reviews_data": reviews_data,
            "abandoned_carts": abandoned_carts,
        }

    except Exception as e:
        logger.error("Failed to fetch Shopify data: %s", e)
        return None


DECISION_TYPE_MAP = {
    "HOLD_ORDER": "fraud_hold",
    "DRAFT_PO": "purchase_order",
    "UPDATE_PRICE": "price_change",
    "POST_REVIEW_RESPONSE": "review_response",
    "DRAFT_MARKETING_CAMPAIGN": "marketing_campaign",
}

# Capability binding for live mutations (M7): only the agent(s) authorized for
# an action type may execute it against Shopify. This is the last line of
# defense against a misbehaving or compromised agent issuing an action of a
# type it has no permission to perform. LLM agents use the snake_case keys
# from the tool-permission matrix; rule-based agents use their PascalCase
# names. The check is enforced in execute_shop_action before any live call.
ACTION_TYPE_AGENT_ALLOWLIST: dict[str, set[str]] = {
    "fraud_hold": {"FraudAgent", "fraud_detection"},
    "purchase_order": {"InventoryAgent", "inventory_management"},
    "price_change": {"PricingAgent", "PriceOptimizationAgent", "price_optimization"},
    "review_response": {"ReviewsAgent", "review_moderation"},
    "marketing_campaign": {"MarketingAgent", "marketing_automation"},
}


async def execute_shop_action(action: ApprovalAction) -> tuple[bool, str]:
    if action.shadow_mode:
        logger.info("[SHADOW] Simulating %s for %s", action.action_type, action.id)
        return True, "Shadow mode simulation"

    # Permission gate (M7): the initiating agent must be allowed to perform
    # this action type. Unknown action types and unlisted agents are refused
    # before any live Shopify call.
    allowed_agents = ACTION_TYPE_AGENT_ALLOWLIST.get(action.action_type)
    if allowed_agents is not None and action.agent not in allowed_agents:
        logger.warning(
            "[LIVE] Permission denied: agent %s cannot execute action_type %s (action %s)",
            action.agent,
            action.action_type,
            action.id,
        )
        return False, (
            f"agent {action.agent!r} does not have permission to execute "
            f"action_type {action.action_type!r}"
        )

    # Live execution requires Shopify credentials; without them a real action
    # cannot be performed, so report an honest failure instead of a fabricated
    # "Executed" result.
    shop_domain = app_settings.SHOPIFY_SHOP_DOMAIN
    access_token = app_settings.SHOPIFY_ACCESS_TOKEN
    if not shop_domain or not access_token:
        logger.warning(
            "[LIVE] Cannot execute %s for %s: Shopify not configured",
            action.action_type,
            action.id,
        )
        return False, (
            "execution requires Shopify credentials (SHOPIFY_SHOP_DOMAIN / SHOPIFY_ACCESS_TOKEN)"
        )

    from ecommerce_ops.connectors.shopify.client import ShopifyClient

    client = ShopifyClient(
        shop_domain=shop_domain,
        access_token=access_token,
        api_version=app_settings.SHOPIFY_API_VERSION,
    )
    payload = action.payload or {}
    try:
        if action.action_type == "fraud_hold":
            order_id = payload.get("order_id") or payload.get("id")
            if not order_id or not str(order_id).isdigit():
                return False, "fraud_hold requires a real Shopify order_id"
            await client.update_order(str(order_id), {"tags": ["FRAUD_HOLD"]})
            logger.info("Applied FRAUD_HOLD to order %s", order_id)
            return True, f"Applied FRAUD_HOLD to order {order_id}"

        if action.action_type == "price_change":
            sku = payload.get("sku")
            new_price = payload.get("proposed_price", payload.get("new_price"))
            if not sku or new_price is None:
                return False, "price_change requires sku and proposed_price in payload"
            products = (await client.get_products(limit=250)).get("products", [])
            target = None
            target_sku = str(sku).strip().upper()
            for product in products:
                for variant in product.get("variants", []):
                    if str(variant.get("sku", "")).strip().upper() == target_sku:
                        target = (str(product["id"]), str(variant["id"]))
                        break
                if target:
                    break
            if not target:
                return False, f"price_change: no product variant found for sku {sku}"
            product_id, variant_id = target
            await client.update_product(
                product_id, {"variants": [{"id": variant_id, "price": str(new_price)}]}
            )
            logger.info("Updated price for variant %s to %s", variant_id, new_price)
            return True, f"Updated price for {sku} to {new_price}"

        if action.action_type == "purchase_order":
            return False, (
                "purchase_order requires inventory_location_id and reorder_quantity; not executed"
            )

        if action.action_type == "review_response":
            return False, (
                "review_response requires a product reviews API scope that is not configured"
            )

        if action.action_type == "marketing_campaign":
            return False, (
                "marketing_campaign requires a marketing events API scope that is not configured"
            )

        return False, f"Unknown action type: {action.action_type}"
    except Exception as e:
        logger.error("Shop action %s for %s failed: %s", action.action_type, action.id, e)
        return False, str(e)
    finally:
        await client.close()


async def update_agent_streak(agent_name: str, approved: bool, confidence: float, db: AsyncSession):
    """Atomically update agent streak metrics via a single UPDATE statement.

    Uses SQL-level expressions instead of read-modify-write to avoid lost
    updates under concurrent approves (M4). SQLite and PostgreSQL both
    serialise row-level writes within a transaction.
    """
    if approved:
        stmt = (
            update(AgentStatus)
            .where(AgentStatus.agent_id == agent_name)
            .values(
                total_decisions=func.coalesce(AgentStatus.total_decisions, 0) + 1,
                total_approvals=func.coalesce(AgentStatus.total_approvals, 0) + 1,
                streak=func.coalesce(AgentStatus.streak, 0) + 1,
                avg_confidence=(
                    func.coalesce(AgentStatus.avg_confidence, 0)
                    * func.coalesce(AgentStatus.total_decisions, 0)
                    + confidence
                )
                / (func.coalesce(AgentStatus.total_decisions, 0) + 1),
            )
            .execution_options(synchronize_session=False)
        )
    else:
        stmt = (
            update(AgentStatus)
            .where(AgentStatus.agent_id == agent_name)
            .values(
                total_decisions=func.coalesce(AgentStatus.total_decisions, 0) + 1,
                total_rejections=func.coalesce(AgentStatus.total_rejections, 0) + 1,
                streak=0,
                avg_confidence=(
                    func.coalesce(AgentStatus.avg_confidence, 0)
                    * func.coalesce(AgentStatus.total_decisions, 0)
                    + confidence
                )
                / (func.coalesce(AgentStatus.total_decisions, 0) + 1),
            )
            .execution_options(synchronize_session=False)
        )
    await db.execute(stmt)

    # Check for autonomy graduation (read the updated value)
    if approved and confidence >= 0.95:
        res = await db.execute(
            select(func.coalesce(AgentStatus.streak, 0)).where(AgentStatus.agent_id == agent_name)
        )
        streak = res.scalar() or 0
        if streak >= 50:
            await db.execute(
                update(AgentStatus)
                .where(AgentStatus.agent_id == agent_name)
                .where(AgentStatus.autonomy_level != "autonomous")
                .values(autonomy_level="autonomous")
                .execution_options(synchronize_session=False)
            )
            logger.info("Agent %s graduated to AUTONOMOUS!", agent_name)
            await notify_agent_graduated(agent_name, "autonomous", streak)
    elif not approved:
        await db.execute(
            update(AgentStatus)
            .where(AgentStatus.agent_id == agent_name)
            .where(AgentStatus.autonomy_level != "supervised")
            .values(autonomy_level="supervised")
            .execution_options(synchronize_session=False)
        )


async def run_pipeline_task(run_id: str, db_settings: StoreSettings):
    # Locked batch guard: prevent re-running the same pipeline
    lock = _get_pipeline_lock(run_id)
    if lock.locked():
        logger.warning("Pipeline run %s already in progress, rejecting", run_id)
        raise RuntimeError(f"Pipeline run {run_id} is already in progress")

    # Idempotency: register run in PipelineRun table (C4)
    async with async_session_factory() as session:
        pipeline_run = await _try_register_pipeline_run(run_id, session)
        if pipeline_run is None:
            logger.warning("Pipeline run %s already registered, rejecting", run_id)
            raise RuntimeError(f"Pipeline run {run_id} has already completed")
        await session.commit()

    async with lock:
        logger.info("Starting pipeline run %s", run_id)

        # Try to fetch real Shopify data first
        shopify_data = await fetch_shopify_data()

    if shopify_data:
        inventory_data = shopify_data["inventory_data"]
        active_orders = shopify_data["active_orders"]
        reviews_data = shopify_data["reviews_data"]
        abandoned_carts = shopify_data.get("abandoned_carts", [])
        support_tickets = []
        data_source = "shopify"
        logger.info(
            "Using Shopify data: %d inventory items, %d active orders, %d abandoned carts",
            len(inventory_data),
            len(active_orders),
            len(abandoned_carts),
        )
    else:
        if app_settings.ENV == Environment.PRODUCTION:
            raise RuntimeError(
                f"Pipeline run {run_id}: Shopify data unavailable in production and "
                "fail-open to mock data is disabled. Configure Shopify "
                "credentials or check the Shopify API."
            )
        # Fallback to mock data (development/testing only)
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
            {
                "id": "r_100",
                "content": "The shipping was delayed and box was damaged!",
                "rating": 2,
            },
        ]

        abandoned_carts = [
            {
                "id": "cart_mock_1",
                "shop_domain": "mock-store.myshopify.com",
                "items": [
                    {
                        "product_id": 101,
                        "variant_id": 201,
                        "title": "Blue T-Shirt",
                        "sku": "TSHIRT-BLUE-L",
                        "quantity": 2,
                        "price": 25.0,
                        "total": 50.0,
                    },
                    {
                        "product_id": 102,
                        "variant_id": 202,
                        "title": "White Mug",
                        "sku": "MUG-WHITE",
                        "quantity": 1,
                        "price": 12.0,
                        "total": 12.0,
                    },
                ],
                "total_value": 62.0,
                "currency": "USD",
                "items_count": 2,
                "status": "abandoned",
                "checkout_url": "https://mock-store.myshopify.com/checkout/abc123",
                "customer": {
                    "email": "customer@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "total_orders": 3,
                    "total_spent": 150.0,
                    "is_repeat_customer": True,
                    "segment": "returning",
                },
            },
        ]

        support_tickets = [
            {
                "id": "ticket_001",
                "shop_domain": "mock-store.myshopify.com",
                "customer_email": "angry@example.com",
                "customer_name": "Sarah",
                "subject": "Where is my order?!",
                "body": "I placed my order 2 weeks ago and still haven't received it! This is unacceptable. I want a refund immediately!",
                "channel": "email",
                "order_id": "12345",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {"total_spent": 250.0, "total_orders": 5},
            },
            {
                "id": "ticket_002",
                "shop_domain": "mock-store.myshopify.com",
                "customer_email": "question@example.com",
                "customer_name": "Mike",
                "subject": "Product question",
                "body": "Hi, what sizes does the blue t-shirt come in? Also, is it machine washable?",
                "channel": "chat",
                "product_id": "101",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {"total_spent": 50.0, "total_orders": 1},
            },
        ]
        data_source = "mock"
        logger.info("Using mock data (Shopify not configured)")

    # Update PipelineRun with data source
    async with async_session_factory() as session:
        await session.execute(
            update(PipelineRun)
            .where(PipelineRun.run_id == run_id)
            .values(data_source=data_source)
        )
        await session.commit()

    initial_state = {
        "inventory_data": inventory_data,
        "active_orders": active_orders,
        "reviews_data": reviews_data,
        "abandoned_carts": abandoned_carts,
        "support_tickets": support_tickets,
        "decisions": [],
        "hitl_queue": [],
        "messages": [],
        "errors": [],
        "run_id": run_id,
        "timestamp": datetime.utcnow(),
    }

    try:
        # Create pipeline trace
        trace = langfuse_client.create_trace(
            name="pipeline.run",
            user_id=None,
            tags=["pipeline", run_id],
            metadata={
                "run_id": run_id,
                "data_source": data_source,
            },
        )

        supervisor = Supervisor()
        final_state = await supervisor.run(initial_state)
        decisions_list = final_state.get("decisions", [])
        logger.info("Pipeline %s finished: %d decisions", run_id, len(decisions_list))

        # Evaluate decisions
        evaluation_results = []
        for d in decisions_list:
            evaluation = evaluation_framework.evaluate_decision(
                agent_name=d.agent_id,
                decision_id=str(uuid.uuid4()),
                decision={
                    "action_type": d.action_type,
                    "reasoning": d.reasoning,
                    "confidence_score": d.confidence_score,
                    "action_data": d.action_data,
                },
                context={"run_id": run_id},
                trace_id=trace.id if trace else None,
            )
            evaluation_results.append(evaluation)

            # Add score to trace
            if trace:
                langfuse_client.score(
                    trace_id=trace.id,
                    name=f"{d.agent_id}.quality",
                    value=evaluation.overall_score,
                    comment=evaluation.feedback,
                )

        async with async_session_factory() as session:
            res_set = await session.execute(select(StoreSettings).where(StoreSettings.id == 1))
            settings = res_set.scalar_one()
            new_actions_count = 0

            for d in decisions_list:
                mapped_type = DECISION_TYPE_MAP.get(d.action_type)
                if mapped_type is None:
                    logger.error(
                        "Unknown action_type '%s' for agent '%s' — refusing to create action",
                        d.action_type,
                        d.agent_id,
                    )
                    continue  # skip, don't silently default to marketing_campaign
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
                    impact["affected_skus"] = [payload.get("sku", "")] if payload.get("sku") else []

                action_id = str(uuid.uuid4())

                # Auto-approval requires BOTH: safety rules permit it AND the
                # decision confidence clears the configured threshold. Otherwise
                # the action is held for human review.
                auto_attempt = (
                    not requires_hitl
                    and not settings.shadow_mode
                    and d.confidence_score >= app_settings.AUTO_APPROVE_CONFIDENCE_SCORE
                )

                action = ApprovalAction(
                    id=action_id,
                    agent=d.agent_id,
                    action_type=mapped_type,
                    status="executing" if auto_attempt else "pending",
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

                executed_ok = False
                execution_msg = None
                if auto_attempt:
                    # C5: Write outbox message before live Shopify call
                    outbox = OutboxMessage(
                        action_id=action_id,
                        status="pending",
                        payload=payload,
                    )
                    session.add(outbox)
                    await session.flush()

                    executed_ok, execution_msg = await execute_shop_action(action)
                    action.status = "executed" if executed_ok else "failed"
                    if not executed_ok:
                        action.operator_notes = f"Auto-execution failed: {execution_msg}"
                        outbox.status = "failed"
                        outbox.error = execution_msg
                    else:
                        outbox.status = "sent"
                        outbox.sent_at = datetime.utcnow()
                        METRIC_DECISIONS_AUTO_APPROVED.labels(agent=d.agent_id).inc()

                session.add(action)

                METRIC_DECISIONS_CREATED.labels(agent=d.agent_id, action_type=mapped_type).inc()
                METRIC_FINANCIAL_IMPACT.labels(agent=d.agent_id, action_type=mapped_type).inc(
                    financial_impact
                )

                if auto_attempt:
                    session.add(
                        AuditEntry(
                            action_id=action_id,
                            timestamp=datetime.utcnow(),
                            agent=d.agent_id,
                            action_type=mapped_type,
                            decision=("auto-approved" if executed_ok else "auto-approval-failed"),
                            operator=None,
                            confidence_score=d.confidence_score,
                            financial_impact=financial_impact,
                            details={
                                "notes": (
                                    "Auto-executed by safety system"
                                    if executed_ok
                                    else f"Auto-execution failed: {execution_msg}"
                                ),
                                "execution_status": action.status,
                                "payload": payload,
                            },
                        )
                    )
                    await update_agent_streak(d.agent_id, executed_ok, d.confidence_score, session)

                new_actions_count += 1
                if action.status == "pending":
                    await notify_hitl_request(
                        agent=d.agent_id,
                        action_id=action_id,
                        action_type=mapped_type,
                        risk_level=risk_level,
                        confidence=d.confidence_score,
                    )

            await session.commit()

            # Log evaluation summary
            avg_score = (
                sum(e.overall_score for e in evaluation_results) / len(evaluation_results)
                if evaluation_results
                else 0
            )
            passed_count = sum(1 for e in evaluation_results if e.passed)
            logger.info(
                "Pipeline %s evaluation: %d/%d passed, avg_score=%.3f",
                run_id,
                passed_count,
                len(evaluation_results),
                avg_score,
            )

            # Add pipeline completion to trace
            if trace:
                langfuse_client.create_span(
                    trace_id=trace.id,
                    name="pipeline_summary",
                    output={
                        "run_id": run_id,
                        "decisions_count": len(decisions_list),
                        "actions_count": new_actions_count,
                        "evaluation_avg_score": round(avg_score, 3),
                        "evaluation_pass_rate": round(passed_count / len(evaluation_results), 3)
                        if evaluation_results
                        else 0,
                    },
                )

            await ws_manager.broadcast(
                {
                    "type": "pipeline_completed",
                    "payload": {
                        "run_id": run_id,
                        "action_count": new_actions_count,
                        "evaluation": {
                            "avg_score": round(avg_score, 3),
                            "pass_rate": round(passed_count / len(evaluation_results), 3)
                            if evaluation_results
                            else 0,
                        },
                    },
                }
            )
            METRIC_PIPELINE_RUNS.labels(status="success").inc()

            # C4: Update PipelineRun with final stats
            await session.execute(
                update(PipelineRun)
                .where(PipelineRun.run_id == run_id)
                .values(
                    status="completed",
                    decisions_count=len(decisions_list),
                    actions_count=new_actions_count,
                    evaluation_avg_score=round(avg_score, 3),
                    evaluation_pass_rate=round(
                        passed_count / len(evaluation_results), 3
                    )
                    if evaluation_results
                    else 0,
                    finished_at=datetime.utcnow(),
                )
            )
            await session.commit()

    except Exception as e:
        logger.exception("Pipeline run %s failed: %s", run_id, e)
        METRIC_PIPELINE_RUNS.labels(status="failure").inc()

        # C4: Mark PipelineRun as failed
        try:
            async with async_session_factory() as session:
                await session.execute(
                    update(PipelineRun)
                    .where(PipelineRun.run_id == run_id)
                    .values(
                        status="failed",
                        error=str(e)[:500],
                        finished_at=datetime.utcnow(),
                    )
                )
                await session.commit()
        except Exception:
            logger.exception("Failed to update PipelineRun status for %s", run_id)

        # Track failure in Langfuse
        if trace:
            langfuse_client.score(
                trace_id=trace.id,
                name="pipeline_success",
                value=0.0,
                comment=f"Pipeline failed: {e!s}",
            )

        await notify_pipeline_failed(run_id, str(e))
        await ws_manager.broadcast(
            {
                "type": "pipeline_failed",
                "payload": {"run_id": run_id, "error": str(e)},
            }
        )
    finally:
        # Flush Langfuse events
        langfuse_client.flush()
