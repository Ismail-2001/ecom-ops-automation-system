# Price Optimization Agent 🤖💰

**AI Employee #3** — AI-powered dynamic pricing and profit maximization for ecommerce businesses.

## What It Does

- **Smart Pricing**: AI recommends optimal prices based on market conditions
- **Competitor Analysis**: Track competitor pricing and respond intelligently  
- **Profit Maximization**: Balance volume vs margin for maximum profit
- **Bulk Analysis**: Price entire catalog in one API call
- **Risk Assessment**: Every recommendation has confidence + risk level
- **Approval Workflow**: Big changes (>5%) require human approval

## Quick Start

```bash
git clone https://github.com/Ismail-2001/price-optimization-agent.git
cd price-optimization-agent
cp .env.example .env

# Run with Docker
docker compose up -d

# Or locally
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8003
```

## Test It

```bash
curl -X POST http://localhost:8003/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-2024" \
  -d '{
    "sku": "HD-001",
    "name": "Wireless Headphones Pro",
    "category": "electronics",
    "current_price": 49.99,
    "unit": 25.00,
    "competitor_price": 44.99,
    "daily_sales": 15,
    "monthly_sales": 450,
    "stock_level": 200,
    "demand_score": 0.8
  }'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Agent info |
| GET | `/health` | Health check |
| POST | `/api/v1/analyze` | Single product pricing |
| POST | `/api/v1/bulk` | Bulk pricing analysis |
| POST | `/api/v1/competitor-insight` | Competitor insights |

## Pricing Strategies

| Strategy | When to Use | Impact |
|----------|-------------|--------|
| **competitive** | Competitor is cheaper | Match/slightly undercut |
| **premium** | High demand, good reviews | Maximize margin |
| **clearance** | Overstocked, old inventory | Quick liquidation |
| **discount** | Low demand, boost volume | Increase velocity |

## Response Example

```json
{
  "sku": "HD-001",
  "current_price": 49.99,
  "recommended_price": 44.99,
  "price_change_percent": -10.0,
  "profit_impact_monthly": 1250.0,
  "strategy": "competitive",
  "confidence": 0.85,
  "requires_approval": true,
  "risk_level": "medium"
}
```

## Pricing Plans

| Plan | Setup | Monthly |
|------|-------|---------|
| Starter | $1,500 | $500 |
| Growth | $3,000 | $1,000 |
| Enterprise | Custom | Custom |