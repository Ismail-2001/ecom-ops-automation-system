from typing import Dict, Any, List
from ecommerce_ops.agents._base import BaseAgent

class MarketingAgent(BaseAgent):
    def __init__(self):
        super().__init__("MarketingAgent")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identifies winning SKUs and drafts marketing materials.
        Always returns with requires_approval=True.
        """
        inventory = state.get("inventory_data", [])
        decisions = []

        # Identify hot sellers (heuristic: stock < 20 but positive velocity)
        for item in inventory:
            if 0 < item.get("stock", 0) < 20:
                decision = self.create_decision(
                    action_type="DRAFT_MARKETING_CAMPAIGN",
                    reasoning=f"High-velocity SKU {item.get('sku')} is running low. Proposing a 'Last Chance' campaign.",
                    data={
                        "sku": item.get("sku"),
                        "channel": "Email",
                        "draft_copy": f"Hurry! Only {item.get('stock')} left of {item.get('sku')}. Get yours before they are gone!"
                    },
                    confidence=0.8,
                    requires_approval=True
                )
                decisions.append(decision)

        state["decisions"] = state.get("decisions", []) + decisions
        return state
