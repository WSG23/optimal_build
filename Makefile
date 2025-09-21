.PHONY: help install format lint test test-cov clean build deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	cd backend && pip install -r requirements-dev.txt
	cd frontend && npm install

format: ## Format code
	cd backend && black . && isort .
	cd frontend && npm run format

lint: ## Run linting
	cd backend && flake8 app tests && mypy app
	cd frontend && npm run lint

test: ## Run tests
	cd backend && pytest
	cd frontend && npm test

test-cov: ## Run tests with coverage
	cd backend && pytest --cov=app --cov-report=html
	@echo "Coverage report: backend/htmlcov/index.html"

clean: ## Clean build artifacts
	cd backend && rm -rf __pycache__ .pytest_cache .coverage htmlcov
	cd frontend && rm -rf dist node_modules/.cache

build: ## Build production images
	docker-compose build

init-db: ## Initialize database
	docker-compose exec backend alembic upgrade head

seed-data: ## Seed initial data
	docker-compose exec backend python scripts/seed-data.py

logs: ## Show application logs
	docker-compose logs -f backend frontend

down: ## Stop all services
	docker-compose down

reset: ## Reset development environment
	docker-compose down -v
	docker-compose up -d
	make init-db
	make seed-data
