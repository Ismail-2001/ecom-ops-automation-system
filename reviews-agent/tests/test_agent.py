"""
Tests for Review Moderation Agent
Run: pytest tests/ -v
"""

import pytest
from agent.reviews_agent import ReviewModerationAgent, Review, BulkReviewRequest


@pytest.fixture
def agent():
    return ReviewModerationAgent()


@pytest.fixture
def positive_review():
    return Review(
        review_id="REV-001",
        customer_name="Sarah",
        rating=5,
        title="Amazing product!",
        content="I absolutely love this product! The quality is incredible and shipping was super fast. Highly recommend!",
        product_name="Wireless Headphones",
        verified_purchase=True,
        platform="shopify"
    )


@pytest.fixture
def negative_review():
    return Review(
        review_id="REV-002",
        customer_name="Mike",
        rating=1,
        title="Terrible experience",
        content="Product arrived broken. Customer service was unhelpful and refused to issue a refund. Worst experience ever.",
        product_name="Wireless Headphones",
        verified_purchase=True
    )


@pytest.fixture
def neutral_review():
    return Review(
        review_id="REV-003",
        customer_name="John",
        rating=3,
        title="It's okay",
        content="Product works as expected but not amazing quality for the price. Shipping was on time though.",
        product_name="Wireless Headphones",
        verified_purchase=True
    )


@pytest.fixture
def short_review():
    return Review(
        review_id="REV-004",
        customer_name="Test",
        rating=4,
        title="OK",
        content="Good",
        product_name="Test Product",
        verified_purchase=False
    )


def test_agent_initialization(agent):
    assert agent is not None
    assert agent.config is not None


def test_review_model():
    r = Review(
        review_id="T-001",
        rating=5,
        content="Great product!"
    )
    assert r.review_id == "T-001"
    assert r.rating == 5
    assert r.language == "en"


@pytest.mark.asyncio
async def test_analyze_positive(agent, positive_review):
    result = await agent.analyze(positive_review)
    assert result.review_id == "REV-001"
    assert result.sentiment == "Positive"
    assert result.rating == 5
    assert len(result.suggested_response) > 0


@pytest.mark.asyncio
async def test_analyze_negative(agent, negative_review):
    result = await agent.analyze(negative_review)
    assert result.review_id == "REV-002"
    assert result.sentiment == "Negative"
    assert result.requires_human_review is True


@pytest.mark.asyncio
async def test_analyze_short_review(agent, short_review):
    result = await agent.analyze(short_review)
    assert result.review_id == "REV-004"
    assert result.confidence <= 0.5


@pytest.mark.asyncio
async def test_bulk_analysis(agent, positive_review, negative_review, neutral_review):
    request = BulkReviewRequest(reviews=[positive_review, negative_review, neutral_review])
    result = await agent.analyze_bulk(request)
    assert len(result.results) == 3
    assert result.summary["total_reviews"] == 3
    assert "sentiment_distribution" in result.summary
    assert result.summary["positive_pct"] > 0


@pytest.mark.asyncio
async def test_trends(agent, positive_review, negative_review):
    trend = await agent.get_trends([positive_review, negative_review])
    assert trend.total_reviews == 2
    assert trend.average_rating > 0


@pytest.mark.asyncio
async def test_fake_detection(agent, positive_review):
    result = await agent.detect_fake_review(positive_review)
    assert "is_fake" in result
    assert "confidence" in result


@pytest.mark.asyncio
async def test_rating_sentiment_alignment(agent):
    r5 = Review(review_id="R5", rating=5, content="This is good")
    r1 = Review(review_id="R1", rating=1, content="This is bad")
    a5 = await agent.analyze(r5)
    a1 = await agent.analyze(r1)
    assert a5.sentiment == "Positive"
    assert a1.sentiment == "Negative"


def test_fallback_response(agent):
    r = agent._fallback_response(5)
    assert "Thank" in r
    r = agent._fallback_response(1)
    assert "sorry" in r.lower()
    r = agent._fallback_response(3)
    assert "feedback" in r.lower()