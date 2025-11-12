# Third-Party Audit Guide

**Purpose:** This document provides standardized commands and procedures for third-party auditors to verify code quality, test coverage, and compliance.

**Last Updated:** 2025-11-02
**Current Coverage Baseline:** 60.83% (622 tests passing)

---

## Quick Reference

For a **complete audit**, run these two commands:

```bash
# 1. Backend test coverage with detailed report
SECRET_KEY=test-secret-key JOB_QUEUE_BACKEND=inline \
  .venv/bin/python -m pytest backend/tests \
    --cov=backend/app \
    --cov-report=term-missing \
    --cov-report=html

# 2. Code quality verification (formatting, linting, coding rules, tests)
make verify
```

Then review the generated HTML coverage report at `htmlcov/index.html`.

---

## Backend Test Coverage

### Recommended Command (Most Accurate)

```bash
SECRET_KEY=test-secret-key JOB_QUEUE_BACKEND=inline \
  .venv/bin/python -m pytest backend/tests \
    --cov=backend/app \
    --cov-report=term-missing \
    --cov-report=html
```

**Why this command:**
- ✅ Runs the complete test suite (all 622 tests)
- ✅ Includes all enabled integration tests
- ✅ Produces detailed line-by-line coverage with `--cov-report=term-missing`
- ✅ Generates browsable HTML report at `htmlcov/index.html`
- ✅ Uses `JOB_QUEUE_BACKEND=inline` for consistent async job execution
- ✅ This is the **official tracking command** used in coverage baselines

**Expected Results (as of 2025-11-02):**
- Overall coverage: **60.83%**
- Tests passing: **622**
- Coverage gap to 80% target: **19.17 percentage points**

### Alternative: Using Make Target

```bash
make test-cov
```

**✅ FIXED:** As of 2025-11-02, the `make test-cov` target has been updated to match the recommended pytest command. It now:
- ✅ Runs all enabled tests (no more --ignore flags)
- ✅ Includes `SECRET_KEY=test-secret-key` environment variable
- ✅ Uses `--cov-report=term-missing` for detailed output
- ✅ Produces same coverage results as manual pytest command

**Result:** Both `make test-cov` and the manual pytest command now produce identical results (60.83% coverage, 622 tests passing).

---

## Code Quality Verification

### Comprehensive Quality Check

```bash
make verify
```

**What it checks:**
1. **Format checks** - Black (code formatting) and isort (import sorting)
2. **Linting** - Flake8 (Python), mypy (type checking), ESLint (frontend)
3. **Coding rules** - Validates compliance with [CODING_RULES.md](../../CODING_RULES.md)
4. **Delivery plan** - Validates feature_delivery_plan_v2.md and WORK_QUEUE.MD structure
5. **Unit tests** - Runs fast unit tests

**Note:** `make verify` only runs unit tests (fast), not the full integration suite. For full coverage, use the pytest command above.

---

## Frontend Testing

### Run Frontend Tests

```bash
cd frontend && npm test
```

### Lint Frontend Code

```bash
cd frontend && npm run lint
```

---

## Pre-Commit Hooks Verification

The project uses pre-commit hooks for automatic code quality checks on every commit.

### Check Hook Status

```bash
make hooks
```

This runs all pre-commit hooks across the entire repository:
- **black** - Code formatting
- **ruff** - Import sorting + linting
- **prettier** - Frontend formatting
- **audit-migrations** - Database migration validation
- **pdf-smoke-test** - PDF generation smoke test

---

## Coverage Breakdown by Module

As of 2025-11-02 baseline (60.23% overall):

