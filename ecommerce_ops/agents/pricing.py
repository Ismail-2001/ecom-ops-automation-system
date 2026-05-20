from typing import Dict, Any
from ecommerce_ops.agents._base import BaseAgent
from ecommerce_ops.config import settings
import structlog

logger = structlog.get_logger(__name__)

class PricingAgent(BaseAgent):
    def __init__(self):
        super().__init__("PricingAgent")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the pricing analysis:
        1. Fetch competitor prices (scraped).
        2. Check margin targets and floor/ceiling bands.
        3. Propose price adjustments.
        """
        inventory = state.get("inventory_data", [])
        decisions = []

        for item in inventory:
            current_price = float(item.get("price", 0))
            sku = item.get("sku")
            
            # Step 1: Competitor Check (Scraper logic would go here)
            competitor_price = await self._get_competitor_price(sku)
            
            # Step 2: Band enforcement (Example: ±20% from settings)
            floor = current_price * (1 - settings.GLOBAL_PRICE_CHANGE_LIMIT_PERCENT / 100)
            ceiling = current_price * (1 + settings.GLOBAL_PRICE_CHANGE_LIMIT_PERCENT / 100)
            
            if competitor_price and competitor_price < current_price:
                new_price = max(competitor_price, floor)
                if new_price != current_price:
                    decision = self.create_decision(
                        action_type="UPDATE_PRICE",
                        reasoning=f"Competitor price for {sku} is {competitor_price}. Adjusted current price {current_price} to {new_price} while staying within floor {floor}.",
                        data={
                            "sku": sku,
                            "old_price": current_price,
                            "new_price": new_price,
                            "variant_id": item.get("variant_id")
                        },
                        confidence=0.85,
                        requires_approval=abs(new_price - current_price) / current_price > 0.05
                    )
                    decisions.append(decision)
                    self.log_audit(decision)

        state["decisions"] = state.get("decisions", []) + decisions
        return state

    async def _get_competitor_price(self, sku: str) -> float:
        """Playwright-based scraper placeholder."""
        # In production, this would use ecommerce_ops/connectors/competitor_scraper.py
        # For now, return a mock competitive price
        return 22.50 # Sample lower price
