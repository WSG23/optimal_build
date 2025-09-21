.PHONY: help install format lint test test-cov clean build deploy init-db seed-data logs down reset dev-start dev-stop

DEV_RUNTIME_DIR ?= .devstack
DEV_RUNTIME_DIR_ABS := $(abspath $(DEV_RUNTIME_DIR))
DEV_BACKEND_PID ?= $(DEV_RUNTIME_DIR_ABS)/backend.pid
DEV_FRONTEND_PID ?= $(DEV_RUNTIME_DIR_ABS)/frontend.pid
DEV_ADMIN_PID ?= $(DEV_RUNTIME_DIR_ABS)/ui-admin.pid
DEV_BACKEND_LOG ?= $(DEV_RUNTIME_DIR_ABS)/backend.log
DEV_FRONTEND_LOG ?= $(DEV_RUNTIME_DIR_ABS)/frontend.log
DEV_ADMIN_LOG ?= $(DEV_RUNTIME_DIR_ABS)/ui-admin.log
BACKEND_CMD ?= uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
FRONTEND_CMD ?= npm run dev
ADMIN_CMD ?= npm run dev
INCLUDE_ADMIN ?= 1

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

test-aec: ## Run AEC backend and frontend test suites
	cd backend && pytest tests/test_workflows/test_aec_pipeline.py
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

dev-start: ## Start supporting services, the backend API, and frontends
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	@docker-compose up -d
	@if [ -f $(DEV_BACKEND_PID) ] && kill -0 $$(cat $(DEV_BACKEND_PID)) 2>/dev/null; then \
		echo "Backend API already running (PID $$(cat $(DEV_BACKEND_PID)))."; \
	else \
		rm -f $(DEV_BACKEND_PID); \
		: > $(DEV_BACKEND_LOG); \
		(cd backend && nohup $(BACKEND_CMD) > $(DEV_BACKEND_LOG) 2>&1 & echo $$! > $(DEV_BACKEND_PID)); \
		echo "Backend API started (PID $$(cat $(DEV_BACKEND_PID))). Logs: $(DEV_BACKEND_LOG)"; \
	fi
	@if [ -f $(DEV_FRONTEND_PID) ] && kill -0 $$(cat $(DEV_FRONTEND_PID)) 2>/dev/null; then \
		echo "Frontend app already running (PID $$(cat $(DEV_FRONTEND_PID)))."; \
	else \
		rm -f $(DEV_FRONTEND_PID); \
		: > $(DEV_FRONTEND_LOG); \
		(cd frontend && nohup $(FRONTEND_CMD) > $(DEV_FRONTEND_LOG) 2>&1 & echo $$! > $(DEV_FRONTEND_PID)); \
		echo "Frontend app started (PID $$(cat $(DEV_FRONTEND_PID))). Logs: $(DEV_FRONTEND_LOG)"; \
	fi
	@if [ "$(INCLUDE_ADMIN)" != "0" ]; then \
		if [ -f $(DEV_ADMIN_PID) ] && kill -0 $$(cat $(DEV_ADMIN_PID)) 2>/dev/null; then \
			echo "Admin UI already running (PID $$(cat $(DEV_ADMIN_PID)))."; \
		else \
			rm -f $(DEV_ADMIN_PID); \
			: > $(DEV_ADMIN_LOG); \
			(cd ui-admin && nohup $(ADMIN_CMD) > $(DEV_ADMIN_LOG) 2>&1 & echo $$! > $(DEV_ADMIN_PID)); \
			echo "Admin UI started (PID $$(cat $(DEV_ADMIN_PID))). Logs: $(DEV_ADMIN_LOG)"; \
		fi; \
	else \
		echo "Skipping admin UI (INCLUDE_ADMIN=0)."; \
	fi

dev-stop: ## Stop services started with dev-start (excluding docker-compose)
	@if [ -f $(DEV_BACKEND_PID) ]; then \
		PID=$$(cat $(DEV_BACKEND_PID)); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "Stopping backend API (PID $$PID)."; \
			kill $$PID; \
		fi; \
		rm -f $(DEV_BACKEND_PID); \
	else \
		echo "Backend API is not running."; \
	fi
	@if [ -f $(DEV_FRONTEND_PID) ]; then \
		PID=$$(cat $(DEV_FRONTEND_PID)); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "Stopping frontend app (PID $$PID)."; \
			kill $$PID; \
		fi; \
		rm -f $(DEV_FRONTEND_PID); \
	else \
		echo "Frontend app is not running."; \
	fi
	@if [ -f $(DEV_ADMIN_PID) ]; then \
		PID=$$(cat $(DEV_ADMIN_PID)); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "Stopping admin UI (PID $$PID)."; \
			kill $$PID; \
		fi; \
		rm -f $(DEV_ADMIN_PID); \
	else \
		echo "Admin UI is not running."; \
	fi
