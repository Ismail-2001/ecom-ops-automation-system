.PHONY: help install dev test lint format migrate docker-up docker-down clean test-ci test-integration security audit db-shell prometheus grafana

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt
	pre-commit install

dev: ## Start development servers (requires Redis + PostgreSQL)
	uvicorn ecommerce_ops.api.app:app --reload --host 127.0.0.1 --port 8000

dev-dashboard: ## Start dashboard dev server
	cd dashboard && npm run dev

test: ## Run test suite with PostgreSQL
	python -m pytest tests/ -v --asyncio-mode=auto --cov=ecommerce_ops --cov-report=term-missing

test-ci: ## Run tests for CI (faster, no coverage, PostgreSQL)
	python -m pytest tests/ -v --asyncio-mode=auto -x

test-sqlite: ## Run test suite with SQLite (local dev, no PostgreSQL needed)
	ENV=testing DATABASE_URL=sqlite+aiosqlite:// python -m pytest tests/ -v --asyncio-mode=auto --cov=ecommerce_ops --cov-report=term-missing

test-integration: ## Run LangGraph integration tests
	python -m pytest tests/test_supervisor_graph.py -v --asyncio-mode=auto

test-load: ## Run load tests
	python -m pytest tests/load_tests/ -v --asyncio-mode=auto

lint: ## Run linters
	ruff check ecommerce_ops/ tests/
	ruff format --check ecommerce_ops/ tests/

format: ## Auto-format code
	ruff check --fix ecommerce_ops/ tests/
	ruff format ecommerce_ops/ tests/

typecheck: ## Run MyPy type checker
	mypy ecommerce_ops/ --ignore-missing-imports

security: ## Run security scan with bandit
	bandit -r ecommerce_ops/ -c pyproject.toml

audit: ## Audit Python dependencies for vulnerabilities
	pip-audit -r requirements.txt --desc

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

docker-up: ## Start all services via Docker Compose
	docker compose up -d --build

docker-down: ## Stop all services
	docker compose down

docker-logs: ## Tail logs from Docker services
	docker compose logs -f

docker-restart: ## Restart API service
	docker compose restart api

prometheus: ## Start Prometheus (if local binary available)
	prometheus --config.file=monitoring/prometheus.yml

grafana: ## Start Grafana (if local binary available)
	grafana-server --config=monitoring/grafana.ini

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name *.pyc -delete
	rm -rf .pytest_cache .coverage coverage.xml
