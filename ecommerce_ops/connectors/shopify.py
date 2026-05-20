import shopify
from typing import List, Dict, Any, Optional
from ecommerce_ops.config import settings
import structlog

logger = structlog.get_logger(__name__)

class ShopifyConnector:
    def __init__(self):
        self.api_key = settings.SHOPIFY_API_KEY.get_secret_value() if settings.SHOPIFY_API_KEY else None
        self.password = settings.SHOPIFY_PASSWORD.get_secret_value() if settings.SHOPIFY_PASSWORD else None
        self.store_url = settings.SHOPIFY_STORE_URL
        self.api_version = settings.SHOPIFY_API_VERSION
        
        if self.api_key and self.password and self.store_url:
            self._setup_session()

    def _setup_session(self):
        session = shopify.Session(self.store_url, self.api_version, self.password)
        shopify.ShopifyResource.activate_session(session)
        logger.info("Shopify session activated", store=self.store_url)

    async def get_inventory_levels(self) -> List[Dict[str, Any]]:
        """Fetch current stock levels for all product variants."""
        # Note: In a real implementation, pagination would be handled here
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
                    "price": v.price
                })
        return inventory

    async def get_recent_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent orders for fraud analysis."""
        orders = shopify.Order.find(limit=limit, status="open")
        return [o.to_dict() for o in orders]

    async def get_recent_reviews(self) -> List[Dict[str, Any]]:
        """Fetch product reviews (often requires a specific Shopify App or Metafield logic)."""
        # Placeholder as native Shopify doesn't have a uniform "Review" resource 
        # normally fetched via metafields or 3rd party apps like Judge.me
        return []

    async def update_variant_price(self, variant_id: str, new_price: float):
        """Update the price of a specific variant."""
        variant = shopify.Variant.find(variant_id)
        if variant:
            variant.price = str(new_price)
            variant.save()
            logger.info("Price updated", variant_id=variant_id, new_price=new_price)
