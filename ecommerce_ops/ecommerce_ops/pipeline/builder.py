from typing import Dict, Any, List


def build_payload_and_evidence(d, reviews_data: List[Dict]) -> tuple:
    """Extract payload and evidence from a decision based on agent type."""
    if d.agent_id == "FraudAgent":
        payload = {
            "order_id": d.action_data.get("order_id", "ORD-UNKNOWN"),
            "customer_name": "Valued Customer",
            "customer_email": "customer@vpnmail.net",
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
