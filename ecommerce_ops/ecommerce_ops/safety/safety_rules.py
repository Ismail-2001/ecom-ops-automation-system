from typing import Dict, Any, Tuple
from ecommerce_ops.models.db import StoreSettings, ApprovalAction

def evaluate_action_safety(
    agent_id: str,
    action_type: str,
    action_data: Dict[str, Any],
    confidence: float,
    settings: StoreSettings
) -> Tuple[bool, str, float]:
    """
    Evaluates safety rules for an agent decision.
    Returns (requires_hitl, risk_level, financial_impact).
    
    Risk levels: 'low', 'medium', 'high', 'critical'
    """
    # Default outputs
    requires_hitl = True
    risk_level = "low"
    financial_impact = 0.0

    # If shadow mode is globally active in database settings, everything requires HITL
    if settings.shadow_mode:
        requires_hitl = True

    if agent_id == "FraudAgent":
        # Fraud always requires HITL holds
        requires_hitl = True
        risk_level = "high"
        # Financial impact could be the total order cost held
        financial_impact = float(action_data.get("order_total", 0.0))

    elif agent_id == "InventoryAgent":
        # PO value threshold check
        total_value = float(action_data.get("total_po_value", 0.0))
        # If total_po_value is missing, check qty * cost
        if total_value == 0.0:
            qty = int(action_data.get("quantity_to_order", 0))
            # Assume a default unit cost of 20.0 if not specified
            unit_cost = float(action_data.get("unit_cost", 20.0))
            total_value = qty * unit_cost
        
        financial_impact = -total_value # Cost is negative impact
        
        if total_value > settings.po_limit:
            requires_hitl = True
            risk_level = "high" if total_value > (settings.po_limit * 5) else "medium"
        else:
            requires_hitl = False or settings.shadow_mode
            risk_level = "low"

    elif agent_id == "PricingAgent":
        # Price change percent check
        old_price = float(action_data.get("old_price", 1.0))
        new_price = float(action_data.get("new_price", 1.0))
        
        if old_price > 0:
            change_pct = abs(new_price - old_price) / old_price * 100
        else:
            change_pct = 0.0
            
        financial_impact = (new_price - old_price) * 100 # Mock potential monthly revenue impact
        
        # pricing_limit matches global_price_change_limit (default 5%)
        # blocked above 20%
        if change_pct > 20.0:
            requires_hitl = True
            risk_level = "critical" # Blocked or Critical risk
        elif change_pct > settings.pricing_limit:
            requires_hitl = True
            risk_level = "high" if change_pct > 12.0 else "medium"
        else:
            requires_hitl = False or settings.shadow_mode
            risk_level = "low"

    elif agent_id == "ReviewsAgent":
        # Rating checks
        rating = int(action_data.get("rating", 5))
        
        if rating < settings.reviews_rating_threshold: # Default < 4
            requires_hitl = True
            risk_level = "medium"
        else:
            requires_hitl = False or settings.shadow_mode
            risk_level = "low"

    elif agent_id == "MarketingAgent":
        # Marketing is always HITL, draft-only
        requires_hitl = True
        risk_level = "medium"
        financial_impact = 0.0 # Standard draft doesn't have immediate direct financial cost

    # Ensure risk_level is elevated if confidence score is low
    if confidence < 0.6 and risk_level == "low":
        risk_level = "medium"
        
    return requires_hitl, risk_level, financial_impact
