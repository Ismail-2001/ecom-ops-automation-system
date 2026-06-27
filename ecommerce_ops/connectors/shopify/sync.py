"""
Shopify Data Sync Service
Synchronizes data between Shopify and our database.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_ops.connectors.shopify.client import ShopifyClient
from ecommerce_ops.connectors.shopify.models import (
    ShopifyCustomer,
    ShopifyOrder,
    ShopifyProduct,
    ShopifyVariant,
)

logger = logging.getLogger("ecommerce_ops.connectors.shopify.sync")


class ShopifySyncResult:
    """Result of a sync operation."""

    def __init__(self):
        self.products_synced = 0
        self.orders_synced = 0
        self.customers_synced = 0
        self.errors: List[str] = []
        self.started_at = time.time()
        self.completed_at: Optional[float] = None

    @property
    def duration_seconds(self) -> float:
        if self.completed_at:
            return self.completed_at - self.started_at
        return time.time() - self.started_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "products_synced": self.products_synced,
            "orders_synced": self.orders_synced,
            "customers_synced": self.customers_synced,
            "errors": self.errors,
            "duration_seconds": round(self.duration_seconds, 2),
        }


class ShopifySyncService:
    """Synchronizes Shopify data to local database."""

    def __init__(self, client: ShopifyClient):
        self.client = client

    async def sync_products(
        self,
        session: AsyncSession,
        since_id: Optional[int] = None,
        limit: int = 250,
    ) -> int:
        """Sync products from Shopify."""
        count = 0
        page_info = None

        while True:
            response = await self.client.get_products(limit=limit, page_info=page_info)
            products_data = response.get("products", [])

            if not products_data:
                break

            for product_data in products_data:
                try:
                    product = ShopifyProduct(**product_data)
                    await self._upsert_product(session, product)
                    count += 1
                except Exception as e:
                    logger.error("Failed to sync product %s: %s", product_data.get("id"), e)

            # Check for next page
            page_info = response.get("page_info")
            if not page_info:
                break

        await session.commit()
        logger.info("Synced %d products from Shopify", count)
        return count

    async def sync_orders(
        self,
        session: AsyncSession,
        status: str = "any",
        since_date: Optional[datetime] = None,
        limit: int = 250,
    ) -> int:
        """Sync orders from Shopify."""
        count = 0
        page_info = None

        while True:
            kwargs: Dict[str, Any] = {"status": status, "limit": limit}
            if page_info:
                kwargs["page_info"] = page_info
                kwargs.pop("limit", None)
            if since_date:
                kwargs["created_at_min"] = since_date.isoformat()

            response = await self.client.get_orders(**kwargs)
            orders_data = response.get("orders", [])

            if not orders_data:
                break

            for order_data in orders_data:
                try:
                    order = ShopifyOrder(**order_data)
                    await self._upsert_order(session, order)
                    count += 1
                except Exception as e:
                    logger.error("Failed to sync order %s: %s", order_data.get("id"), e)

            page_info = response.get("page_info")
            if not page_info:
                break

        await session.commit()
        logger.info("Synced %d orders from Shopify", count)
        return count

    async def sync_customers(
        self,
        session: AsyncSession,
        limit: int = 250,
    ) -> int:
        """Sync customers from Shopify."""
        count = 0
        page_info = None

        while True:
            response = await self.client.get_customers(limit=limit, page_info=page_info)
            customers_data = response.get("customers", [])

            if not customers_data:
                break

            for customer_data in customers_data:
                try:
                    customer = ShopifyCustomer(**customer_data)
                    await self._upsert_customer(session, customer)
                    count += 1
                except Exception as e:
                    logger.error(
                        "Failed to sync customer %s: %s", customer_data.get("id"), e
                    )

            page_info = response.get("page_info")
            if not page_info:
                break

        await session.commit()
        logger.info("Synced %d customers from Shopify", count)
        return count

    async def full_sync(self, session: AsyncSession) -> ShopifySyncResult:
        """Run full data sync (products, orders, customers)."""
        result = ShopifySyncResult()

        try:
            result.products_synced = await self.sync_products(session)
        except Exception as e:
            result.errors.append(f"Product sync failed: {e}")
            logger.error("Product sync failed: %s", e)

        try:
            result.orders_synced = await self.sync_orders(session)
        except Exception as e:
            result.errors.append(f"Order sync failed: {e}")
            logger.error("Order sync failed: %s", e)

        try:
            result.customers_synced = await self.sync_customers(session)
        except Exception as e:
            result.errors.append(f"Customer sync failed: {e}")
            logger.error("Customer sync failed: %s", e)

        result.completed_at = time.time()
        logger.info("Full sync completed: %s", result.to_dict())
        return result

    async def _upsert_product(self, session: AsyncSession, product: ShopifyProduct) -> None:
        """Insert or update product in database."""
        # TODO: Implement actual database upsert
        # This is a placeholder that shows the data flow
        logger.debug(
            "Upsert product: %s (%s) - $%.2f-%.2f, %d variants, %d inventory",
            product.title,
            product.id,
            product.min_price,
            product.max_price,
            len(product.variants),
            product.total_inventory,
        )

    async def _upsert_order(self, session: AsyncSession, order: ShopifyOrder) -> None:
        """Insert or update order in database."""
        logger.debug(
            "Upsert order: #%s (%s) - $%s %s [%s/%s]",
            order.order_number,
            order.id,
            order.total_price,
            order.currency,
            order.financial_status.value,
            order.fulfillment_status.value if order.fulfillment_status else "unfulfilled",
        )

    async def _upsert_customer(self, session: AsyncSession, customer: ShopifyCustomer) -> None:
        """Insert or update customer in database."""
        logger.debug(
            "Upsert customer: %s (%s) - %d orders, $%s spent",
            customer.full_name,
            customer.id,
            customer.orders_count,
            customer.total_spent,
        )
