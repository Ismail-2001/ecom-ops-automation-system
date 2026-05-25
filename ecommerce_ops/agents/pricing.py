from typing import Dict, Any, Optional
from ecommerce_ops.agents._base import BaseAgent
from ecommerce_ops.config import settings
from ecommerce_ops.connectors.competitor_scraper import scrape_competitor_price
from ecommerce_ops.memory import cache
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
            
            # Step 1: Competitor Check (Scraper logic with Redis caching)
            competitor_price = await self._get_competitor_price(sku)
            
            # Step 2: Band enforcement (Example: ±20% from settings)
            floor = current_price * (1 - settings.GLOBAL_PRICE_CHANGE_LIMIT_PERCENT / 100)
            ceiling = current_price * (1 + settings.GLOBAL_PRICE_CHANGE_LIMIT_PERCENT / 100)
            
            if competitor_price is None:
                logger.info(f"Skipping {sku}: no competitor price available")
                continue

            if competitor_price < current_price:
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

        state["decisions"] = state.get("decisions", []) + decisions
        return state

    async def _get_competitor_price(self, sku: str) -> Optional[float]:
        cache_key = f"competitor_price:{sku}"

        cached_price = await cache.get(cache_key)
        if cached_price is not None:
            logger.info(f"Cache hit for {sku} competitor price: {cached_price}")
            return float(cached_price)

        price = await scrape_competitor_price(sku)
        if price is not None:
            await cache.set(cache_key, price, ttl=3600)
            return price

        logger.warning(f"No competitor price available for {sku}")
        return None

