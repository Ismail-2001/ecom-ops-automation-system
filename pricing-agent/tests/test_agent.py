"""
Tests for Price Optimization Agent
Run: pytest tests/ -v
"""

import pytest
from agent.pricing_agent import PriceOptimizationAgent, Product, BulkPriceRequest


@pytest.fixture
def agent():
    return PriceOptimizationAgent()


@pytest.fixture
def competitive_product():
    return Product(
        sku="HD-001",
        name="Wireless Headphones Pro",
        category="electronics",
        current_price=49.99,
        unit=25.00,
        competitor_price=44.99,
        daily_sales=15,
        monthly_sales=450,
        stock_level=200,
        demand_score=0.8,
        reviews_rating=4.5,
        seasonality="peak",
        product_age_days=120
    )


@pytest.fixture
def overstocked_product():
    return Product(
        sku="WT-002",
        name="Smart Watch Gen 1",
        category="electronics",
        current_price=199.99,
        unit=80.00,
        competitor_price=189.99,
        daily_sales=2,
        monthly_sales=60,
        stock_level=500,
        demand_score=0.2,
        seasonality="low",
        product_age_days=365
    )


@pytest.fixture
def premium_product():
    return Product(
        sku="PR-003",
        name="Premium Leather Bag",
        category="fashion",
        current_price=299.99,
        unit=100.00,
        competitor_price=349.99,
        daily_sales=5,
        monthly_sales=150,
        stock_level=80,
        demand_score=0.85,
        reviews_rating=4.8,
        seasonality="normal",
        product_age_days=60
    )


def test_agent_initialization(agent):
    assert agent is not None
    assert agent.config is not None


def test_product_model():
    p = Product(
        sku="TEST",
        name="Test",
        category="general",
        current_price=100.0,
        unit=50.0
    )
    assert p.sku == "TEST"
    assert p.current_price == 100.0


@pytest.mark.asyncio
async def test_analyze_competitive(agent, competitive_product):
    result = await agent.analyze(competitive_product)
    assert result.sku == "HD-001"
    assert result.strategy in ["competitive", "premium", "clearance", "dynamic"]
    assert result.risk_level in ["low", "medium", "high"]
    assert 0 <= result.confidence <= 1


@pytest.mark.asyncio
async def test_analyze_overstocked(agent, overstocked_product):
    result = await agent.analyze(overstocked_product)
    assert result.sku == "WT-002"
    assert result.current_price == 199.99


@pytest.mark.asyncio
async def test_analyze_premium(agent, premium_product):
    result = await agent.analyze(premium_product)
    assert result.sku == "PR-003"
    assert isinstance(result.requires_approval, bool)


@pytest.mark.asyncio
async def test_bulk_analysis(agent, competitive_product, overstocked_product):
    request = BulkPriceRequest(products=[competitive_product, overstocked_product])
    result = await agent.analyze_bulk(request)
    assert len(result.recommendations) == 2
    assert result.summary["total_products"] == 2
    assert "strategies_used" in result.summary


@pytest.mark.asyncio
async def test_competitor_insight(agent, competitive_product):
    result = await agent.get_competitor_insight(competitive_product)
    assert "market_position" in result
    assert "recommendation" in result


def test_rule_based_fallback(agent, competitive_product):
    result = agent._rule_based_fallback(competitive_product)
    assert result.sku == "HD-001"
    assert isinstance(result.price_change_percent, float)


@pytest.mark.asyncio
async def test_price_change_calculation(agent, competitive_product):
    result = await agent.analyze(competitive_product)
    expected_change = (result.recommended_price - competitive_product.current_price) / competitive_product.current_price * 100
    assert abs(result.price_change_percent - round(expected_change, 1)) < 0.01


def test_bulk_request_model():
    p = Product(sku="T1", name="Test1", category="gen", current_price=10.0, unit=5.0)
    req = BulkPriceRequest(products=[p], global_price_change_limit_percent=15.0)
    assert len(req.products) == 1
    assert req.global_price_change_limit_percent == 15.0