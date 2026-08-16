"""Tests for Agent Factory — LLM + rule-based with fallback."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ecommerce_ops.agents.factory import AgentFactory, UnifiedAgent
from ecommerce_ops.agents.fraud import FraudAgent
from ecommerce_ops.agents.fraud_llm import FraudDetectionAgentLLM


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
    assert result["id"] == "o1"
    assert result["total"] == 100.0
    assert result["item_count"] == 0


def test_adapt_fraud_input_multiple_selects_highest_value(factory):
    orders = [{"id": "o1", "order_total": 50}, {"id": "o2", "order_total": 900}]
    result = factory._adapt_fraud_input({"active_orders": orders})
    assert result is not None
    assert result["id"] == "o2"
    assert result["total"] == 900.0


def test_adapt_inventory_input_empty(factory):
    result = factory._adapt_inventory_input({"inventory_data": []})
    assert result is None


def test_adapt_inventory_input_single(factory):
    item = {"sku": "X", "stock": 10, "price": 5.0, "variant_id": "v1"}
    result = factory._adapt_inventory_input({"inventory_data": [item]})
    assert result is not None
    assert result["sku"] == "X"
    assert result["current_stock"] == 10
    assert result["product_id"] == "v1"


def test_adapt_inventory_input_skips_non_dict_items(factory):
    result = factory._adapt_inventory_input({"inventory_data": ["junk"]})
    assert result is None


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
        "sku": "SKU-1",
        "reorder_quantity": 100,
        "confidence": 0.95,
        "urgency": "high",
        "demand_forecast": {"30_days": 60},
        "cost_impact": 500,
    })
    assert result is not None
    assert result["action_type"] == "DRAFT_PO"
    assert result["confidence"] == 0.95
    assert result["requires_approval"] is False
    assert result["data"]["sku"] == "SKU-1"
    assert result["data"]["quantity_to_order"] == 100


def test_adapt_inventory_output_low_confidence_requires_approval(factory):
    result = factory._adapt_inventory_output({
        "recommended_action": "reorder",
        "sku": "SKU-1",
        "reorder_quantity": 50,
        "confidence": 0.7,
    })
    assert result is not None
    assert result["requires_approval"] is True


def test_adapt_inventory_output_missing_sku_falls_back(factory):
    result = factory._adapt_inventory_output({
        "recommended_action": "reorder",
        "reorder_quantity": 50,
        "confidence": 0.9,
    })
    assert result is None


def test_adapt_inventory_output_zero_reorder_quantity_falls_back(factory):
    result = factory._adapt_inventory_output({
        "recommended_action": "reorder",
        "sku": "SKU-1",
        "reorder_quantity": 0,
        "confidence": 0.9,
    })
    assert result is None


def test_adapt_inventory_output_non_reorder_falls_back(factory):
    result = factory._adapt_inventory_output({
        "recommended_action": "clearance",
        "sku": "SKU-1",
        "reorder_quantity": 100,
        "confidence": 0.9,
    })
    assert result is None


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
