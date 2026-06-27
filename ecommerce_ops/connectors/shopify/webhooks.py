"""
Shopify Webhook Validator and Router
Validates HMAC signatures and routes events to handlers.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional

from ecommerce_ops.config import settings

logger = logging.getLogger("ecommerce_ops.connectors.shopify.webhooks")


class WebhookEvent:
    """Parsed Shopify webhook event."""

    topic: str
    shop_domain: str
    api_version: str
    body: Dict[str, Any]
    headers: Dict[str, str]
    received_at: float

    def __init__(
        self,
        topic: str,
        shop_domain: str,
        api_version: str,
        body: Dict[str, Any],
        headers: Dict[str, str],
    ):
        self.topic = topic
        self.shop_domain = shop_domain
        self.api_version = api_version
        self.body = body
        self.headers = headers
        self.received_at = time.time()


# Type alias for webhook handler functions
WebhookHandler = Callable[[WebhookEvent], Coroutine[Any, Any, None]]


class ShopifyWebhookRouter:
    """Routes Shopify webhook events to registered handlers."""

    def __init__(self):
        self._handlers: Dict[str, List[WebhookHandler]] = {}
        self._shopify_oauth = None

    def _get_oauth(self):
        """Lazy import to avoid circular dependencies."""
        if self._shopify_oauth is None:
            from ecommerce_ops.connectors.shopify.oauth import shopify_oauth
            self._shopify_oauth = shopify_oauth
        return self._shopify_oauth

    def register(self, topic: str, handler: WebhookHandler):
        """Register a handler for a webhook topic."""
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append(handler)
        logger.debug("Registered handler for topic: %s", topic)

    def register_many(self, handlers: Dict[str, WebhookHandler]):
        """Register multiple handlers at once."""
        for topic, handler in handlers.items():
            self.register(topic, handler)

    def get_supported_topics(self) -> List[str]:
        """Get list of all registered webhook topics."""
        return list(self._handlers.keys())

    def verify_hmac(self, body: bytes, hmac_header: str) -> bool:
        """Verify HMAC signature from Shopify."""
        return self._get_oauth().verify_webhook(body, hmac_header)

    def parse_event(
        self,
        topic: str,
        shop_domain: str,
        body: bytes,
        headers: Dict[str, str],
    ) -> Optional[WebhookEvent]:
        """Parse raw webhook into a WebhookEvent."""
        try:
            body_dict = json.loads(body)
            api_version = headers.get("X-Shopify-Api-Version", "unknown")

            return WebhookEvent(
                topic=topic,
                shop_domain=shop_domain,
                api_version=api_version,
                body=body_dict,
                headers=headers,
            )
        except json.JSONDecodeError as e:
            logger.error("Failed to parse webhook body: %s", e)
            return None

    async def dispatch(self, event: WebhookEvent) -> Dict[str, Any]:
        """Dispatch event to registered handlers."""
        handlers = self._handlers.get(event.topic, [])

        if not handlers:
            logger.warning("No handlers for topic: %s", event.topic)
            return {"status": "no_handlers", "topic": event.topic}

        logger.info(
            "Dispatching webhook %s for shop %s to %d handler(s)",
            event.topic,
            event.shop_domain,
            len(handlers),
        )

        results = []
        for handler in handlers:
            try:
                await handler(event)
                results.append({"handler": handler.__name__, "status": "success"})
            except Exception as e:
                logger.error("Handler %s failed for %s: %s", handler.__name__, event.topic, e)
                results.append({"handler": handler.__name__, "status": "error", "error": str(e)})

        return {"status": "dispatched", "topic": event.topic, "results": results}

    async def handle_webhook(
        self,
        topic: str,
        shop_domain: str,
        body: bytes,
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Full webhook processing pipeline: verify → parse → dispatch."""
        # Step 1: Verify HMAC
        hmac_header = headers.get("X-Shopify-Hmac-SHA256", "")
        if hmac_header and not self.verify_hmac(body, hmac_header):
            logger.warning("Invalid HMAC for webhook from %s", shop_domain)
            return {"status": "unauthorized", "topic": topic}

        # Step 2: Parse event
        event = self.parse_event(topic, shop_domain, body, headers)
        if event is None:
            return {"status": "parse_error", "topic": topic}

        # Step 3: Dispatch
        return await self.dispatch(event)


# Singleton
webhook_router = ShopifyWebhookRouter()
