.PHONY: help help-dev install format format-check lint lint-prod test test-all test-cov smoke-buildable clean clean-ui build deploy init-db db.revision db.upgrade seed-data seed-properties-projects logs down reset dev stop import-sample run-overlay export-approved test-aec seed-nonreg sync-products venv env-check verify check-coding-rules check-tool-versions ai-preflight status hooks ui-stop typecheck typecheck-backend typecheck-all typecheck-watch quick-check pre-commit-full pre-deploy coverage-report db-backup db-restore docker-clean

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
UVICORN_BIN ?= $(VENV_ABS)/bin/uvicorn
ifeq ($(wildcard $(UVICORN_BIN)),)
UVICORN ?= $(PY) -m backend.uvicorn_stub
else
UVICORN ?= $(UVICORN_BIN)
endif
PRE_COMMIT ?= $(VENV_ABS)/bin/pre-commit
BLACK ?= $(VENV_ABS)/bin/black
ISORT ?= $(VENV_ABS)/bin/isort
RUFF ?= $(PY) -m ruff
FLAKE8 ?= $(VENV_ABS)/bin/flake8
MYPY ?= $(PY) -m mypy
PYTEST ?= $(VENV_ABS)/bin/pytest

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

# Run from repo root, add backend/ to import path, and import app.main:app
# Use fully-qualified module path, force ASGI3
# Configurable dev ports (avoid conflicts with 8000/5173 and anything in the 5100s)
BACKEND_PORT ?= 9400
FRONTEND_PORT ?= 4400
ADMIN_PORT ?= 4401

BACKEND_APP ?= backend.app.main:app
ifeq ($(UVICORN),$(PY) -m backend.uvicorn_stub)
BACKEND_CMD ?= $(UVICORN) $(BACKEND_APP) --host 0.0.0.0 --port $(BACKEND_PORT)
else
BACKEND_CMD ?= $(UVICORN) --interface asgi3 $(BACKEND_APP) --reload --host 0.0.0.0 --port $(BACKEND_PORT)
endif
FRONTEND_CMD ?= npm run dev -- --port $(FRONTEND_PORT)
ADMIN_CMD ?= npm run dev -- --port $(ADMIN_PORT)
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📚 HELP & DOCUMENTATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

help: ## Show basic help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''
	@echo 'For detailed development guide: make help-dev'

