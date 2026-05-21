import pytest
import os
import json
from unittest.mock import MagicMock, patch, AsyncMock
from ecommerce_ops.agents.pricing import PricingAgent

os.environ["DEEPSEEK_API_KEY"] = "sk-dummy-key"

@pytest.fixture
def mock_state():
    with open("tests/fixtures/shopify_data.json", "r") as f:
        data = json.load(f)
    
    return {
        "inventory_data": data["inventory"],
        "decisions": [],
    }

@pytest.mark.asyncio
async def test_pricing_agent_scrapes_and_adjusts(mock_state):
    # Mock the scraper and cache to return a low competitor price (e.g. 21.00)
    with patch("ecommerce_ops.agents.pricing.scrape_competitor_price", new_callable=AsyncMock) as mock_scrape, \
         patch("ecommerce_ops.agents.pricing.cache.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("ecommerce_ops.agents.pricing.cache.set", new_callable=AsyncMock) as mock_cache_set:
         
        # Simulate cache miss then successful scrape
        mock_cache_get.return_value = None
        mock_scrape.return_value = 21.00
        
        agent = PricingAgent()
        updated_state = await agent.run(mock_state)
        
        decisions = updated_state["decisions"]
        
        # TSHIRT-BLUE-L current price is 25.00
        # Competitor is 21.00. 
        # Floor is 25 * 0.8 = 20.00.
        # New price should be max(21.00, 20.00) = 21.00.
        # TSHIRT-RED-M current is 25.00. New price 21.00.
        # MUG-WHITE current is 12.00. Competitor 21.00 is NOT < 12.00. No adjustment.
        
        pricing_decisions = [d for d in decisions if d.action_type == "UPDATE_PRICE"]
        assert len(pricing_decisions) >= 1
        
        blue_tshirt_decision = next((d for d in pricing_decisions if d.action_data["sku"] == "TSHIRT-BLUE-L"), None)
        assert blue_tshirt_decision is not None
        assert blue_tshirt_decision.action_data["new_price"] == 21.00
        
        mock_scrape.assert_called()
        mock_cache_set.assert_called()
