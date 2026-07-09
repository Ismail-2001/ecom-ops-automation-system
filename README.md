<div align="center">

# OpsIQ

**Autonomous operations brain for e-commerce stores.**
Multi-agent AI system for fraud detection, inventory, pricing, marketing, cart recovery, and customer support — built on LangGraph, FastAPI, and Postgres, with production-grade observability and safety rails from day one.

[![CI/CD](https://github.com/Ismail-2001/ecom-ops-automation-system/actions/workflows/ci.yml/badge.svg)](https://github.com/Ismail-2001/ecom-ops-automation-system/actions/workflows/ci.yml)
[![Docker](https://github.com/Ismail-2001/ecom-ops-automation-system/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/Ismail-2001/ecom-ops-automation-system/actions/workflows/docker-publish.yml)
[![Security](https://github.com/Ismail-2001/ecom-ops-automation-system/actions/workflows/security.yml/badge.svg)](https://github.com/Ismail-2001/ecom-ops-automation-system/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Node 20](https://img.shields.io/badge/node-20-339933.svg)](frontend/package.json)

[Quick Start](#quick-start) · [Architecture](#architecture) · [API](#api-reference) · [Deployment](#deployment) · [Security](#security) · [Roadmap](#roadmap--known-limitations)

</div>

---

## What This Is

OpsIQ is not a chatbot bolted onto a Shopify store. It is a **decision-making system**: seven cooperating agents that watch orders, inventory, pricing, and support tickets in real time, propose actions, and — depending on configured confidence thresholds — either execute autonomously or queue for human approval.

Every agent ships in two forms:

- A **deterministic rules engine** (fast, auditable, zero API cost, always available as a fallback)
- An **LLM-reasoning variant** (`*_llm.py`) for cases where fixed rules break down — ambiguous fraud signals, nuanced support tickets, competitive pricing calls

A LangGraph supervisor coordinates both, and nothing ships to production traffic without passing through the guardrail layer first. That ordering — rules before reasoning, guardrails before autonomy — is the single design decision everything else in this repo is built around.

## Architecture

```
                              ┌───────────────────────────┐
                              │        CLIENT LAYER        │
                              │  Web · Mobile · 3rd-party   │
                              └──────────────┬─────────────┘
                                             │
                              ┌──────────────▼─────────────┐
                              │     NGINX REVERSE PROXY     │
                              │  TLS · Rate Limiting · LB    │
                              └──────────────┬─────────────┘
                                             │
                              ┌──────────────▼─────────────┐
                              │      FASTAPI APPLICATION     │
                              │  JWT/API-Key Auth · RBAC ·   │
                              │  Input Sanitization           │
                              └──────────────┬─────────────┘
                                             │
        ┌───────────┬───────────┬───────────┼───────────┬───────────┬───────────┐
        │  Shopify   │   Cart    │  Support  │  Memory   │ Security  │   Demo    │
        │Integration │ Recovery  │   Agent   │  System   │   RBAC    │    ROI    │
        └───────────┴───────────┴───────────┼───────────┴───────────┴───────────┘
                                             │
                              ┌──────────────▼─────────────┐
                              │        AGENT LAYER          │
                              │  LangGraph Supervisor        │
                              ├───────────┬───────────┬─────┤
                              │  Fraud    │ Inventory │Pricing│
                              │  Reviews  │ Marketing │ Cart  │
                              └───────────┴───────────┴─────┘
                                             │
                              ┌──────────────▼─────────────┐
                              │       INFRASTRUCTURE         │
                              │ Postgres(async)·Redis·Prom-  │
                              │ etheus·Grafana·Tempo·Langfuse │
                              └───────────────────────────┘
```

**Why this shape, specifically:**

- **Nginx in front of FastAPI, not instead of it** — TLS termination and rate limiting belong at the edge, not duplicated in application code.
- **Agents are pure functions over explicit state**, orchestrated by LangGraph rather than a bespoke event loop — state transitions are inspectable and replayable, which matters the day something goes wrong in production and you need to know *why* an agent did what it did.
- **Observability is not an afterthought bolted on later** — structured logging, OpenTelemetry traces, and Langfuse LLM-call tracing are wired in from the `agents/_base.py` layer up, so every agent decision is traceable to the prompt, tokens, and cost that produced it.

## Core Agents

| Agent | Mode | Responsibility |
|---|---|---|
| **Fraud Detection** | Rules + LLM | Real-time order risk scoring |
| **Inventory Management** | Rules + LLM | Stock-level monitoring, reorder signals |
| **Price Optimization** | Rules + LLM | Competitor-aware dynamic pricing |
| **Review Moderation** | Rules | Sentiment analysis, auto-response |
| **Marketing Automation** | Rules + LLM | Campaign trigger optimization |
| **Cart Recovery** | Rules | 5-strategy abandoned cart recovery |
| **Customer Support** | Rules + LLM | Sentiment-aware ticket routing and response |

All seven register through `agents/factory.py` and communicate over `agents/message_bus.py` — no agent calls another agent directly, which keeps the coupling low enough to delete or replace any single agent without a rewrite.

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | LangGraph 1.2.6 | Explicit, inspectable state graphs over implicit agent chains |
| LLM Providers | Gemini 2.0 Flash, DeepSeek | Cost-efficient defaults; provider is swappable via `LLM_MODEL` |
| API | FastAPI + Pydantic v2 | Async-first, typed at the boundary |
| Database | PostgreSQL 16 (async, SQLAlchemy 2.0) | Correctness under concurrent agent writes |
| Cache / Queue | Redis 7 | Session cache + task queue backing |
| Migrations | Alembic | No manual schema drift |
| Frontend | Next.js 14, Tailwind, TanStack Query, Zustand | Server-rendered dashboard, 13 pages, dark theme |
| Tracing | OpenTelemetry + Tempo + Langfuse | Infra traces *and* LLM-specific traces — different tools for different jobs |
| Metrics | Prometheus + Grafana | 16 custom metrics, pre-built dashboards |
| Browser Automation | Playwright | Competitor price scraping |

Full pinned versions: [`requirements.txt`](requirements.txt) / [`pyproject.toml`](pyproject.toml).

## Quick Start

### Prerequisites
Docker & Docker Compose · Python 3.11+ · Node 20+ (frontend only) · one LLM API key (Google or DeepSeek)

### Fastest path — demo environment

```bash
git clone https://github.com/Ismail-2001/ecom-ops-automation-system.git
cd ecom-ops-automation-system
cp .env.example .env               # set GOOGLE_API_KEY or DEEPSEEK_API_KEY

docker compose -f docker-compose.demo.yml up -d
docker compose -f docker-compose.demo.yml exec app alembic upgrade head
docker compose -f docker-compose.demo.yml exec app python -m ecommerce_ops.demo.seed

open http://localhost:8000   # API + docs at /docs
open http://localhost:3001   # Grafana — admin / demo
```

### Local development (editing code)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

uvicorn ecommerce_ops.api.app:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd frontend
npm install
npm run dev                  # → http://localhost:3000
```

### Verify before you change anything

```bash
pytest tests/ -x -q                          # backend
cd frontend && npx vitest run                # frontend unit
cd frontend && npx playwright test           # e2e
ruff check ecommerce_ops/ && mypy ecommerce_ops
```

## API Reference

<details>
<summary><strong>Core</strong></summary>

| Endpoint | Method | Description |
|---|---|---|
| `/api/decisions` | GET | Pending agent decisions |
| `/api/decisions/{id}/approve` | POST | Approve a decision |
| `/api/decisions/{id}/reject` | POST | Reject a decision |
| `/api/dashboard` | GET | Aggregate dashboard metrics |
| `/api/agents/status` | GET | Live agent status |
| `/api/metrics` | GET | Prometheus scrape endpoint |

</details>

<details>
<summary><strong>Shopify, Cart Recovery, Support, Memory, Security</strong></summary>

| Endpoint | Method | Description |
|---|---|---|
| `/api/shopify/auth/authorize` | GET | Start OAuth flow |
| `/api/shopify/auth/callback` | GET | OAuth callback |
| `/api/shopify/webhooks` | POST | Webhook ingestion |
| `/api/shopify/sync` | POST | Manual data sync trigger |
| `/api/cart-recovery/analyze` | POST | Score an abandoned cart |
| `/api/cart-recovery/recover` | POST | Execute recovery sequence |
| `/api/customer-support/tickets` | POST | Create ticket |
| `/api/customer-support/resolve` | POST | Resolve ticket |
| `/api/memory/store` / `/search` | POST | Vector memory read/write |
| `/api/security/users` / `/api-keys` / `/roles` | POST/GET | RBAC administration |

</details>

Full interactive schema at `/docs` (Swagger) once the app is running.

## Configuration

Every setting is centralized in `ecommerce_ops/config.py` via Pydantic `Settings` — no scattered `os.environ.get()` calls. Notable safety-relevant defaults:

```bash
SHADOW_MODE=true                        # agents propose, never execute, until explicitly disabled
GLOBAL_PO_LIMIT=1000.0                  # hard ceiling on autonomous purchase orders
GLOBAL_PRICE_CHANGE_LIMIT_PERCENT=20.0  # max autonomous price swing
AUTO_APPROVE_CONFIDENCE_SCORE=0.95      # below this, a human decides
```

Do not flip `SHADOW_MODE` to `false` in a new environment before reading `ecommerce_ops/safety/guardrails.py` end to end. This is the one file in the repo where a shortcut costs real money.

See [`.env.example`](.env.example) for the full variable list.

## Security

- **AuthN**: JWT (web), API keys (programmatic), header-based (service-to-service)
- **AuthZ**: RBAC — 5 roles (`super_admin` → `api_only`), 30+ granular permissions
- **Hardening**: HSTS, CSP, X-Frame-Options, request-body size limits, input sanitization against XSS/injection
- **Audit**: every privileged action logged with actor, target, and outcome — see `security/audit.py`
- **Credential hygiene**: see [`CREDENTIAL_ROTATION.md`](CREDENTIAL_ROTATION.md) before your first production deploy

Found a vulnerability? See [`SECURITY.md`](SECURITY.md) — do not open a public issue.

## Observability

| Signal | Tool | What it answers |
|---|---|---|
| Infra traces | OpenTelemetry → Tempo | Where did latency come from? |
| LLM traces | Langfuse | What prompt, tokens, cost, and output produced this decision? |
| Metrics | Prometheus → Grafana | Is the system healthy right now? |
| Alerts | Alertmanager | Who gets paged, and for what? |

16 custom Prometheus metrics ship out of the box, including `agent_decisions_total`, `agent_confidence_average`, and `fraud_alerts_total` — the metrics that answer "is the AI actually working" rather than just "is the server up."

## Testing

```bash
pytest tests/ --cov=ecommerce_ops --cov-report=term-missing
```

~8,900 lines of tests against ~36,000 lines of application code. Coverage is concentrated where it matters most: the guardrails, the supervisor graph, and the security layer — not evenly smeared across every file for the sake of a percentage.

## Deployment

Production deploy targets a single VPS via Docker Compose + Nginx + systemd — see [`DEPLOY.md`](DEPLOY.md) for the full Hostinger walkthrough, and [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the general case. Disaster recovery scripts (`scripts/backup-db.sh`, `restore-db.sh`, `disaster-recovery.sh`) are not decorative — run `scripts/verify-backup.sh` on a schedule, not just when you remember to.

## Project Structure

```
ecommerce_ops/
├── api/            # FastAPI routes — app.py is the entrypoint
├── agents/         # 7 agents, each rules-based + LLM variant
├── graph/          # LangGraph supervisor — the orchestration core
├── connectors/     # Shopify OAuth, sync, webhooks
├── memory/         # Vector store, sessions, semantic retrieval
├── safety/         # Guardrails — read before disabling shadow mode
├── security/       # RBAC, audit, auth
├── observability/  # Tracing, evaluation, Langfuse client
├── infra/          # Circuit breakers, retry, rate limiting, task queue
└── pipeline/       # Task builder/runner

frontend/           # Next.js 14 dashboard, 13 pages
alembic/            # Schema migrations
monitoring/         # Prometheus, Grafana, Tempo, Alertmanager config
tests/               # 8,900 lines — backend, load, e2e
```

## Roadmap & Known Limitations

Written honestly, because a README that only lists strengths isn't useful to the next engineer:

- **Single-VPS deployment target** — no horizontal autoscaling yet; fine at current scale, a real constraint past it
- **Two LLM providers wired, not abstracted behind a router** — switching mid-flight requires a config change and a restart, not yet a runtime decision
- **`requirements.txt` and `pyproject.toml` are maintained in parallel** — pick one source of truth before version drift becomes a real bug
- Repository hygiene pass pending: a stray duplicated package directory needs to be removed from git history

Contributions welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md). Version history in [`CHANGELOG.md`](CHANGELOG.md).

## License

MIT — see [`LICENSE`](LICENSE).

---

<div align="center">
<sub>Built for e-commerce operators who want AI agents that show their work.</sub>
</div>
