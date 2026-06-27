"""
Shopify API Routes
OAuth flow, webhooks, and sync endpoints.
"""

import logging
import secrets
import time
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_ops.config import settings
from ecommerce_ops.connectors.shopify.client import ShopifyClient
from ecommerce_ops.connectors.shopify.handlers.order_handlers import WEBHOOK_HANDLERS
from ecommerce_ops.connectors.shopify.oauth import shopify_oauth
from ecommerce_ops.connectors.shopify.sync import ShopifySyncService
from ecommerce_ops.connectors.shopify.webhooks import webhook_router
from ecommerce_ops.models import async_session_factory

logger = logging.getLogger("ecommerce_ops.api.shopify")

router = APIRouter(prefix="/shopify", tags=["shopify"])

# In-memory state store (production: use Redis)
_oauth_states: Dict[str, float] = {}
_oauth_states_max_age = 600  # 10 minutes


class InstallRequest(BaseModel):
    shop_domain: str


class WebhookPayload(BaseModel):
    topic: str
    shop_domain: str
    body: dict


class SyncResponse(BaseModel):
    status: str
    products_synced: int = 0
    orders_synced: int = 0
    customers_synced: int = 0
    duration_seconds: float = 0.0
    errors: list = []


# ── OAuth Flow ─────────────────────────────────────────────


@router.post("/install")
async def install_shopify(req: InstallRequest):
    """Start Shopify OAuth installation flow."""
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = time.time()

    url = shopify_oauth.get_install_url(req.shop_domain, state)
    logger.info("Generated install URL for %s", req.shop_domain)
    return {"url": url, "state": state}


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    hmac: str = Query(...),
    shop: str = Query(...),
    state: str = Query(...),
    timestamp: str = Query(...),
):
    """Handle OAuth callback from Shopify."""
    # Verify state
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    # Check timestamp freshness
    state_time = _oauth_states.pop(state)
    if time.time() - state_time > _oauth_states_max_age:
        raise HTTPException(status_code=400, detail="State expired")

    # Verify HMAC
    params = {
        "code": code,
        "hmac": hmac,
        "shop": shop,
        "state": state,
        "timestamp": timestamp,
    }
    if not shopify_oauth.verify_hmac(params, hmac):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")

    # Exchange code for token
    session = await shopify_oauth.exchange_code(shop, code)
    if not session:
        raise HTTPException(status_code=500, detail="Token exchange failed")

    # TODO: Store session in database (for now, log it)
    logger.info(
        "Shopify app installed: shop=%s, scope=%s",
        session.shop_domain,
        session.scope,
    )

    # Register webhook handlers
    webhook_router.register_many(WEBHOOK_HANDLERS)

    # Redirect to app dashboard
    return {
        "status": "success",
        "shop_domain": session.shop_domain,
        "message": "Shopify app installed successfully",
    }


# ── Webhooks ───────────────────────────────────────────────


@router.post("/webhooks/{topic:path}")
async def shopify_webhook(
    topic: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Handle incoming Shopify webhooks."""
    body = await request.body()
    headers = dict(request.headers)

    # Extract shop domain from headers or topic
    shop_domain = headers.get("x-shopify-shop-domain", "unknown")

    logger.info("Received webhook: topic=%s shop=%s", topic, shop_domain)

    # Process in background to respond quickly
    background_tasks.add_task(
        webhook_router.handle_webhook,
        topic=topic,
        shop_domain=shop_domain,
        body=body,
        headers=headers,
    )

    return {"status": "received", "topic": topic}


# ── Sync ───────────────────────────────────────────────────


@router.post("/sync", response_model=SyncResponse)
async def sync_shopify_data(
    background_tasks: BackgroundTasks,
    full: bool = Query(False, description="Full sync or incremental"),
):
    """Trigger data synchronization from Shopify."""
    from ecommerce_ops.config import settings as app_settings

    shop_domain = app_settings.SHOPIFY_SHOP_DOMAIN
    access_token = app_settings.SHOPIFY_ACCESS_TOKEN

    if not shop_domain or not access_token:
        raise HTTPException(
            status_code=400,
            detail="Shopify credentials not configured",
        )

    client = ShopifyClient(
        shop_domain=shop_domain,
        access_token=access_token,
        api_version=app_settings.SHOPIFY_API_VERSION,
    )

    sync_service = ShopifySyncService(client)

    async with async_session_factory() as session:
        result = await sync_service.full_sync(session)

    await client.close()

    return SyncResponse(
        status="completed",
        **result.to_dict(),
    )


# ── Status ─────────────────────────────────────────────────


@router.get("/status")
async def shopify_status():
    """Check Shopify integration status."""
    from ecommerce_ops.config import settings as app_settings

    configured = bool(app_settings.SHOPIFY_SHOP_DOMAIN and app_settings.SHOPIFY_ACCESS_TOKEN)

    return {
        "configured": configured,
        "shop_domain": app_settings.SHOPIFY_SHOP_DOMAIN if configured else None,
        "api_version": app_settings.SHOPIFY_API_VERSION,
        "webhook_topics": webhook_router.get_supported_topics(),
    }


# ── Products ───────────────────────────────────────────────


@router.get("/products")
async def list_shopify_products(
    limit: int = Query(50, ge=1, le=250),
):
    """List products from Shopify."""
    from ecommerce_ops.config import settings as app_settings

    if not app_settings.SHOPIFY_SHOP_DOMAIN or not app_settings.SHOPIFY_ACCESS_TOKEN:
        raise HTTPException(status_code=400, detail="Shopify not configured")

    client = ShopifyClient(
        shop_domain=app_settings.SHOPIFY_SHOP_DOMAIN,
        access_token=app_settings.SHOPIFY_ACCESS_TOKEN,
        api_version=app_settings.SHOPIFY_API_VERSION,
    )

    try:
        response = await client.get_products(limit=limit)
        return response
    finally:
        await client.close()


# ── Orders ─────────────────────────────────────────────────


@router.get("/orders")
async def list_shopify_orders(
    status: str = Query("any"),
    limit: int = Query(50, ge=1, le=250),
):
    """List orders from Shopify."""
    from ecommerce_ops.config import settings as app_settings

    if not app_settings.SHOPIFY_SHOP_DOMAIN or not app_settings.SHOPIFY_ACCESS_TOKEN:
        raise HTTPException(status_code=400, detail="Shopify not configured")

    client = ShopifyClient(
        shop_domain=app_settings.SHOPIFY_SHOP_DOMAIN,
        access_token=app_settings.SHOPIFY_ACCESS_TOKEN,
        api_version=app_settings.SHOPIFY_API_VERSION,
    )

    try:
        response = await client.get_orders(status=status, limit=limit)
        return response
    finally:
        await client.close()
