# Fraud Detection Agent 🤖🛡️

**AI Employee #6** — AI-powered real-time fraud detection, risk scoring, and transaction analysis for ecommerce businesses.

## What It Does

- **Real-time Fraud Scoring**: Analyze orders instantly (0.0-1.0 risk score)
- **Hybrid Detection**: Rule-based pre-checks + LLM deep analysis
- **10 Risk Categories**: Payment, account, address, velocity, device, behavior, etc.
- **Temp Email Detection**: Auto-block known disposable email domains
- **Bulk Analysis**: Process entire order batches with velocity checks
- **Chargeback Prevention**: Flag accounts with history of chargebacks
- **Approval Rate Dashboard**: Track approve/flag/reject ratios

## Quick Start

```bash
git clone https://github.com/Ismail-2001/fraud-detection-agent.git
cd fraud-detection-agent
cp .env.example .env

# Run with Docker
docker compose up -d

# Or locally
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8007
```

## Test It

```bash
curl -X POST http://localhost:8007/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-2024" \
  -d '{
    "order_id": "ORD-001",
    "customer_email": "sarah@example.com",
    "total": 149.99,
    "item_count": 3,
    "payment": {
      "method": "credit_card",
      "card_last_four": "4242",
      "ip_country": "US"
    },
    "shipping_address": {
      "street": "123 Main St",
      "city": "New York",
      "state": "NY",
      "country": "US"
    },
    "account_age_days": 365,
    "previous_orders": 12,
    "previous_chargebacks": 0,
    "is_guest_checkout": false
  }'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Agent info |
| GET | `/health` | Health check |
| POST | `/api/v1/analyze` | Single order analysis |
| POST | `/api/v1/bulk` | Bulk order analysis |

## Risk Decisions

| Decision | Risk Score | Action |
|----------|-----------|--------|
| **approve** | <0.3 | Process order normally |
| **flag** | 0.3-0.7 | Manual review recommended |
| **reject** | >0.7 | Block order, alert team |

## Rule-Based Pre-checks

| Signal | Action |
|--------|--------|
| Temp email domain | Auto-reject |
| >2 chargebacks | Auto-flag |
| New account + >$500 order | Extra scrutiny |
| Guest checkout + >$1000 | Auto-flag |
| >5 chargebacks | Definitive reject |

## Pricing Plans

| Plan | Setup | Monthly |
|------|-------|---------|
| Starter | $1,500 | $500 |
| Growth | $3,000 | $1,000 |
| Enterprise | Custom | Custom |