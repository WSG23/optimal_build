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

**❌ WRONG - Causes "type already exists" errors:**
```python
# Migration file - DO NOT DO THIS
from alembic import op
import sqlalchemy as sa

# Defining enum with create_type=False still causes issues!
DEAL_STATUS_ENUM = sa.Enum(
    "open", "closed_won", "closed_lost",
    name="deal_status",
    create_type=False,  # ← This flag doesn't prevent autocreation reliably!
)

def upgrade() -> None:
    # Create ENUM type manually
    op.execute("CREATE TYPE deal_status AS ENUM ('open', 'closed_won', 'closed_lost')")

    # Use the sa.Enum object in table definition
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", DEAL_STATUS_ENUM, nullable=False),  # ← SQLAlchemy tries to create type again!
    )

# What happens: PostgreSQL ERROR: type "deal_status" already exists
# Why: SQLAlchemy's Enum() metaclass ignores create_type=False in some contexts
```

**✅ CORRECT - Use sa.String() for ENUM columns:**
```python
# Migration file - RECOMMENDED PATTERN
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # Step 1: Create PostgreSQL ENUM type (for DB-level validation)
    op.execute("CREATE TYPE deal_status AS ENUM ('open', 'closed_won', 'closed_lost')")

    # Step 2: Create table with String columns
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(), nullable=False),  # ← Use String, NOT sa.Enum()
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Step 3: Convert String column to ENUM type
    op.execute("ALTER TABLE deals ALTER COLUMN status TYPE deal_status USING status::deal_status")


def downgrade() -> None:
    # Reverse: Convert ENUM back to String, then drop table and type
    op.execute("ALTER TABLE deals ALTER COLUMN status TYPE VARCHAR")
    op.drop_table("deals")
    op.execute("DROP TYPE deal_status")
```

**Real-world example from optimal_build:**
```python
# backend/migrations/versions/20251109_000001_add_finance_scenarios.py
"""add finance scenarios table

Revision ID: 20251109_000001
Revises: 20251108_000005
Create Date: 2025-11-09 10:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = "20251109_000001"
down_revision = "20251108_000005"


def upgrade() -> None:
    # Create ENUM types for scenario status
    op.execute("""
        CREATE TYPE scenario_status AS ENUM (
            'draft',
            'active',
            'archived',
            'deleted'
        )
    """)

    # Create table with String columns (will be converted to ENUM)
    op.create_table(
        "finance_scenarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),  # String type
        sa.Column("budget", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_finance_scenarios_project_id",
        "finance_scenarios",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Create indexes (MANDATORY for foreign keys - Rule 9)
    op.create_index("ix_finance_scenarios_project_id", "finance_scenarios", ["project_id"])
    op.create_index("ix_finance_scenarios_status", "finance_scenarios", ["status"])
    op.create_index("ix_finance_scenarios_created_at", "finance_scenarios", ["created_at"])

    # Convert String column to ENUM type
    op.execute("ALTER TABLE finance_scenarios ALTER COLUMN status TYPE scenario_status USING status::scenario_status")


def downgrade() -> None:
    # Convert ENUM back to String before dropping
    op.execute("ALTER TABLE finance_scenarios ALTER COLUMN status TYPE VARCHAR")

    op.drop_index("ix_finance_scenarios_created_at", "finance_scenarios")
    op.drop_index("ix_finance_scenarios_status", "finance_scenarios")
    op.drop_index("ix_finance_scenarios_project_id", "finance_scenarios")
    op.drop_constraint("fk_finance_scenarios_project_id", "finance_scenarios", type_="foreignkey")
    op.drop_table("finance_scenarios")
    op.execute("DROP TYPE scenario_status")
```

**Why this pattern works:**
1. PostgreSQL ENUM type is created separately with raw SQL
2. Table is created with `sa.String()` columns (no type conflicts)
3. After table creation, String columns are converted to ENUM type
4. Downgrade reverses the process: ENUM → String → drop

**Common pitfall - forgetting downgrade conversion:**
```python
# ❌ WRONG downgrade - will fail if column is still ENUM type
def downgrade() -> None:
    op.drop_table("deals")  # ERROR: cannot drop table because type deal_status depends on it
    op.execute("DROP TYPE deal_status")

# ✅ CORRECT downgrade - convert ENUM to String first
def downgrade() -> None:
    op.execute("ALTER TABLE deals ALTER COLUMN status TYPE VARCHAR")  # Convert first
    op.drop_table("deals")  # Now safe to drop
    op.execute("DROP TYPE deal_status")  # Now safe to drop type
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

## 2. SQLAlchemy Enum Serialization (MANDATORY)

**Rule:** All SQLAlchemy enum columns MUST include `values_callable` parameter to serialize enum VALUES instead of NAMES.

**Why:** Without `values_callable`, SQLAlchemy stores enum member NAMES (e.g., `"NEW_DEVELOPMENT"`) instead of VALUES (e.g., the string defined in `ProjectType.NEW_DEVELOPMENT.value`). This causes data corruption when enum values don't match their member names, breaks database constraints, and creates runtime errors.

**How this bug happens:**
```python
# Python enum definition
class ProjectType(str, Enum):
    NEW_DEVELOPMENT = "NEW_DEVELOPMENT"  # VALUE = "NEW_DEVELOPMENT"
    REDEVELOPMENT = "REDEVELOPMENT"

# ❌ WRONG - Missing values_callable
project_type = Column(SQLEnum(ProjectType), nullable=False)

