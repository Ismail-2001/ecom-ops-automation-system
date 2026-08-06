# Review Moderation Agent 🤖⭐

**AI Employee #4** — AI-powered review analysis, sentiment detection, and automated response drafting for ecommerce businesses.

## What It Does

- **Sentiment Analysis**: Detect Positive, Neutral, Negative sentiment with confidence scoring
- **Theme Extraction**: Identify key topics (Quality, Shipping, Support, etc.)
- **Auto Response Drafting**: Generate brand-voice responses for every review
- **Bulk Analysis**: Process hundreds of reviews at once
- **Fake Review Detection**: Flag suspicious or spam reviews
- **Trend Analysis**: Track sentiment trends over time
- **Actionable Insights**: Extract product improvement opportunities

## Quick Start

```bash
git clone https://github.com/Ismail-2001/review-moderation-agent.git
cd review-moderation-agent
cp .env.example .env

# Run with Docker
docker compose up -d

# Or locally
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8004
```

## Test It

```bash
curl -X POST http://localhost:8004/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-2024" \
  -d '{
    "review_id": "REV-001",
    "customer_name": "Sarah",
    "rating": 5,
    "title": "Amazing product!",
    "content": "I absolutely love this product! The quality is incredible and shipping was super fast.",
    "product_name": "Wireless Headphones Pro",
    "verified_purchase": true,
    "platform": "shopify"
  }'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Agent info |
| GET | `/health` | Health check |
| POST | `/api/v1/analyze` | Single review analysis |
| POST | `/api/v1/bulk` | Bulk review analysis |
| POST | `/api/v1/trends` | Review trend analysis |
| POST | `/api/v1/fake-detect` | Fake review detection |

## Response Example

```json
{
  "review_id": "REV-001",
  "rating": 5,
  "sentiment": "Positive",
  "sentiment_score": 0.85,
  "themes": ["Quality", "Value", "Shipping"],
  "customer_emotion": "happy",
  "urgency": "low",
  "suggested_response": "Thank you so much for your amazing review!...",
  "contains_refund_offer": false,
  "requires_human_review": false,
  "confidence": 0.92,
  "category": "product_quality",
  "actionable_insights": ["Product quality consistently praised"]
}
```

## Pricing Plans

| Plan | Setup | Monthly |
|------|-------|---------|
| Starter | $1,500 | $500 |
| Growth | $3,000 | $1,000 |
| Enterprise | Custom | Custom |