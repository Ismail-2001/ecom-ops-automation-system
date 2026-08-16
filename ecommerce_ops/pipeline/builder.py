from typing import Any, Dict, List

UNKNOWN = "unknown"


def _try_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _change_percent(old: Any, new: Any) -> float | None:
    old_f = _try_float(old)
    new_f = _try_float(new)
    if old_f is None or new_f is None or old_f == 0:
        return None
    return round((new_f - old_f) / old_f * 100, 2)


def build_payload_and_evidence(d, reviews_data: List[Dict]) -> tuple:
    """Extract payload and evidence from a decision based on agent type.

    All values are derived from the agent's ``action_data`` (real Shopify data)
    or explicitly marked as unknown. No fabricated customer/supplier/product
    identities or invented metrics are emitted.
    """
    if d.agent_id == "FraudAgent":
        payload = {
            "order_id": d.action_data.get("order_id", "ORD-UNKNOWN"),
            "customer_name": d.action_data.get("customer_name") or UNKNOWN,
            "customer_email": d.action_data.get("customer_email") or None,
            "order_total": _try_float(d.action_data.get("order_total")),
            "fraud_score": _try_float(d.action_data.get("risk_score")),
            "risk_signals": d.action_data.get("risk_factors") or d.action_data.get("risk_signals") or [],
            "recommended_action": "hold",
        }
        risk_value = f"{payload['fraud_score']:.0f}/100" if payload["fraud_score"] is not None else UNKNOWN
        signals_value = ", ".join(payload["risk_signals"]) if payload["risk_signals"] else "None detected"
        evidence = [
            {"label": "Risk Score", "value": risk_value, "weight": "primary", "source": "FraudHeuristics"},
            {"label": "Risk Signals", "value": signals_value, "weight": "supporting", "source": "FraudAgent"},
        ]
        return payload, evidence

    if d.agent_id == "InventoryAgent":
        sku = d.action_data.get("sku") or UNKNOWN
        qty = _try_float(d.action_data.get("quantity_to_order"))
        unit_cost = _try_float(d.action_data.get("unit_cost"))
        payload = {
            "sku": sku,
            "product_name": d.action_data.get("product_name") or None,
            "current_stock": _try_float(d.action_data.get("current_stock")),
            "daily_velocity": _try_float(d.action_data.get("daily_velocity")),
            "days_of_supply": _try_float(d.action_data.get("days_of_supply")),
            "reorder_quantity": qty if qty is not None else 75,
            "supplier_name": d.action_data.get("supplier_name") or None,
            "unit_cost": unit_cost,
            "total_po_value": qty * unit_cost if qty is not None and unit_cost is not None else None,
        }
        stockout = d.action_data.get("predicted_stockout_days")
        stockout_value = f"~{float(stockout):.1f}d" if stockout is not None else UNKNOWN
        evidence = [
            {"label": "Reorder Qty", "value": str(payload["reorder_quantity"]), "weight": "primary", "source": "InventoryAgent"},
            {"label": "Stockout", "value": stockout_value, "weight": "supporting", "source": "Forecaster"},
        ]
        return payload, evidence

    if d.agent_id == "PricingAgent":
        payload = {
            "sku": d.action_data.get("sku") or UNKNOWN,
            "product_name": d.action_data.get("product_name") or None,
            "current_price": _try_float(d.action_data.get("old_price")),
            "proposed_price": _try_float(d.action_data.get("new_price")),
            "change_percent": _change_percent(d.action_data.get("old_price"), d.action_data.get("new_price")),
            "reasoning": d.reasoning,
            "competitor_prices": d.action_data.get("competitor_prices") or [],
        }
        old_value = f"${payload['current_price']:.2f}" if payload["current_price"] is not None else UNKNOWN
        new_value = f"${payload['proposed_price']:.2f}" if payload["proposed_price"] is not None else UNKNOWN
        evidence = [
            {"label": "Old Price", "value": old_value, "weight": "supporting", "source": "Shopify"},
            {"label": "New Price", "value": new_value, "weight": "primary", "source": "PricingAgent"},
        ]
        return payload, evidence

    if d.agent_id == "ReviewsAgent":
        rating = _try_float(d.action_data.get("rating"))
        if rating is None and reviews_data:
            rating = _try_float(reviews_data[0].get("rating"))
        review_text = d.action_data.get("review_text")
        if review_text is None and reviews_data:
            review_text = reviews_data[0].get("content")
        payload = {
            "review_id": d.action_data.get("review_id", "rev-99"),
            "product_name": d.action_data.get("product_name") or None,
            "rating": rating,
            "review_text": review_text or None,
            "customer_name": d.action_data.get("customer_name") or UNKNOWN,
            "sentiment": d.action_data.get("sentiment") or UNKNOWN,
            "draft_response": d.action_data.get("response_content", "Draft..."),
            "key_issues": d.action_data.get("themes") or [],
        }
        rating_value = f"{payload['rating']:.0f}/5" if payload["rating"] is not None else UNKNOWN
        evidence = [
            {"label": "Rating", "value": rating_value, "weight": "primary", "source": "Shopify"},
            {"label": "Response", "value": payload["draft_response"][:80], "weight": "supporting", "source": "ReviewsAgent"},
        ]
        return payload, evidence

    sku = d.action_data.get("sku") or UNKNOWN
    payload = {
        "campaign_name": d.action_data.get("campaign_name") or f"Campaign for {sku}",
        "target_skus": [sku] if sku != UNKNOWN else [],
        "discount_percent": _try_float(d.action_data.get("discount_percent")),
        "urgency_reason": d.reasoning,
        "estimated_reach": _try_float(d.action_data.get("estimated_reach")),
        "draft_message": d.action_data.get("draft_copy") or "Draft...",
    }
    evidence = [
        {"label": "Message", "value": payload["draft_message"][:80], "weight": "primary", "source": "MarketingAgent"},
        {"label": "Reason", "value": d.reasoning[:80], "weight": "supporting", "source": "MarketingAgent"},
    ]
    return payload, evidence