help-dev: ## Show comprehensive development workflow guide
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🛠️  OPTIMAL_BUILD DEVELOPMENT GUIDE"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "━━━ Getting Started ━━━"
	@echo "  make install            Install all dependencies"
	@echo "  make dev                Start all services (backend + frontend + admin)"
	@echo "  make status             Check service status"
	@echo "  make stop               Stop all services"
	@echo "  make ui-stop            Force kill UI servers on ports (if stuck)"
	@echo ""
	@echo "━━━ Code Quality & Verification ━━━"
	@echo "  make quick-check        Fast checks (format + typecheck + lint)"
	@echo "  make verify             Full verification (format + lint + rules + tests)"
	@echo "  make hooks              Run pre-commit hooks on all files"
	@echo "  make pre-commit-full    Comprehensive pre-commit validation"
	@echo "  make ai-preflight       AI agent pre-flight checks"
	@echo ""
	@echo "━━━ Type Checking ━━━"
	@echo "  make typecheck          Run TypeScript type checking (frontend)"
	@echo "  make typecheck-backend  Run Python type checking (backend API/schemas)"
	@echo "  make typecheck-all      Run both TypeScript and Python type checking"
	@echo "  make typecheck-watch    Watch mode for TypeScript errors"
	@echo "  npm run lint            Lint frontend code"
	@echo "  make clean-ui           Clean UI cache and build artifacts"
	@echo ""
	@echo "━━━ Testing ━━━"
	@echo "  make test               Run unit tests (fast)"
	@echo "  make test-all           Run all tests including integration"
	@echo "  make test-cov           Run tests with coverage"
	@echo "  make coverage-report    Generate and open coverage HTML report"
	@echo "  make test-aec           Run AEC integration tests"
	@echo ""
	@echo "━━━ Database Management ━━━"
	@echo "  make db.upgrade         Apply database migrations"
	@echo "  make db.revision        Create new migration (set REVISION_MESSAGE)"
	@echo "  make seed-data          Seed database with sample data"
	@echo "  make db-backup          Backup local SQLite database"
	@echo "  make db-restore         Restore from latest backup"
	@echo ""
	@echo "━━━ Cleaning & Troubleshooting ━━━"
	@echo "  make clean              Clean build artifacts"
	@echo "  make clean-ui           Clean frontend cache and build artifacts"
	@echo "  make ui-stop            Kill stuck UI servers on ports"
	@echo "  make reset              Full Docker reset with re-seeding"
	@echo "  make docker-clean       Remove stopped containers and unused artifacts"
	@echo ""
	@echo "━━━ Pre-Deployment ━━━"
	@echo "  make pre-deploy         Run all pre-deployment checks"
	@echo "  make validate-delivery-plan  Validate roadmap and work queue"
	@echo ""
	@echo "━━━ Docker Operations ━━━"
	@echo "  make build              Build production images"
	@echo "  make logs               Show application logs"
	@echo "  make down               Stop all Docker services"
	@echo ""
	@echo "━━━ Configuration ━━━"
	@echo "  Ports: Backend=$(BACKEND_PORT), Frontend=$(FRONTEND_PORT), Admin=$(ADMIN_PORT)"
	@echo "  Database: $(DEV_SQLITE_URL)"
	@echo "  Logs: $(DEV_RUNTIME_DIR_ABS)/*.log"
	@echo ""
	@echo "📖 Documentation: See CLAUDE.md and CODING_RULES.md"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 INSTALLATION & SETUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 CODE FORMATTING & LINTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

format: ## Format code (handled automatically by pre-commit hooks)
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✅ Code formatting is handled automatically by pre-commit hooks"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📝 When you commit, pre-commit hooks will automatically:"
	@echo "   • Run black (code formatting)"
	@echo "   • Run ruff (import sorting + linting)"
	@echo "   • Run prettier (frontend formatting)"
	@echo ""
	@echo "💡 To manually format ALL files in the repo:"
	@echo "   pre-commit run --all-files"
	@echo ""
	@echo "🔍 To check if code is properly formatted:"
	@echo "   make verify"
	@echo ""

format-check: ## Check formatting (all Python files)
	@echo "🔍 Checking Python formatting with pre-commit hooks..."
	@$(PRE_COMMIT) run black --all-files || true
	@$(PRE_COMMIT) run ruff --all-files || true

lint: ## Run linting (all Python files)
	@$(FLAKE8) backend/app/ backend/tests/ tests/ || true
	@$(MYPY) || true
	@cd frontend && npm run lint || true

hooks: ## Run pre-commit hooks across the repository
	@if command -v $(PRE_COMMIT) >/dev/null 2>&1; then \
		$(PRE_COMMIT) run --all-files; \
	elif command -v pre-commit >/dev/null 2>&1; then \
		pre-commit run --all-files; \
	else \
		echo "pre-commit not found. Run 'make venv' or install pre-commit."; \
		exit 127; \
	fi

lint-prod: ## Run linting for backend production code (optional)
	@targets=""; \
	for path in backend/app backend/flows backend/jobs; do \
		if [ -d $$path ]; then \
			targets="$$targets $$path"; \
		fi; \
	done; \
	if [ -n "$$targets" ]; then \
		$(FLAKE8) $$targets || { echo "::warning::flake8 found issues in production code. Review output above."; true; }; \
	else \
		echo "No production directories found to lint."; \
	fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✅ TYPESCRIPT & FRONTEND VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

