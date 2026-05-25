.PHONY: help install dev test lint format migrate docker-up docker-down clean test-integration

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt
	pre-commit install

dev: ## Start development servers (requires Redis + PostgreSQL)
	uvicorn ecommerce_ops.api.app:app --reload --host 127.0.0.1 --port 8000

test: ## Run test suite
	python -m pytest tests/ -v --asyncio-mode=auto --cov=ecommerce_ops --cov-report=term-missing

test-ci: ## Run tests for CI (faster, no coverage)
	python -m pytest tests/ -v --asyncio-mode=auto -x

test-integration: ## Run LangGraph integration tests
	python -m pytest tests/test_supervisor_graph.py -v --asyncio-mode=auto

lint: ## Run linters
	ruff check ecommerce_ops/ tests/
	ruff format --check ecommerce_ops/ tests/

format: ## Auto-format code
	ruff check --fix ecommerce_ops/ tests/
	ruff format ecommerce_ops/ tests/

migrate: ## Run database migrations
	alembic upgrade head

migrate-new: ## Create a new migration
	@read -p "Migration name: " name; alembic revision --autogenerate -m "$$name"

docker-up: ## Start all services via Docker Compose
	docker compose up -d --build

docker-down: ## Stop all services
	docker compose down

docker-logs: ## Tail logs from Docker services
	docker compose logs -f

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name *.pyc -delete
	rm -rf .pytest_cache .coverage
