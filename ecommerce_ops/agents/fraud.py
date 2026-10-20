from typing import Any, Dict, List

import structlog

from ecommerce_ops.agents._base import BaseAgent
from ecommerce_ops.cod.phone import sanitize_phone

logger = structlog.get_logger(__name__)

FRAUD_RULES = {
    "o_suspicious": {
        "score": 85,
        "factors": ["ip_shipping_mismatch", "velocity_threshold_breached"],
    },
    "o_high_value": {"score": 60, "factors": ["amount_above_threshold"]},
}

# COD phone-signal penalties (Phase 3). An unparseable number is the stronger
# signal (checkout capture is broken or forged); a well-formed but risky number
# only warrants an OTP step-up challenge.
PHONE_INVALID_PENALTY = 40
PHONE_STEP_UP_PENALTY = 25


def _extract_phone(order: Dict[str, Any]) -> str | None:
    """Find the checkout phone on the order, customer, or shipping address.

    Blank/whitespace values count as absent so a missing field never penalises
    an otherwise clean order.
    """
    customer = order.get("customer")
    shipping = order.get("shipping_address")
    for source in (order, customer, shipping):
        if not isinstance(source, dict):
            continue
        raw = source.get("phone")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def _phone_risk(phone: str) -> tuple[int, str | None]:
    """Score a raw phone via the Pakistani sanitizer.

    Returns ``(penalty, factor_name)`` — ``(0, None)`` for a clean number.
    """
    sanitized = sanitize_phone(phone)
    if not sanitized.is_valid:
        return PHONE_INVALID_PENALTY, "invalid_phone_number"
    if sanitized.is_suspicious:
        return PHONE_STEP_UP_PENALTY, "suspicious_phone_number"
    return 0, None


class FraudAgent(BaseAgent):
    def __init__(self):
        super().__init__("FraudAgent")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        orders = state.get("active_orders", [])
        decisions = []

        for order in orders:
            risk_score, risk_factors = self._assess_risk(order)

            if risk_score > 50:
                requires_hitl = risk_score >= 70
                conf = min(0.5 + risk_score / 200, 0.95)

                decision = self.create_decision(
                    action_type="HOLD_ORDER",
                    reasoning=(
                        f"Risk score {risk_score}/100. "
                        f"Factors: {', '.join(risk_factors)}. "
                        f"Order {order.get('id')} flagged for review."
                    ),
                    data={
                        "order_id": order.get("id"),
                        "risk_score": risk_score,
                        "risk_factors": risk_factors,
                    },
                    confidence=conf,
                    requires_approval=requires_hitl,
                )
                decisions.append(decision)
                await self.persist_decision(decision)

        state["decisions"] = state.get("decisions", []) + decisions
        return state

    def _assess_risk(self, order: Dict[str, Any]) -> tuple[int, List[str]]:
        order_id = order.get("id", "")
        rules = FRAUD_RULES.get(order_id)
        if rules:
            return rules["score"], rules["factors"]

        base_score = 50
        factors = []
        raw_phone = _extract_phone(order)
        if raw_phone is not None:
            penalty, factor = _phone_risk(raw_phone)
            if factor is not None:
                base_score += penalty
                factors.append(factor)
        if order.get("order_total", 0) > 1000:
            base_score += 20
            factors.append("amount_above_threshold")
        if len(order.get("line_items", [])) > 10:
            base_score += 10
            factors.append("bulk_order")
        return min(base_score, 100), factors or ["standard_check"]
