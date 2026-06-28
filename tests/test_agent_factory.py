"""Tests for Agent Factory — LLM + rule-based with fallback."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ecommerce_ops.agents.factory import AgentFactory, UnifiedAgent
from ecommerce_ops.agents.fraud import FraudAgent
from ecommerce_ops.agents.fraud_llm import FraudDetectionAgentLLM
from ecommerce_ops.agents.inventory import InventoryAgent
from ecommerce_ops.agents.inventory_llm import InventoryManagementAgentLLM
from ecommerce_ops.agents.marketing import MarketingAgent
from ecommerce_ops.agents.marketing_llm import MarketingAutomationAgentLLM


@pytest.fixture
def factory():
    return AgentFactory()


@pytest.fixture
def mock_fraud_state():
    return {
        "active_orders": [{"id": "o1", "order_total": 1500, "line_items": [{"sku": "X"}] * 12}],
        "decisions": [],
    }


@pytest.fixture
def mock_inventory_state():
    return {
        "inventory_data": [{"sku": "TSHIRT", "stock": 5, "price": 25.0}],
        "active_orders": [{"id": "o1", "line_items": [{"sku": "TSHIRT", "quantity": 3}]}],
        "decisions": [],
    }


@pytest.fixture
def mock_marketing_state():
    return {
        "inventory_data": [{"sku": "TSHIRT", "stock": 3, "price": 25.0}],
        "decisions": [],
    }


# ── Factory Tests ─────────────────────────────────────────


def test_factory_creates_fraud_agent(factory):
    agent = factory.get_agent("fraud")
    assert isinstance(agent, UnifiedAgent)
    assert agent.name == "fraud"


def test_factory_creates_inventory_agent(factory):
    agent = factory.get_agent("inventory")
    assert isinstance(agent, UnifiedAgent)
    assert agent.name == "inventory"


def test_factory_creates_pricing_agent(factory):
    agent = factory.get_agent("pricing")
    assert isinstance(agent, UnifiedAgent)
    assert agent.name == "pricing"
    assert agent.llm_agent is None


def test_factory_creates_reviews_agent(factory):
    agent = factory.get_agent("reviews")
    assert isinstance(agent, UnifiedAgent)
    assert agent.name == "reviews"
    assert agent.llm_agent is None


def test_factory_creates_marketing_agent(factory):
    agent = factory.get_agent("marketing")
    assert isinstance(agent, UnifiedAgent)
    assert agent.name == "marketing"


def test_factory_caches_instances(factory):
    a1 = factory.get_agent("fraud")
    a2 = factory.get_agent("fraud")
    assert a1 is a2


def test_factory_unknown_agent_raises(factory):
    with pytest.raises(ValueError, match="Unknown agent"):
        factory.get_agent("nonexistent")


# ── UnifiedAgent LLM Fallback Tests ───────────────────────


@pytest.mark.asyncio
async def test_fraud_agent_falls_back_to_rules(factory, mock_fraud_state):
    with patch.object(FraudDetectionAgentLLM, "__init__", lambda s: None):
        agent = factory.get_agent("fraud")
        agent.llm_agent = MagicMock()
        agent.llm_agent.analyze = AsyncMock(side_effect=Exception("LLM down"))

        result = await agent.run(mock_fraud_state)
        assert "decisions" in result
        assert len(result["decisions"]) > 0


@pytest.mark.asyncio
async def test_fraud_agent_uses_llm_when_available(factory, mock_fraud_state):
    agent = factory.get_agent("fraud")
    mock_llm = MagicMock()
    mock_llm.analyze = AsyncMock(return_value={
        "risk_score": 0.85,
        "decision": "reject",
        "confidence": 0.9,
        "risk_factors": ["high_value"],
        "reasoning": "High risk order",
        "recommended_actions": ["hold"],
    })
    agent.llm_agent = mock_llm

    result = await agent.run(mock_fraud_state)
    assert "decisions" in result


@pytest.mark.asyncio
async def test_inventory_agent_falls_back_to_rules(factory, mock_inventory_state):
    agent = factory.get_agent("inventory")
    agent.llm_agent = MagicMock()
    agent.llm_agent.analyze = AsyncMock(side_effect=Exception("LLM down"))

    result = await agent.run(mock_inventory_state)
    assert "decisions" in result


@pytest.mark.asyncio
async def test_pricing_agent_always_rules(factory, mock_inventory_state):
    agent = factory.get_agent("pricing")
    assert agent.llm_agent is None

    with patch("ecommerce_ops.agents.factory.PricingAgent.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_inventory_state
        result = await agent.run(mock_inventory_state)
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_reviews_agent_always_rules(mock_review_state):
    factory = AgentFactory()
    agent = factory.get_agent("reviews")
    assert agent.llm_agent is None

    with patch("ecommerce_ops.agents.factory.ReviewsAgent.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_review_state
        result = await agent.run(mock_review_state)
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_marketing_agent_falls_back_to_rules(factory, mock_marketing_state):
    agent = factory.get_agent("marketing")
    agent.llm_agent = MagicMock()
    agent.llm_agent.create_campaign = AsyncMock(side_effect=Exception("LLM down"))

    result = await agent.run(mock_marketing_state)
    assert "decisions" in result


@pytest.mark.asyncio
async def test_agent_both_fail_returns_errors(factory, mock_fraud_state):
    agent = factory.get_agent("fraud")
    agent.llm_agent = MagicMock()
    agent.llm_agent.analyze = AsyncMock(side_effect=Exception("LLM down"))

    with patch.object(FraudAgent, "run", new_callable=AsyncMock, side_effect=Exception("Rules also broken")):
        result = await agent.run(mock_fraud_state)
        assert any(e["agent"] == "fraud" for e in result.get("errors", []))


# ── Input Adapter Tests ───────────────────────────────────


def test_adapt_fraud_input_empty(factory):
    result = factory._adapt_fraud_input({"active_orders": []})
    assert result is None


def test_adapt_fraud_input_single(factory):
    order = {"id": "o1", "order_total": 100}
    result = factory._adapt_fraud_input({"active_orders": [order]})
    assert result == order


def test_adapt_fraud_input_multiple(factory):
    orders = [{"id": "o1"}, {"id": "o2"}]
    result = factory._adapt_fraud_input({"active_orders": orders})
    assert result == orders


def test_adapt_inventory_input_empty(factory):
    result = factory._adapt_inventory_input({"inventory_data": []})
    assert result is None


def test_adapt_inventory_input_single(factory):
    item = {"sku": "X", "stock": 10}
    result = factory._adapt_inventory_input({"inventory_data": [item]})
    assert result == item


def test_adapt_marketing_input_no_low_stock(factory):
    result = factory._adapt_marketing_input({"inventory_data": [{"stock": 100}]})
    assert result is None


def test_adapt_marketing_input_low_stock(factory):
    result = factory._adapt_marketing_input({"inventory_data": [{"stock": 5}]})
    assert result is not None
    assert result["trigger"] == "low_stock"


# ── Output Adapter Tests ──────────────────────────────────


def test_adapt_fraud_output_approve(factory):
    result = factory._adapt_fraud_output({"decision": "approve"})
    assert result is None


def test_adapt_fraud_output_reject(factory):
    result = factory._adapt_fraud_output({
        "decision": "reject",
        "reasoning": "High risk",
        "confidence": 0.9,
        "risk_score": 0.85,
        "risk_factors": ["high_value"],
        "recommended_actions": ["hold"],
    })
    assert result is not None
    assert result["action_type"] == "HOLD_ORDER"
    assert result["confidence"] == 0.9


def test_adapt_inventory_output_maintain(factory):
    result = factory._adapt_inventory_output({"recommended_action": "maintain"})
    assert result is None


def test_adapt_inventory_output_reorder(factory):
    result = factory._adapt_inventory_output({
        "recommended_action": "reorder",
        "reasoning": "Low stock",
        "product_id": "P1",
        "reorder_quantity": 100,
        "urgency": "high",
        "demand_forecast": {},
        "cost_impact": 500,
    })
    assert result is not None
    assert result["action_type"] == "DRAFT_PO"


def test_adapt_marketing_output(factory):
    result = factory._adapt_marketing_output({
        "reasoning": "Campaign needed",
        "campaign_name": "Test",
        "campaign_type": "email",
        "target_audience": {},
        "content": {},
        "estimated_reach": 1000,
        "estimated_ctr": 0.05,
        "estimated_revenue": 5000,
    })
    assert result is not None
    assert result["action_type"] == "DRAFT_MARKETING_CAMPAIGN"