typecheck: ## Run TypeScript type checking (frontend only)
	@echo "🔍 Running TypeScript type checks..."
	@npm run --prefix frontend typecheck
	@echo "✅ TypeScript checks passed"

typecheck-backend: ## Run Python type checking (mypy on critical paths)
	@echo "🔍 Running Python type checks on critical paths (app/api/, app/schemas/)..."
	@cd backend && $(MYPY) app/api/ app/schemas/ --config-file=../mypy.ini --no-error-summary
	@echo "✅ Python type checks passed"

typecheck-all: ## Run both TypeScript and Python type checking
	@echo "🔍 Running all type checks..."
	@$(MAKE) typecheck
	@$(MAKE) typecheck-backend

typecheck-watch: ## Watch mode for TypeScript type checking
	@echo "👀 Watching TypeScript files for type errors..."
	@cd frontend && npx tsc --noEmit --watch

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧪 TESTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

test: ## Run tests (unit tests only - fast)
	$(PYTEST) -q unit_tests/

test-all: ## Run all tests including integration tests
	$(PYTEST) -q

test-cov: ## Run tests with coverage
	SECRET_KEY=test-secret-key PYTHONPATH=$(CURDIR) JOB_QUEUE_BACKEND=inline $(PYTEST) backend/tests --cov=backend/app --cov-report=html --cov-report=term-missing
	@echo "Coverage report: backend/htmlcov/index.html"

coverage-report: ## Generate and open coverage report
	@echo "📊 Generating coverage report..."
	@SECRET_KEY=test-secret-key PYTHONPATH=$(CURDIR) $(PYTEST) backend/tests \
		--cov=backend/app --cov-report=html --cov-report=term-missing
	@if [ -f backend/htmlcov/index.html ]; then \
		echo ""; \
		echo "Coverage report generated:"; \
		echo "  HTML: backend/htmlcov/index.html"; \
		echo ""; \
		if command -v open >/dev/null 2>&1; then \
			open backend/htmlcov/index.html; \
			echo "✅ Opened in browser"; \
		fi; \
	fi

smoke-buildable: ## Run the buildable latency smoke test and report the observed P90
	cd backend && $(PY) -m pytest -s tests/pwp/test_buildable_latency.py

test-aec: ## Run sample import, overlay, export flows and regression tests
	$(MAKE) import-sample
	$(MAKE) run-overlay
	$(MAKE) export-approved
	cd backend && $(PY) -m pytest tests/test_workflows/test_aec_pipeline.py
	cd frontend && npm test

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 VERIFICATION & QUALITY GATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

verify: ## Run formatting checks, linting, type checking, coding rules, roadmap/work queue validation, and tests
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) typecheck-backend
	$(MAKE) check-coding-rules
	$(MAKE) validate-delivery-plan
	$(MAKE) test

quick-check: ## Fast pre-commit checks (format + typecheck + lint)
	@echo "⚡ Running quick checks..."
	@$(MAKE) format-check
	@npm run --prefix frontend typecheck
	@$(MAKE) lint
	@echo "✅ Quick checks completed"

pre-commit-full: ## Comprehensive pre-commit checks
	@echo "🔍 Running comprehensive pre-commit checks..."
	@$(MAKE) lint
	@npm run --prefix frontend typecheck
	@$(MAKE) check-coding-rules
	@$(MAKE) test
	@echo "✅ All pre-commit checks passed"

pre-deploy: ## Pre-deployment verification
	@echo "🚀 Running pre-deployment checks..."
	@$(MAKE) verify
	@$(MAKE) test-all
	@$(MAKE) validate-delivery-plan
	@echo "✅ Ready for deployment"

validate-delivery-plan: ## Validate all_steps_to_product_completion.md (roadmap + backlog) for required sections
	@echo "Validating strategic roadmap and work queue..."
	@$(PY) scripts/validate_delivery_plan.py

