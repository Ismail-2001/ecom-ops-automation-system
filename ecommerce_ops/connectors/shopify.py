import asyncio
import logging
from typing import List, Dict, Any, Optional
from ecommerce_ops.config import settings

logger = logging.getLogger("ecommerce_ops.connectors.shopify")


class ShopifyConnector:
    def __init__(self):
        self.api_key = settings.SHOPIFY_API_KEY.get_secret_value() if settings.SHOPIFY_API_KEY else None
        self.password = settings.SHOPIFY_PASSWORD.get_secret_value() if settings.SHOPIFY_PASSWORD else None
        self.store_url = settings.SHOPIFY_STORE_URL
        self.api_version = settings.SHOPIFY_API_VERSION
        self._loop = asyncio.get_event_loop()

    async def _run_sync(self, func, *args, **kwargs):
        return await self._loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def _ensure_session(self):
        if not (self.api_key and self.password and self.store_url):
            logger.warning("Shopify credentials not configured")
            return
        import shopify
        session = shopify.Session(self.store_url, self.api_version, self.password)
        shopify.ShopifyResource.activate_session(session)

    async def get_inventory_levels(self) -> List[Dict[str, Any]]:
        import shopify
        await self._ensure_session()

        def _fetch():
            products = shopify.Product.find()
            inventory = []
            for p in products:
                for v in p.variants:
                    inventory.append({
                        "sku": v.sku,
                        "variant_id": v.id,
                        "product_title": p.title,
                        "inventory_item_id": v.inventory_item_id,
                        "stock": v.inventory_quantity,
                        "price": v.price,
                    })
            return inventory

        return await self._run_sync(_fetch)

    async def get_recent_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        import shopify
        await self._ensure_session()

        def _fetch():
            orders = shopify.Order.find(limit=limit, status="open")
            return [o.to_dict() for o in orders]

        return await self._run_sync(_fetch)

    async def get_recent_reviews(self) -> List[Dict[str, Any]]:
        return []

    async def update_variant_price(self, variant_id: str, new_price: float):
        import shopify
        await self._ensure_session()

        def _update():
            variant = shopify.Variant.find(variant_id)
            if variant:
                variant.price = str(new_price)
                variant.save()
                logger.info("Price updated: variant=%s price=%.2f", variant_id, new_price)

        await self._run_sync(_update)
