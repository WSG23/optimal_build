# Coding Rules for optimal_build

This document defines the coding standards for the `optimal_build` repository. All new code and modified files should follow these rules. CODEX and other contributors should adhere to these standards.

For workflow, tooling setup, and detailed linting guidance, see [CONTRIBUTING.md](CONTRIBUTING.md).

If a temporary exception is truly necessary, record it in
`.coding-rules-exceptions.yml` and include context plus a clean-up plan. The
automation in `scripts/check_coding_rules.py` reads that file when evaluating
rule violations.

---

## 1. Database Migrations

### 1.1 Never Edit Existing Migrations

**Rule:** Never edit existing Alembic migration files. Always create a new migration for schema changes.

**Why:** Editing existing migrations breaks version history and can corrupt databases that have already applied those migrations.

**How to follow:**
- Use `alembic revision -m "description"` to create new migration files
- Migration files live in `backend/migrations/versions/` (main app) or `db/versions/` (regstack)
- Never modify files like `20240919_000005_enable_postgis_geometry.py` after they're committed
- Use descriptive names: `YYYYMMDD_NNNNNN_brief_description.py`

**Examples:**
```bash
# ✅ Correct - create new migration
cd backend && alembic revision -m "add compliance_score column"

# ❌ Wrong - editing existing migration
# Don't open and modify backend/migrations/versions/20240919_000005_enable_postgis_geometry.py
```

### 1.2 PostgreSQL ENUM Types in Migrations

**Rule:** Do NOT use `sa.Enum()` objects with `create_type=False` in migrations. Use plain `sa.String()` for ENUM columns instead.

**Why:** SQLAlchemy's `sa.Enum()` tries to autocreate the ENUM type even when `create_type=False`, causing "type already exists" errors. This pattern caused 9 migration failures in Oct 2025 (see git history for 20250220_000009-000017).

**How to follow:**
- Use `sa.String()` for columns that will store ENUM values
- PostgreSQL will still validate against the ENUM type if you manually create it
- If you need the ENUM type for validation, create it separately with raw SQL
- Do NOT define `SOME_ENUM = sa.Enum(..., create_type=False)` variables

**Examples:**
```python
# ❌ WRONG - causes "duplicate type" errors
DEAL_STATUS_ENUM = sa.Enum(
    "open", "closed_won", "closed_lost",
    name="deal_status",
    create_type=False,  # ← This doesn't actually prevent autocreation!
)

def upgrade() -> None:
    # Manual creation
    op.execute("CREATE TYPE deal_status AS ENUM ('open', 'closed_won', 'closed_lost')")

    op.create_table(
        "deals",
        sa.Column("status", DEAL_STATUS_ENUM, nullable=False),  # ← Tries to create type again!
    )

# ✅ CORRECT - use String type
def upgrade() -> None:
    # Optional: Create ENUM type if you want DB-level validation
    op.execute(
        "CREATE TYPE deal_status AS ENUM ('open', 'closed_won', 'closed_lost')"
    )

    op.create_table(
        "deals",
        sa.Column("status", sa.String(), nullable=False),  # ← Simple string type
    )

    # Optional: Convert to ENUM type after table creation
    op.execute(
        "ALTER TABLE deals ALTER COLUMN status TYPE deal_status USING status::deal_status"
    )
```

**Related issues:**
- Foreign keys to non-existent tables: Remove them and add TODO comments for later
- UUID columns: Use `postgresql.UUID(as_uuid=True)` not `String(36)`

**Enforcement:**
This rule is enforced by:
- Pre-commit hook: `check-migration-enums` (runs on every commit)
- Script: `scripts/check_migration_enums.py` (can run manually)
- CI: Will be added in Phase 3 of migration validation infrastructure

To check manually:
```bash
python3 scripts/check_migration_enums.py
```

**Exceptions:**
Pre-existing migrations that use the forbidden pattern are listed in `.coding-rules-exceptions.yml` under `rule_1_2_enum_pattern`. These are grandfathered in but should NOT be edited. All NEW migrations must follow the correct pattern.

### 1.3 ENUM Value Naming Convention

**Rule:** PostgreSQL ENUM values must EXACTLY match the Python enum string values. Use consistent casing between database and code.

**Why:** PostgreSQL ENUM values are case-sensitive. If the Python model uses `ProjectType.NEW_DEVELOPMENT` with value `"NEW_DEVELOPMENT"`, the SQL ENUM must contain `'NEW_DEVELOPMENT'`, not `'new_development'`. Mismatches cause runtime errors like `invalid input value for enum`.

