# Coding Rules for optimal_build

Mandatory coding standards. Pre-commit hooks enforce most rules automatically.

> **Quick Start:** Critical rules are in `.cursorrules` (auto-loaded by AI tools).
> This file is the detailed reference.

**For detailed examples:** See [docs/archive/CODING_RULES_detailed_archived_2025-12-30.md](docs/archive/CODING_RULES_detailed_archived_2025-12-30.md)

---

## 1. Database Migrations

### 1.1 Never Edit Existing Migrations

**Rule:** Never edit existing Alembic migration files. Always create new migrations.

```bash
# CORRECT
cd backend && alembic revision -m "add compliance_score column"

# WRONG - editing existing migration
# Don't modify backend/migrations/versions/20240919_*.py
```

### 1.2 ENUM Types in Migrations

**Rule:** Use `sa.String()` for ENUM columns, NOT `sa.Enum()`.

```python
# CORRECT
def upgrade() -> None:
    op.execute("CREATE TYPE deal_status AS ENUM ('open', 'closed')")
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(), nullable=False),  # String, not Enum
    )
    op.execute("ALTER TABLE deals ALTER COLUMN status TYPE deal_status USING status::deal_status")

def downgrade() -> None:
    op.execute("ALTER TABLE deals ALTER COLUMN status TYPE VARCHAR")
    op.drop_table("deals")
    op.execute("DROP TYPE deal_status")
```

**Why:** `sa.Enum()` causes "type already exists" errors even with `create_type=False`.

### 1.3 ENUM Value Naming

**Rule:** PostgreSQL ENUM values must EXACTLY match Python enum string values.

```python
# Python
class ProjectType(str, Enum):
    NEW_DEVELOPMENT = "NEW_DEVELOPMENT"  # VALUE is uppercase

# SQL - must match Python VALUE
op.execute("CREATE TYPE projecttype AS ENUM ('NEW_DEVELOPMENT', 'REDEVELOPMENT')")
```

---

## 2. SQLAlchemy Enum Serialization

**Rule:** All SQLAlchemy enum columns MUST include `values_callable`.

```python
# CORRECT
project_type = Column(
    SQLEnum(ProjectType, values_callable=lambda x: [e.value for e in x]),
    nullable=False,
)

# WRONG - stores enum NAME instead of VALUE
project_type = Column(SQLEnum(ProjectType), nullable=False)
```

---

## 3. Async/Await (CRITICAL)

**Rule:** ALL database calls and API routes must use `async`/`await`.

```python
# CORRECT
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_property(session: AsyncSession, property_id: str):
    result = await session.execute(
        select(Property).where(Property.id == property_id)
    )
    return result.scalar_one_or_none()

@router.get("/properties/{property_id}")
async def fetch_property(property_id: str, session: AsyncSession = Depends(get_db)):
    return await get_property(session, property_id)

# WRONG - sync code blocks event loop
from sqlalchemy.orm import Session

def get_property(session: Session, property_id: str):  # Missing async
    return session.query(Property).filter(...).first()  # Sync query
```

---

## 4. Testing Before Commits

**Rule:** Run `make verify` before committing.

```bash
make verify    # Must pass before commit
git commit -m "your message"  # Pre-commit hooks auto-format
```

---

## 5. Dependency Management

**Rule:** Pin exact versions. Sync formatter versions across all config files.

```bash
# Backend
echo "pydantic==2.4.2" >> backend/requirements.txt

# CRITICAL: Black version must match in requirements.txt AND .pre-commit-config.yaml
```

---

## 6. Singapore Property Compliance

**Rule:** Run compliance tests when modifying Singapore property models.

```bash
pytest backend/tests/test_api/test_feasibility.py -v
```

---

## 7. Python Import Ordering

**Rule:** Follow PEP 8 import order (standard library → third-party → local).

```python
# CORRECT
import os
import sys

from sqlalchemy import select
from fastapi import APIRouter

from app.models import User
```

Pre-commit hooks auto-fix import ordering.

---

## 8. Code Quality Standards

### 8.1 No Unused Variables (Ruff F841)

```python
# CORRECT - use underscore for intentionally ignored
_ = await create_item(session, item_data)

# WRONG
result = await create_item(session, item_data)  # Never used
```

### 8.2 Exception Chaining (Ruff B904)

