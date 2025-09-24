.PHONY: help install format lint test test-cov smoke-buildable clean build deploy init-db db.upgrade seed-data logs down reset dev dev-stop import-sample run-overlay export-approved test-aec seed-nonreg sync-products venv env-check

DEV_RUNTIME_DIR ?= .devstack
DEV_RUNTIME_DIR_ABS := $(abspath $(DEV_RUNTIME_DIR))
DEV_BACKEND_PID ?= $(DEV_RUNTIME_DIR_ABS)/backend.pid
DEV_FRONTEND_PID ?= $(DEV_RUNTIME_DIR_ABS)/frontend.pid
DEV_ADMIN_PID ?= $(DEV_RUNTIME_DIR_ABS)/ui-admin.pid
DEV_BACKEND_LOG ?= $(DEV_RUNTIME_DIR_ABS)/backend.log
DEV_FRONTEND_LOG ?= $(DEV_RUNTIME_DIR_ABS)/frontend.log
DEV_ADMIN_LOG ?= $(DEV_RUNTIME_DIR_ABS)/ui-admin.log
DEV_SQLITE_URL ?= sqlite+aiosqlite:///$(DEV_RUNTIME_DIR_ABS)/app.db
# --- Python / venv -----------------------------------------------------------
VENV ?= .venv
VENV_ABS := $(abspath $(VENV))
PY ?= $(VENV_ABS)/bin/python
PIP ?= $(VENV_ABS)/bin/pip
UVICORN ?= $(VENV_ABS)/bin/uvicorn
PRE_COMMIT ?= $(VENV_ABS)/bin/pre-commit

PYENV ?= $(shell command -v pyenv 2>/dev/null)
PYENV_PREFERRED_VERSION ?= 3.11.12
PYTHON_FOR_VENV ?= python3
ifneq ($(PYENV),)
ifneq ($(shell $(PYENV) versions --bare 2>/dev/null | grep -x $(PYENV_PREFERRED_VERSION)),)
PYTHON_FOR_VENV := PYENV_VERSION=$(PYENV_PREFERRED_VERSION) python3
endif
endif

PIP_WHEEL_DIR ?= third_party/python
PIP_INSTALL_FLAGS ?=
ifneq ($(wildcard $(PIP_WHEEL_DIR)),)
PIP_WHEEL_DIR_ABS := $(abspath $(PIP_WHEEL_DIR))
PIP_INSTALL_FLAGS += --no-index --find-links $(PIP_WHEEL_DIR_ABS)
endif

# Use fully-qualified module path and uvicorn from the venv
BACKEND_CMD ?= $(UVICORN) backend.app.main:app --reload --host 0.0.0.0 --port 8000
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

venv: ## Create venv & install backend+frontend deps
	@if [ ! -d $(VENV) ]; then \
		printf 'Creating virtualenv with %s\n' "$(PYTHON_FOR_VENV)"; \
		$(PYTHON_FOR_VENV) -m venv $(VENV); \
	fi
	@if [ -n "$(PIP_INSTALL_FLAGS)" ]; then \
		printf 'Using local Python wheelhouse: %s\n' "$(PIP_WHEEL_DIR_ABS)"; \
	else \
		$(PIP) install --upgrade pip; \
	fi
	@if [ -f backend/requirements.txt ]; then \
		if [ -n "$(PIP_INSTALL_FLAGS)" ]; then \
			$(PIP) install $(PIP_INSTALL_FLAGS) sqlalchemy[asyncio]==2.0.23; \
			$(PIP) install $(PIP_INSTALL_FLAGS) --no-deps alembic==1.13.0; \
			$(PIP) install $(PIP_INSTALL_FLAGS) python-multipart==0.0.6; \
			$(PIP) install $(PIP_INSTALL_FLAGS) python-jose==3.3.0; \
			$(PIP) install $(PIP_INSTALL_FLAGS) passlib==1.7.4; \
$(PIP) install $(PIP_INSTALL_FLAGS) python-dateutil==2.8.2; \
$(PIP) install $(PIP_INSTALL_FLAGS) prometheus-client==0.19.0; \
$(PIP) install $(PIP_INSTALL_FLAGS) aiosqlite==0.21.0; \
		else \
			$(PIP) install -r backend/requirements.txt; \
		fi; \
	fi
	@if [ -f backend/requirements-dev.txt ]; then \
		if [ -n "$(PIP_INSTALL_FLAGS)" ]; then \
			$(PIP) install $(PIP_INSTALL_FLAGS) pytest==7.4.3; \
			$(PIP) install $(PIP_INSTALL_FLAGS) pytest-asyncio==0.21.1; \
			$(PIP) install $(PIP_INSTALL_FLAGS) isort==5.12.0; \
			$(PIP) install $(PIP_INSTALL_FLAGS) flake8==6.1.0; \
		else \
			$(PIP) install -r backend/requirements-dev.txt; \
		fi; \
	fi
	@if [ -d frontend/node_modules ]; then \
		echo "Skipping npm install; frontend/node_modules already present."; \
	else \
		cd frontend && npm install; \
	fi
	@command -v $(PRE_COMMIT) >/dev/null 2>&1 && $(PRE_COMMIT) install || true