**How to follow:**
- Check the Python enum definition to see what string VALUES it uses (not the member names)
- Create the PostgreSQL ENUM with the exact same values
- For Python enums with uppercase values, use uppercase in SQL
- For Python enums with lowercase values, use lowercase in SQL
- When seeding data, use `enum_value.value` to get the string value

**Examples:**

```python
# Python model - check the VALUES
class ProjectType(str, Enum):
    NEW_DEVELOPMENT = "NEW_DEVELOPMENT"  # ← VALUE is uppercase
    REDEVELOPMENT = "REDEVELOPMENT"

class EntApprovalCategory(str, Enum):
    PLANNING = "planning"  # ← VALUE is lowercase
    BUILDING = "building"
```

```python
# ✅ CORRECT - migration matches Python enum VALUES
def upgrade() -> None:
    # ProjectType uses uppercase VALUES
    op.execute("""
        CREATE TYPE projecttype AS ENUM (
            'NEW_DEVELOPMENT',  -- matches ProjectType.NEW_DEVELOPMENT.value
            'REDEVELOPMENT'     -- matches ProjectType.REDEVELOPMENT.value
        )
    """)

    # EntApprovalCategory uses lowercase VALUES
    op.execute("""
        CREATE TYPE ent_approval_category AS ENUM (
            'planning',  -- matches EntApprovalCategory.PLANNING.value
            'building'   -- matches EntApprovalCategory.BUILDING.value
        )
    """)

# ❌ WRONG - case mismatch with Python enum
def upgrade() -> None:
    op.execute("""
        CREATE TYPE projecttype AS ENUM (
            'new_development',  -- ❌ Python has "NEW_DEVELOPMENT"
            'redevelopment'     -- ❌ Python has "REDEVELOPMENT"
        )
    """)
```

```python
# When seeding data
# ✅ CORRECT - use .value to get the string
approval_type = EntApprovalType(
    category=EntApprovalCategory.PLANNING.value  # Gets "planning" string
)

# ❌ WRONG - passing enum object can send the member name instead of value
approval_type = EntApprovalType(
    category=EntApprovalCategory.PLANNING  # Might send "PLANNING" instead of "planning"
)
```

**Verification:**
```bash
# Check what value the Python enum actually uses
python3 -c "from app.models.projects import ProjectType; print(ProjectType.NEW_DEVELOPMENT.value)"
# Output: NEW_DEVELOPMENT  ← Use this in SQL

# Check database ENUM values
psql -c "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'projecttype'::regtype;"
```

---

## 2. Async/Await for Database and API Operations

**Rule:** All database calls, API routes, and I/O operations must use `async`/`await`. No synchronous blocking operations in FastAPI routes or database queries.

**Why:** The FastAPI backend is fully asynchronous. Mixing sync code breaks the async event loop and causes performance issues.

**How to follow:**
- Mark all API route functions with `async def`
- Use `async with session.begin()` for database transactions
- Use `await session.execute()` for queries
- Import from `sqlalchemy.ext.asyncio` not sync `sqlalchemy.orm`

**Examples:**
```python
# ✅ Correct - async patterns
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_property(session: AsyncSession, property_id: str):
    result = await session.execute(
        select(SingaporeProperty).where(SingaporeProperty.id == property_id)
    )
    return result.scalar_one_or_none()

@router.get("/properties/{property_id}")
async def fetch_property(property_id: str, session: AsyncSession = Depends(get_db)):
    return await get_property(session, property_id)

# ❌ Wrong - sync patterns
from sqlalchemy.orm import Session

def get_property(session: Session, property_id: str):  # Missing async
    return session.query(SingaporeProperty).filter(...).first()  # Sync query
```

---

## 3. Testing Before Commits

**Rule:** Code formatting is **automatically handled by pre-commit hooks**. Run `make verify` before committing to ensure all checks pass.

**Why:**
- Pre-commit hooks automatically fix formatting issues (black, ruff, prettier)
- `make verify` catches lint failures, unused variables, and test regressions
- Automation prevents "commit fails → fix issues → re-commit" cycles

**New Workflow (Simplified):**
```bash
# STEP 1 (MANDATORY): Verify everything passes
make verify

# STEP 2: Commit (pre-commit hooks auto-format)
git add .
git commit -m "your message"

# If hooks modified files, they're auto-staged - just commit again
```

**Manual formatting (optional):**
```bash
# To format ALL files before committing:
pre-commit run --all-files
```

**Note:** `make format` is now deprecated - it just shows a help message explaining that formatting is automatic.

