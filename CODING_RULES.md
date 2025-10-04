# Coding Rules for optimal_build

This document defines the coding standards for the `optimal_build` repository. All new code and modified files should follow these rules. CODEX and other contributors should adhere to these standards.

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

**Rule:** Run `make verify` before creating pull requests or committing major changes. All tests must pass.

**Why:** Catches formatting issues, linting errors, and test failures before they reach the main branch.

**How to follow:**
- Run `make verify` before creating a PR (runs format-check, lint, and tests)
- Fix any issues reported by the command
- For comprehensive checks, run `make hooks` to execute pre-commit hooks
- Individual components: `make format-check`, `make lint`, `make test`

**Examples:**
```bash
# ✅ Correct - verify before committing
make verify
# ... fix any issues ...
git add .
git commit -m "Add compliance validation"

# Optional: run full pre-commit hooks
make hooks

# ❌ Wrong - committing without testing
git commit -m "quick fix" && git push  # No testing!
```

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

## Code Style Summary

Based on majority patterns in the codebase:

### Python (Backend)
- **Naming:** `snake_case` for functions, variables, files
- **Classes:** `PascalCase`
- **Imports:** Organize with `from __future__ import annotations` at top, then stdlib, then third-party, then local
- **Formatting:** Use `black` for auto-formatting (run via `make format`)
- **Linting:** Follow `flake8` rules (check via `make lint`)

### TypeScript/React (Frontend)
- **Naming:** `camelCase` for variables/functions, `PascalCase` for components/types
- **Interfaces:** Use `interface` not `type` for object shapes
- **Async:** Use `async`/`await`, not `.then()` chains
- **API calls:** snake_case in API responses, map to camelCase in frontend (see [client.ts:344-366](frontend/src/api/client.ts#L344-L366))

### File Organization
- Python modules: `backend/app/{feature}/` (e.g., `backend/app/models/`, `backend/app/api/routes/`)
- Tests mirror structure: `backend/tests/test_api/test_{feature}.py`
- Frontend components: `frontend/src/components/`, `frontend/src/pages/`
- Shared types: `frontend/src/types/`

---

## Enforcement

These rules are enforced through:
1. **Automated checks** in `make verify` (see Makefile:160-163)
2. **Pre-commit hooks** via `make hooks` (optional but recommended)
3. **Code review** - reviewers should reference this document
4. **CI/CD** - GitHub Actions runs `make verify` on all PRs

---

## Questions?

If a rule is unclear or seems wrong for a specific case:
1. Ask in the PR comments
2. Propose a rule change by updating this document in a separate PR
3. Document exceptions inline with `# Exception: <reason>` comments

**Last updated:** 2025-10-04
