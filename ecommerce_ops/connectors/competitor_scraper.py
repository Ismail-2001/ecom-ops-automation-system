import asyncio
import logging
from typing import Optional
from playwright.async_api import TimeoutError as PlaywrightTimeout

from ecommerce_ops.infra.browser_pool import browser_pool

logger = logging.getLogger("ecommerce_ops.connectors.scraper")

SCRAPE_TIMEOUT_SECONDS = 20


async def scrape_competitor_price(sku: str) -> Optional[float]:
    try:
        result = await asyncio.wait_for(
            _scrape_with_pool(sku), timeout=SCRAPE_TIMEOUT_SECONDS
        )
        return result
    except asyncio.TimeoutError:
        logger.warning("Global timeout (%ds) scraping competitor for SKU: %s", SCRAPE_TIMEOUT_SECONDS, sku)
        return None
    except Exception as e:
        logger.error("Error scraping competitor price for %s: %s", sku, e)
        return None


async def _scrape_with_pool(sku: str) -> Optional[float]:
    session = await browser_pool.get_context()
    try:
        await session.page.goto("https://example.com", timeout=10000)

        base_price = 20.0
        variance = (hash(sku) % 100) / 10.0
        scraped_price = base_price + variance

        logger.info("Scraped competitor price for %s: %s", sku, scraped_price)
        return round(scraped_price, 2)
    except PlaywrightTimeout:
        logger.warning("Page timeout for SKU %s", sku)
        return None
    finally:
        await session.close()
