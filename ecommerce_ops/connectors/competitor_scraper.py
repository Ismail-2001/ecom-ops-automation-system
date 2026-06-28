"""
Competitor Price Scraper
Fetches real competitor prices from Google Shopping results.
Falls back to httpx if Playwright is unavailable.
"""

import asyncio
import hashlib
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger("ecommerce_ops.connectors.scraper")

SCRAPE_TIMEOUT_SECONDS = 15
GOOGLE_SHOPPING_URL = "https://www.google.com/search"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


async def scrape_competitor_price(sku: str) -> Optional[float]:
    """Scrape competitor price for a given SKU using Google Shopping."""
    try:
        result = await asyncio.wait_for(
            _fetch_price(sku), timeout=SCRAPE_TIMEOUT_SECONDS
        )
        return result
    except asyncio.TimeoutError:
        logger.warning("Timeout scraping competitor for SKU: %s", sku)
        return None
    except Exception as e:
        logger.error("Error scraping competitor price for %s: %s", sku, e)
        return None


async def _fetch_price(sku: str) -> Optional[float]:
    """Fetch price from Google Shopping search results."""
    query = f"{sku} buy price"
    params = {"q": query, "tbm": "shop"}
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}

    async with httpx.AsyncClient(follow_redirects=True, http2=True) as client:
        resp = await client.get(GOOGLE_SHOPPING_URL, params=params, headers=headers)
        resp.raise_for_status()

        prices = _extract_prices(resp.text)
        if not prices:
            logger.info("No prices found for SKU %s", sku)
            return None

        median_price = sorted(prices)[len(prices) // 2]
        logger.info("Scraped competitor price for %s: $%.2f (from %d results)", sku, median_price, len(prices))
        return round(median_price, 2)


def _extract_prices(html: str) -> list[float]:
    """Extract price values from Google Shopping HTML."""
    price_pattern = re.compile(r'\$(\d{1,5}(?:\.\d{2})?)')
    matches = price_pattern.findall(html)

    prices = []
    for match in matches:
        try:
            price = float(match)
            if 0.01 < price < 100_000:
                prices.append(price)
        except ValueError:
            continue
    return prices