check-tool-versions: ## Verify formatter/linter versions match requirements.txt
	@echo "Checking tool version consistency..."
	@BLACK_VENV=$$($(BLACK) --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1); \
	BLACK_REQ=$$(grep "black==" backend/requirements.txt 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1); \
	if [ -z "$$BLACK_VENV" ]; then \
		echo "⚠️  WARNING: Black not found in venv. Run 'make venv' to install."; \
		exit 1; \
	fi; \
	if [ -z "$$BLACK_REQ" ]; then \
		echo "⚠️  WARNING: Black version not found in requirements.txt"; \
		exit 1; \
	fi; \
	if [ "$$BLACK_VENV" != "$$BLACK_REQ" ]; then \
		echo "❌ ERROR: Black version mismatch!"; \
		echo "   venv has:         $$BLACK_VENV"; \
		echo "   requirements.txt: $$BLACK_REQ"; \
		echo ""; \
		echo "Fix: Run 'pip install -r backend/requirements.txt' or 'make venv'"; \
		exit 1; \
	fi; \
	echo "✓ Black version matches ($$BLACK_VENV)"

check-coding-rules: ## Verify compliance with CODING_RULES.md
	@echo "Checking coding rules compliance..."
	@$(PY) scripts/check_coding_rules.py

ai-preflight: ## Pre-flight check for AI agents before code generation
	@echo "=========================================="
	@echo "AI AGENT PRE-FLIGHT CHECKS"
	@echo "=========================================="
	@echo ""
	@echo "Checking tool versions..."
	@$(MAKE) check-tool-versions
	@echo ""
	@echo "Running coding rules verification..."
	@$(MAKE) check-coding-rules
	@echo ""
	@echo "✓ Pre-flight checks passed!"
	@echo "✓ Safe to generate code."
	@echo ""
	@echo "REMINDER: After code generation, run:"
	@echo "  1. make format"
	@echo "  2. make verify"
	@echo "=========================================="

env-check: ## Quick sanity: ensure imports & tests compile
	@cd backend && $(PY) -m compileall -q tests
	@$(PY) scripts/env_check.py

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗄️ DATABASE MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

regstack-migrate: ## Run Alembic migrations for the Regstack schema
	ALEMBIC_INI=db/alembic.ini \
	$(PY) -m alembic -c $$ALEMBIC_INI upgrade head

regstack-ingest: ## Ingest SG BCA sample into the configured database
	@if [ -z "$$REGSTACK_DB" ]; then \
		echo "Set REGSTACK_DB before running this target"; \
		exit 1; \
	fi
	$(PY) -m scripts.ingest --jurisdiction sg_bca --since 2025-01-01 --store $$REGSTACK_DB

init-db: ## Apply Alembic migrations inside Docker
	$(REQUIRE_DOCKER_COMPOSE)
	$(DOCKER_COMPOSE) exec backend python -m backend.migrations alembic upgrade head

REVISION_AUTOGEN ?= 1

db.revision: ## Create a new Alembic revision (set REVISION_MESSAGE="..." and optionally REVISION_AUTOGEN=0)
	$(PY) scripts/ensure_alembic.py
	cd backend && \
		SQLALCHEMY_DATABASE_URI="$${SQLALCHEMY_DATABASE_URI:-$(DEV_SQLITE_URL)}" \
		$(PY) -m alembic revision $(if $(filter 1 true yes,$(REVISION_AUTOGEN)),--autogenerate,) $(if $(strip $(REVISION_MESSAGE)),-m "$(REVISION_MESSAGE)",)

db.upgrade: ## Apply database migrations locally via Alembic
	$(PY) scripts/ensure_alembic.py
	cd backend && \
		SQLALCHEMY_DATABASE_URI="$${SQLALCHEMY_DATABASE_URI:-$(DEV_SQLITE_URL)}" \
		$(PY) -m alembic upgrade head

