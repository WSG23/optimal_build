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

## 8. AI Agent Planning References

**Rule:** Plans, “next steps,” and wrap-up instructions produced by AI agents must cite the canonical testing guides so humans can run the right checks.

**Why:** Phase gates depend on manual walkthroughs and targeted smoke suites. Referencing the official docs keeps every agent in sync with the approved testing scope.

**How to follow:**
- Before proposing work, open:
  - `docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md`
  - Your phase section in `docs/feature_delivery_plan_v2.md`
  - `TESTING_KNOWN_ISSUES.md`, `UI_STATUS.md`, `TESTING_DOCUMENTATION_SUMMARY.md`, and the `README` (`make dev` notes for log monitoring)
- Mirror those references (or the exact commands they prescribe) in your response.
- If expectations change, update the docs first so the automation stays accurate.

**Automatic Enforcement:**
- `scripts/check_coding_rules.py` verifies the guidance docs contain the mandatory references. Do not remove them without adding a replacement rule.
- During reviews, reject any “next steps” that omit the required citations.

---

## Questions?

If a rule is unclear or seems wrong for a specific case:
1. Ask in the PR comments
2. Propose a rule change by updating this document in a separate PR
3. Document exceptions inline with `# Exception: <reason>` comments

**Last updated:** 2025-10-13
