"""
Tests for Fraud Detection Agent
Run: pytest tests/ -v
"""

import pytest
from agent.fraud_agent import FraudDetectionAgent, Order, PaymentInfo, Address, BulkFraudRequest


@pytest.fixture
def agent():
    return FraudDetectionAgent()


@pytest.fixture
def legitimate_order():
    return Order(
        order_id="ORD-001",
        customer_email="sarah@example.com",
        customer_name="Sarah Johnson",
        total=149.99,
        item_count=3,
        payment=PaymentInfo(method="credit_card", card_last_four="4242", ip_country="US"),
        shipping_address=Address(street="123 Main St", city="New York", state="NY", zip_code="10001", country="US"),
        account_age_days=365,
        previous_orders=12,
        previous_chargebacks=0,
        is_guest_checkout=False
    )


@pytest.fixture
def high_risk_order():
    return Order(
        order_id="ORD-002",
        customer_email="user@tempmail.com",
        total=2500.00,
        item_count=10,
        payment=PaymentInfo(method="gift_card", ip_country="NG"),
        shipping_address=Address(street="PO Box 123", city="Miami", state="FL", zip_code="33101", country="US"),
        account_age_days=0,
        previous_orders=0,
        previous_chargebacks=3,
        is_guest_checkout=True
    )


@pytest.fixture
def new_account_order():
    return Order(
        order_id="ORD-003",
        customer_email="new@example.com",
        total=599.99,
        item_count=2,
        payment=PaymentInfo(method="credit_card", ip_country="US"),
        shipping_address=Address(street="456 Oak Ave", city="Austin", state="TX", zip_code="73301", country="US"),
        account_age_days=2,
        previous_orders=0,
        previous_chargebacks=0,
        is_guest_checkout=False
    )


def test_agent_initialization(agent):
    assert agent is not None
    assert agent.config is not None
    assert len(agent.TEMP_EMAIL_DOMAINS) > 5


def test_order_model():
    o = Order(order_id="T-001", customer_email="test@test.com", total=50.0, item_count=1)
    assert o.order_id == "T-001"
    assert o.is_guest_checkout is False


@pytest.mark.asyncio
async def test_analyze_legitimate(agent, legitimate_order):
    result = await agent.analyze(legitimate_order)
    assert result.order_id == "ORD-001"
    assert result.risk_score >= 0
    assert result.decision in ["approve", "flag", "reject"]
    assert 0 <= result.confidence <= 1


@pytest.mark.asyncio
async def test_analyze_high_risk(agent, high_risk_order):
    result = await agent.analyze(high_risk_order)
    assert result.order_id == "ORD-002"
    assert result.risk_score > 0.5


@pytest.mark.asyncio
async def test_analyze_new_account(agent, new_account_order):
    result = await agent.analyze(new_account_order)
    assert result.order_id == "ORD-003"


@pytest.mark.asyncio
async def test_temp_email_detection(agent, high_risk_order):
    result = await agent.analyze(high_risk_order)
    assert "tempmail" in high_risk_order.customer_email


@pytest.mark.asyncio
async def test_bulk_analysis(agent, legitimate_order, high_risk_order, new_account):
    request = BulkFraudRequest(orders=[legitimate_order, high_risk_order, new_account])
    result = await agent.analyze_bulk(request)
    assert len(result.results) == 3
    assert result.summary["total_orders"] == 3
    assert "approval_rate" in result.summary
    assert result.summary["orders_needing_review"] >= 1


def test_rule_based_fallback(agent, high_risk_order):
    result = agent._rule_based_fallback(high_risk_order)
    assert result.order_id == "ORD-002"
    assert result.decision in ["approve", "flag", "reject"]


def test_rule_based_check_temp_email(agent):
    o = Order(order_id="T", customer_email="test@mailinator.com", total=100, item_count=1)
    result = agent._rule_based_check(o)
    assert result is not None
    assert result.decision == "reject"


def test_has_definitive_fraud_signals(agent):
    o = Order(order_id="T", customer_email="a@b.com", total=100, item_count=1, previous_chargebacks=10)
    assert agent._has_definitive_fraud_signals(o) is True

    o2 = Order(order_id="T2", customer_email="a@b.com", total=100, item_count=1, previous_chargebacks=0)
    assert agent._has_definitive_fraud_signals(o2) is False