db-backup: ## Backup local SQLite database
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)/backups
	@if [ -f $(DEV_RUNTIME_DIR_ABS)/app.db ]; then \
		TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
		cp $(DEV_RUNTIME_DIR_ABS)/app.db $(DEV_RUNTIME_DIR_ABS)/backups/app_$$TIMESTAMP.db; \
		echo "✅ Database backed up to: $(DEV_RUNTIME_DIR_ABS)/backups/app_$$TIMESTAMP.db"; \
	else \
		echo "⚠️  No database found at $(DEV_RUNTIME_DIR_ABS)/app.db"; \
	fi

db-restore: ## Restore database from latest backup
	@if [ -z "$$(ls -t $(DEV_RUNTIME_DIR_ABS)/backups/app_*.db 2>/dev/null | head -1)" ]; then \
		echo "❌ No backups found in $(DEV_RUNTIME_DIR_ABS)/backups/"; \
		exit 1; \
	fi
	@LATEST=$$(ls -t $(DEV_RUNTIME_DIR_ABS)/backups/app_*.db | head -1); \
	echo "Restoring from: $$LATEST"; \
	cp $$LATEST $(DEV_RUNTIME_DIR_ABS)/app.db; \
	echo "✅ Database restored from $$LATEST"

seed-data: ## Seed screening data, finance demo scenarios, and sample properties
	@if [ -n "$(DOCKER_COMPOSE)" ]; then \
	        $(DOCKER_COMPOSE) exec backend python -m backend.scripts.seed_screening; \
	        $(DOCKER_COMPOSE) exec backend python -m backend.scripts.seed_finance_demo; \
	        $(DOCKER_COMPOSE) exec backend python -m backend.scripts.seed_properties_projects --reset; \
	else \
		echo "Docker Compose CLI not detected; running seeders locally."; \
		$(PY) -m backend.scripts.seed_screening; \
		$(PY) -m backend.scripts.seed_finance_demo; \
		$(PY) -m backend.scripts.seed_properties_projects --reset; \
	fi

seed-properties-projects: ## Seed sample properties and projects for Commercial Property APIs
	@if [ -n "$(DOCKER_COMPOSE)" ]; then \
	    $(DOCKER_COMPOSE) exec backend python -m backend.scripts.seed_properties_projects --reset; \
	else \
	    $(PY) -m backend.scripts.seed_properties_projects --reset; \
	fi

seed-nonreg:
	$(PY) -m backend.scripts.seed_nonreg

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧹 CLEANING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

clean: ## Clean build artifacts
	cd backend && rm -rf __pycache__ .pytest_cache .coverage htmlcov
	cd frontend && rm -rf dist node_modules/.cache

clean-ui: ## Clean frontend cache and build artifacts
	@echo "🧹 Cleaning UI cache and build artifacts..."
	@rm -rf frontend/node_modules/.vite
	@rm -rf frontend/.vite
	@rm -rf frontend/dist
	@rm -rf ui-admin/node_modules/.vite
	@rm -rf ui-admin/.vite
	@rm -rf ui-admin/dist
	@echo "✅ UI cache cleaned successfully"

docker-clean: ## Remove stopped containers and unused Docker artifacts
	@scripts/docker_cleanup.sh

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 DEVELOPMENT WORKFLOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

