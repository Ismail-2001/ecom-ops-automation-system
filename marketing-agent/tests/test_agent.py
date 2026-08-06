"""
Tests for Marketing Automation Agent
Run: pytest tests/ -v
"""

import pytest
from agent.marketing_agent import MarketingAutomationAgent, CampaignRequest, CustomerProfile, BulkCampaignRequest


@pytest.fixture
def agent():
    return MarketingAutomationAgent()


@pytest.fixture
def cart_abandonment():
    return CampaignRequest(
        trigger="cart_abandonment",
        customer=CustomerProfile(
            name="Sarah",
            email="sarah@example.com",
            segment="high_value",
            total_spent=450.0,
            total_orders=5
        ),
        campaign_type="email",
        cart_value=89.99
    )


@pytest.fixture
def post_purchase():
    return CampaignRequest(
        trigger="post_purchase",
        customer=CustomerProfile(
            name="John",
            email="john@example.com",
            segment="new",
            total_orders=1
        ),
        campaign_type="email"
    )


@pytest.fixture
def re_engagement():
    return CampaignRequest(
        trigger="re_engagement",
        customer=CustomerProfile(
            name="Mike",
            email="mike@example.com",
            segment="lapsed",
            total_spent=200.0,
            total_orders=3,
            days_since_last_purchase=90
        ),
        campaign_type="email"
    )


def test_agent_initialization(agent):
    assert agent is not None
    assert agent.config is not None


def test_campaign_request_model():
    req = CampaignRequest(trigger="manual")
    assert req.trigger == "manual"
    assert req.budget is None


@pytest.mark.asyncio
async def test_create_cart_abandonment_campaign(agent, cart_abandonment):
    result = await agent.create_campaign(cart_abandonment)
    assert result.campaign_id.startswith("CAMP-")
    assert result.trigger == "cart_abandonment"
    assert result.estimated_revenue > 0
    assert len(result.ab_test_variants) > 0
    assert len(result.content.subject) > 0
    assert result.target_segment == "high_value"


@pytest.mark.asyncio
async def test_create_post_purchase_campaign(agent, post_purchase):
    result = await agent.create_campaign(post_purchase)
    assert result.trigger == "post_purchase"
    assert result.campaign_cost > 0
    assert result.roi > 0


@pytest.mark.asyncio
async def test_create_re_engagement_campaign(agent, re_engagement):
    result = await agent.create_campaign(re_engagement)
    assert result.trigger == "re_engagement"
    assert result.target_segment == "lapsed"


@pytest.mark.asyncio
async def test_bulk_campaigns(agent, cart_abandonment, post_purchase, re_engagement):
    request = BulkCampaignRequest(campaigns=[cart_abandonment, post_purchase, re_engagement])
    result = await agent.create_bulk(request)
    assert len(result.results) == 3
    assert result.summary["total_campaigns"] == 3
    assert result.summary["total_estimated_revenue"] > 0
    assert result.summary["average_roi"] > 0
    assert "campaign_type_breakdown" in result.summary


@pytest.mark.asyncio
async def test_campaign_has_ab_test_variants(agent, cart_abandonment):
    result = await agent.create_campaign(cart_abandonment)
    assert len(result.ab_test_variants) >= 1
    for v in result.ab_test_variants:
        assert len(v.name) > 0
        assert len(v.subject) > 0
        assert len(v.expected_improvement) > 0


@pytest.mark.asyncio
async def test_campaign_content_complete(agent, post_purchase):
    result = await agent.create_campaign(post_purchase)
    c = result.content
    assert len(c.subject) > 0
    assert len(c.preview_text) > 0
    assert len(c.body) > 0
    assert len(c.cta_text) > 0


@pytest.mark.asyncio
async def test_multiple_triggers(agent):
    triggers = ["manual", "cart_abandonment", "post_purchase", "re_engagement"]
    for t in triggers:
        req = CampaignRequest(trigger=t, customer=CustomerProfile(name="Test", segment="new"))
        result = await agent.create_campaign(req)
        assert result.trigger == t
        assert result.estimated_reach > 0