```python
# CORRECT
except ValueError as e:
    raise HTTPException(status_code=422, detail=str(e)) from e

# Suppress original when not relevant
except FileNotFoundError:
    raise HTTPException(status_code=403, detail="Invalid path") from None

# WRONG - loses stack trace
except ValueError:
    raise HTTPException(status_code=422, detail="Error")
```

### 8.3 No Mutable Default Arguments (Ruff B006)

```python
# CORRECT
def process(items: Optional[list] = None):
    if items is None:
        items = []

# WRONG - shared across calls
def process(items: list = []):  # Dangerous!
```

### 8.4 Type Hints on Public APIs

```python
# CORRECT
async def create_scenario(data: dict[str, Any], user: User) -> FinanceScenario:
    ...
```

---

## 9. AI Agent Testing Instructions

**Rule:** After completing ANY feature, provide test commands:

```markdown
Backend tests:
pytest backend/tests/test_api/test_[feature].py -v

UI Manual Testing:
1. Navigate to [URL]
2. Click [button]
3. Verify [expected outcome]
```

---

## 10. Database Indexing

**Rule:** ALL foreign keys MUST have indexes.

```python
# CORRECT
op.create_table("scenarios", ...)
op.create_index("ix_scenarios_project_id", "scenarios", ["project_id"])

# WRONG - no index on foreign key
op.create_table("scenarios", sa.Column("project_id", sa.Integer()))  # No index!
```

---

## 11. Testing Requirements

**Rule:** All new features need automated tests. Backend critical paths >80% coverage.

```bash
# Run with coverage
pytest backend/tests/ --cov=app --cov-report=term-missing
```

---

## 12. Security Practices

### Authentication Required

```python
# CORRECT
@router.post("/finance/scenarios")
async def create(data: Data, current_user: User = Depends(get_current_user)):
    if not await user_owns_project(db, current_user.id, data.project_id):
        raise HTTPException(status_code=403, detail="Not authorized")
```

### Input Validation with Pydantic

```python
class ScenarioCreate(BaseModel):
    project_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=200)
    budget: float = Field(..., gt=0, le=1e9)
```

### SQL Injection Prevention

```python
# CORRECT - use ORM
stmt = select(Scenario).where(Scenario.project_id == project_id)

# WRONG - f-strings enable injection
query = f"SELECT * FROM scenarios WHERE project_id = {project_id}"
```

### Secrets Management

```python
# CORRECT - environment variables
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    class Config:
        env_file = ".env"  # Never commit .env!

# WRONG - hardcoded
DATABASE_URL = "postgresql://user:password@localhost/db"
```

---

## 13. Phase Completion Gates

**Rule:** Never mark phase "✅ COMPLETE" while tasks remain incomplete.

Before marking complete:
- [ ] No open tasks in Unified Execution Backlog for this phase
- [ ] All checklist items checked `[x]`
- [ ] UI manual testing passed
- [ ] User approval obtained

---

## 14. Python Import Safety

### 14.1 NEVER Create Shadow Directories

**Rule:** NEVER create directories matching Python package names.

**FORBIDDEN:** `fastapi/`, `sqlalchemy/`, `pydantic/`, `pytest/`, etc.

**Why:** Python imports local directory FIRST, breaking all imports.

**Whitelisted vendor shims (intentional):** `prefect/`, `httpx/`, `structlog/`, `backend/sqlalchemy/`, `backend/prefect/`

### 14.2 Documentation Sprawl Prevention

**Rule:** Don't create new .md files in `docs/` without user approval. Add to existing docs instead.

---

## Quick Reference

| Rule | Enforcement |
|------|-------------|
| 1. No editing migrations | Pre-commit hook |
| 2. sa.String() for ENUMs | Pre-commit hook |
| 3. Async/await required | Manual review |
| 4. make verify before commit | Pre-commit hook |
| 5. Pin dependencies | Manual review |
| 6. Compliance tests | Scripts |
| 7. Import ordering | Auto-fixed by ruff |
| 8. Code quality | Ruff auto-checks |
| 9. Test instructions | Manual review |
| 10. Index foreign keys | Manual review |
| 11. Test coverage >80% | CI check |
| 12. Security practices | Manual review |
| 13. Phase gates | Pre-commit hook |
| 14. No shadow directories | Pre-commit hook |

---

**For detailed examples and edge cases:** See [docs/archive/CODING_RULES_detailed_archived_2025-12-30.md](docs/archive/CODING_RULES_detailed_archived_2025-12-30.md)

**Last updated:** 2025-12-30