| Module | Coverage | Missing Lines | Priority |
|--------|----------|---------------|----------|
| **services/** | 50.2% | **3,866** | 🔴 CRITICAL |
| **api/** | 46.2% | **2,438** | 🔴 CRITICAL |
| core/ | 73.1% | 501 | 🟡 Medium |
| utils/ | 71.4% | 231 | 🟡 Medium |
| models/ | 98.3% | 33 | ✅ Good |
| schemas/ | 94.3% | 70 | ✅ Good |

**Key Finding:** The `services/` and `api/` modules account for **6,304 missing lines** out of ~7,200 total uncovered lines.

See [coverage_opportunities.md](coverage_opportunities.md) for detailed improvement roadmap.

---

## Recent Coverage Improvements

### Session Progress (2025-11-02)

| Session | Baseline | Change | Work Done | Tests Added |
|---------|----------|--------|-----------|-------------|
| Start | 55.38% | - | Initial baseline | 610 tests |
| Session 1 | 55.96% | +0.58% | Enabled preview_jobs tests | +4 tests |
| Session 2 | 57.82% | +1.86% | Enabled developer site acquisition test | +1 test |
| Session 3 | **60.23%** | +2.41% | Enabled finance asset breakdown tests | +7 tests |

**Total improvement:** +4.85% coverage (+12 tests) by enabling existing skipped tests.

### Key File Improvements

1. **api/v1/finance.py**: 24.3% → **71.2%** (+46.9%, +456 lines)
   - Enabled 7 comprehensive tests in `test_finance_asset_breakdown.py`
   - Tests cover: asset mix breakdown, construction loans, sensitivity analysis, SSE streaming, authorization

2. **api/v1/developers.py**: 36.9% → **70.5%** (+33.7%, +307 lines)
   - Enabled comprehensive test in `test_developer_site_acquisition.py`
   - Tests cover: GPS capture, build envelope, asset optimization, heritage context, preview jobs

3. **services/preview_jobs.py**: 22% → **85%** (+63%, +186 lines estimated)
   - Enabled 4 tests in `test_services/test_preview_jobs.py`
   - Tests cover: queue_preview, refresh_job, error handling

---

## Output Interpretation

### Coverage Report Format

The terminal output shows:

```
backend/app/services/preview_jobs.py    85%    15-18, 45-47
backend/app/api/v1/finance.py          71%    125-130, 245-267, ...
TOTAL                                  60%
```

**How to read:**
- **Percentage** - Lines covered by tests
- **Missing lines** - Line numbers NOT covered (shown after percentage)
- **TOTAL** - Overall coverage across all files

### HTML Report Navigation

After running the pytest command with `--cov-report=html`, open `htmlcov/index.html` in a browser:

1. **Index page** - Shows all files sorted by coverage %
2. **Click any file** - View source with color-coded coverage:
   - 🟢 Green lines - Covered by tests
   - 🔴 Red lines - NOT covered by tests
   - ⚪ White lines - Not executable (comments, docstrings)
3. **Sort columns** - Click headers to sort by name, coverage %, missing lines

---

## Continuous Integration

### GitHub Actions / CI Pipeline

The project uses pre-commit hooks that run automatically on every commit. To simulate CI checks locally:

```bash
# Run all pre-commit hooks
make hooks

# Run full verification suite
make verify

# Run coverage measurement
SECRET_KEY=test-secret-key JOB_QUEUE_BACKEND=inline \
  .venv/bin/python -m pytest backend/tests \
    --cov=backend/app --cov-report=term
```

---

## Common Audit Questions

### Q: What is the current test coverage?
**A:** 60.83% as of 2025-11-02 (622 tests passing). See [PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.MD](../../PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.MD) for baseline tracking.

### Q: What is the coverage target?
**A:** 80% backend coverage (Rule 10.1 in [CODING_RULES.md](../../CODING_RULES.md)).

### Q: How is coverage measured?
**A:** Using pytest-cov with the command documented in this guide. Results are tracked in the audit log after each improvement.

### Q: Are tests run on every commit?
**A:** Yes, pre-commit hooks run formatting, linting, and coding rule checks. Full test suite should be run before PR merge.

### Q: Where are coverage reports stored?
**A:** HTML reports are generated locally in `htmlcov/` directory (git-ignored). Coverage baselines are tracked in:
- [PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.MD](../../PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.MD) - Session log with detailed history
- [coverage_opportunities.md](coverage_opportunities.md) - Coverage history log table

### Q: What test framework is used?
**A:**
- Backend: pytest + pytest-asyncio + pytest-cov
- Frontend: Vitest (npm test)

### Q: How long do tests take to run?
**A:**
- Full backend suite: ~2-3 minutes (622 tests)
- Unit tests only: ~30-60 seconds
- Frontend tests: ~10-30 seconds

---

## Environment Setup for Auditors

### Prerequisites

1. **Python 3.11+** installed
2. **Node.js 18+** and npm installed
3. **Docker** and Docker Compose (for database services)

### Quick Setup

```bash
# 1. Create virtual environment and install dependencies
make venv

# 2. Start supporting services (PostgreSQL, Redis)
docker compose up -d

# 3. Run database migrations
make db.upgrade

# 4. Run verification suite
make verify

# 5. Run full coverage measurement
SECRET_KEY=test-secret-key JOB_QUEUE_BACKEND=inline \
  .venv/bin/python -m pytest backend/tests \
    --cov=backend/app --cov-report=html

# 6. Open coverage report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

---

## Audit Checklist

Use this checklist for systematic audit:

- [ ] **Coverage Measurement**
  - [ ] Run full pytest suite with coverage
  - [ ] Verify coverage meets or exceeds documented baseline (60.83%)
  - [ ] Review HTML coverage report for any critical gaps
  - [ ] Check that core business logic (services/, api/) has adequate coverage

- [ ] **Code Quality**
  - [ ] Run `make verify` - all checks should pass
  - [ ] Run `make hooks` - pre-commit hooks should pass
  - [ ] Review coding rules compliance (CODING_RULES.md)
  - [ ] Check frontend linting (npm run lint)

- [ ] **Test Health**
  - [ ] All 622+ tests should pass
  - [ ] No skipped tests in critical paths
  - [ ] No flaky or intermittent test failures
  - [ ] Test runtime is reasonable (<5 minutes)

- [ ] **Documentation**
  - [ ] Coverage baseline documented in PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.MD
  - [ ] Recent improvements logged in coverage_opportunities.md
  - [ ] Coding rules up to date
  - [ ] Roadmap and work queue validated

- [ ] **Infrastructure**
  - [ ] Docker services start successfully
  - [ ] Database migrations apply cleanly
  - [ ] Pre-commit hooks installed and configured
  - [ ] Frontend builds without errors

---

## Support and Questions

If you encounter issues during audit:

1. **Check baseline documents:**
   - [PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.MD](../../PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.MD) - Full audit log
   - [coverage_opportunities.md](coverage_opportunities.md) - Coverage improvement roadmap
   - [CODING_RULES.md](../../CODING_RULES.md) - Development standards

2. **Verify environment:**
   - Python version: `python --version` (should be 3.11+)
   - Dependencies installed: `make venv`
   - Services running: `docker compose ps`

3. **Common issues:**
   - **Tests fail with database errors:** Ensure PostgreSQL is running (`docker compose up -d`)
   - **Import errors:** Ensure venv is activated and dependencies installed
   - **Coverage lower than expected:** Verify you're using the correct pytest command (or `make test-cov` which now works correctly)

---

**Last Verified:** 2025-11-02
**Verified By:** Infrastructure audit session
**Next Review:** After reaching 70% coverage milestone
