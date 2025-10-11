# Coding Rules for optimal_build

This document defines the coding standards for the `optimal_build` repository. All new code and modified files should follow these rules. CODEX and other contributors should adhere to these standards.

For workflow, tooling setup, and detailed linting guidance, see [CONTRIBUTING.md](CONTRIBUTING.md).

If a temporary exception is truly necessary, record it in
`.coding-rules-exceptions.yml` and include context plus a clean-up plan. The
automation in `scripts/check_coding_rules.py` reads that file when evaluating
rule violations.

---

## 1. Database Migrations

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

**Rule:** Run `make format` then `make verify` before committing or opening a pull request.

**Why:**
- `make format` fixes all formatting issues (black, isort, ruff)
- `make verify` catches lint failures and test regressions
- Running format first prevents pre-commit hook failures

**Workflow:**
```bash
# 1. Format code (fixes issues automatically)
make format

# 2. Verify everything passes (checks only, no modifications)
make verify

# 3. Commit (pre-commit hooks should pass immediately)
git add .
git commit -m "your message"
```

**Tip:** See [CONTRIBUTING.md](CONTRIBUTING.md#testing-and-quality-checks) for the full testing and linting workflow.

---

## 4. Dependency Management

**Rule:** When adding new dependencies, update the appropriate dependency file. Never install packages without tracking them.

**Backend (Python):**
- Add to `backend/requirements.txt` (production) or `backend/requirements-dev.txt` (dev/test only)
- Pin exact versions: `fastapi==0.104.1`

**Frontend (TypeScript/React):**
- Add to `frontend/package.json` using `npm install --save <package>` or `npm install --save-dev <package>`
- Admin UI: Add to `ui-admin/package.json`

**Why:** Keeps dependencies reproducible across environments and prevents "works on my machine" issues.

**Examples:**
```bash
# ✅ Correct - track dependencies
cd backend
echo "pydantic==2.4.2" >> requirements.txt
pip install pydantic==2.4.2

cd frontend
npm install --save axios

# ❌ Wrong - untracked dependencies
pip install some-random-package  # Not added to requirements.txt
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

## Questions?

If a rule is unclear or seems wrong for a specific case:
1. Ask in the PR comments
2. Propose a rule change by updating this document in a separate PR
3. Document exceptions inline with `# Exception: <reason>` comments

**Last updated:** 2025-10-08
