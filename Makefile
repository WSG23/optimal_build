.PHONY: help install format lint test test-cov smoke-buildable clean build deploy init-db db.upgrade seed-data logs down reset dev-start dev-stop import-sample run-overlay export-approved test-aec seed-nonreg sync-products

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

DOCKER_COMPOSE := $(shell \
        if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
                printf '%s' "docker compose"; \
        elif command -v docker-compose >/dev/null 2>&1; then \
                printf '%s' "docker-compose"; \
        fi)

REQUIRE_DOCKER_COMPOSE = @if [ -z "$(DOCKER_COMPOSE)" ]; then echo "Error: Docker Compose CLI not found. Install Docker (with the compose plugin) or docker-compose."; exit 1; fi

AEC_SAMPLE ?= tests/samples/sample_floorplan.json
AEC_PROJECT_ID ?= 101
AEC_EXPORT_FORMAT ?= pdf
AEC_DECIDED_BY ?= Planner Bot
AEC_APPROVAL_NOTES ?= Approved via make export-approved

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

smoke-buildable: ## Run the buildable latency smoke test and report the observed P90
	cd backend && pytest -s tests/pwp/test_buildable_latency.py

import-sample: ## Upload the bundled sample payload and seed overlay geometry
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	cd backend && AEC_RUNTIME_DIR=$(DEV_RUNTIME_DIR_ABS) python -m scripts.aec_flow import-sample --sample $(AEC_SAMPLE) --project-id $(AEC_PROJECT_ID)

run-overlay: ## Execute the overlay engine using the inline worker queue
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	cd backend && AEC_RUNTIME_DIR=$(DEV_RUNTIME_DIR_ABS) python -m scripts.aec_flow run-overlay --project-id $(AEC_PROJECT_ID)

export-approved: ## Approve overlays and generate a CAD/BIM export artefact
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	cd backend && AEC_RUNTIME_DIR=$(DEV_RUNTIME_DIR_ABS) python -m scripts.aec_flow export-approved --project-id $(AEC_PROJECT_ID) --format $(AEC_EXPORT_FORMAT) --decided-by "$(AEC_DECIDED_BY)" --notes "$(AEC_APPROVAL_NOTES)"

test-aec: ## Run sample import, overlay, export flows and regression tests
	$(MAKE) import-sample
	$(MAKE) run-overlay
	$(MAKE) export-approved
	cd backend && pytest tests/test_workflows/test_aec_pipeline.py
	cd frontend && npm test

test-cov: ## Run tests with coverage
	cd backend && pytest --cov=app --cov-report=html
	@echo "Coverage report: backend/htmlcov/index.html"

clean: ## Clean build artifacts
	cd backend && rm -rf __pycache__ .pytest_cache .coverage htmlcov
	cd frontend && rm -rf dist node_modules/.cache

build: ## Build production images
	$(REQUIRE_DOCKER_COMPOSE)
	$(DOCKER_COMPOSE) build

init-db: ## Apply Alembic migrations inside Docker
	$(REQUIRE_DOCKER_COMPOSE)
	$(DOCKER_COMPOSE) exec backend python -m backend.migrations alembic upgrade head

db.upgrade: ## Apply Alembic migrations locally
	python scripts/ensure_alembic.py
	python -m backend.migrations alembic upgrade head

seed-data: ## Seed screening data and finance demo scenarios
	@if [ -n "$(DOCKER_COMPOSE)" ]; then \
	        $(DOCKER_COMPOSE) exec backend python -m backend.scripts.seed_screening; \
	        $(DOCKER_COMPOSE) exec backend python -m backend.scripts.seed_finance_demo; \
	else \
	        echo "Docker Compose CLI not detected; running seeders locally."; \
	        python -m backend.scripts.seed_screening; \
	        python -m backend.scripts.seed_finance_demo; \
	fi

logs: ## Show application logs
	$(REQUIRE_DOCKER_COMPOSE)
	$(DOCKER_COMPOSE) logs -f backend frontend

down: ## Stop all services
	$(REQUIRE_DOCKER_COMPOSE)
	$(DOCKER_COMPOSE) down

reset: ## Reset development environment
	$(REQUIRE_DOCKER_COMPOSE)
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up -d
	$(MAKE) init-db
	$(MAKE) seed-data

dev-start: ## Start supporting services, the backend API, and frontends
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	@if [ -z "$(DOCKER_COMPOSE)" ]; then \
	        echo "Error: Docker Compose CLI not found. Install Docker (with the compose plugin) or docker-compose."; \
	        exit 1; \
	fi
	@$(DOCKER_COMPOSE) up -d
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

seed-nonreg:
	python -m backend.scripts.seed_nonreg

sync-products:
	python -m backend.flows.sync_products --csv-path vendor.csv
