# Marketing Automation Agent 🤖📧

**AI Employee #7** — AI-powered campaign creation, audience segmentation, content optimization, and A/B testing for ecommerce businesses.

## What It Does

- **Campaign Creation**: Generate full campaigns from triggers (cart abandonment, post-purchase, re-engagement, etc.)
- **Audience Segmentation**: Target VIP, high-value, at-risk, new, lapsed, and cart abandoners
- **Content Generation**: Write personalized subject lines, body copy, and CTAs
- **A/B Testing**: Every campaign comes with test variants for optimization
- **ROI Estimation**: Calculate projected revenue, cost, and return on investment
- **Bulk Campaigns**: Create multiple campaigns at once

## Quick Start

```bash
git clone https://github.com/Ismail-2001/marketing-automation-agent.git
cd marketing-automation-agent
cp .env.example .env

# Run with Docker
docker compose up -d

# Or locally
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8005
```

## Test It (Cart Abandonment)

```bash
curl -X POST http://localhost:8005/api/v1/campaign/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-2024" \
  -d '{
    "trigger": "cart_abandonment",
    "customer": {
      "name": "Sarah",
      "email": "sarah@example.com",
      "segment": "high_value",
      "total_spent": 450.0,
      "total_orders": 5
    },
    "campaign_type": "email",
    "cart_value": 89.99
  }'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Agent info |
| GET | `/health` | Health check |
| POST | `/api/v1/campaign/create` | Create single campaign |
| POST | `/api/v1/campaign/bulk` | Create multiple campaigns |

## Campaign Triggers

| Trigger | Best For |
|---------|---------|
| **cart_abandonment** | Recover lost sales |
| **post_purchase** | Upsell/cross-sell |
| **re_engagement** | Win-back lapsed customers |
| **seasonal** | Holiday/time-based |
| **product_launch** | New arrivals |
| **manual** | Custom campaigns |

## Audience Segments

| Segment | Type | Priority |
|---------|------|----------|
| VIP | Top 10% spenders | High |
| high_value | Regular buyers 5+ orders | High |
| at_risk | No purchase 30-60 days | Medium |
| new | First 30 days | Medium |
| lapsed | 60+ days inactive | Low |
| cart_abandoner | Left items in cart | High |

## Example Response

```json
{
  "campaign_id": "CAMP-20260709-0001",
  "campaign_name": "Cart Recovery Campaign",
  "campaign_type": "email",
  "trigger": "cart_abandonment",
  "estimated_reach": 500,
  "estimated_ctr": 0.05,
  "estimated_revenue": 2000.0,
  "roi": 12.3,
  "content": {
    "subject": "Hey Sarah, your cart is waiting!",
    "body": "You left items worth $89.99 in your cart...",
    "cta_text": "Complete Your Order"
  },
  "ab_test_variants": [
    {"name": "Free Shipping", "expected_improvement": "+15%"}
  ]
}
```

## Pricing Plans

| Plan | Setup | Monthly |
|------|-------|---------|
| Starter | $1,500 | $500 |
| Growth | $3,000 | $1,000 |
| Enterprise | Custom | Custom |