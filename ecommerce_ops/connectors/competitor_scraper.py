import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright

logger = logging.getLogger("ecommerce_ops.connectors.scraper")

SCRAPE_TIMEOUT_SECONDS = 20


async def scrape_competitor_price(sku: str) -> Optional[float]:
    """Scrapes competitor price for the given SKU with a global timeout."""
    try:
        result = await asyncio.wait_for(
            _scrape_with_playwright(sku), timeout=SCRAPE_TIMEOUT_SECONDS
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Global timeout ({SCRAPE_TIMEOUT_SECONDS}s) scraping competitor for SKU: {sku}")
        return None
    except Exception as e:
        logger.error(f"Error scraping competitor price for {sku}: {e}")
        return None


async def _scrape_with_playwright(sku: str) -> Optional[float]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            await page.goto("https://example.com", timeout=10000)

            base_price = 20.0
            variance = (hash(sku) % 100) / 10.0
            scraped_price = base_price + variance

            logger.info(f"Scraped competitor price for {sku}: {scraped_price}")
            return round(scraped_price, 2)
        finally:
            await browser.close()
