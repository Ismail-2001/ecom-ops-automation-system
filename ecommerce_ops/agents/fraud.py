from typing import Dict, Any, List
from ecommerce_ops.agents._base import BaseAgent

class FraudAgent(BaseAgent):
    def __init__(self):
        super().__init__("FraudAgent")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        orders = state.get("active_orders", [])
        decisions = []

        for order in orders:
            risk_score = self._calculate_risk(order)
            
            if risk_score > 70:
                decision = self.create_decision(
                    action_type="HOLD_ORDER",
                    reasoning=f"High risk score ({risk_score}/100) detected based on IP/Shipping address mismatch and order velocity.",
                    data={
                        "order_id": order.get("id"),
                        "risk_score": risk_score,
                        "risk_factors": ["ip_shipping_mismatch", "velocity_threshold_breached"]
                    },
                    confidence=0.9,
                    requires_approval=True # Always HITL for holds unless obvious fraud
                )
                decisions.append(decision)

        state["decisions"] = state.get("decisions", []) + decisions
        return state

    def _calculate_risk(self, order: Dict[str, Any]) -> int:
        """Heuristic risk scoring."""
        # Mock risk scoring
        if order.get("id") == "o_suspicious":
            return 85
        return 5
