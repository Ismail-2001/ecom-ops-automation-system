import uuid
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

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
from ecommerce_ops.api.metrics import (
    METRIC_PIPELINE_RUNS,
    METRIC_DECISIONS_CREATED,
    METRIC_DECISIONS_APPROVED,
    METRIC_DECISIONS_REJECTED,
    METRIC_DECISIONS_AUTO_APPROVED,
    METRIC_FINANCIAL_IMPACT,
)
from ecommerce_ops.infra.notifications import notify_hitl_request, notify_pipeline_failed, notify_agent_graduated
from ecommerce_ops.observability.langfuse_client import langfuse_client
from ecommerce_ops.observability.evaluation import evaluation_framework

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
                inventory_data.append({
                    "sku": variant.get("sku", f"SKU-{variant['id']}"),
                    "stock": variant.get("inventory_quantity", 0),
                    "price": float(variant.get("price", 0)),
                    "variant_id": str(variant["id"]),
                })

        # Fetch recent orders (last 24h)
        orders_response = await client.get_orders(
            status="any",
            limit=50,
            created_at_min=(datetime.utcnow() - timedelta(hours=24)).isoformat(),
        )
        active_orders = []
        for order in orders_response.get("orders", []):
            if order.get("fulfillment_status") != "fulfilled":
                active_orders.append({
                    "id": str(order["id"]),
                    "line_items": [
                        {"sku": item.get("sku", ""), "quantity": item.get("quantity", 1)}
                        for item in order.get("line_items", [])
                    ],
                    "order_total": float(order.get("total_price", 0)),
                })

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
                    items.append({
                        "product_id": item.get("product_id", 0),
                        "variant_id": item.get("variant_id", 0),
                        "title": item.get("title", "Unknown"),
                        "sku": item.get("sku"),
                        "quantity": item.get("quantity", 1),
                        "price": float(item.get("price", 0)),
                        "total": float(item.get("line_price", 0)),
                    })

                abandoned_carts.append({
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
                    } if checkout.get("email") else None,
                })

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

    # Try to fetch real Shopify data first
    shopify_data = await fetch_shopify_data()

    if shopify_data:
        inventory_data = shopify_data["inventory_data"]
        active_orders = shopify_data["active_orders"]
        reviews_data = shopify_data["reviews_data"]
        abandoned_carts = shopify_data.get("abandoned_carts", [])
        data_source = "shopify"
        logger.info(
            "Using Shopify data: %d inventory items, %d active orders, %d abandoned carts",
            len(inventory_data),
            len(active_orders),
            len(abandoned_carts),
        )
    else:
        # Fallback to mock data
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

        abandoned_carts = [
            {
                "id": "cart_mock_1",
                "shop_domain": "mock-store.myshopify.com",
                "items": [
                    {"product_id": 101, "variant_id": 201, "title": "Blue T-Shirt", "sku": "TSHIRT-BLUE-L", "quantity": 2, "price": 25.0, "total": 50.0},
                    {"product_id": 102, "variant_id": 202, "title": "White Mug", "sku": "MUG-WHITE", "quantity": 1, "price": 12.0, "total": 12.0},
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
            name=f"pipeline.run",
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

                METRIC_DECISIONS_CREATED.labels(
                    agent=d.agent_id, action_type=mapped_type
                ).inc()
                METRIC_FINANCIAL_IMPACT.labels(
                    agent=d.agent_id, action_type=mapped_type
                ).inc(financial_impact)

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
                        "evaluation_pass_rate": round(
                            passed_count / len(evaluation_results), 3
                        ) if evaluation_results else 0,
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
                            "pass_rate": round(
                                passed_count / len(evaluation_results), 3
                            ) if evaluation_results else 0,
                        },
                    },
                }
            )
            METRIC_PIPELINE_RUNS.labels(status="success").inc()

    except Exception as e:
        logger.exception("Pipeline run %s failed: %s", run_id, e)
        METRIC_PIPELINE_RUNS.labels(status="failure").inc()

        # Track failure in Langfuse
        if trace:
            langfuse_client.score(
                trace_id=trace.id,
                name="pipeline_success",
                value=0.0,
                comment=f"Pipeline failed: {str(e)}",
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
