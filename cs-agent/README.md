# Customer Support Agent

AI-powered customer support automation for ecommerce

## Features

- Replace 60-80% of support tickets with AI
- REST API with OpenAPI docs
- Docker support
- Easy integration

## Quick Start

### 1. Clone and setup

```bash
git clone https://github.com/YOUR_USERNAME/cs-agent.git
cd cs-agent
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run with Docker

```bash
docker compose up -d
```

### 3. Or run locally

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8001
```

### 4. Test the API

```bash
curl http://localhost:8001/health

curl -X POST http://localhost:8001/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "T-1234",
    "customer_email": "user@example.com",
    "subject": "Order not received",
    "body": "I ordered 5 days ago and haven\'t received it yet."
  }'
```

## API Documentation

Once running, visit: `http://localhost:8001/docs`

## Pricing

| Plan | Price | Includes |
|------|-------|----------|
| Starter | $1,500 setup | 1 agent, basic integration |
| Growth | $3,000 setup + $1,000/mo | Full integration, support |
| Enterprise | Custom | Multi-agent, SLA |

## Contact

- Email: your@email.com
- LinkedIn: your-linkedin
