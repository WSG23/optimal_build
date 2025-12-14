# Claude AI Agent Guide for optimal_build

> [!IMPORTANT] > **PRIMARY DIRECTIVE**: As an Anthropic agent (Claude), your primary operating procedure is to adhere to the Master Control Prompt.

**Pointer**: You must read and follow **[MCP.md](./MCP.md)** before proceeding with any task.

**Version:** 1.2
**Last Updated:** 2025-12-06

This document provides comprehensive guidance for Claude (and other AI agents) when working on the optimal_build codebase. Follow these rules strictly to maintain code quality and project consistency.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Communication Style](#communication-style)
3. [Required Reading Order](#required-reading-order)
4. [Pre-Flight Checks](#pre-flight-checks)
5. [Code Generation Workflow](#code-generation-workflow)
6. [Common Development Workflows](#common-development-workflows)
7. [Pre-Commit Rules Integration](#pre-commit-rules-integration)
8. [Coding Standards Summary](#coding-standards-summary)
9. [Testing Requirements](#testing-requirements)
10. [Troubleshooting Common Issues](#troubleshooting-common-issues)
11. [Common Pitfalls](#common-pitfalls)
12. [Phase Gate Compliance](#phase-gate-compliance)
13. [CI/CD Workflow](#cicd-workflow)
14. [Quality Checklist](#quality-checklist)

---

## Quick Start

**BEFORE doing anything:**

```bash
# 1. Run pre-flight checks
make ai-preflight

# 2. Check current status
make status

# 3. Verify environment
make verify
```

**AFTER writing code:**

```bash
# 1. Format code (auto-fixes issues)
make format

# 2. Verify everything passes
make verify

# 3. Run pre-commit hooks
make hooks
```

---

## Communication Style

**Tone:** Professional, precise, and quality-focused. No apologies or filler phrases.

**Code References:** When referencing files or code locations, use markdown links to make them clickable:

-   For files: `[filename.py](backend/app/filename.py)`
-   For specific lines: `[filename.py:42](backend/app/filename.py#L42)`
-   For line ranges: `[filename.py:42-51](backend/app/filename.py#L42-L51)`
-   For folders: `[backend/app/models/](backend/app/models/)`

**Commit Messages:** Use imperative mood with "why" context

-   ✅ "Add compliance scoring to Property model to track regulatory violations"
-   ❌ "Added compliance_score field"
-   ✅ "Fix ENUM migration pattern to prevent 'type already exists' errors"
-   ❌ "Fixed migrations"

**Checkpoint Protocol (CRITICAL):**

-   **Stop after critical steps** and wait for user approval
-   Ask "Should I proceed with implementing X?" before large changes
-   Show implementation plan before execution for complex features
-   Never make large architectural changes without explicit user approval
-   Example: "I've identified 12 files that need updates. Should I proceed with refactoring the authentication system?"

**Explanations:**

-   Provide concise explanations with the "why" behind technical decisions
-   Focus on **why** this solution was chosen, not just **what** was done
-   Include file paths with line numbers: `backend/app/models/property.py:142`
-   Use active voice over passive voice
-   Clarity over comprehensiveness

**Examples:**

```markdown
✅ GOOD - Clear, actionable, with context:
I've updated the Property model to include compliance scoring [backend/app/models/property.py:142-156].
This uses an ENUM for compliance status to prevent invalid states and adds an indexed foreign key
to enable fast querying of non-compliant properties.

Should I proceed with:

1. Creating the database migration
2. Adding API endpoints for compliance filtering
3. Writing unit tests for the new scoring logic

❌ BAD - Verbose, apologetic, no context:
I apologize for the confusion earlier. Here is the updated code for the property model.
I have made some changes that I think will help with what you're trying to do. Let me know
if this works for you or if you'd like me to change anything.
```

---

## Required Reading Order

Read these documents IN ORDER before writing any code:

### Priority 1: Product Requirements (MANDATORY)

1. **[docs/planning/features.md](docs/planning/features.md)** - Complete product vision

    - Source of truth for ALL features
    - Defines user roles and requirements
    - ~30 min read

2. **[docs/all_steps_to_product_completion.md](docs/all_steps_to_product_completion.md)** - Delivery roadmap

    - Maps 100% of features into 6 phases
    - Shows dependencies and priorities
    - Check BEFORE starting new work
    - ~20 min read

3. **[docs/ai-agents/next_steps.md](docs/ai-agents/next_steps.md)** - Current priorities
    - What to build next
    - Completed vs. in-progress features
    - Check daily
    - ~5 min read

### Priority 2: Technical Standards (MANDATORY)

4. **[CODING_RULES.md](CODING_RULES.md)** - Technical standards

    - 12 rules covering migrations, async, security
    - Pre-commit hooks enforce these
    - Must follow in ALL code
    - ~45 min read

5. **[frontend/UI_STANDARDS.md](frontend/UI_STANDARDS.md)** - UI Design Token Standards (CRITICAL for UI work)

    - Design token usage for spacing, radius, colors, typography
    - Square Cyber-Minimalism border-radius standards
    - Canonical component requirements
    - MUST READ before any frontend UI changes
    - ~10 min read

6. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Workflow and tooling
    - Setup, testing, linting
    - Code review checklist
    - ~15 min read

### Priority 3: Context Documents (REFERENCE)

7. **[README.md](README.md)** - Project overview
8. **[docs/planning/ui-status.md](docs/planning/ui-status.md)** - UI implementation status
9. **[docs/all_steps_to_product_completion.md#-known-testing-issues](docs/all_steps_to_product_completion.md#-known-testing-issues)** - Known test failures
10. **[docs/development/testing/summary.md](docs/development/testing/summary.md)** - Test suites

### Verification Checkpoint

Before proceeding, confirm:

-   [ ] I have read features.md completely
-   [ ] I have reviewed all_steps_to_product_completion.md for the current phase
-   [ ] I have checked next_steps.md for priorities
-   [ ] I have read CODING_RULES.md sections relevant to my task
-   [ ] I understand which phase I'm working in
-   [ ] I know the acceptance criteria for my task

---

## Pre-Flight Checks

**ALWAYS run before generating code:**

```bash
# Comprehensive pre-flight check
make ai-preflight
```

This verifies:

-   Tool versions match (Black, Ruff, etc.)
-   Coding rules compliance
-   No existing violations

**Manual checks:**

```bash
# Check tool versions
make check-tool-versions

# Check coding rules
make check-coding-rules

# Validate delivery plan
make validate-delivery-plan
```

---

## Code Generation Workflow

### Step 1: Plan and Document (BEFORE coding)

1. **Check existing work:**

    ```bash
    git status
    git log --oneline -10
    ```

2. **Review relevant documentation:**

    - Check all_steps_to_product_completion.md for your phase
    - Review next_steps.md for current priorities
    - Review the Known Testing Issues section in `docs/all_steps_to_product_completion.md`

3. **Plan your changes:**
    - Identify files to modify
    - Check for existing migrations (NEVER edit existing ones)
    - Verify no conflicts with in-progress work

### Step 2: Write Code (DURING coding)

Follow ALL rules in CODING_RULES.md:

**Rule 1: Database Migrations**

-   NEVER edit existing migration files
-   Create new migrations: `alembic revision -m "description"`
-   Use `sa.String()` for ENUM columns (NOT `sa.Enum()`)
-   Match Python enum VALUES exactly in SQL

**Rule 2: Async/Await**

-   ALL database calls use `async`/`await`
-   ALL API routes use `async def`
-   Use `AsyncSession` not `Session`

**Rule 3: Testing**

-   Run `make verify` before committing
-   Pre-commit hooks auto-format code

**Import Ordering (Python)**

Import ordering is enforced for Python via Ruff/isort (see `CODING_RULES.md` “Python Import Ordering and Formatting”).

```python
# 1. Standard library
import os
import sys

# 2. Third-party
from sqlalchemy import select
from fastapi import APIRouter

# 3. Local
from app.models import User
```

**Rule 7: Code Quality**

-   No unused variables or imports
-   Use `raise ... from e` for exception chaining
-   No mutable default arguments

### Step 3: Validate (AFTER coding)

**MANDATORY validation sequence:**

```bash
# 1. Format code (auto-fixes)
make format

# 2. Run type checking on new code (if you modified app/api/ or app/schemas/)
make typecheck-backend

# 3. Run all checks
make verify

# 4. Fix any violations
# (Repeat steps 1-3 until clean)

# 5. Run pre-commit hooks
make hooks

# 6. Test your changes
pytest backend/tests/test_[your_feature].py -v
```

**NEVER present code to the user until:**

-   `make format` passes ✅
-   `make typecheck-backend` passes ✅ (if you modified app/api/ or app/schemas/)
-   `make verify` passes ✅
-   `make hooks` passes ✅
-   Tests pass ✅

### Step 4: Provide Test Instructions (MANDATORY)

When you complete ANY feature, you MUST provide:

**a) Backend test commands:**

```bash
.venv/bin/pytest backend/tests/test_api/test_[feature].py -v
.venv/bin/pytest backend/tests/test_services/test_[feature].py -v
```

**b) Frontend test commands (if applicable):**

```bash
cd frontend && npm test -- src/modules/[feature]/__tests__
cd frontend && npm run lint
```

**c) UI manual test steps:**

```markdown
UI Manual Testing:

1. Navigate to [URL]
2. Click [button/action]
3. Verify [expected outcome]
4. Test edge cases: [scenarios]
```

**Example:**

```markdown
I've completed the finance scenario privacy feature. Please test:

Backend tests:
.venv/bin/pytest backend/tests/test_api/test_finance.py::test_scenario_privacy -v

Frontend tests:
cd frontend && npm test -- src/modules/finance/**tests**/FinanceScenarioTable.test.tsx

UI Manual Testing:

1. Navigate to /finance/scenarios
2. Create a new scenario
3. Toggle "Make Private" checkbox
4. Save and verify lock icon appears
5. Login as different user and verify scenario is hidden
```

---

## Common Development Workflows

This section provides detailed step-by-step workflows for common development tasks. Follow these workflows to ensure consistency and quality.

### API Endpoint Development Checklist

When creating a new API endpoint, ensure ALL of the following:

**Setup & Design:**

-   [ ] Uses `async def` for route handler (Rule 2)
-   [ ] Type hints for all parameters and return values
-   [ ] Pydantic request model defined with validation
-   [ ] Pydantic response model defined
-   [ ] Endpoint follows RESTful naming conventions

**Validation & Security:**

-   [ ] Input validation with Pydantic `Field()` validators
-   [ ] Authentication check: `current_user: User = Depends(get_current_user)` (Rule 11)
-   [ ] Authorization check: verify user owns resource or has required role
-   [ ] SQL injection prevented: use SQLAlchemy ORM, never f-strings (Rule 11)
-   [ ] XSS prevention: output validation for user-generated content
-   [ ] Rate limiting configured (if public endpoint)

**Error Handling & Logging:**

-   [ ] Specific error handling (no bare `except:` clauses) (Rule 7)
-   [ ] HTTPException with proper status codes (401, 403, 404, 422, 500)
-   [ ] Proper exception chaining with `from e` (Rule 7 - Ruff B904)
-   [ ] Logging for errors and important events
-   [ ] Audit logging for sensitive operations (user data, financial data)

**Documentation:**

-   [ ] Google-style docstring with Args, Returns, Raises sections
-   [ ] OpenAPI schema will be updated (run: `make openapi` if available)
-   [ ] API documentation updated (if applicable)

**Testing:**

-   [ ] Unit tests for business logic
-   [ ] Integration tests with test database
-   [ ] Test success case (200/201 response)
-   [ ] Test unauthorized case (401 response)
-   [ ] Test forbidden case (403 response)
-   [ ] Test not found case (404 response)
-   [ ] Test invalid input case (422 response)
-   [ ] Verify with: `pytest backend/tests/test_api/test_[feature].py -v`

**Performance:**

-   [ ] Database indexes on foreign keys used in query (Rule 9)
-   [ ] No N+1 query problems (use `selectinload()` or `joinedload()`)
-   [ ] Query performance <500ms for typical requests

**Example API Endpoint:**

```python
# backend/app/api/v1/finance.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.finance import FinanceScenario

router = APIRouter()


class FinanceScenarioCreate(BaseModel):
    """Request model for creating a finance scenario."""

    project_id: int = Field(..., gt=0, description="ID of the project")
    name: str = Field(..., min_length=1, max_length=200, description="Scenario name")
    budget: float = Field(..., gt=0, le=1e9, description="Total budget in dollars")


class FinanceScenarioResponse(BaseModel):
    """Response model for finance scenario."""

    id: int
    project_id: int
    name: str
    budget: float
    created_at: str


@router.post("/finance/scenarios", response_model=FinanceScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_finance_scenario(
    data: FinanceScenarioCreate,
    current_user: User = Depends(get_current_user),  # Authentication required
    db: AsyncSession = Depends(get_db),
) -> FinanceScenarioResponse:
    """Create a new finance scenario.

    Args:
        data: Finance scenario creation data
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        Created finance scenario with ID and timestamps

    Raises:
        HTTPException 403: User does not own the project
        HTTPException 422: Invalid input data
    """
    # Authorization check
    project = await db.get(Project, data.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create scenarios for this project"
        )

    # Create scenario
    try:
        scenario = FinanceScenario(
            project_id=data.project_id,
            name=data.name,
            budget=data.budget,
            created_by=current_user.id,
        )
        db.add(scenario)
        await db.commit()
        await db.refresh(scenario)

        return FinanceScenarioResponse(
            id=scenario.id,
            project_id=scenario.project_id,
            name=scenario.name,
            budget=scenario.budget,
            created_at=scenario.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
```

### Database Table Addition Workflow

When adding a new database table, follow these 8 steps:

**Step 1: Design Schema**

-   Define SQLAlchemy model in `backend/app/models/`
-   Add indexes for:
    -   All foreign keys (Rule 9 - MANDATORY)
    -   Frequently queried columns (status, created_at, etc.)
    -   Columns used in WHERE clauses
-   Include timestamps: `created_at`, `updated_at`
-   Add foreign key constraints with proper cascades (`CASCADE`, `SET NULL`, `RESTRICT`)
-   Choose appropriate column types (use `sa.String()` for ENUMs per Rule 1.2)

**Step 2: Create Migration**

```bash
cd backend && alembic revision -m "add user_preferences table"
```

**Step 3: Review Generated Migration**

-   Verify all columns, constraints, and indexes are correct
-   Use `sa.String()` for ENUM columns (NOT `sa.Enum()` - Rule 1.2)
-   Match Python enum VALUES exactly in SQL (Rule 1.3)
-   Add custom SQL if needed (triggers, functions, check constraints)
-   Test both upgrade AND downgrade paths

**Step 4: Update Models**

-   Add Pydantic schemas for API request/response in `backend/app/schemas/`
-   Update related models with SQLAlchemy relationships
-   Add type hints for all fields
-   Add docstrings for complex fields

**Step 5: Write Repository Layer (if applicable)**

-   Create repository class with CRUD operations
-   Use async methods: `async def create()`, `async def get()`, etc.
-   Add proper transaction handling with `async with session.begin()`
-   Add query optimization: `selectinload()`, `joinedload()` for relationships

**Step 6: Test Thoroughly**

-   Unit tests for model validation
-   Integration tests with real database
-   Test migration upgrade: `alembic upgrade head`
-   Test migration downgrade: `alembic downgrade -1`
-   Test foreign key constraints and cascades
-   Test unique constraints with duplicate data

**Step 7: Run Migration**

```bash
cd backend
alembic upgrade head
pytest backend/tests/test_models/test_[new_model].py -v
```

**Step 8: Update Documentation**

-   Add table to database schema docs (if applicable)
-   Update ER diagrams (if applicable)
-   Document retention policies (if sensitive data)

**Example Migration:**

```python
# backend/migrations/versions/20251109_add_user_preferences.py
"""add user_preferences table

Revision ID: 20251109_000001
Revises: 20251108_000005
Create Date: 2025-11-09 10:30:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "20251109_000001"
down_revision = "20251108_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM type for theme preference
    op.execute("CREATE TYPE theme_type AS ENUM ('light', 'dark', 'auto')")

    # Create table with proper column types
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("theme", sa.String(), nullable=False, server_default="auto"),  # Use String for ENUM
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Add foreign key constraint
    op.create_foreign_key("fk_user_preferences_user_id", "user_preferences", "users", ["user_id"], ["id"], ondelete="CASCADE")

    # Create indexes (MANDATORY for foreign keys)
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"])
    op.create_index("ix_user_preferences_created_at", "user_preferences", ["created_at"])

    # Ensure ENUM column uses the ENUM type
    op.execute("ALTER TABLE user_preferences ALTER COLUMN theme TYPE theme_type USING theme::theme_type")


def downgrade() -> None:
    op.drop_index("ix_user_preferences_created_at", "user_preferences")
    op.drop_index("ix_user_preferences_user_id", "user_preferences")
    op.drop_constraint("fk_user_preferences_user_id", "user_preferences", type_="foreignkey")
    op.drop_table("user_preferences")
    op.execute("DROP TYPE theme_type")
```

### Checkpoint Protocol Integration

**When to use checkpoints:**

1. **Before large refactors:** "I've identified 12 files that need updates for the authentication refactor. Should I proceed?"
2. **Before architectural changes:** "This would require changing the database schema and updating 8 API endpoints. May I proceed?"
3. **After discovering scope creep:** "While implementing feature X, I found that feature Y also needs updates. Should I include that in this work?"
4. **Before making breaking changes:** "This change will require frontend updates to 5 components. Should I proceed?"
5. **When encountering ambiguity:** "The requirements mention 'user management' but don't specify roles vs permissions. Should I implement both?"

**Checkpoint template:**

```markdown
I've completed the planning phase for [FEATURE NAME]. Here's the implementation plan:

**Scope:**

-   3 new database tables (user_preferences, user_sessions, user_audit_log)
-   5 new API endpoints (CRUD + search)
-   2 frontend components (PreferencesModal, SessionsTable)
-   Estimated 8-12 hours of work

**Files to modify:**

1. [backend/app/models/user.py:142-200](backend/app/models/user.py#L142-L200) - Add relationships
2. [backend/app/api/v1/users.py](backend/app/api/v1/users.py) - Add new endpoints
3. [frontend/src/pages/settings/Preferences.tsx](frontend/src/pages/settings/Preferences.tsx) - Add UI

**Dependencies:**

-   Requires PostgreSQL 13+ (for JSONB column)
-   No breaking changes to existing APIs
-   Backward compatible migration

**Risks:**

-   User table will grow by ~1KB per user (acceptable for <100K users)
-   New audit_log table may need retention policy (recommend 90 days)

**Should I proceed with:**

1. Creating the migrations
2. Implementing the API endpoints
3. Adding the frontend components
4. Writing the test suite

Or would you like me to adjust the scope?
```

---

## Pre-Commit Rules Integration

This project uses **comprehensive pre-commit hooks** defined in [.pre-commit-config.yaml](.pre-commit-config.yaml):

### Automated Checks (Run on Every Commit)

**Local hooks (scripts/):**

-   `audit-migrations` - Verifies migration integrity
-   `check-migration-enums` - Enforces ENUM pattern rules (Rule 1.2)
-   `pdf-smoke-test` - Tests PDF generation
-   `phase-gate` - Enforces phase completion rules (Rule 12)

**Standard hooks:**

-   `end-of-file-fixer` - Ensures files end with newline
-   `trailing-whitespace` - Removes trailing whitespace
-   `check-yaml` - Validates YAML syntax
-   `check-merge-conflict` - Detects merge conflict markers

**Python formatting:**

-   `black` - Code formatting (88 chars, auto-fix)
-   `ruff` - Import sorting + linting (auto-fix)
-   `flake8` - Additional linting for test files
-   `mypy` - Type checking (backend/)

**Frontend formatting:**

-   `prettier` - Format JS/TS/CSS (frontend/ and ui-admin/)
-   `eslint` - Lint JS/TS (frontend/ and ui-admin/)

### How Pre-Commit Hooks Work

**During `git commit`:**

1. Hooks run automatically
2. Auto-fixable issues are corrected (black, ruff, prettier)
3. Modified files are auto-staged
4. Commit succeeds or fails based on results

**If hooks modify files:**

```bash
# Files were auto-formatted
# Just commit again
git commit -m "your message"
```

**To run hooks manually:**

```bash
# Run on staged files
pre-commit run

# Run on all files
pre-commit run --all-files

# Or use Make target
make hooks
```

**To bypass hooks (NOT RECOMMENDED):**

```bash
# Skip pre-commit hooks
git commit --no-verify

# Skip pre-push checks
SKIP_PRE_PUSH_CHECKS=1 git push
```

### Custom Pre-Commit Scripts

**audit_migrations.py:**

-   Checks migration file integrity
-   Verifies no edits to existing migrations
-   Ensures migrations are sequential

**check_migration_enums.py:**

-   Enforces Rule 1.2 (no `sa.Enum()` with `create_type=False`)
-   Scans migration files for forbidden patterns
-   Grandfathers existing violations (see .coding-rules-exceptions.yml)

**check_phase_gate.py:**

-   Enforces Rule 12 (phase completion gates)
-   Verifies no unchecked `[ ]` items in completed phases
-   Checks files listed in "Files Delivered" exist
-   Validates test status (no ❌ or ⚠️ in completed phases)

**smoke_test_pdfs.py:**

-   Runs when PDF generation code changes
-   Validates PDF can be generated and has content
-   Checks Safari compatibility (strictest browser)

### Coding Rules Exceptions

Some pre-existing code violates current rules. These are documented in:

-   **.coding-rules-exceptions.yml** - Rule violations (with cleanup plan)
-   **.coding-rules.yaml** - Rule configuration

**Format:**

```yaml
exceptions:
    rule_1_2_enum_pattern:
        - backend/migrations/versions/20250220_000009_old_migration.py
        # Reason: Pre-existing migration, grandfathered
        # Cleanup: Do not edit; follow new pattern for future migrations
```

**Adding exceptions (RARE):**

1. Document WHY exception is needed
2. Add cleanup plan
3. Update .coding-rules-exceptions.yml
4. Get approval in PR comments

---

## Coding Standards Summary

### Database Migrations (Rule 1)

**NEVER edit existing migrations:**

```bash
# ✅ CORRECT
alembic revision -m "add compliance_score column"

# ❌ WRONG
# Editing backend/migrations/versions/20240919_000005_enable_postgis.py
```

**ENUM types (Rule 1.2):**
See comprehensive examples in [CODING_RULES.md Rule 1.2](CODING_RULES.md#12-postgresql-enum-types-in-migrations)

**ENUM values match Python (Rule 1.3):**

```python
# Python model
class ProjectType(str, Enum):
    NEW_DEVELOPMENT = "NEW_DEVELOPMENT"  # ← VALUE is uppercase

# ✅ CORRECT - SQL matches Python VALUE
op.execute("CREATE TYPE projecttype AS ENUM ('NEW_DEVELOPMENT', 'REDEVELOPMENT')")

# ❌ WRONG - Case mismatch
op.execute("CREATE TYPE projecttype AS ENUM ('new_development', 'redevelopment')")
```

### Async Patterns (Rule 2)

See comprehensive examples in [CODING_RULES.md Rule 2](CODING_RULES.md#2-asyncawait-for-database-and-api-operations)

### Import Ordering (Rule 6)

```python
# ✅ CORRECT
import os
import sys
from pathlib import Path

from sqlalchemy import select
from fastapi import APIRouter

from app.models import User
from app.core.config import settings

# ❌ WRONG - Mixed ordering
from sqlalchemy import select
import os
from app.models import User
import sys
```

### Code Quality (Rule 7)

See comprehensive examples in [CODING_RULES.md Rule 7](CODING_RULES.md#7-code-quality-standards)

### Security (Rule 11)

```python
# ✅ CORRECT - Authentication required
@router.post("/finance/scenarios")
async def create_scenario(
    data: FinanceScenarioCreate,
    current_user: User = Depends(get_current_user),  # ← Required
    db: AsyncSession = Depends(get_db)
):
    if not await user_owns_project(db, current_user.id, data.project_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    return await create_finance_scenario(db, data)

# ❌ WRONG - No authentication
@router.post("/finance/scenarios")
async def create_scenario(data: FinanceScenarioCreate, db: AsyncSession = Depends(get_db)):
    return await create_finance_scenario(db, data)
```

### Database Indexing (Rule 9)

```python
# ✅ CORRECT - Index foreign keys
op.create_index('ix_finance_scenarios_project_id', 'finance_scenarios', ['project_id'])

# ❌ WRONG - No indexes
# Foreign key without index will cause slow queries
```

---

## Testing Requirements

### Backend Testing (Rule 10)

**MANDATORY for all features:**

```python
# backend/tests/test_api/test_finance.py
async def test_create_scenario_success(client, test_user):
    """Test creating a scenario returns 201 and correct data."""
    response = await client.post(
        "/api/v1/finance/scenarios",
        json={"project_id": 1, "name": "Test Scenario"},
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Scenario"

async def test_create_scenario_unauthorized(client):
    """Test creating scenario without auth returns 401."""
    response = await client.post(
        "/api/v1/finance/scenarios",
        json={"project_id": 1, "name": "Test"}
    )
    assert response.status_code == 401
```

**Run tests:**

```bash
# Unit tests (fast)
pytest backend/tests/ -v

# With coverage
pytest backend/tests/ --cov=app --cov-report=html

# Specific test
pytest backend/tests/test_api/test_finance.py::test_create_scenario_success -v
```

### Frontend Testing (Rule 10)

**RECOMMENDED for critical flows:**

```typescript
// frontend/src/modules/finance/components/__tests__/FinanceScenarioTable.test.tsx
import { render, screen } from '@testing-library/react'
import { FinanceScenarioTable } from '../FinanceScenarioTable'

test('renders scenario table with data', () => {
    const scenarios = [{ id: 1, name: 'Test', npv: 1000000 }]
    render(<FinanceScenarioTable scenarios={scenarios} />)

    expect(screen.getByText('Test')).toBeInTheDocument()
    expect(screen.getByText('$1,000,000')).toBeInTheDocument()
})
```

**Run tests:**

```bash
cd frontend && npm test
cd frontend && npm run lint
```

### Coverage Requirements

-   Backend critical paths: **>80%**
-   Backend overall: **>70%**
-   Frontend critical paths: **Covered**
-   Frontend overall: Best effort (JSDOM timing issues documented)

---

## Troubleshooting Common Issues

This section helps AI agents quickly diagnose and fix common issues without reinventing solutions. Before reporting a bug, check if it's a known issue documented in [docs/all_steps_to_product_completion.md#-known-testing-issues](docs/all_steps_to_product_completion.md#-known-testing-issues).

### Pre-Commit Hook Failures

**Symptom:** `make hooks` or `git commit` fails with rule violation messages

**Common Causes:**

1. **Black/Ruff formatting issues**

    ```bash
    # Fix automatically
    make format

    # Re-run hooks
    make hooks
    ```

2. **Migration ENUM pattern violation** (Rule 1.2)

    ```
    ERROR: Migration uses forbidden sa.Enum() pattern
    File: backend/migrations/versions/20251109_000001_add_table.py
    ```

    **Solution:**

    - Replace `sa.Enum()` with `sa.String()` in column definition
    - See [CODING_RULES.md Rule 1.2](CODING_RULES.md#12-postgresql-enum-types-in-migrations) for correct pattern

3. **Phase gate violation** (Rule 12)

    ```
    ERROR: Phase 1D marked COMPLETE but has unchecked [ ] items
    ```

    **Solution:**

    - Update docs/all_steps_to_product_completion.md to reflect actual status
    - Mark phase as "⚠️ IN PROGRESS" until all items complete
    - Or complete remaining items before marking phase COMPLETE
    - See [Phase Gate Compliance](#phase-gate-compliance) section

4. **Ruff linting violations**

    ```
    backend/app/api/v1/finance.py:142: F841 local variable 'result' is assigned to but never used
    backend/app/services/property.py:89: B904 Within an except clause, raise exceptions with from err
    ```

    **Solution:**

    - F841: Remove unused variable or prefix with `_` if intentionally unused
    - B904: Add `from e` to exception: `raise CustomError("Failed") from e`
    - See [CODING_RULES.md Rule 7](CODING_RULES.md#7-code-quality-standards) for details

5. **Still failing after fixes?**
    - Check `.coding-rules-exceptions.yml` for documented exceptions
    - Review [CODING_RULES.md](CODING_RULES.md) for the specific rule
    - Ask user for clarification if requirements are unclear

### Test Coverage Below Threshold

**Symptom:** CI or `make verify` fails with "Coverage below 80%"

**Solution:**

1. **Run coverage report:**

    ```bash
    pytest backend/tests/ --cov=app --cov-report=html
    # Open: backend/htmlcov/index.html in browser
    ```

2. **Identify uncovered lines:**

    - Look for red lines in the HTML report
    - Focus on critical paths (authentication, data validation, business logic)
    - Ignore boilerplate code (imports, class definitions)

3. **Add unit tests for uncovered code:**

    ```python
    # Example: Cover error handling path
    async def test_create_scenario_with_invalid_project_id(client, test_user):
        """Test creating scenario with non-existent project returns 403."""
        response = await client.post(
            "/api/v1/finance/scenarios",
            json={"project_id": 99999, "name": "Test"},
            headers={"Authorization": f"Bearer {test_user.token}"}
        )
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    ```

4. **Re-run coverage:**

    ```bash
    pytest backend/tests/ --cov=app --cov-report=term-missing
    # Check that coverage increased
    ```

5. **Update coverage tracking:**
    - If coverage increases, note it in commit message
    - If coverage decreases, explain why in PR description

### Database Migration Conflicts

**Symptom:** `alembic upgrade head` fails with "multiple heads detected" or "can't locate revision"

**Common Solutions:**

1. **Multiple migration heads (branching):**

    ```bash
    # Check for multiple heads
    cd backend && alembic heads

    # If multiple heads exist, create merge migration
    alembic merge heads -m "merge migration branches"

    # Review generated merge migration carefully
    # Then run upgrade
    alembic upgrade head
    ```

2. **Migration dependency out of order:**

    ```
    ERROR: Can't locate revision identifier: '20251108_000005'
    ```

    **Solution:**

    - Check `down_revision` in your migration matches the actual latest migration
    - Run `alembic history` to see migration chain
    - Fix the `down_revision` value in your migration file

3. **ENUM type already exists:**

    ```
    ERROR: type "deal_status" already exists
    ```

    **Solution:**

    - Add `IF NOT EXISTS` to CREATE TYPE:

    ```python
    op.execute("CREATE TYPE IF NOT EXISTS deal_status AS ENUM ('open', 'closed')")
    ```

4. **NEVER edit existing migrations** (Rule 1.1)
    - Always create NEW migration to fix issues
    - Use `alembic revision -m "fix enum type creation"` for corrections

### Async/Await Errors

**Symptom:** `RuntimeWarning: coroutine was never awaited` or `TypeError: object async_generator can't be used in 'await' expression`

**Common Solutions:**

1. **Missing `await` on database operation:**

    ```python
    # ❌ WRONG - forgot await
    result = session.execute(select(Property).where(Property.id == property_id))

    # ✅ CORRECT
    result = await session.execute(select(Property).where(Property.id == property_id))
    ```

2. **Using sync Session instead of AsyncSession:**

    ```python
    # ❌ WRONG
    from sqlalchemy.orm import Session

    def get_property(session: Session, property_id: str):
        return session.query(Property).filter(...).first()

    # ✅ CORRECT
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select

    async def get_property(session: AsyncSession, property_id: str):
        result = await session.execute(select(Property).where(Property.id == property_id))
        return result.scalar_one_or_none()
    ```

3. **API route missing `async def`:**

    ```python
    # ❌ WRONG
    @router.get("/properties/{property_id}")
    def fetch_property(property_id: str, session: AsyncSession = Depends(get_db)):
        return get_property(session, property_id)  # Can't await in sync function!

    # ✅ CORRECT
    @router.get("/properties/{property_id}")
    async def fetch_property(property_id: str, session: AsyncSession = Depends(get_db)):
        return await get_property(session, property_id)
    ```

4. **Reference:** See [CODING_RULES.md Rule 2](CODING_RULES.md#2-asyncawait-for-database-and-api-operations) for complete async patterns

### Frontend Test Failures

**Symptom:** `npm test` fails with "Unable to find element" or "window is not defined"

**Known Issues:**

1. **React Testing Library async timing issues:**

    - Check [docs/all_steps_to_product_completion.md#-known-testing-issues](docs/all_steps_to_product_completion.md#-known-testing-issues#frontend-react-testing-library-async-timing)
    - These are JSDOM environment issues, NOT application bugs
    - Application code works correctly in browser
    - Solution: Manual testing in browser + backend test coverage

2. **JSDOM environment setup issues:**
    - Check [docs/all_steps_to_product_completion.md#-known-testing-issues](docs/all_steps_to_product_completion.md#-known-testing-issues#frontend-nodejs-test-runner-jsdom-environment-setup-issues)
    - 10 out of 26 tests fail due to JSDOM setup
    - These failures don't indicate broken functionality
    - Solution: Run backend tests + manual UI testing

**Workaround for frontend development:**

1. Run backend tests for backend changes: `pytest backend/tests/ -v`
2. Run linting: `npm --prefix frontend run lint`
3. Test manually in browser: `make dev` and navigate to component
4. Accept that some pre-existing component tests will fail due to test harness issues

### `make verify` Failures

**Symptom:** `make verify` fails with linting, formatting, or test errors

**Diagnostic Steps:**

1. **Run individual checks to isolate the issue:**

    ```bash
    # Check formatting (usually auto-fixable)
    make format-check

    # Check linting (may need manual fixes)
    make lint

    # Check coding rules compliance
    make check-coding-rules

    # Run tests
    make test
    ```

2. **Fix issues one by one:**

    - **Format issues:** Run `make format` to auto-fix
    - **Lint issues:** Fix manually based on error messages
    - **Rule violations:** See specific rule in [CODING_RULES.md](CODING_RULES.md)
    - **Test failures:** See "Test Coverage Below Threshold" above

3. **Re-run verify:**

    ```bash
    make verify
    ```

4. **Common gotchas:**
    - Pre-commit hooks may have modified files → commit again
    - Version mismatch in Black/Ruff → check [CODING_RULES.md Rule 4](CODING_RULES.md#4-dependency-management)
    - New dependencies not tracked → add to requirements.txt

### PDF Generation Errors (Sandbox Environment)

**Symptom:** `ImportError: cannot import name 'HTML' from 'weasyprint'` or PDF tests fail

**Root Cause:** WeasyPrint requires system libraries (Cairo, Pango, GDK-Pixbuf) not available in all environments

**Check Known Issues:**

-   See [docs/all_steps_to_product_completion.md#-known-testing-issues](docs/all_steps_to_product_completion.md#-known-testing-issues#pdf-rendering-dependencies-absent-in-sandbox)
-   This is an **environment limitation**, not an application bug

**Solutions:**

1. **For local development:**

    ```bash
    # macOS
    brew install cairo pango gdk-pixbuf libffi

    # Ubuntu/Debian
    sudo apt-get install libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev

    # Then reinstall Python packages
    pip install -r backend/requirements.txt
    ```

2. **For sandbox/CI environments without system packages:**

    - Tests are automatically skipped with `@pytest.mark.skip` decorator
    - PDF functionality works in Docker/production environments
    - Use manual testing for PDF verification

3. **Check if PDF generation works in your environment:**
    ```bash
    python -c "from weasyprint import HTML; print('PDF generation available')"
    ```

---

## Common Pitfalls

### 1. Editing Existing Migrations

**NEVER DO THIS:**

```bash
# ❌ WRONG
vim backend/migrations/versions/20240919_000005_enable_postgis.py
# Making changes to existing migration
```

**INSTEAD:**

```bash
# ✅ CORRECT
cd backend && alembic revision -m "add new column"
# Create new migration file
```

### 2. Using sa.Enum() in Migrations

See detailed examples in [Troubleshooting](#pre-commit-hook-failures) and [CODING_RULES.md Rule 1.2](CODING_RULES.md#12-postgresql-enum-types-in-migrations)

### 3. Sync Database Code

See detailed examples in [Troubleshooting](#asyncawait-errors) and [CODING_RULES.md Rule 2](CODING_RULES.md#2-asyncawait-for-database-and-api-operations)

### 4. Missing Test Instructions

**NEVER DO THIS:**

```markdown
I've completed the feature. The implementation is done.
```

**INSTEAD:**

```markdown
I've completed the finance scenario privacy feature. Please test:

Backend tests:
.venv/bin/pytest backend/tests/test_api/test_finance.py::test_scenario_privacy -v

UI Manual Testing:

1. Navigate to /finance/scenarios
2. Create a scenario and toggle "Make Private"
3. Verify lock icon appears
4. Login as different user and verify scenario is hidden
```

### 5. Marking Incomplete Phases Complete

**NEVER DO THIS:**

```markdown
### Phase 1D: Business Performance ✅ COMPLETE

**UI Implementation Checklist:**

-   [ ] Pipeline Kanban board
-   [ ] Deal insights panel
```

**INSTEAD:**

```markdown
### Phase 1D: Business Performance ⚠️ 80% COMPLETE

**Completed:**

-   ✅ Backend API
-   ✅ Page scaffold

**In Progress (see next_steps.md):**

-   🔄 Pipeline Kanban board (1-2 days)
-   🔄 Deal insights panel (1-2 days)
```

### 6. No Database Indexes

**NEVER DO THIS:**

```python
# ❌ WRONG - Foreign key without index
op.create_table(
    'scenarios',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('project_id', sa.Integer(), nullable=False),  # No index!
)
```

**INSTEAD:**

```python
# ✅ CORRECT - Index foreign keys
op.create_table(
    'scenarios',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('project_id', sa.Integer(), nullable=False),
)
op.create_index('ix_scenarios_project_id', 'scenarios', ['project_id'])
```

---

## Phase Gate Compliance

### Rule 12: Phase Completion Gates

**Before marking ANY phase "✅ COMPLETE" in all_steps_to_product_completion.md:**

1. **Check for incomplete items:**

    - Search for `- [ ]` (unchecked) → Must be ZERO
    - Search for `🔄` (In Progress) → Must be ZERO
    - Search for `❌` (Incomplete) → Must be ZERO

2. **Verify UI testing:**

    - User must confirm: "✅ All manual tests passing"

3. **Verify files exist:**

    - All files in "Files Delivered:" section must exist on disk

4. **Verify tests pass:**

    - "Test Status:" shows ✅ (no ❌ or ⚠️)

5. **Ask user for approval:**

    ```markdown
    Phase X checklist is complete:

    -   ✅ All [ ] items checked
    -   ✅ No 🔄 In Progress markers
    -   ✅ No ❌ incomplete items
    -   ✅ UI manual testing passed
    -   ✅ All files in "Files Delivered" exist
    -   ✅ All tests passing

    May I mark Phase X as "✅ COMPLETE"?
    ```

**Automated enforcement:**

The pre-commit hook `check_phase_gate.py` verifies:

-   No unchecked `[ ]` items in completed phases
-   No `🔄` or `❌` markers in completed phases
-   All files in "Files Delivered:" exist
-   Test status shows ✅ (not ❌ or ⚠️)

**Example violation caught:**

```
RULE VIOLATION: Phase 1D marked '✅ COMPLETE' but has:
  -> 4 unchecked [ ] checklist items
  -> 3 files listed but missing:
     frontend/src/pages/business-performance/PipelineKanban.tsx
  -> Test Status shows ⚠️ warnings
```

---

## CI/CD Workflow

This section documents the continuous integration and deployment workflow for optimal_build. Understanding this workflow helps AI agents ensure their code changes pass all automated checks.

### Make Targets Overview

The project uses GNU Make for workflow automation. All quality checks are defined as Make targets:

**Pre-Flight Checks:**

```bash
# Run before starting any work (MANDATORY)
make ai-preflight
# Verifies: tool versions, coding rules compliance, no existing violations

# Check current project status
make status
# Shows: git status, recent commits, branch info
```

**Code Quality Checks:**

```bash
# Format code automatically (Black, Ruff, isort)
make format
# Auto-fixes: line length, import ordering, trailing whitespace

# Check formatting without modifying files
make format-check
# Used in CI to verify code is formatted correctly

# Run linting checks (Ruff, flake8, mypy)
make lint
# Checks: code quality, type hints, unused imports
```

**Testing:**

```bash
# Run all backend tests
make test
# Runs: pytest backend/tests/ -v

# Run tests with coverage report
pytest backend/tests/ --cov=app --cov-report=html
# Generates: backend/htmlcov/index.html (coverage report)

# Run specific test file
pytest backend/tests/test_api/test_finance.py -v
```

**Comprehensive Verification:**

```bash
# Run ALL quality checks (use before committing)
make verify
# Runs: format-check, lint, check-coding-rules, test
# This is the gatekeeper - must pass before committing
```

**Pre-Commit Hooks:**

```bash
# Run pre-commit hooks manually (runs on git commit automatically)
make hooks
# Runs: black, ruff, flake8, mypy, custom scripts

# Install pre-commit hooks (first-time setup)
pre-commit install
```

**Database Operations:**

```bash
# Create new migration
cd backend && alembic revision -m "description"

# Run migrations (upgrade to latest)
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check migration history
alembic history

# Check for multiple heads
alembic heads
```

**Development Server:**

```bash
# Start development server (backend + frontend)
make dev

# Stop development server
make stop

# View logs
make logs
```

### Pre-Commit Hook Pipeline

The pre-commit framework runs automatically on `git commit`. Here's what it does:

**1. File Format Checks (Auto-fix):**

-   `end-of-file-fixer` - Ensures files end with newline
-   `trailing-whitespace` - Removes trailing whitespace
-   `check-yaml` - Validates YAML syntax
-   `check-merge-conflict` - Detects merge conflict markers

**2. Python Formatting (Auto-fix):**

-   `black` - Code formatting (88 char line length)
-   `ruff` - Import sorting + linting (with `--fix` flag)
    -   Fixes: import order, unused imports, line length
    -   Checks: code quality (F841, B904, B006, etc.)

**3. Python Type Checking (Manual fix required):**

-   `mypy` - Type checking for `backend/` directory
    -   Verifies: type hints, return types, parameter types
    -   Failures require manual code changes

**4. Frontend Formatting (Auto-fix):**

-   `prettier` - Format JS/TS/CSS (`frontend/` and `ui-admin/`)
-   `eslint` - Lint JS/TS with auto-fix where possible

**5. Custom Project Rules (Manual fix required):**

-   `audit-migrations` - Verifies migration integrity (Rule 1.1)
-   `check-migration-enums` - Enforces ENUM pattern (Rule 1.2)
-   `phase-gate` - Enforces phase completion rules (Rule 12)
-   `pdf-smoke-test` - Tests PDF generation (when PDF code changes)

**Hook Behavior:**

-   **Auto-fix hooks:** Modify files in-place, then you commit again
-   **Check hooks:** Block commit if they fail, require manual fixes
-   **Skip hooks:** `git commit --no-verify` (NOT RECOMMENDED - only with user approval)

**Example commit workflow:**

```bash
# 1. Stage your changes
git add backend/app/models/finance.py

# 2. Attempt commit
git commit -m "Add finance scenario privacy feature"

# 3. Hooks run automatically
#    - Black reformats code
#    - Ruff fixes imports
#    - Files are auto-staged

# 4. If hooks modified files, commit again
git commit -m "Add finance scenario privacy feature"

# 5. If all hooks pass, commit succeeds
```

### Quality Gates

**Before Committing:**

-   [ ] `make ai-preflight` passes (verify environment is correct)
-   [ ] `make verify` passes (format, lint, rules, tests all pass)
-   [ ] `make hooks` passes (pre-commit hooks run successfully)
-   [ ] Tests added for new functionality
-   [ ] Coverage maintained or improved (>80% for critical paths)

**Before Marking Phase Complete (Rule 12):**

-   [ ] No unchecked `[ ]` items in phase section
-   [ ] No `🔄` (In Progress) or `❌` (Incomplete) markers
-   [ ] All files in "Files Delivered" exist on disk
-   [ ] Test status shows ✅ (no ❌ or ⚠️)
-   [ ] Manual UI QA completed (for phases with frontend work)
-   [ ] User approval obtained

**Before Pushing to Remote:**

-   [ ] All commits have passed pre-commit hooks
-   [ ] Branch is up to date with main: `git pull origin main`
-   [ ] No merge conflicts
-   [ ] Commit messages follow standards (imperative mood + context)

### CI/CD Best Practices

**For AI Agents:**

1. **Always run `make verify` before claiming work is complete**

    - Don't rely on pre-commit hooks alone
    - Verify tests pass locally before pushing

2. **Never bypass quality checks without user approval**

    - Don't use `git commit --no-verify` unless explicitly approved
    - Don't use `SKIP_PRE_PUSH_CHECKS=1` unless explicitly approved

3. **Fix root causes, not symptoms**

    - If a hook fails, fix the underlying issue
    - Don't add exceptions to `.coding-rules-exceptions.yml` without justification

4. **Document when tests are deferred**

    - If test coverage is temporarily lower, explain why in commit message
    - Create follow-up task to add missing tests
    - Update `docs/all_steps_to_product_completion.md#-known-testing-issues` if applicable

5. **Checkpoint before large changes**
    - If `make verify` will take >5 minutes, ask user if you should proceed
    - Show scope of changes before implementing

**Common CI/CD Issues:**

1. **"make verify fails but pre-commit passes"**

    - `make verify` runs additional checks (test coverage, coding rules)
    - Fix the specific failure reported by `make verify`

2. **"Tests pass locally but fail in CI"**

    - Check environment differences (Python version, dependencies)
    - Verify `.env` values aren't hardcoded
    - Check for race conditions in async tests

3. **"Pre-commit hooks modify files repeatedly"**

    - Usually Black/Ruff version mismatch between venv and `.pre-commit-config.yaml`
    - See [CODING_RULES.md Rule 4](CODING_RULES.md#4-dependency-management) for version sync

4. **"Hooks are slow (>30 seconds)"**
    - Pre-commit caches hook environments
    - First run after changes is slower
    - Run `pre-commit run --all-files` once to pre-cache

---

## Quality Checklist

### Before Committing Code

-   [ ] Read all required documentation (see [Required Reading Order](#required-reading-order))
-   [ ] Ran `make ai-preflight` successfully
-   [ ] **Asked user for approval before large changes** (Checkpoint Protocol)
-   [ ] Code follows ALL rules in CODING_RULES.md
-   [ ] No unused variables or imports (Ruff F841, F401)
-   [ ] Proper exception chaining with `from e` (Ruff B904)
-   [ ] All database operations use async/await (Rule 2)
-   [ ] Import ordering correct (Rule 6)
-   [ ] No edits to existing migrations (Rule 1)
-   [ ] Database indexes on foreign keys (Rule 9)
-   [ ] Input validation with Pydantic (Rule 11)
-   [ ] Authentication required on endpoints (Rule 11)
-   [ ] Ran `make typecheck-backend` and passes ✅ (if modified app/api/ or app/schemas/)
-   [ ] Mypy errors in new code = 0 (no new type errors introduced)
-   [ ] Ran `make verify` and all checks pass ✅
-   [ ] Ran `make hooks` and pre-commit passes ✅
-   [ ] Tests written and passing ✅
-   [ ] **Provided test instructions to user (Rule 8)** - backend, frontend, and UI manual tests

### Before Committing UI/Frontend Code (ADDITIONAL)

-   [ ] Read [frontend/UI_STANDARDS.md](frontend/UI_STANDARDS.md) before making UI changes
-   [ ] No hardcoded pixel values (use `--ob-space-*` or `--ob-size-*` tokens)
-   [ ] No MUI spacing numbers like `spacing={2}` (use `spacing="var(--ob-space-200)"`)
-   [ ] No hardcoded border-radius (use `--ob-radius-*` tokens)
-   [ ] Cards/panels use `--ob-radius-sm` (4px), NOT larger radii
-   [ ] Buttons use `--ob-radius-xs` (2px)
-   [ ] Modals/dialogs use `--ob-radius-lg` (8px)
-   [ ] No hardcoded colors (use theme palette or design tokens)
-   [ ] Using canonical components from `src/components/canonical/` where available
-   [ ] Font sizes use `--ob-font-size-*` tokens
-   [ ] Ran `cd frontend && npm run lint` and passes ✅

### Before Marking Phase Complete

-   [ ] No unchecked `[ ]` items in phase section
-   [ ] No `🔄` (In Progress) or `❌` (Incomplete) markers
-   [ ] All files in "Files Delivered" exist on disk
-   [ ] Test status shows ✅ (no ❌ or ⚠️)
-   [ ] User confirmed UI manual testing passed
-   [ ] User approved marking phase complete

---

## Emergency Procedures

### If Pre-Commit Hooks Fail

**1. Read the error message carefully**

**2. Common fixes:**

```bash
# Black formatting issues
make format

# Ruff linting issues
.venv/bin/ruff check --fix backend/app/

# Migration ENUM pattern violation
# Fix: Use sa.String() instead of sa.Enum()

# Phase gate violation
# Fix: Update all_steps_to_product_completion.md to reflect actual status
```

**3. Re-run verification:**

```bash
make verify
make hooks
```

**4. If still failing:**

-   Check .coding-rules-exceptions.yml for documented exceptions
-   Review CODING_RULES.md for the specific rule
-   Ask user for clarification

### If Tests Fail

**1. Check known issues:**

```bash
# Review known test failures
cat docs/all_steps_to_product_completion.md#-known-testing-issues
```

**2. Run specific test:**

```bash
pytest backend/tests/test_api/test_[feature].py::test_[specific] -vv
```

**3. Check test logs:**

```bash
pytest backend/tests/ -v --tb=short
```

**4. Frontend test issues:**

-   JSDOM timing issues are documented
-   Check docs/all_steps_to_product_completion.md#-known-testing-issues
-   May need to adjust test timeouts

### If Make Verify Fails

**1. Run individual checks:**

```bash
make format-check  # Check formatting
make lint          # Check linting
make check-coding-rules  # Check rule compliance
make test          # Run tests
```

**2. Fix issues one by one**

**3. Re-run verify:**

```bash
make verify
```

---

## Quick Reference

### Essential Commands

```bash
# Pre-flight checks
make ai-preflight

# Format and verify
make format
make verify

# Run pre-commit hooks
make hooks

# Run tests
make test
pytest backend/tests/ -v

# Check status
make status
git status

# Development server
make dev
make stop
```

### Essential Files

-   **CODING_RULES.md** - 12 technical rules (MUST follow)
-   **CONTRIBUTING.md** - Workflow and tooling
-   **docs/all_steps_to_product_completion.md** - Roadmap and phases
-   **docs/ai-agents/next_steps.md** - Current priorities
-   **.pre-commit-config.yaml** - Pre-commit hook configuration
-   **.coding-rules-exceptions.yml** - Documented rule exceptions

### Essential Rules

1. **NEVER** edit existing migrations
2. **ALWAYS** use async/await for database operations
3. **ALWAYS** run `make verify` before committing
4. **ALWAYS** provide test instructions (Rule 8)
5. **NEVER** mark phases complete without user approval (Rule 12)
6. **ALWAYS** index foreign keys (Rule 9)
7. **ALWAYS** validate inputs with Pydantic (Rule 11)
8. **ALWAYS** require authentication on endpoints (Rule 11)

---

## Support and Feedback

**If you need help:**

-   Review CODING_RULES.md for specific rule guidance
-   Check docs/all_steps_to_product_completion.md#-known-testing-issues for test issues
-   Ask user for clarification if requirements unclear

**If documentation is unclear:**

-   Ask user to clarify requirements
-   Suggest documentation improvements
-   Never guess or assume

**If pre-commit hooks are blocking you:**

-   Read the error message carefully
-   Fix the underlying issue (don't bypass hooks)
-   Use `--no-verify` ONLY as last resort with user approval

---

## Version History

**v1.1 (2025-11-09):**

-   Added Communication Style section with checkpoint protocol
-   Added Common Development Workflows section:
    -   API Endpoint Development Checklist (18 items)
    -   Database Table Addition Workflow (8 steps)
    -   Checkpoint Protocol Integration with templates
-   Added Troubleshooting Common Issues section:
    -   Pre-commit hook failures
    -   Test coverage issues
    -   Database migration conflicts
    -   Async/await errors
    -   Frontend test failures
    -   PDF generation errors
-   Added CI/CD Workflow section:
    -   Make targets overview
    -   Pre-commit hook pipeline details
    -   Quality gates documentation
    -   CI/CD best practices
-   Enhanced Quality Checklist with checkpoint protocol
-   Improved Table of Contents with new sections

**v1.0 (2025-10-30):**

-   Initial comprehensive guide
-   Integrated with pre-commit rules
-   Added phase gate compliance
-   Added emergency procedures

---

**End of Claude AI Agent Guide**

Remember: Quality over speed. Follow the rules. Test thoroughly. Document everything.