install: venv ## Install dependencies (alias)

format: ## Format code
	cd backend && $(PY) -m black . && $(PY) -m isort .
	cd frontend && npm run format

lint: ## Run linting
	cd backend && $(PY) -m flake8 app tests && $(PY) -m mypy app
	cd frontend && npm run lint

test: ## Run tests
	cd backend && $(PY) -m pytest tests
	cd backend && $(PY) -m pytest ../tests
	cd frontend && npm test

smoke-buildable: ## Run the buildable latency smoke test and report the observed P90
	cd backend && $(PY) -m pytest -s tests/pwp/test_buildable_latency.py

import-sample: ## Upload the bundled sample payload and seed overlay geometry
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	cd backend && AEC_RUNTIME_DIR=$(DEV_RUNTIME_DIR_ABS) $(PY) -m scripts.aec_flow import-sample --sample $(AEC_SAMPLE) --project-id $(AEC_PROJECT_ID)

run-overlay: ## Execute the overlay engine using the inline worker queue
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	cd backend && AEC_RUNTIME_DIR=$(DEV_RUNTIME_DIR_ABS) $(PY) -m scripts.aec_flow run-overlay --project-id $(AEC_PROJECT_ID)

export-approved: ## Approve overlays and generate a CAD/BIM export artefact
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	cd backend && AEC_RUNTIME_DIR=$(DEV_RUNTIME_DIR_ABS) $(PY) -m scripts.aec_flow export-approved --project-id $(AEC_PROJECT_ID) --format $(AEC_EXPORT_FORMAT) --decided-by "$(AEC_DECIDED_BY)" --notes "$(AEC_APPROVAL_NOTES)"

test-aec: ## Run sample import, overlay, export flows and regression tests
	$(MAKE) import-sample
	$(MAKE) run-overlay
	$(MAKE) export-approved
	cd backend && $(PY) -m pytest tests/test_workflows/test_aec_pipeline.py
	cd frontend && npm test

test-cov: ## Run tests with coverage
	cd backend && $(PY) -m pytest --cov=app --cov-report=html
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

db.upgrade: ## Apply database migrations locally
	DEV_SQLITE_URL=$(DEV_SQLITE_URL) DATABASE_URL="$${DATABASE_URL:-$(DEV_SQLITE_URL)}" $(PY) scripts/sqlite_upgrade.py

seed-data: ## Seed screening data and finance demo scenarios
	@if [ -n "$(DOCKER_COMPOSE)" ]; then \
	        $(DOCKER_COMPOSE) exec backend python -m backend.scripts.seed_screening; \
	        $(DOCKER_COMPOSE) exec backend python -m backend.scripts.seed_finance_demo; \
	else \
		echo "Docker Compose CLI not detected; running seeders locally."; \
		$(PY) -m backend.scripts.seed_screening; \
		$(PY) -m backend.scripts.seed_finance_demo; \
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

dev: ## Start supporting services, the backend API, and frontends
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	@if [ -d uvicorn ]; then echo "WARNING: './uvicorn/' package detected; it will shadow the real uvicorn. Rename or remove it." >&2; fi
	@if [ -z "$(DOCKER_COMPOSE)" ]; then \
		echo "Docker Compose CLI not found; skipping container startup."; \
	else \
		$(DOCKER_COMPOSE) up -d; \
	fi
	@if [ -f $(DEV_BACKEND_PID) ] && kill -0 $$(cat $(DEV_BACKEND_PID)) 2>/dev/null; then \
		echo "Backend API already running (PID $$(cat $(DEV_BACKEND_PID)))."; \
	else \
		rm -f $(DEV_BACKEND_PID); \
		: > $(DEV_BACKEND_LOG); \
			(cd backend && DEV_SQLITE_URL=$(DEV_SQLITE_URL) SQLALCHEMY_DATABASE_URI=$(DEV_SQLITE_URL) DATABASE_URL=$(DEV_SQLITE_URL) nohup $(BACKEND_CMD) > $(DEV_BACKEND_LOG) 2>&1 & echo $$! > $(DEV_BACKEND_PID)); \
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

dev-stop: ## Stop services started with dev (excluding docker-compose)
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
	$(PY) -m backend.scripts.seed_nonreg

sync-products:
	$(PY) -m backend.flows.sync_products --csv-path vendor.csv

env-check: ## Quick sanity: ensure imports & tests compile
	@cd backend && $(PY) -m compileall -q tests
	@$(PY) scripts/env_check.py