**Tip:** See [CONTRIBUTING.md](CONTRIBUTING.md#testing-and-quality-checks) for the full testing and linting workflow.

---

## 4. Dependency Management

**Rule:** When adding new dependencies, update the appropriate dependency file. Never install packages without tracking them. For formatters and linters, versions MUST match across all configuration files.

**Backend (Python):**
- Add to `backend/requirements.txt` (production) or `backend/requirements-dev.txt` (dev/test only)
- Pin exact versions: `fastapi==0.104.1`
- **CRITICAL:** Black version in `requirements.txt` MUST match `.pre-commit-config.yaml` to avoid formatting inconsistencies

**Frontend (TypeScript/React):**
- Add to `frontend/package.json` using `npm install --save <package>` or `npm install --save-dev <package>`
- Admin UI: Add to `ui-admin/package.json`

**Version Synchronization (IMPORTANT):**
When updating formatter/linter versions, update ALL occurrences:
- **Black:** Update in `requirements.txt`, `requirements-dev.txt`, AND `.pre-commit-config.yaml` (all 3 must match)
- **Ruff:** Update in `requirements.txt` AND `.pre-commit-config.yaml`
- Failing to sync versions causes "code formatted by venv → reformatted by pre-commit hooks" issues

**Why:** Keeps dependencies reproducible across environments and prevents "works on my machine" issues. Version mismatches in formatters cause commit failures where `make format` produces different output than pre-commit hooks.

**Examples:**
```bash
# ✅ Correct - track dependencies
cd backend
echo "pydantic==2.4.2" >> requirements.txt
pip install pydantic==2.4.2

cd frontend
npm install --save axios

# ✅ Correct - update black version everywhere
# Step 1: Update requirements files
echo "black==24.8.0" >> backend/requirements.txt
echo "black==24.8.0" >> backend/requirements-dev.txt
# Step 2: Update .pre-commit-config.yaml rev: 24.8.0
# Step 3: pip install and pre-commit install --install-hooks

# ❌ Wrong - untracked dependencies
pip install some-random-package  # Not added to requirements.txt

# ❌ Wrong - version mismatch
# requirements.txt has black==23.11.0
# .pre-commit-config.yaml has rev: 24.8.0  # MISMATCH!
```

---

## 5. Singapore Property Compliance Validation

**Rule:** When modifying Singapore property models or compliance logic, always run compliance validation tests to ensure regulatory requirements are met.

**Why:** The app has legal/regulatory requirements for BCA and URA compliance. Breaking these could have real-world consequences.

**How to follow:**
- Run compliance tests: `pytest backend/tests/test_api/test_feasibility.py -v`
- Test the compliance endpoint: `curl -X POST http://localhost:9400/api/v1/singapore-property/check-compliance`
- Check models: `backend/app/models/singapore_property.py`
- Compliance statuses must use proper enums: `ComplianceStatus.PENDING`, `ComplianceStatus.PASSED`, `ComplianceStatus.WARNING`, `ComplianceStatus.FAILED`

**Examples:**
```bash
# ✅ Correct - test compliance after changes
# After modifying backend/app/models/singapore_property.py:
pytest backend/tests/test_api/test_feasibility.py -v

# Check compliance endpoint works:
curl -X POST http://localhost:9400/api/v1/singapore-property/check-compliance \
  -H "Content-Type: application/json" \
  -d '{"property_id": "test-123"}'

# ❌ Wrong - modifying compliance logic without testing
# Editing singapore_property.py and committing without running tests
```

### Automatic enforcement

- `scripts/check_coding_rules.py` runs automatically via `make check-coding-rules` and as part of `make verify`.
- The script executes the compliance tests automatically whenever files under
  `backend/app/models/singapore_property*` or
  `backend/app/api/v1/singapore_property*` are modified.
- If a temporary exception is unavoidable, document it in
  `.coding-rules-exceptions.yml` under `rule_5_singapore`, together with a plan
  for removal.

---

## 6. Python Import Ordering and Formatting

**Rule:** Follow strict import ordering and formatting to match Black, Ruff, and isort hook standards. Imports must be grouped, sorted, and formatted according to the project's automated formatters.

**Why:** Pre-commit hooks automatically fix import formatting. Writing imports correctly the first time prevents unnecessary "write code → hooks modify it → commit modified code" cycles.

**Import Order (PEP 8 + isort):**
1. Standard library imports (e.g., `os`, `sys`, `pathlib`)
2. Third-party package imports (e.g., `sqlalchemy`, `fastapi`, `alembic`)
3. Local application imports (e.g., `app.models`, `app.core`)
4. One blank line between each group

**Within Each Group:**
- `import X` statements come before `from X import Y` statements
- Alphabetical ordering
- Combine multiple imports from the same module: `from X import A, B` (not separate lines)

**Line Length:**
- Maximum 88 characters (Black standard)
- Avoid unnecessary line wrapping for lines under 88 characters

**File Formatting:**
- All files must end with a single newline character
- No trailing whitespace on any line

**Examples:**

```python
# ✅ Correct - proper import ordering
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models.audit
import app.models.finance
import app.models.imports
from app.models.base import BaseModel

# ❌ Wrong - mixed ordering, separate imports from same module
from logging.config import fileConfig  # from statement before import
import os
import sys

from sqlalchemy import engine_from_config  # should combine
from sqlalchemy import pool

from alembic import context  # third-party mixed with above

import app.models.finance  # not alphabetical
import app.models.audit
```

**Tool Configuration:**
- Black: 88 character line length ([.pre-commit-config.yaml:28](.pre-commit-config.yaml#L28))
- Ruff: Uses isort for import ordering ([.pre-commit-config.yaml:35](.pre-commit-config.yaml#L35))
- See [pyproject.toml](pyproject.toml) for detailed tool settings

**Quick Check:**
Always run formatters before committing:
```bash
make format  # Runs black, isort, and ruff with --fix
make verify  # Verify everything passes (runs format-check, lint, tests)
```

**Note:** Pre-commit hooks will auto-format files, but running `make format` first prevents the "hooks modify files → commit fails" cycle.

---

## 7. Code Quality Standards

**Rule:** Write clean, maintainable Python code following PEP 8 and Ruff linting standards. Avoid common code smells caught by automated linters.

**Why:** Clean code is easier to maintain, debug, and extend. The pre-commit hooks enforce these standards automatically, but writing code correctly the first time prevents commit failures.

**Key Standards:**

1. **No unused variables or imports** (Ruff F841, F401)
   - Remove any variables that are assigned but never used
   - Remove any imports that aren't referenced

2. **Proper exception chaining** (Ruff B904)
   - Use `from err` to chain exceptions and preserve stack traces
   - Use `from None` to suppress the original exception when it's not relevant
   - Re-raise caught `HTTPException` without modification

3. **No mutable default arguments** (Ruff B006)
   - Never use `def func(items=[]):`
   - Use `def func(items=None):` and initialize inside the function

4. **Type hints on public APIs** (gradual adoption)
   - Add type hints to function signatures for better IDE support
   - Use `Optional[T]` for nullable parameters

**Examples:**

```python
# ✅ Correct - no unused variables
await generator.save_to_storage(...)
# Variable not assigned if not needed

# ❌ Wrong - unused variable
storage_url = await generator.save_to_storage(...)  # Assigned but never used!

# ✅ Correct - proper exception chaining
try:
    risky_operation()
except ValueError as e:
    raise CustomError("Operation failed") from e  # Preserves original stack trace

# ✅ Correct - suppress original exception when not relevant
try:
    file_path.resolve()
except Exception:
    raise HTTPException(status_code=403, detail="Invalid path") from None

# ✅ Correct - re-raise HTTPException without modification
except HTTPException:
    raise  # Don't wrap or chain HTTPException

# ❌ Wrong - missing exception chain
except ValueError:
    raise CustomError("Operation failed")  # Lost original error context!

# ✅ Correct - no mutable defaults
def process_items(items: Optional[List[str]] = None) -> List[str]:
    if items is None:
        items = []
    return items

# ❌ Wrong - mutable default argument
def process_items(items: List[str] = []) -> List[str]:  # Dangerous!
    return items
```

**Automatic Enforcement:**
- Ruff runs automatically via pre-commit hooks
- Run `make format` to auto-fix many issues
- Run `make verify` to check for violations

**Common Ruff Codes:**
- `F841` - Unused variable
- `F401` - Unused import
- `B904` - Exception must use `raise ... from err` or `from None`
- `B006` - Mutable default argument
- See [Ruff rules documentation](https://docs.astral.sh/ruff/rules/) for full list

---

## 8. AI Agent Testing Instructions (MANDATORY)

**Rule:** When AI agents complete ANY feature, they MUST provide test instructions to the user. This includes backend tests, frontend tests, and UI manual test steps.

**Why:** Phase gates depend on manual walkthroughs and targeted smoke suites. Referencing the official docs keeps every agent in sync with the approved testing scope. Without explicit test instructions, features go untested and regressions accumulate.

**How to follow:**

### 8.1 MANDATORY Testing Checklist After Feature Completion

When you complete ANY feature implementation, you MUST:

**a) Provide backend test commands:**
```markdown
Backend tests:
.venv/bin/pytest backend/tests/test_api/test_[feature].py -v
.venv/bin/pytest backend/tests/test_services/test_[feature].py -v
```

**b) Provide frontend test commands (if applicable):**
```markdown
Frontend tests:
npm test -- src/modules/[feature]/__tests__
npm run lint
```

**c) Provide UI manual test steps:**
```markdown
UI Manual Testing:
1. Navigate to [URL or component]
2. Click [button/action]
3. Verify [expected outcome]
4. Test edge cases: [list specific scenarios]
```

### 8.2 Required Documentation References

Before proposing work, AI agents must read:
- [`docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md`](docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md) (MANDATORY TESTING CHECKLIST section)
- Your phase section in [`docs/feature_delivery_plan_v2.md`](docs/feature_delivery_plan_v2.md)
- [`docs/development/testing/known-issues.md`](docs/development/testing/known-issues.md) (check for known test failures before reporting)
- [`ui-status.md`](docs/planning/ui-status.md) (understand UI implementation status)
- [`TESTING_DOCUMENTATION_SUMMARY.md`](TESTING_DOCUMENTATION_SUMMARY.md) (find smoke/regression suites)
- [`README.md`](README.md) (`make dev` notes for log monitoring)

Mirror those references (or the exact commands they prescribe) in your response.

If expectations change, update the docs first so the automation stays accurate.

### 8.3 Examples

**✅ CORRECT - Complete test instructions:**
```markdown
I've completed the finance scenario privacy feature. Please test:

Backend tests:
.venv/bin/pytest backend/tests/test_api/test_finance.py::test_scenario_privacy -v
.venv/bin/pytest backend/tests/test_models/test_finance_scenario.py -v

Frontend tests:
npm test -- src/modules/finance/__tests__/FinanceScenarioTable.test.tsx

UI Manual Testing:
1. Navigate to /finance/scenarios
2. Create a new scenario
3. Toggle "Make Private" checkbox
4. Save and verify scenario shows lock icon
5. Logout and login as different user
6. Verify private scenario is NOT visible
```

**❌ WRONG - No test instructions:**
```markdown
I've completed the finance scenario privacy feature. The implementation is done.
```

**❌ WRONG - Generic test instructions:**
```markdown
Run the tests to verify the feature works.
```

### 8.4 Automatic Enforcement

- `scripts/check_coding_rules.py` verifies the guidance docs contain the mandatory references. Do not remove them without adding a replacement rule.
- During reviews, reject any "next steps" that omit the required test instructions.
- **FUTURE:** Commit message hook will enforce that feature commits include test commands in the message body.

### 8.5 Compliance Check

When completing a feature, ask yourself:
- [ ] Did I provide backend pytest commands?
- [ ] Did I provide frontend test commands (if applicable)?
- [ ] Did I provide specific UI manual test steps?
- [ ] Did I reference `docs/development/testing/known-issues.md` to avoid duplicate reports?
- [ ] Did I check `docs/planning/ui-status.md` to understand current implementation state?

**If you answered NO to any of these, your work is incomplete.**

---

## 9. Database Performance & Indexing

**Rule:** All foreign keys MUST have indexes. Frequently queried columns SHOULD have indexes. Never deploy tables >1000 rows without appropriate indexes.

**Why:** 89% of failed startups (per Inc.com audit) had no database indexing, causing significant performance degradation. Queries without indexes cause full table scans (O(n) instead of O(log n)).

**How to follow:**
- **ALWAYS index foreign key columns** (user_id, project_id, property_id, etc.)
- **Index columns used in WHERE clauses** frequently
- **Index columns used in JOIN conditions**
- **Index columns used in ORDER BY** if the query is frequent
- **Add indexes in the same migration** that creates the table

**Examples:**
```python
# ✅ CORRECT - Create table with indexes
def upgrade() -> None:
    op.create_table(
        'finance_scenarios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), nullable=False),  # Foreign key
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
    )

    # Index foreign keys
    op.create_index('ix_finance_scenarios_project_id', 'finance_scenarios', ['project_id'])

    # Index frequently queried columns
    op.create_index('ix_finance_scenarios_created_at', 'finance_scenarios', ['created_at'])
    op.create_index('ix_finance_scenarios_status', 'finance_scenarios', ['status'])

    # Composite index for common query pattern
    op.create_index(
        'ix_finance_scenarios_project_status',
        'finance_scenarios',
        ['project_id', 'status']
    )

# ❌ WRONG - No indexes on foreign keys or query columns
def upgrade() -> None:
    op.create_table(
        'finance_scenarios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), nullable=False),  # No index!
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),  # No index!
        sa.Column('status', sa.String(), nullable=False),  # No index!
    )
```

**When to add indexes:**
- **New tables:** Add indexes in the same migration that creates the table
- **Existing tables:** Add indexes in a separate migration if queries are slow (>500ms)
- **After adding columns:** If the new column will be queried frequently, add an index

**Performance targets:**
- All queries <500ms in local testing
- No full table scans on tables >1000 rows
- Foreign key queries return in <100ms

**Check if indexes exist:**
```sql
-- List all indexes on a table
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'finance_scenarios';

-- Find tables missing indexes on foreign keys
SELECT schemaname, tablename
FROM pg_stat_user_tables
WHERE seq_scan > idx_scan
AND seq_scan > 100;
```

**Enforcement:**
- Manual review during code review
- Query performance testing before Phase transitions
- Pre-Phase 2D audit will add missing indexes to existing tables

---

## 10. Testing Requirements

**Rule:** All new features MUST have automated tests. Backend coverage >80% for critical paths. Frontend critical paths must have unit tests.

**Why:** 91% of failed startups (per Inc.com audit) had no automated testing, making feature additions unpredictable and causing regressions.

**How to follow:**

### Backend Testing (MANDATORY)
- **API endpoints:** Integration tests for all new endpoints
- **Service layer:** Unit tests for all business logic functions
- **Database models:** CRUD tests for new models
- **Critical calculations:** 100% coverage for finance, compliance, ROI calculations

**Backend test structure:**
```python
# backend/tests/test_api/test_finance.py
async def test_create_finance_scenario_success(client, test_user):
    """Test creating a finance scenario returns 201 and correct data."""
    response = await client.post(
        "/api/v1/finance/scenarios",
        json={"project_id": 1, "name": "Test Scenario"},
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Scenario"

async def test_create_finance_scenario_unauthorized(client):
    """Test creating scenario without auth returns 401."""
    response = await client.post(
        "/api/v1/finance/scenarios",
        json={"project_id": 1, "name": "Test"}
    )
    assert response.status_code == 401
```

### Frontend Testing (RECOMMENDED)
- **Critical user flows:** E2E tests for login, data submission, calculations
- **Components:** Unit tests for complex components with business logic
- **API clients:** Integration tests for API communication layer

**Frontend test structure:**
```typescript
// frontend/src/modules/finance/components/__tests__/FinanceScenarioTable.test.tsx
import { render, screen } from '@testing-library/react';
import { FinanceScenarioTable } from '../FinanceScenarioTable';

test('renders scenario table with data', () => {
  const scenarios = [{ id: 1, name: 'Test', npv: 1000000 }];
  render(<FinanceScenarioTable scenarios={scenarios} />);

  expect(screen.getByText('Test')).toBeInTheDocument();
  expect(screen.getByText('$1,000,000')).toBeInTheDocument();
});
```

### CI/CD Integration (MANDATORY)
- **Pre-commit:** Tests run automatically before commit
- **PR checks:** All tests must pass before merge
- **No bypassing:** Never use `--no-verify` to skip tests

**Running tests:**
```bash
# Backend tests
pytest backend/tests/ -v

# Frontend tests
npm test

# All tests
make test
```

**Coverage requirements:**
- Backend critical paths: >80%
- Backend overall: >70%
- Frontend critical paths: Covered
- Frontend overall: Best effort (JSDOM timing issues documented in `docs/development/testing/known-issues.md`)

**Enforcement:**
- CI blocks merges without passing tests
- Pre-commit hooks run tests automatically
- Phase gate checks verify test coverage before phase completion

**Exceptions:**
- Frontend tests have known JSDOM timing issues (see `docs/development/testing/known-issues.md`)
- Test harness UI (non-production) may have lower coverage
- Document test gaps in commit messages if test is deferred

---

## 11. Security Practices

**Rule:** Follow security best practices for authentication, input validation, secrets management, and API security. Never commit secrets.

**Why:** 68% of failed startups (per Inc.com audit) had security vulnerabilities leading to breaches and compliance failures.

**How to follow:**

### Authentication & Authorization (MANDATORY)
```python
# ✅ CORRECT - All endpoints require authentication
from app.api.deps import get_current_user, require_developer_role

@router.post("/finance/scenarios")
async def create_scenario(
    data: FinanceScenarioCreate,
    current_user: User = Depends(get_current_user),  # Required auth
    db: AsyncSession = Depends(get_db)
):
    # Verify user owns the project
    if not await user_owns_project(db, current_user.id, data.project_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    return await create_finance_scenario(db, data)

# ❌ WRONG - No authentication required
@router.post("/finance/scenarios")
async def create_scenario(
    data: FinanceScenarioCreate,
    db: AsyncSession = Depends(get_db)
):
    # Anyone can create scenarios!
    return await create_finance_scenario(db, data)
```

### Input Validation (MANDATORY)
```python
# ✅ CORRECT - Pydantic validates all inputs
from pydantic import BaseModel, Field, validator

class FinanceScenarioCreate(BaseModel):
    project_id: int = Field(..., gt=0)  # Must be positive
    name: str = Field(..., min_length=1, max_length=200)  # Length limits
    budget: float = Field(..., gt=0, le=1e9)  # Reasonable range

    @validator('name')
    def name_must_not_contain_html(cls, v):
        if '<' in v or '>' in v:
            raise ValueError('HTML tags not allowed')
        return v

# ❌ WRONG - No input validation
@router.post("/finance/scenarios")
async def create_scenario(project_id: int, name: str, budget: float):
    # Could inject SQL, XSS, or cause overflow!
    return await db.execute(f"INSERT INTO scenarios VALUES ({project_id}, '{name}', {budget})")
```

### SQL Injection Prevention (MANDATORY)
```python
# ✅ CORRECT - Use SQLAlchemy ORM or parameterized queries
from sqlalchemy import select

async def get_scenarios(db: AsyncSession, project_id: int):
    stmt = select(FinanceScenario).where(FinanceScenario.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalars().all()

# ❌ WRONG - SQL injection vulnerability
async def get_scenarios(db: AsyncSession, project_id: int):
    query = f"SELECT * FROM finance_scenarios WHERE project_id = {project_id}"
    # Attacker can inject: project_id = "1 OR 1=1"
    result = await db.execute(query)
    return result.fetchall()
```

### Secrets Management (MANDATORY)
```python
# ✅ CORRECT - Secrets in environment variables
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    api_key: str

    class Config:
        env_file = ".env"  # Never commit .env to git!

# ❌ WRONG - Hardcoded secrets
DATABASE_URL = "postgresql://user:password123@localhost/db"  # Never do this!
JWT_SECRET = "super-secret-key"  # Never do this!
API_KEY = "abc123xyz"  # Never do this!
```

### Rate Limiting (MANDATORY for production)
```python
# ✅ CORRECT - Rate limiting on all endpoints
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/finance/scenarios")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def create_scenario(...):
    pass

# For expensive operations, stricter limits
@router.post("/finance/sensitivity-analysis")
@limiter.limit("2/minute")  # Max 2 requests per minute
async def run_sensitivity(...):
    pass
```

### Security Headers (MANDATORY for production)
```python
# ✅ CORRECT - Add security headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### Password Hashing (MANDATORY)
```python
# ✅ CORRECT - Use bcrypt or argon2
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ❌ WRONG - Plain text or weak hashing
def hash_password(password: str) -> str:
    return password  # Never store plain text!
    # or
    return hashlib.md5(password.encode()).hexdigest()  # MD5 is broken!
```

### Security Checklist for New Features:
- [ ] All endpoints require authentication
- [ ] User authorization checked (owns resource)
- [ ] All inputs validated with Pydantic
- [ ] No SQL injection vulnerabilities (use ORM)
- [ ] No XSS vulnerabilities (escape output)
- [ ] Secrets in environment variables (not code)
- [ ] Rate limiting configured
- [ ] Security headers added
- [ ] Passwords hashed (bcrypt/argon2)
- [ ] HTTPS enforced (production)

**Checking for vulnerabilities:**
```bash
# Check Python dependencies
safety check
pip list --outdated

# Check Node dependencies
npm audit
npm audit fix

# Check for exposed secrets
git log -p | grep -i "password\|secret\|key\|token"

# Check for SQL injection patterns
grep -r 'f".*SELECT\|f".*INSERT\|f".*UPDATE' backend/app --include="*.py"
```

**Enforcement:**
- Manual code review checks security practices
- Automated scans: `npm audit`, `safety check`, `bandit`
- Pre-Phase 2D audit will verify security practices across codebase
- CI will block high/critical vulnerabilities (future Phase 3)

**Deferred Security Work (Requires Money):**
See [TRANSITION_PHASE_CHECKLIST.md](TRANSITION_PHASE_CHECKLIST.md) for:
- Third-party security audits ($5K-15K)
- Penetration testing ($3K-10K)
- Compliance certifications ($15K-50K+)
- WAF, DDoS protection, bug bounty programs

---

## 12. Phase Completion Gates (MANDATORY)

**Rule:** AI agents MUST NOT mark a phase as "✅ COMPLETE" in [feature_delivery_plan_v2.md](docs/feature_delivery_plan_v2.md) if the phase section contains unchecked `- [ ]` checklist items, `🔄 In Progress` markers, or `❌` incomplete items.

**Why:** Phase 1D and Phase 2B were left 60% and 85% incomplete because AI agents marked backend work as "done" and moved to Phase 2C without completing frontend UI components. This creates abandoned features and technical debt.

**How to follow:**

### Before marking ANY phase "✅ COMPLETE":

1. **Check the phase section in feature_delivery_plan_v2.md:**
   - Search for `- [ ]` (unchecked items) → Must be ZERO
   - Search for `🔄` (In Progress markers) → Must be ZERO
   - Search for `❌` (incomplete items) → Must be ZERO

2. **Verify UI manual testing complete:**
   - User must have run all UI manual test steps (see Rule 8)
   - User must have confirmed: "✅ All manual tests passing"

3. **Ask user for explicit approval:**
   ```markdown
   Phase X checklist is complete:
   - ✅ All [ ] items checked
   - ✅ No 🔄 In Progress markers
   - ✅ No ❌ incomplete items
   - ✅ UI manual testing passed

   May I mark Phase X as "✅ COMPLETE" in feature_delivery_plan_v2.md?
   ```

4. **Only after user approval:**
   - Change phase header from "⚠️ IN PROGRESS" → "✅ COMPLETE"
   - Update status percentage to 100%

### If phase has ANY incomplete work:

1. **Keep status as "⚠️ IN PROGRESS"**
2. **Document incomplete items clearly:**
   - Use `🔄` for work in progress
   - Use `❌` for blocked or deferred work
   - Add unchecked `- [ ]` items to checklist

3. **Add incomplete work to [BACKLOG.md](BACKLOG.md):**
   - List each incomplete item with estimate
   - Mark as "BLOCKED - waiting for Phase X completion"

4. **Ask user for decision:**
   ```markdown
   Phase X is 85% complete. Remaining work:
   - 🔄 4 UI components (estimated 1 week)
   - ❌ 3D visualization (blocked on GLB generation)

   Options:
   1. Complete Phase X now (1 week delay to Phase Y)
   2. Defer UI work to backlog and start Phase Y
   3. Complete critical items only, defer rest

   What would you like to do?
   ```

### Examples:

**❌ WRONG - Marking incomplete phase as COMPLETE:**
```markdown
### Phase 1D: Business Performance Management ✅ COMPLETE
**Status:** Backend 100%, Frontend 60%

**UI Implementation Checklist:**
- [ ] Pipeline Kanban board component
- [ ] Deal insights panel
- [ ] Analytics panel
- [ ] ROI panel
```
*Problem: Marked COMPLETE but has 4 unchecked [ ] items*

**✅ CORRECT - Keeping incomplete phase as IN PROGRESS:**
```markdown
### Phase 1D: Business Performance Management ⚠️ 80% COMPLETE
**Status:** Backend 100%, Frontend 60% (4 UI components remaining)

**Completed:**
- ✅ Deal pipeline backend API
- ✅ Commission ledger backend
- ✅ Business Performance page scaffold

**In Progress (see BACKLOG.md):**
- 🔄 Pipeline Kanban board component (1-2 days)
- 🔄 Deal insights panel (1-2 days)
- 🔄 Analytics panel (1-2 days)
- 🔄 ROI panel (1-2 days)

**UI Implementation Checklist:**
- [ ] Pipeline Kanban board component
- [ ] Deal insights panel
- [ ] Analytics panel
- [ ] ROI panel

**Next Steps:** User to decide whether to complete Phase 1D UI or defer to backlog
```

**Enforcement (Automated):**

`scripts/check_coding_rules.py` Rule 12 verifies:

1. **Checklist items:** No unchecked `[ ]` items remain
2. **Progress markers:** No `🔄` or `❌` markers remain
3. **Files exist:** All files listed in "Files Delivered:" section actually exist on disk
4. **Tests pass:** "Test Status:" section shows ✅ passing tests (no ❌ or ⚠️ failures)

**Why file verification matters:**
- Solo founders cannot review code quality
- AI agents could check boxes without writing code
- File verification ensures code was actually written
- Test verification ensures code actually works

**Example violations caught:**
```
RULE VIOLATION: Phase 1D marked '✅ COMPLETE' but has:
  -> 4 unchecked [ ] checklist items
  -> 3 files listed in 'Files Delivered' but missing:
     frontend/src/app/pages/business-performance/PipelineKanban.tsx,
     frontend/src/app/pages/business-performance/DealInsights.tsx,
     frontend/src/app/pages/business-performance/Analytics.tsx
  -> Test Status shows ⚠️ warnings (not all tests passing)
```

Blocks commits until violations are fixed.

---

## Questions?

If a rule is unclear or seems wrong for a specific case:
1. Ask in the PR comments
2. Propose a rule change by updating this document in a separate PR
3. Document exceptions inline with `# Exception: <reason>` comments

**Last updated:** 2025-10-27
