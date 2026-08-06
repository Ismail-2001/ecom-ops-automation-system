"""
Tests for Cart Recovery Agent
Run: pytest tests/ -v
"""

import pytest
from agent.cart_recovery_agent import CartRecoveryAgent, AbandonedCart, CartItem, CustomerProfile


@pytest.fixture
def agent():
    return CartRecoveryAgent()


@pytest.fixture
def high_value_cart():
    return AbandonedCart(
        cart_id="CART-001",
        customer=CustomerProfile(
            email="sarah@example.com",
            first_name="Sarah",
            total_orders=3,
            total_spent=250.0,
            is_repeat_customer=True
        ),
        items=[
            CartItem(product_id="P-001", title="Wireless Headphones", quantity=1, price=79.99, total=79.99),
            CartItem(product_id="P-002", title="Phone Case", quantity=2, price=19.99, total=39.98),
        ],
        total_value=119.97,
        items_count=3,
        checkout_url="https://store.com/checkout/token",
        abandoned_hours=2.5
    )


@pytest.fixture
def low_value_cart():
    return AbandonedCart(
        cart_id="CART-002",
        customer=CustomerProfile(email="john@example.com", first_name="John"),
        items=[CartItem(product_id="P-003", title="Sticker Pack", quantity=1, price=5.99, total=5.99)],
        total_value=5.99,
        items_count=1,
        abandoned_hours=48.0
    )


@pytest.fixture
def expired_cart():
    return AbandonedCart(
        cart_id="CART-003",
        items=[CartItem(product_id="P-004", title="Socks", quantity=1, price=12.99, total=12.99)],
        total_value=12.99,
        items_count=1,
        status="expired"
    )


def test_agent_initialization(agent):
    assert agent is not None
    assert agent.strategy_engine is not None
    assert agent.discount_generator is not None


def test_cart_model():
    c = AbandonedCart(cart_id="T-001", items=[], total_value=0, items_count=0)
    assert c.cart_id == "T-001"
    assert c.is_recoverable is True


def test_cart_not_recoverable():
    c = AbandonedCart(cart_id="T-002", items=[], total_value=0, items_count=0, status="expired")
    assert c.is_recoverable is False


def test_recovery_probability(agent, high_value_cart):
    prob = high_value_cart.recovery_probability
    assert 0 <= prob <= 1
    assert prob > 0.5  # High-value, repeat customer


@pytest.mark.asyncio
async def test_analyze_high_value(agent, high_value_cart):
    result = await agent.analyze(high_value_cart)
    assert result.cart_id == "CART-001"
    assert result.is_recoverable is True
    assert result.recovery_probability > 0
    assert result.estimated_revenue > 0
    assert len(result.reasoning) > 0


@pytest.mark.asyncio
async def test_analyze_low_value(agent, low_value_cart):
    result = await agent.analyze(low_value_cart)
    assert result.cart_id == "CART-002"
    assert result.total_value == 5.99


@pytest.mark.asyncio
async def test_analyze_expired(agent, expired_cart):
    result = await agent.analyze(expired_cart)
    assert result.cart_id == "CART-003"
    assert result.is_recoverable is False
    assert result.recovery_probability == 0


@pytest.mark.asyncio
async def test_bulk_analysis(agent, high_value_cart, low_value_cart, expired_cart):
    carts = [high_value_cart, low_value_cart, expired_cart]
    result = await agent.analyze_bulk(carts)
    assert result.summary["total_carts"] == 3
    assert result.summary["recoverable_carts"] == 2
    assert result.summary["total_potential_revenue"] > 0


def test_strategy_selection(agent):
    engine = agent.strategy_engine
    cart = AbandonedCart(cart_id="T", total_value=250, items_count=2, abandoned_hours=1)
    strategy = engine.select_strategy(cart)
    assert strategy.value in ["discount_percent", "discount_fixed", "free_shipping"]


def test_discount_generation(agent):
    cart = AbandonedCart(cart_id="TEST-001", items=[], total_value=100, items_count=1)
    from agent.cart_recovery_agent import RecoveryStrategy
    code = agent.discount_generator.generate(cart, RecoveryStrategy.DISCOUNT_PERCENT, 10)
    assert code.startswith("REC-")
    assert len(code) > 5


def test_email_generation(agent):
    ctx = {"customer_name": "Sarah", "cart_items": "Test Item (x1)", "cart_value": "$100", "discount_text": "10% OFF", "discount_code": "REC-TEST", "cta_text": "Buy Now", "checkout_url": ""}
    subject = agent._default_subject(ctx)
    body = agent._default_body(ctx)
    assert "Sarah" in subject or "Sarah" in body
    assert "10% OFF" in body or "10%" in body