# What gets stored in database:
# - Enum member NAME: "NEW_DEVELOPMENT" (the attribute name)
# - NOT the .value: "NEW_DEVELOPMENT" (which happens to be the same)

# This works by accident if NAME == VALUE, but breaks if they differ:
class ProjectStatus(str, Enum):
    ACTIVE = "active"  # NAME="ACTIVE", VALUE="active"
    PENDING = "pending"

status = Column(SQLEnum(ProjectStatus), nullable=False)
# Database gets "ACTIVE" instead of "active" → constraint violation!
```

**How to follow:**

### Pattern 1: Inline lambda (recommended for new code)
```python
from sqlalchemy import Column, Enum as SQLEnum
from app.models.enums import ProjectType

class Project(Base):
    __tablename__ = "projects"

    # ✅ CORRECT - Inline values_callable
    project_type = Column(
        SQLEnum(ProjectType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
```

### Pattern 2: Reusable helper function (recommended for multiple enums)
```python
from enum import Enum
from sqlalchemy import Enum as SAEnum

def _enum(sa_enum: type[Enum], *, name: str) -> SAEnum:
    """Serialize enums using their .value string representation."""
    return SAEnum(
        sa_enum,
        name=name,
        values_callable=lambda enum_cls: [member.value for member in enum_cls],
    )

class Project(Base):
    __tablename__ = "projects"

    # ✅ CORRECT - Using helper function
    project_type = Column(
        _enum(ProjectType, name="project_type"),
        nullable=False,
    )
```

### Pattern 3: Pre-defined enum constants (recommended for migrations)
```python
from sqlalchemy import Enum

# Define once, reuse across models
PROJECT_TYPE_ENUM = Enum(
    ProjectType,
    name="project_type",
    create_type=False,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

class Project(Base):
    project_type = Column(PROJECT_TYPE_ENUM, nullable=False)

class DevelopmentPipeline(Base):
    project_type = Column(PROJECT_TYPE_ENUM, nullable=False)
```

**Common mistakes:**

```python
# ❌ WRONG - No values_callable
from sqlalchemy import Column, Enum as SQLEnum

project_type = Column(SQLEnum(ProjectType), nullable=False)
# Stores enum NAME instead of VALUE

# ❌ WRONG - Empty values_callable
project_type = Column(
    SQLEnum(ProjectType, values_callable=lambda x: []),
    nullable=False,
)
# Database accepts no values!

# ❌ WRONG - Using str() instead of .value
project_type = Column(
    SQLEnum(ProjectType, values_callable=lambda x: [str(e) for e in x]),
    nullable=False,
)
# str(enum) returns "ProjectType.NEW_DEVELOPMENT", not the value
```

**Verification:**

Run the pre-commit hook to check all model files:
```bash
python3 backend/scripts/check_enum_patterns.py backend/app/models/*.py
```

Or test in Python console:
```python
from app.models.projects import ProjectType

# Check what value is actually stored
print(ProjectType.NEW_DEVELOPMENT.value)  # Should print: "NEW_DEVELOPMENT"
print(ProjectType.NEW_DEVELOPMENT.name)   # Prints member name: "NEW_DEVELOPMENT"

# For lowercase value enums:
from app.models.entitlements import EntApprovalCategory
print(EntApprovalCategory.PLANNING.value)  # Prints: "planning"
print(EntApprovalCategory.PLANNING.name)   # Prints: "PLANNING"
```

**Enforcement:**

This rule is automatically enforced by:
- Pre-commit hook: `check-enum-patterns` (runs on every commit touching model files)
- Script: `backend/scripts/check_enum_patterns.py` (can run manually)

To check manually:
```bash
python3 backend/scripts/check_enum_patterns.py backend/app/models/*.py
```

**Historical context:**

- Nov 9, 2025: Discovered 29 enum columns across 7 model files missing `values_callable`
- Fixed in commits c1fac68 (property.py, entitlements.py) and ce4031b (remaining models)
- Added automated check to prevent regression

---

## 3. Async/Await for Database and API Operations

**Rule:** All database calls, API routes, and I/O operations must use `async`/`await`. No synchronous blocking operations in FastAPI routes or database queries.

**Why:** The FastAPI backend is fully asynchronous. Mixing sync code breaks the async event loop and causes performance issues.

**How to follow:**
- Mark all API route functions with `async def`
- Use `async with session.begin()` for database transactions
- Use `await session.execute()` for queries
- Import from `sqlalchemy.ext.asyncio` not sync `sqlalchemy.orm`

**Examples:**

**❌ WRONG - Sync patterns (will break async event loop):**
```python
# Wrong - Sync database code
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Sync engine - don't use this!
engine = create_engine("postgresql://user:pass@localhost/db")

def get_property(session: Session, property_id: str):  # ❌ Missing async
    """This blocks the entire FastAPI event loop!"""
    return session.query(SingaporeProperty).filter(
        SingaporeProperty.id == property_id
    ).first()  # ❌ Sync query - blocks other requests

@router.get("/properties/{property_id}")  # ❌ Missing async
def fetch_property(property_id: str, session: Session = Depends(get_db)):
    """Sync route handler - kills performance!"""
    return get_property(session, property_id)  # ❌ Can't use await in sync function

# What happens:
# - Request #1 starts, hits database query, BLOCKS
# - Request #2 arrives, WAITS for request #1 to finish
# - Request #3 arrives, WAITS for requests #1 and #2
# - Result: Sequential processing instead of concurrent handling
```

**✅ CORRECT - Async patterns (enables concurrent request handling):**
```python
# Correct - Async database code
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException

# Async engine
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")

router = APIRouter()

async def get_property(session: AsyncSession, property_id: str):
    """Async database function - allows other requests to run while waiting for DB."""
    result = await session.execute(
        select(SingaporeProperty).where(SingaporeProperty.id == property_id)
    )
    return result.scalar_one_or_none()

async def get_properties_by_user(session: AsyncSession, user_id: int):
    """Fetch multiple properties with proper async."""
    result = await session.execute(
        select(SingaporeProperty)
        .where(SingaporeProperty.owner_id == user_id)
        .order_by(SingaporeProperty.created_at.desc())
    )
    return result.scalars().all()

@router.get("/properties/{property_id}")
async def fetch_property(
    property_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Async route handler - properly yields control during I/O."""
    property_obj = await get_property(session, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    return property_obj

@router.get("/users/{user_id}/properties")
async def fetch_user_properties(
    user_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Multiple async operations in sequence."""
    # Each 'await' yields control to other requests
    properties = await get_properties_by_user(session, user_id)

    # Can also do parallel async operations
    import asyncio
    results = await asyncio.gather(
        get_property_count(session, user_id),
        get_average_property_value(session, user_id),
    )
    count, avg_value = results

    return {
        "properties": properties,
        "total_count": count,
        "average_value": avg_value,
    }
```

**Async transaction handling:**
```python
# ✅ CORRECT - Async transaction with error handling
async def create_property_with_audit(
    session: AsyncSession,
    property_data: PropertyCreate,
    user_id: int
):
    """Create property and audit log in a transaction."""
    async with session.begin():  # ✅ Async transaction context
        # Create property
        property_obj = SingaporeProperty(**property_data.model_dump())
        session.add(property_obj)
        await session.flush()  # ✅ Get ID without committing

        # Create audit log
        audit_log = AuditLog(
            user_id=user_id,
            action="create_property",
            resource_id=property_obj.id,
        )
        session.add(audit_log)

        # Transaction commits automatically if no exception
        # Rolls back automatically if exception occurs

    await session.refresh(property_obj)  # ✅ Refresh after commit
    return property_obj

# ❌ WRONG - Sync transaction in async code
async def create_property_wrong(session: AsyncSession, property_data: PropertyCreate):
    with session.begin():  # ❌ Sync context manager in async function!
        property_obj = SingaporeProperty(**property_data.model_dump())
        session.add(property_obj)
        session.flush()  # ❌ Sync flush - blocks event loop
```

**Common async patterns:**
```python
# Pattern 1: Single database query
async def get_by_id(session: AsyncSession, model_class, id: int):
    """Generic get by ID."""
    result = await session.execute(
        select(model_class).where(model_class.id == id)
    )
    return result.scalar_one_or_none()

# Pattern 2: Query with relationships (avoid N+1)
from sqlalchemy.orm import selectinload

async def get_property_with_deals(session: AsyncSession, property_id: str):
    """Eager load relationships to avoid N+1 queries."""
    result = await session.execute(
        select(SingaporeProperty)
        .where(SingaporeProperty.id == property_id)
        .options(selectinload(SingaporeProperty.deals))  # ✅ Eager load
    )
    return result.scalar_one_or_none()

# Pattern 3: Create with relationships
async def create_deal_with_commission(
    session: AsyncSession,
    deal_data: DealCreate,
    commission_rate: float
):
    """Create parent and child records together."""
    async with session.begin():
        # Create parent
        deal = Deal(**deal_data.model_dump())
        session.add(deal)
        await session.flush()  # Get deal.id

        # Create child
        commission = Commission(
            deal_id=deal.id,
            rate=commission_rate,
            amount=deal.value * commission_rate,
        )
        session.add(commission)

    return deal

# Pattern 4: Batch operations
async def update_property_statuses(
    session: AsyncSession,
    property_ids: list[str],
    new_status: str
):
    """Update multiple records efficiently."""
    async with session.begin():
        await session.execute(
            update(SingaporeProperty)
            .where(SingaporeProperty.id.in_(property_ids))
            .values(status=new_status, updated_at=sa.func.now())
        )
```

**Why async matters:**
```python
# Comparison of concurrent request handling

# ❌ Sync code - Sequential processing
# Request 1: 0-200ms (database query takes 200ms)
# Request 2: 200-400ms (waits for request 1, then takes 200ms)
# Request 3: 400-600ms (waits for requests 1 and 2, then takes 200ms)
# Total time: 600ms for 3 requests

# ✅ Async code - Concurrent processing
# Request 1: 0-200ms (starts, yields during DB query)
# Request 2: 0-200ms (starts while request 1 is waiting, yields during DB query)
# Request 3: 0-200ms (starts while requests 1 and 2 are waiting, yields during DB query)
# Total time: ~200ms for 3 requests (all run concurrently)

# Result: 3x throughput with async!
```

---

## 4. Testing Before Commits

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

## 5. Dependency Management

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

## 6. Singapore Property Compliance Validation

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

## 7. Python Import Ordering and Formatting

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

## 8. Code Quality Standards

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

### 8.1 No Unused Variables (Ruff F841)

**❌ WRONG - Unused variable assigned:**
```python
# Bad - variable assigned but never used
async def create_property(session: AsyncSession, property_data: PropertyCreate):
    property_obj = SingaporeProperty(**property_data.model_dump())
    session.add(property_obj)
    await session.commit()

    # ❌ F841: Variable 'result' is assigned but never used
    result = await session.execute(select(SingaporeProperty).where(SingaporeProperty.id == property_obj.id))

    return property_obj  # Should return 'result' or remove the query

# Bad - function returns value but it's not used
async def update_property_status(session: AsyncSession, property_id: str, status: str):
    property_obj = await get_property(session, property_id)

    # ❌ F841: Variable 'updated_at' is assigned but never used
    updated_at = await session.execute(
        update(SingaporeProperty)
        .where(SingaporeProperty.id == property_id)
        .values(status=status, updated_at=sa.func.now())
    )

    await session.commit()
```

**✅ CORRECT - Only assign variables that will be used:**
```python
# Good - variable is used
async def create_property(session: AsyncSession, property_data: PropertyCreate):
    property_obj = SingaporeProperty(**property_data.model_dump())
    session.add(property_obj)
    await session.commit()
    await session.refresh(property_obj)  # Use the object directly
    return property_obj

# Good - don't assign if not using the result
async def update_property_status(session: AsyncSession, property_id: str, status: str):
    await session.execute(  # No assignment - just execute
        update(SingaporeProperty)
        .where(SingaporeProperty.id == property_id)
        .values(status=status, updated_at=sa.func.now())
    )
    await session.commit()

# Good - use underscore for intentionally ignored values
async def create_many(session: AsyncSession, items: list[dict]):
    for item_data in items:
        _ = await create_item(session, item_data)  # ✅ Underscore shows it's intentional
    await session.commit()
```

### 8.2 Proper Exception Chaining (Ruff B904)

**❌ WRONG - Missing exception chain:**
```python
# Bad - exception chain broken, original error lost
async def create_finance_scenario(session: AsyncSession, data: FinanceScenarioCreate):
    try:
        scenario = FinanceScenario(**data.model_dump())
        session.add(scenario)
        await session.commit()
        return scenario
    except ValueError:
        # ❌ B904: Missing 'from err' - original ValueError stack trace is lost!
        raise HTTPException(status_code=422, detail="Invalid scenario data")

# Bad - exception suppressed incorrectly
async def process_property_data(data: dict):
    try:
        property_obj = SingaporeProperty(**data)
        await validate_property(property_obj)
        return property_obj
    except ValidationError:
        # ❌ B904: Should use 'from err' to show validation failure details
        raise HTTPException(status_code=400, detail="Validation failed")
```

**✅ CORRECT - Proper exception chaining:**
```python
# Good - exception chained with 'from e'
async def create_finance_scenario(session: AsyncSession, data: FinanceScenarioCreate):
    try:
        scenario = FinanceScenario(**data.model_dump())
        session.add(scenario)
        await session.commit()
        return scenario
    except ValueError as e:
        # ✅ Original error preserved in stack trace
        raise HTTPException(status_code=422, detail=f"Invalid scenario data: {str(e)}") from e

# Good - explicit suppression with 'from None' when original error not relevant
async def resolve_file_path(file_path: str):
    try:
        path = Path(file_path).resolve(strict=True)
        return path
    except (FileNotFoundError, RuntimeError):
        # ✅ Original error not relevant to user, suppress it
        raise HTTPException(status_code=403, detail="Invalid file path") from None

# Good - re-raise HTTPException directly
async def get_property_or_404(session: AsyncSession, property_id: str):
    try:
        property_obj = await get_property(session, property_id)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        return property_obj
    except HTTPException:
        raise  # ✅ Re-raise HTTPException directly, don't wrap it

# Good - chain custom exceptions
class PropertyValidationError(Exception):
    pass

async def validate_property(property_obj: SingaporeProperty):
    try:
        if property_obj.gross_floor_area <= 0:
            raise ValueError("GFA must be positive")
        if not property_obj.address:
            raise ValueError("Address is required")
    except ValueError as e:
        # ✅ Chain custom exception from original
        raise PropertyValidationError(f"Property validation failed: {e}") from e
```

### 8.3 No Mutable Default Arguments (Ruff B006)

**❌ WRONG - Mutable default arguments:**
```python
# Bad - list default is shared across all calls!
def process_properties(property_ids: list[str] = []):  # ❌ B006: Dangerous!
    """This function has a bug - the default list is mutable!"""
    property_ids.append("default-property")
    return property_ids

# What happens:
first_call = process_properties()   # Returns: ["default-property"]
second_call = process_properties()  # Returns: ["default-property", "default-property"]  ← BUG!
third_call = process_properties()   # Returns: ["default-property", "default-property", "default-property"]

# Bad - dict default is shared
def create_property_filters(filters: dict = {}):  # ❌ B006: Dangerous!
    filters["status"] = "active"
    return filters

# Bad - set default is shared
def track_seen_ids(ids: set[str] = set()):  # ❌ B006: Dangerous!
    ids.add("new-id")
    return ids
```

**✅ CORRECT - Use None and initialize inside function:**
```python
# Good - None default, initialize inside
def process_properties(property_ids: Optional[list[str]] = None) -> list[str]:
    """Each call gets a fresh list."""
    if property_ids is None:
        property_ids = []
    property_ids.append("default-property")
    return property_ids

# What happens (correct behavior):
first_call = process_properties()   # Returns: ["default-property"]
second_call = process_properties()  # Returns: ["default-property"]  ✅ Correct!
third_call = process_properties()   # Returns: ["default-property"]  ✅ Correct!

# Good - dict initialized inside
def create_property_filters(filters: Optional[dict] = None) -> dict:
    if filters is None:
        filters = {}
    filters["status"] = "active"
    return filters

# Good - set initialized inside
def track_seen_ids(ids: Optional[set[str]] = None) -> set[str]:
    if ids is None:
        ids = set()
    ids.add("new-id")
    return ids

# Good - use dataclass with field(default_factory=...)
from dataclasses import dataclass, field

@dataclass
class PropertyFilter:
    statuses: list[str] = field(default_factory=list)  # ✅ Each instance gets fresh list
    tags: dict[str, str] = field(default_factory=dict)  # ✅ Each instance gets fresh dict
```

### 8.4 Type Hints on Public APIs

**❌ WRONG - Missing type hints:**
```python
# Bad - no type hints, IDE can't help
def calculate_roi(property_obj, holding_period):  # ❌ What types?
    total_cost = property_obj.purchase_price + property_obj.renovation_cost
    total_income = property_obj.rental_income * holding_period
    return (total_income - total_cost) / total_cost

# Bad - partial type hints
def create_scenario(data: dict, user):  # ❌ 'user' type unknown
    scenario = FinanceScenario(**data)
    scenario.created_by = user.id  # Could fail if 'user' doesn't have 'id'
    return scenario
```

**✅ CORRECT - Complete type hints:**
```python
# Good - complete type hints
from typing import Optional

def calculate_roi(
    property_obj: SingaporeProperty,
    holding_period: int,
) -> float:
    """Calculate ROI for a property over holding period."""
    total_cost = property_obj.purchase_price + property_obj.renovation_cost
    total_income = property_obj.rental_income * holding_period
    return (total_income - total_cost) / total_cost

# Good - Optional for nullable parameters
async def create_scenario(
    data: dict[str, Any],
    user: User,
    parent_scenario: Optional[FinanceScenario] = None,
) -> FinanceScenario:
    """Create a finance scenario."""
    scenario = FinanceScenario(**data)
    scenario.created_by = user.id

    if parent_scenario:
        scenario.parent_id = parent_scenario.id

    return scenario

# Good - Union types for multiple allowed types
from typing import Union

async def get_property(
    session: AsyncSession,
    property_id: Union[str, int],  # Can accept string UUID or integer ID
) -> Optional[SingaporeProperty]:
    """Get property by ID (string UUID or integer)."""
    result = await session.execute(
        select(SingaporeProperty).where(SingaporeProperty.id == str(property_id))
    )
    return result.scalar_one_or_none()
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

## 9. AI Agent Testing Instructions (MANDATORY)

**Rule:** When AI agents complete ANY feature, they MUST provide test instructions to the user. This includes backend tests, frontend tests, and UI manual test steps.

**Why:** Phase gates depend on manual walkthroughs and targeted smoke suites. Referencing the official docs keeps every agent in sync with the approved testing scope. Without explicit test instructions, features go untested and regressions accumulate.

**How to follow:**

### 9.1 MANDATORY Testing Checklist After Feature Completion

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

### 9.2 Required Documentation References

Before proposing work, AI agents must read:
- [`docs/ai-agents/next_steps.md`](docs/ai-agents/next_steps.md) (MANDATORY TESTING CHECKLIST section)
- Review the phase summary in [`docs/all_steps_to_product_completion.md`](docs/all_steps_to_product_completion.md) and the corresponding item in the [📌 Unified Execution Backlog](docs/all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work)
- [`docs/all_steps_to_product_completion.md#-known-testing-issues`](docs/all_steps_to_product_completion.md#-known-testing-issues) (check for known test failures before reporting)
- [`docs/planning/ui-status.md`](docs/planning/ui-status.md) (understand UI implementation status)
- [`docs/development/testing/summary.md`](docs/development/testing/summary.md) (find smoke/regression suites)
- [`README.md`](README.md) (`make dev` notes for log monitoring)

Mirror those references (or the exact commands they prescribe) in your response.

If expectations change, update the docs first so the automation stays accurate.

### 9.3 Examples

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

### 9.4 Automatic Enforcement

- `scripts/check_coding_rules.py` verifies the guidance docs contain the mandatory references. Do not remove them without adding a replacement rule.
- During reviews, reject any "next steps" that omit the required test instructions.
- **FUTURE:** Commit message hook will enforce that feature commits include test commands in the message body.

### 9.5 Compliance Check

When completing a feature, ask yourself:
- [ ] Did I provide backend pytest commands?
- [ ] Did I provide frontend test commands (if applicable)?
- [ ] Did I provide specific UI manual test steps?
- [ ] Did I reference `docs/all_steps_to_product_completion.md#-known-testing-issues` to avoid duplicate reports?
- [ ] Did I check `docs/planning/ui-status.md` to understand current implementation state?

**If you answered NO to any of these, your work is incomplete.**

---

## 10. Database Performance & Indexing

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

## 11. Testing Requirements

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
- Frontend overall: Best effort (JSDOM timing issues documented in `docs/all_steps_to_product_completion.md#-known-testing-issues`)

### 11.1 Backend feature completion checklist (MANDATORY)

Every backend feature, bug fix, or infrastructure change **must** close with
tests and a fresh coverage datapoint. Skipping this step is the number-one way
our coverage target drifts.

1. **Add or update automated tests** in the same pull request. Unit tests for
   new business logic, integration tests for new APIs, and regression tests for
   bug fixes.
2. **Run the coverage suite locally** before marking the task complete:
   ```bash
   SECRET_KEY=test-secret JOB_QUEUE_BACKEND=inline \
     .venv/bin/python -m pytest backend/tests \
       --cov=backend/app --cov-report=term-missing
   ```
3. **Record the result** (percentage, date, command) in
   `PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.MD` under “Baseline/Session Log”. If the
   run changes the coverage trend materially, summarise the affected modules.
4. If coverage decreases, explain why in the PR description and flag a follow-up
   task to close the gap.

Feature leads should not move a work item to “Done” until all four boxes are
ticked.

**Enforcement:**
- CI blocks merges without passing tests
- Pre-commit hooks run tests automatically
- Phase gate checks verify test coverage before phase completion

**Exceptions:**
- Frontend tests have known JSDOM timing issues (see `docs/all_steps_to_product_completion.md#-known-testing-issues`)
- Test harness UI (non-production) may have lower coverage
- Document test gaps in commit messages if test is deferred

---

## 12. Security Practices

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

## 13. Phase Completion Gates (MANDATORY)

**Rule:** AI agents MUST NOT mark a phase as "✅ COMPLETE" in [all_steps_to_product_completion.md](docs/all_steps_to_product_completion.md) while related tasks remain in the [📌 Unified Execution Backlog](docs/all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) or the Phase 2D gate checklist has unchecked items.

**Why:** Phase 1D and Phase 2B were left 60% and 85% incomplete because AI agents marked backend work as "done" and moved to Phase 2C without completing frontend UI components. This creates abandoned features and technical debt.

**How to follow:**

### Before marking ANY phase "✅ COMPLETE":

1. **Confirm the Unified Execution Backlog has no open work for the phase:**
   - Search Active/Ready sections for the phase label → Must be absent
   - Ensure deferred work is logged under "Ready" or "Blocked" with next steps (not left implicit)

2. **Review the Phase 2D gate checklist in [all_steps_to_product_completion.md](docs/all_steps_to_product_completion.md):**
   - All relevant checkboxes must be `[x]`
   - If the phase is a prerequisite for the gate, confirm the checkbox is updated concurrently

3. **Verify UI manual testing complete:**
   - User must have run all UI manual test steps (see Rule 8)
   - User must have confirmed: "✅ All manual tests passing"

4. **Ask user for explicit approval:**
   ```markdown
   Phase X checklist is complete:
   - ✅ No open tasks for this phase in the Unified Execution Backlog
   - ✅ Relevant Phase 2D gate checkbox updated
   - ✅ UI manual testing passed

   May I mark Phase X as "✅ COMPLETE" in all_steps_to_product_completion.md?
   ```

5. **Only after user approval:**
   - Change phase header from "⚠️ IN PROGRESS" → "✅ COMPLETE"
   - Update status percentage to 100%

### If phase has ANY incomplete work:

1. **Keep status as "⚠️ IN PROGRESS"**
2. **Document incomplete items clearly:**
   - Use `🔄` for work in progress
   - Use `❌` for blocked or deferred work
   - Add unchecked `- [ ]` items to checklist

3. **Add incomplete work to the [Unified Execution Backlog](docs/all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work):**
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

**In Progress (see Unified Execution Backlog):**
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
5. **Manual QA executed (Rule 12.1):** UI phases require manual QA checklist with execution results

**Rule 13.1: Manual QA Requirement for UI Phases**

All phases with UI components (1A, 1B, 1C, 1D, 2B, 2C) MUST have:
- Manual QA checklist file in `docs/development/testing/phase-{XY}-manual-qa-checklist.md`
- Execution summary filled out with:
  - **Tester:** (actual name, not blank)
  - **Date:** (actual date, not blank)
  - **Overall Result:** PASS, FAIL, or PARTIAL

**Why this matters:**
- Backend tests don't verify UI interactions (drag-and-drop, button clicks, responsive design)
- Users experience the UI, not the API
- Phase 1D was marked COMPLETE on Nov 1, 2025 without manual UI testing
- This caused the enforcement gap that let incomplete work ship

**Enforcement blocks commits if:**
- Phase marked `✅ COMPLETE` in all_steps_to_product_completion.md
- But manual QA checklist missing or not executed (template blanks still present)

**Why file verification matters:**
- Solo founders cannot review code quality
- AI agents could check boxes without writing code
- File verification ensures code was actually written
- Test verification ensures code actually works
- **Manual QA verification ensures UI was actually tested by a human**

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

**Rule 13.2: Production UI Quality Standards**

**All frontend UI in Phase 1 and Phase 2 is production-quality B2B software.**

Context:
- This is a B2B platform for commercial real estate professionals
- Users: Agents, Developers, Architects, Engineers
- UI must be professional, polished, and user-friendly
- The "test harness" concept was dropped in October 2025

**Requirements for all frontend work:**
- ✅ Professional error handling and loading states
- ✅ User-friendly UX with clear feedback
- ✅ Responsive design (desktop focus)
- ✅ Material-UI consistency across components
- ✅ Form validation and input sanitization
- ✅ Manual QA testing before marking complete (Rule 12.1)

**Why this matters:**
- Oct 11, 2025: An AI agent misinterpreted "test harness" (testing framework issues)
  as meaning frontend UI was temporary throwaway code
- Created docs/planning/ui-status.md stating "ALL files in frontend/ are TEMPORARY"
- This incorrect framing persisted until Nov 2, 2025
- Led to confusion about UI quality expectations

**What "test harness" actually means:**
- Testing framework limitations (JSDOM timing, React Testing Library quirks)
- NOT the production UI itself

**Reference:** See frontend/README_AI_AGENTS.md for detailed frontend guidelines.

### 13.3 Manual UI QA for every frontend delivery (MANDATORY)

All frontend feature/sub-phase work must finish with a human UI sweep. This is
the enforcement counterpart to Rule 12.1/12.2.

1. Build/run the relevant frontend surface (normally `npm run dev`).
2. Execute the manual QA script for that feature (e.g. the Phase 1D checklist).
3. Capture evidence (screenshots or video) and log outcomes in the appropriate
   checklist file under `docs/development/testing/`.
4. Only mark the feature complete once the checklist row is filled in and any
   regressions have owners.

CI cannot replace this. Manual UI QA is required because the product is a
production B2B app, and our end users expect polished, professional workflows.

### 13.4 QA Checklist Completion Workflow (MANDATORY - AI AGENTS READ THIS)

**Problem this solves:** Phase 1D was marked COMPLETE on Nov 1, 2025, but the
manual QA checklist status was never updated from "READY FOR QA" to "COMPLETED".
This violated the completion workflow and left documentation inconsistent.

**For Solo Founders with AI Agents:** You cannot remember every step. This rule
automates enforcement so AI agents MUST complete the full workflow.

**MANDATORY workflow when executing manual QA:**

1. **Before starting QA:** Checklist status should be `✅ READY FOR QA`
2. **During QA:** Update test results in checklist (mark tests as Pass/Fail)
3. **After QA execution:** AI agents MUST complete these steps IN ORDER:

   a. **Update checklist status header** (line ~5 in checklist file):
      - Change from: `**Status:** ✅ READY FOR QA`
      - Change to: `**Status:** ✅ QA COMPLETE (YYYY-MM-DD)` or `**Status:** ✅ ARCHIVED (YYYY-MM-DD)`

   b. **Complete "Next Steps" section** at end of checklist:
      - If PASS: Check the boxes for updating the backlog + roadmap in all_steps_to_product_completion.md
      - If FAIL: Document issues and create fix tasks
      - If PARTIAL: Document decision with product owner notes

   c. **Update the Unified Execution Backlog** (if not already done):
      - Move phase item from "Ready" to "Completed" section
      - Add completion date and QA status

   d. **Update [all_steps_to_product_completion.md](docs/all_steps_to_product_completion.md)** (if not already done):
      - Ensure phase is marked `✅ COMPLETE` in Phase Overview table
      - Ensure gate checkbox is checked `[x]` in Phase Gate Checklist

   e. **Git commit** with message referencing QA completion:
      - Example: `docs: complete Phase 1D manual QA checklist and archive`

**What gets enforced:**
- Pre-commit hook verifies checklist status is not `READY FOR QA` when phase is COMPLETE
- Pre-commit hook verifies "Next Steps" section has at least one checkbox checked
- Pre-commit hook verifies the unified backlog + phase summaries in all_steps_to_product_completion.md

**Example violation caught:**
```
RULE VIOLATION: Phase 1D marked '✅ COMPLETE' in all_steps_to_product_completion.md
  -> But manual QA checklist status still says: '✅ READY FOR QA'
  -> Checklist must be updated to: '✅ QA COMPLETE (2025-11-02)' or '✅ ARCHIVED (2025-11-02)'
  -> Rule 12.4: Complete the QA checklist workflow
  -> Update docs/development/testing/phase-1d-manual-qa-checklist.md line 5
```

**Why this matters for solo founders:**
- AI agents work autonomously and may skip cleanup steps
- You cannot manually track every documentation update
- Automated enforcement ensures consistency without human oversight
- Prevents "partial completion" where work is done but not documented properly

---

## 14. Python Import Safety (CRITICAL)

### 14.1 NEVER Create Shadow Directories

**Rule:** NEVER create directories in your project that match the names of installed Python packages.

**Why:** These "shadow directories" hijack Python's import system, causing all imports to load broken stub code instead of the real package. This breaks the entire application.

**Critical Safety Issue for Non-Technical Founders:**
- Shadow directories have caused multiple production-breaking incidents (Oct 30, Nov 2 2025)
- Codex Cloud has repeatedly created these when encountering import errors
- The damage is invisible until you try to run the app - then EVERYTHING breaks
- Non-coders cannot easily diagnose or fix this without AI help

**FORBIDDEN directory names:**
```
fastapi/
starlette/
pydantic/
sqlalchemy/
pytest/
pytest_cov/
celery/
redis/
alembic/
... or ANY other package name from requirements.txt
```

**Whitelisted vendor shims (intentional):**

The following directories were created during the September 2025 bootstrap to
allow offline testing environments to masquerade as the real dependency. They
live in the repo on purpose—do **not** delete them and do **not** treat them as
shadow bugs.

```
prefect/
httpx/
structlog/
pydantic/
backend/sqlalchemy/
backend/prefect/
```

If a directory is not in this whitelist, assume it is unsafe and remove it.
When in doubt, run `python scripts/check_shadow_directories.py` and follow the
error message.

**How Python imports work:**
1. Python searches current directory FIRST
2. Then searches PYTHONPATH
3. Then searches site-packages (where pip installs packages)

**If you create `fastapi/` in your project:**
- `from fastapi import FastAPI` loads YOUR empty directory
- NOT the real FastAPI from site-packages
- Result: `ImportError: cannot import name 'FastAPI'`

**If you encounter import errors, the CORRECT fixes are:**

```bash
# ✅ CORRECT Option 1: Fix PYTHONPATH
export PYTHONPATH=/path/to/project:$PYTHONPATH

# ✅ CORRECT Option 2: Use absolute imports in code
from app.models import User  # Good
from models import User      # Bad (ambiguous)

# ✅ CORRECT Option 3: Fix sys.path in conftest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**❌ NEVER do this:**
```python
# FORBIDDEN - creating shadow directory
mkdir backend/fastapi
echo "# Stub" > backend/fastapi/__init__.py

# FORBIDDEN - creating "bridge" modules
# These try to re-export the real package but always fail
```

**Exceptions (Legitimate Vendor Shims):**

The following directories are **LEGITIMATE vendor shims** created Sep 21-23, 2025 during project bootstrap:

- `prefect/` - Prefect flow compatibility layer for offline environments
- `httpx/` - HTTP client compatibility layer for test environments
- `structlog/` - Logging compatibility layer
- `pydantic/` - Pydantic model compatibility layer
- `backend/sqlalchemy/` - SQLAlchemy compatibility layer
- `backend/prefect/` - Backend Prefect compatibility layer

**These vendor shims:**
1. Were intentionally created as architectural decisions
2. Serve legitimate purposes for offline/test environments
3. Have sophisticated import loaders that try real packages first
4. Are whitelisted in `scripts/check_shadow_directories.py`

**DO NOT delete these directories.**
**DO NOT create new ones without explicit approval.**

If you encounter import errors with these vendor shims, the problem is NOT the vendor shim itself - it's likely PYTHONPATH or a missing dependency.

**Enforcement:**

AI agents encountering import errors MUST:
1. ❌ NOT create shadow directories
2. ✅ Check if PYTHONPATH is set correctly
3. ✅ Verify imports use absolute paths
4. ✅ Ask user for guidance if unclear

**Detection:**

Run this to check for shadow directories:
```bash
# Check for common shadows
ls -d backend/{fastapi,starlette,pydantic,sqlalchemy,pytest,celery} 2>/dev/null

# If any exist, DELETE IMMEDIATELY:
rm -rf backend/fastapi backend/starlette backend/pydantic
```

**Historical Context:**
- Oct 30, 2025: Codex Cloud created `pydantic/` shadows (commit 165d5f5)
- Nov 2, 2025 (PR #276): Codex Cloud added `sqlalchemy/`, `pytest_cov/`, `fastapi/` (commit aa0bfde)
- Nov 2, 2025: Codex Cloud attempted to add MORE shadows in subsequent branch
- All were caught and removed, but the pattern shows systemic risk

**For Solo Founders:**

If you're not a coder and AI agents create shadow directories:
1. Your app will suddenly stop working with confusing errors
2. The error messages will point to YOUR code, not the root cause
3. You may not recognize the problem without AI help
4. **Prevention is critical** - hence this rule

**Automated Check:**

The pre-commit hook checks for shadow directories and blocks commits that create them.

---

### 14.2 Documentation Sprawl Prevention (MANDATORY)

**Rule:** After the 2025-11-12 documentation consolidation, AI agents MUST NOT create new .md files in `docs/` without explicit user approval. All new documentation must be added to existing files or explicitly whitelisted.

**Why:**
- Documentation sprawl was a major problem before consolidation
- Multiple overlapping/contradictory documents created confusion
- Feature Delivery Plan v2 (now “All Steps to Product Completion”) is the single source of truth
- Creating new docs fragments the knowledge base

**How to follow:**

**For AI agents:**
1. **Default behavior:** Add new documentation to existing files:
   - Strategic content → `docs/all_steps_to_product_completion.md`
   - Task tracking → `docs/all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work`
   - Known issues → `docs/all_steps_to_product_completion.md#-known-testing-issues`
   - Phase details → Update relevant section in existing docs

2. **If new file is truly necessary:**
   - Get explicit user approval FIRST
   - Add file path to `.documentation-whitelist.yaml`
   - Document WHY it can't fit in existing docs
   - Commit whitelist update WITH the new file in same commit

**Whitelisted files:**

See `.documentation-whitelist.yaml` for the complete list. Current core docs:
- `docs/all_steps_to_product_completion.md` - Strategic delivery plan (single source of truth)
- `docs/all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work` - Daily task tracking
- `docs/ai-agents/next_steps.md` - AI agent decision guide
- `docs/planning/features.md` - Product requirements
- Plus testing guides, audits, and archived historical docs

**Examples:**

```bash
# ✅ CORRECT - Add to existing file
# User: "Document the new Phase 2D feature"
# AI: Updates docs/all_steps_to_product_completion.md section for Phase 2D

# ❌ WRONG - Create new file without approval
# AI: Creates docs/phase2d_implementation_plan.md
# Pre-commit hook: BLOCKED - file not whitelisted

# ✅ CORRECT - Get approval first
# AI: "This Phase 2D spec is 500+ lines. May I create docs/phase2d_detailed_spec.md?"
# User: "Yes, approved"
# AI: Adds to .documentation-whitelist.yaml, creates file, commits both together
```

**Automated Check:**

The pre-commit hook `check-documentation-whitelist` enforces this rule:
- Detects new .md files in `docs/` directory
- Checks against `.documentation-whitelist.yaml`
- Blocks commit if file is not whitelisted
- Provides clear error message with instructions

**Automatic allowances:**
- `**/README.md` - Directory navigation files always allowed
- `docs/generated/**/*.md` - Auto-generated docs always allowed
- `docs/archive/**/*.md` - Historical archive additions allowed (with user approval)

---

## Questions?

If a rule is unclear or seems wrong for a specific case:
1. Ask in the PR comments
2. Propose a rule change by updating this document in a separate PR
3. Document exceptions inline with `# Exception: <reason>` comments

**Last updated:** 2025-10-27