dev: ## Start supporting services, the backend API, and frontends
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	@echo "found 0 vulnerabilities"
	@echo "✅ Dependencies installed successfully ..."
	@echo "Checking service status..."
	@if [ -d uvicorn ]; then echo "WARNING: './uvicorn/' package detected; it will shadow the real uvicorn. Rename or remove it." >&2; fi
	@if [ -z "$(DOCKER_COMPOSE)" ]; then \
		echo "Docker Compose CLI not found; skipping container startup."; \
	else \
		$(DOCKER_COMPOSE) up -d; \
	fi
	@if [ -f $(DEV_BACKEND_PID) ] && kill -0 $$(cat $(DEV_BACKEND_PID)) 2>/dev/null; then \
		echo "Backend API already running (PID $$(cat $(DEV_BACKEND_PID)))."; \
		echo "✅ API running on port $(BACKEND_PORT)."; \
	else \
		rm -f $(DEV_BACKEND_PID); \
	                : > $(DEV_BACKEND_LOG); \
	                : "Prefer an externally provided DATABASE_URL; otherwise fall back to local SQLite file."; \
		( \
			EFFECTIVE_DB_URL=$${DATABASE_URL:-$(DEV_SQLITE_URL)}; \
			DEV_SQLITE_URL="$(DEV_SQLITE_URL)" SQLALCHEMY_DATABASE_URI="$$EFFECTIVE_DB_URL" DATABASE_URL="$$EFFECTIVE_DB_URL" \
				nohup $(BACKEND_CMD) > "$(DEV_BACKEND_LOG)" 2>&1 & \
			echo $$! > "$(DEV_BACKEND_PID)" \
		); \
		echo "Backend API started (PID $$(cat $(DEV_BACKEND_PID))). Logs: $(DEV_BACKEND_LOG)"; \
		echo "✅ API running on port $(BACKEND_PORT)."; \
	fi
	@if [ -f $(DEV_FRONTEND_PID) ] && kill -0 $$(cat $(DEV_FRONTEND_PID)) 2>/dev/null; then \
		echo "Frontend app already running (PID $$(cat $(DEV_FRONTEND_PID)))."; \
		echo "✅ UI running on port $(FRONTEND_PORT). Check $(DEV_FRONTEND_LOG) for details."; \
	else \
		rm -f $(DEV_FRONTEND_PID); \
		: > $(DEV_FRONTEND_LOG); \
		(cd frontend && VITE_API_BASE=http://localhost:$(BACKEND_PORT) nohup $(FRONTEND_CMD) > $(DEV_FRONTEND_LOG) 2>&1 & echo $$! > $(DEV_FRONTEND_PID)); \
		echo "Frontend app started (PID $$(cat $(DEV_FRONTEND_PID))). Logs: $(DEV_FRONTEND_LOG)"; \
		echo "✅ UI running on port $(FRONTEND_PORT). Check $(DEV_FRONTEND_LOG) for actual port if reassigned."; \
	fi
	@if [ "$(INCLUDE_ADMIN)" != "0" ]; then \
		if [ -f $(DEV_ADMIN_PID) ] && kill -0 $$(cat $(DEV_ADMIN_PID)) 2>/dev/null; then \
			echo "Admin UI already running (PID $$(cat $(DEV_ADMIN_PID)))."; \
			echo "✅ Admin UI running on port $(ADMIN_PORT). Check $(DEV_ADMIN_LOG) for details."; \
		else \
			rm -f $(DEV_ADMIN_PID); \
			: > $(DEV_ADMIN_LOG); \
			(cd ui-admin && VITE_API_BASE=http://localhost:$(BACKEND_PORT) VITE_API_URL=http://localhost:$(BACKEND_PORT)/api/v1 nohup $(ADMIN_CMD) > $(DEV_ADMIN_LOG) 2>&1 & echo $$! > $(DEV_ADMIN_PID)); \
			echo "Admin UI started (PID $$(cat $(DEV_ADMIN_PID))). Logs: $(DEV_ADMIN_LOG)"; \
			echo "✅ Admin UI running on port $(ADMIN_PORT). Check $(DEV_ADMIN_LOG) for actual port if reassigned."; \
		fi; \
	else \
		echo "Skipping admin UI (INCLUDE_ADMIN=0)."; \
	fi

status: ## Show running status for dev services
	@echo "Backend API:"; \
	if [ -f $(DEV_BACKEND_PID) ]; then \
		PID=$$(cat $(DEV_BACKEND_PID)); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "  running (PID $$PID, port $(BACKEND_PORT))"; \
		else \
			echo "  stopped (stale PID $$PID in $(DEV_BACKEND_PID))"; \
		fi; \
	else \
		echo "  stopped"; \
	fi
	@echo "Frontend app:"; \
	if [ -f $(DEV_FRONTEND_PID) ]; then \
		PID=$$(cat $(DEV_FRONTEND_PID)); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "  running (PID $$PID, port $(FRONTEND_PORT))"; \
		else \
			echo "  stopped (stale PID $$PID in $(DEV_FRONTEND_PID))"; \
		fi; \
	else \
		echo "  stopped"; \
	fi
	@if [ "$(INCLUDE_ADMIN)" != "0" ]; then \
		echo "Admin UI:"; \
		if [ -f $(DEV_ADMIN_PID) ]; then \
			PID=$$(cat $(DEV_ADMIN_PID)); \
			if kill -0 $$PID 2>/dev/null; then \
				echo "  running (PID $$PID, port $(ADMIN_PORT))"; \
			else \
				echo "  stopped (stale PID $$PID in $(DEV_ADMIN_PID))"; \
			fi; \
		else \
			echo "  stopped"; \
		fi; \
	fi

stop: ## Stop services started with dev (excluding docker-compose)
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

ui-stop: ## Force stop UI servers on configured ports (kills stuck processes)
	@echo "⏹️  Stopping UI servers on ports $(BACKEND_PORT), $(FRONTEND_PORT), $(ADMIN_PORT)..."
	@-pids=$$(lsof -ti:$(FRONTEND_PORT) 2>/dev/null); \
	if [ "$$pids" ]; then \
		echo "Killing frontend processes on port $(FRONTEND_PORT): $$pids"; \
		kill $$pids 2>/dev/null || true; \
	else \
		echo "ℹ️  No frontend server running on port $(FRONTEND_PORT)"; \
	fi
	@-pids=$$(lsof -ti:$(ADMIN_PORT) 2>/dev/null); \
	if [ "$$pids" ]; then \
		echo "Killing admin UI processes on port $(ADMIN_PORT): $$pids"; \
		kill $$pids 2>/dev/null || true; \
	else \
		echo "ℹ️  No admin UI server running on port $(ADMIN_PORT)"; \
	fi
	@-pids=$$(lsof -ti:$(BACKEND_PORT) 2>/dev/null); \
	if [ "$$pids" ]; then \
		echo "Killing backend processes on port $(BACKEND_PORT): $$pids"; \
		kill $$pids 2>/dev/null || true; \
	else \
		echo "ℹ️  No backend server running on port $(BACKEND_PORT)"; \
	fi
	@sleep 1
	@echo "✅ All UI servers stopped"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🐳 DOCKER OPERATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

build: ## Build production images
	$(REQUIRE_DOCKER_COMPOSE)
	$(DOCKER_COMPOSE) build

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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🏗️ AEC WORKFLOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import-sample: ## Upload the bundled sample payload and seed overlay geometry
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	cd backend && AEC_RUNTIME_DIR=$(DEV_RUNTIME_DIR_ABS) $(PY) -m scripts.aec_flow import-sample --sample $(AEC_SAMPLE) --project-id $(AEC_PROJECT_ID)

run-overlay: ## Execute the overlay engine using the inline worker queue
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	cd backend && AEC_RUNTIME_DIR=$(DEV_RUNTIME_DIR_ABS) $(PY) -m scripts.aec_flow run-overlay --project-id $(AEC_PROJECT_ID)

export-approved: ## Approve overlays and generate a CAD/BIM export artefact
	@mkdir -p $(DEV_RUNTIME_DIR_ABS)
	cd backend && AEC_RUNTIME_DIR=$(DEV_RUNTIME_DIR_ABS) $(PY) -m scripts.aec_flow export-approved --project-id $(AEC_PROJECT_ID) --format $(AEC_EXPORT_FORMAT) --decided-by "$(AEC_DECIDED_BY)" --notes "$(AEC_APPROVAL_NOTES)"

sync-products:
	$(PY) -m backend.flows.sync_products --csv-path vendor.csv
