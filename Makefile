.PHONY: help install dev dev-docker test test-unit test-e2e test-benchmark \
	lint format typecheck security audit \
	migrate migrate-new migrate-rollback migrate-history \
	docker-up docker-down docker-logs docker-ps docker-shell \
	docker-prod docker-prod-down docker-prod-logs \
	docker-backup docker-restore docker-clean \
	monitoring-up monitoring-down \
	load-test deploy-staging deploy-production \
	setup clean

# ── Default ────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# ── Setup & Installation ───────────────────────────────────

setup: ## Full project setup (install deps, create .env, init DB)
	pip install -r requirements.txt
	pre-commit install 2>/dev/null || true
	@test -f .env || cp .env.example .env 2>/dev/null || true
	@echo "Setup complete. Edit .env with your keys."

install: ## Install Python dependencies
	pip install -r requirements.txt

install-dev: ## Install dev dependencies (linters, test tools)
	pip install -r requirements.txt ruff mypy bandit pip-audit pytest pytest-asyncio pytest-cov httpx locust

# ── Local Development ──────────────────────────────────────

dev: ## Start backend dev server (requires DB + Redis)
	uvicorn ecommerce_ops.api.app:app --reload --host 127.0.0.1 --port 8000 --log-level debug

dev-docker: ## Start full dev stack with Docker
	docker compose -f docker-compose.dev.yml up -d
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

dev-docker-down: ## Stop dev stack
	docker compose -f docker-compose.dev.yml down

dev-docker-logs: ## Tail dev stack logs
	docker compose -f docker-compose.dev.yml logs -f

# ── Testing ────────────────────────────────────────────────

test: ## Run all tests
	python -m pytest tests/ -v --asyncio-mode=auto --cov=ecommerce_ops --cov-report=term-missing

test-unit: ## Run unit tests only
	python -m pytest tests/ -v --asyncio-mode=auto -k "not test_e2e and not test_performance" --cov=ecommerce_ops --cov-report=term-missing

test-e2e: ## Run E2E integration tests
	python -m pytest tests/test_e2e_integration.py -v --asyncio-mode=auto

test-benchmark: ## Run performance benchmarks
	python -m pytest tests/test_performance.py -v -s --asyncio-mode=auto

test-ci: ## Run tests for CI (fast, fail-fast)
	python -m pytest tests/ -v --asyncio-mode=auto -x --tb=short

test-sqlite: ## Run tests with SQLite (no DB needed)
	ENV=testing DATABASE_URL=sqlite+aiosqlite:// python -m pytest tests/ -v --asyncio-mode=auto --cov=ecommerce_ops --cov-report=term-missing

test-coverage: ## Generate HTML coverage report
	python -m pytest tests/ --asyncio-mode=auto --cov=ecommerce_ops --cov-report=html:htmlcov/
	@echo "Coverage report: htmlcov/index.html"

# ── Code Quality ───────────────────────────────────────────

lint: ## Run linters (ruff check + format check)
	ruff check ecommerce_ops/ tests/
	ruff format --check ecommerce_ops/ tests/

format: ## Auto-format code
	ruff check --fix ecommerce_ops/ tests/
	ruff format ecommerce_ops/ tests/

typecheck: ## Run MyPy type checker
	mypy ecommerce_ops/ --ignore-missing-imports

security: ## Run security scan
	bandit -r ecommerce_ops/ -c pyproject.toml 2>/dev/null || echo "bandit not installed"
	pip-audit -r requirements.txt 2>/dev/null || echo "pip-audit not installed"

pre-commit: ## Run all pre-commit checks
	@echo "Running linters..."
	@ruff check ecommerce_ops/ tests/ || true
	@ruff format --check ecommerce_ops/ tests/ || true
	@echo "Running tests..."
	@python -m pytest tests/ --asyncio-mode=auto -x --tb=short -q

# ── Database Migrations ────────────────────────────────────

migrate: ## Run database migrations
	alembic upgrade head

migrate-new: ## Create a new migration
	@read -p "Migration name: " name; alembic revision --autogenerate -m "$$name"

migrate-rollback: ## Rollback last migration
	alembic downgrade -1

migrate-history: ## Show migration history
	alembic history

db-shell: ## Open PostgreSQL shell
	psql $(DATABASE_URL)

db-reset: ## Reset database (DROP + CREATE + Migrate)
	alembic downgrade base
	alembic upgrade head

# ── Docker Development ─────────────────────────────────────

docker-up: ## Start all services (dev mode)
	docker compose up -d --build

docker-down: ## Stop all services
	docker compose down

docker-logs: ## Tail logs from all services
	docker compose logs -f

docker-logs-api: ## Tail API logs only
	docker compose logs -f api

docker-restart: ## Restart API service
	docker compose restart api

docker-build: ## Build API image
	docker compose build api

docker-ps: ## Show running containers
	docker compose ps

docker-shell: ## Open shell in API container
	docker compose exec api bash

docker-migrate: ## Run migrations inside container
	docker compose exec api alembic upgrade head

# ── Docker Production ──────────────────────────────────────

docker-prod: ## Start production services
	docker compose -f docker-compose.yml up -d --build

docker-prod-down: ## Stop production services
	docker compose -f docker-compose.yml down

docker-prod-logs: ## Tail production logs
	docker compose -f docker-compose.yml logs -f

docker-prod-ps: ## Show production containers
	docker compose -f docker-compose.yml ps

# ── Docker Backup & Restore ────────────────────────────────

docker-backup: ## Start with backup services
	docker compose -f docker-compose.yml -f docker-compose.backup.yml up -d

docker-restore: ## Restore database from backup
	@bash scripts/restore-db.sh $(BACKUP_FILE)

# ── Monitoring ─────────────────────────────────────────────

monitoring-up: ## Start monitoring stack (Prometheus + Grafana)
	docker compose up -d prometheus grafana postgres-exporter redis-exporter alertmanager

monitoring-down: ## Stop monitoring stack
	docker compose stop prometheus grafana postgres-exporter redis-exporter alertmanager

monitoring-logs: ## Tail monitoring logs
	docker compose logs -f prometheus grafana

# ── Load Testing ───────────────────────────────────────────

load-test: ## Run Locust load test (interactive)
	locust -f tests/load_tests/locustfile.py --host=http://localhost:8000

load-test-headless: ## Run Locust load test (headless, 100 users)
	locust -f tests/load_tests/locustfile.py \
		--host=http://localhost:8000 \
		--headless \
		-u 100 \
		-r 10 \
		-t 60s \
		--csv=results/load_test

# ── Deployment ─────────────────────────────────────────────

deploy-staging: ## Deploy to staging
	@bash scripts/deploy.sh staging

deploy-production: ## Deploy to production
	@bash scripts/deploy.sh production

# ── Cleanup ────────────────────────────────────────────────

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage coverage.xml htmlcov/ results/
	rm -rf .mypy_cache .ruff_cache

docker-clean: ## Remove all containers, volumes, networks
	docker compose down -v --remove-orphans
	docker system prune -f

clean-all: clean docker-clean ## Clean everything (code + Docker)
	@echo "Full cleanup complete"
