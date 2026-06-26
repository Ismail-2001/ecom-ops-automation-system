# Contributing to OpsIQ

Thank you for your interest in contributing to OpsIQ — the autonomous ecommerce operations engine. We welcome contributions from engineers, ecommerce operators, and AI enthusiasts who want to help shape the future of automated commerce.

## Code of Conduct

By participating, you agree to maintain a respectful, inclusive, and constructive environment. Harassment, discriminatory language, and unprofessional behavior will not be tolerated.

## How to Contribute

### 1. Report Bugs
Open a [Bug Report](https://github.com/Ismail-2001/ecom-ops-automation-system/issues/new?template=bug_report.md) with:
- Clear reproduction steps
- Environment details (Python version, LLM provider, deployment method)
- Log output from `structlog` if available
- Whether Redis/PostgreSQL were running

### 2. Suggest Features
Open a [Feature Request](https://github.com/Ismail-2001/ecom-ops-automation-system/issues/new?template=feature_request.md) focused on:
- The operational pain point you're solving
- The ecommerce business impact (revenue, efficiency, risk)
- Which agent or system area it affects

### 3. Submit Code Changes

#### Prerequisites
- Python 3.11+
- Node.js 20+
- Redis 7 (recommended)
- PostgreSQL 16 (recommended for production)

#### Setup
```bash
git clone https://github.com/Ismail-2001/ecom-ops-automation-system.git
cd ecom-ops-automation-system

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Frontend
cd dashboard
npm install
cd ..
```

#### Development Workflow
```bash
# Format & lint
ruff format ecommerce_ops/ tests/
ruff check --fix ecommerce_ops/ tests/

# Type check
mypy ecommerce_ops/ --ignore-missing-imports

# Run tests
python -m pytest tests/ -v --asyncio-mode=auto

# Run integration tests
python -m pytest tests/test_supervisor_graph.py -v --asyncio-mode=auto
```

#### Commit Guidelines
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Keep commits focused — one logical change per commit
- Reference issues where applicable: `feat: add klaviyo integration (#42)`

#### Pull Request Process
1. Create a feature branch from `main`: `git checkout -b feat/my-feature`
2. Make your changes with clear commit messages
3. Run the full test suite and ensure all tests pass
4. Run `ruff check` and `mypy` to verify code quality
5. Push and open a PR against `main`
6. In the PR description, explain:
   - What operational problem this solves
   - How you tested it
   - Any configuration changes needed

### 4. Improve Documentation
Documentation improvements are always welcome — whether it's fixing a typo in the README, improving docstrings, or adding deployment guides.

## Development Priorities

| Area | Priority | Description |
|:---|---:|---:|
| Shopify connector wiring | 🔴 High | Connect real agents to live Shopify API data |
| Redis resilience | 🟠 Medium | Graceful degradation when Redis is unavailable |
| New integrations | 🟢 Low | Zendesk, Gorgias, Klaviyo connectors |
| Performance | 🟢 Low | LLM caching, query optimization, browser pool tuning |

## Questions?
Open a [Discussion](https://github.com/Ismail-2001/ecom-ops-automation-system/discussions) or reach out to the maintainer.

Thank you for helping make ecommerce operations better for everyone.
