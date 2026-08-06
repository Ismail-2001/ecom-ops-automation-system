# Cart Recovery Agent 🤖🛒

**AI Employee #5** — AI-powered abandoned cart detection, recovery strategy optimization, and discount code generation.

## What It Does

- **Cart Analysis**: Analyze abandoned carts and determine recovery probability
- **Smart Strategies**: 6 recovery strategies (discount %, fixed, free shipping, urgency, social proof, personal outreach)
- **Discount Code Generation**: Unique, trackable discount codes for every cart
- **Bulk Analysis**: Process all abandoned carts at once with revenue estimation
- **Email Copy**: Auto-generate compelling recovery email content
- **Revenue Forecasting**: Estimate potential recovery revenue

## Quick Start

```bash
git clone https://github.com/Ismail-2001/cart-recovery-agent.git
cd cart-recovery-agent
cp .env.example .env

# Run with Docker
docker compose up -d

# Or locally
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8006
```

## Test It

```bash
curl -X POST http://localhost:8006/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-2024" \
  -d '{
    "cart_id": "CART-001",
    "customer": {
      "email": "sarah@example.com",
      "first_name": "Sarah",
      "total_orders": 3,
      "total_spent": 250.0,
      "is_repeat_customer": true
    },
    "items": [
      {"product_id": "P-001", "title": "Wireless Headphones", "quantity": 1, "price": 79.99, "total": 79.99},
      {"product_id": "P-002", "title": "Phone Case", "quantity": 2, "price": 19.99, "total": 39.98}
    ],
    "total_value": 119.97,
    "items_count": 3,
    "checkout_url": "https://store.com/checkout/token",
    "abandoned_hours": 2.5
  }'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Agent info |
| GET | `/health` | Health check |
| POST | `/api/v1/analyze` | Single cart analysis |
| POST | `/api/v1/bulk` | Bulk cart analysis |

## Recovery Strategies

| Strategy | Best For | Discount |
|----------|----------|----------|
| **discount_percent** | Carts >$200 | 5-20% off |
| **discount_fixed** | Carts $50-150 | $2-$15 off |
| **free_shipping** | Carts >$100 | Free shipping |
| **urgency** | Time-sensitive | Scarcity based |
| **social_proof** | Low value carts | Community FOMO |
| **personal_outreach** | VIP customers | Personal touch |

## Pricing Plans

| Plan | Setup | Monthly |
|------|-------|---------|
| Starter | $1,500 | $500 |
| Growth | $3,000 | $1,000 |
| Enterprise | Custom | Custom |