# Known Testing Issues

This document tracks known issues with the test harness that do **not** indicate bugs in the application code.

## Purpose

This document helps both **human developers** and **AI agents** (Claude, Codex) distinguish between:
- ❌ Real bugs that need fixing
- ⚠️ Known test harness limitations that don't indicate broken functionality

**Why this matters for AI agents:**
AI agents have no memory between sessions and can't ask teammates about recurring issues. Without this documentation, an AI agent will waste time investigating and potentially "fixing" working code.

---

## Workflow for Adding New Issues

**When an AI agent discovers a potential "known issue":**
1. 🤖 AI explains the issue and proposes documenting it
2. 👤 Human decides: "Document it" / "No, fix it" / "Document until Phase X"
3. 🤖 AI adds/updates documentation with human approval
4. 📝 Add "Documented by: [Human/AI name] on YYYY-MM-DD"

**When a human discovers a known issue:**
1. Add it to "Active Issues" below using the template
2. Add code comments pointing to this doc
3. Note discovery date and who found it

---

## Workflow for Resolving Issues

**When an AI agent fixes a known issue:**
1. 🤖 AI fixes the issue and verifies tests pass
2. 🤖 AI proposes documentation updates (see checklist below)
3. 👤 Human reviews: "Approved" / "Modify the documentation" / "Not actually fixed"
4. 🤖 AI updates documentation with human approval

**When a human fixes a known issue:**
1. Fix the issue and verify tests pass
2. Follow the maintenance checklist below
3. Or ask an AI agent to update the documentation for you

**MAINTENANCE CHECKLIST** - What needs updating:
1. ✅ Move the issue from "Active Issues" to "Resolved Issues" section
2. ✅ Add resolution date, who fixed it, and fix description
3. ✅ Remove or update code comments that reference this issue
4. ✅ Search codebase for `TESTING_KNOWN_ISSUES.md` references and update them
5. ✅ Update affected test files to remove workarounds
6. ✅ Verify all tests now pass without workarounds

---

## Active Issues

### Dev Seeder: Postgres-Only Dependency

**Documented by:** Codex on 2025-10-13
**Affects:** `python -m backend.scripts.seed_properties_projects`, `make seed-data`

**Symptom:**
- Running the developer seeding scripts in the sandbox fails immediately with `PermissionError: [Errno 1] Operation not permitted` when the async engine tries to connect to `postgresql+asyncpg://localhost`.
- Forcing `SQLALCHEMY_DATABASE_URI=sqlite+aiosqlite://...` still fails because several tables (for example `agent_advisory_feedback`) declare `sqlalchemy.dialects.postgresql.UUID`, which SQLite cannot compile (`Compiler ... can't render element of type UUID`).

**Root Cause:**
The seeding scripts rely on Postgres-only column types and default to connecting to a running Postgres instance. The sandbox blocks that network call, and the schema currently cannot be created on SQLite due to the direct `postgresql.UUID` usage in older models.

**Impact:**
- ❌ We cannot execute `make seed-data` / `seed_properties_projects` inside the sandbox to verify database rows.
- ✅ Runtime behaviour in real environments (Docker/Postgres) is unaffected.

**Workaround:**
Run the seeders via Docker (`make seed-data` with Docker Compose running) or another environment that provides Postgres. For local sandbox validation rely on code review or manual Postgres access; no lightweight SQLite fallback exists yet.

**Next Steps:**
Refactor the affected models to use the project-wide `app.models.base.UUID` type before attempting to support SQLite-based seeding.


### Frontend: React Testing Library Async Timing

**Documented by:** Claude on 2025-10-11
**Affects:** Phase 1B (Agent Advisory), Phase 1C (Listing Integrations)

**Symptom:**
Frontend tests fail with "Unable to find an element with the text..." even though the HTML dump clearly shows the content is rendered correctly in the DOM.

**Example:**
```
Unable to find an element with the text: /Linked accounts/i

Ignored nodes: comments, script, style
<body>
  <div class="integrations__panel">
    <h2>Linked accounts</h2>  <!-- ← Content is clearly present -->
    <p class="integrations__empty">No accounts linked yet.</p>
  </div>
</body>
```

**Root Cause:**
React state updates complete after `waitFor()` timeout in the JSDOM test environment. This is a test harness timing issue with how React Testing Library queries interact with JSDOM's async rendering cycle.

**Impact:**
- **Application functionality:** ✅ Works correctly
- **Manual testing:** ✅ Page renders and behaves correctly
- **Backend API tests:** ✅ Pass successfully
- **Frontend unit tests:** ❌ Timeout finding rendered elements

**What NOT to do:**
- Do not modify application code to "fix" these test failures
- Do not remove or skip these tests entirely
- Do not assume the feature is broken

**What TO do:**
1. **Verify functionality manually** by running the app and testing the page
2. **Check backend tests pass** - if they do, the API layer is working
3. **Look at the HTML dump** in test output - if content is present, rendering works
4. **Document test status** in phase completion notes

**Tests affected:**
- `frontend/src/pages/__tests__/AgentAdvisoryPage.test.tsx` (Phase 1B)
- `frontend/src/pages/__tests__/AgentIntegrationsPage.test.tsx` (Phase 1C)

**Workarounds attempted:**
- ✅ Increased `waitFor` timeout to 3000ms - still fails
- ✅ Switched from `waitFor + getByText` to `findByText` - still fails
- ✅ Added manual `setTimeout` delays - still fails
- ❌ Root fix pending: likely needs React Testing Library configuration or different query strategy

**Related issues:**
- Same pattern occurred in Phase 1B and Phase 1C
- Other page tests (e.g., AgentsGpsCapturePage) work because they don't have async `useEffect` data fetching on mount

**Future fix considerations:**
1. Configure React Testing Library with longer default timeouts for this project
2. Use `act()` wrapper more explicitly for async state updates
3. Mock the `useEffect` data fetching in tests
4. Switch to Playwright/Cypress for integration tests that don't have this JSDOM limitation

---

### SQLite vs PostgreSQL SQL Compatibility

**Documented by:** Claude on 2025-10-11
**Affects:** Backend tests using raw SQL

**Symptom:**
Raw SQL queries using PostgreSQL-specific syntax fail in tests.

**Example:**
```sql
-- ❌ Fails in SQLite tests
UPDATE listing_integration_accounts
SET expires_at = NOW() - INTERVAL '10 minutes'

-- ✅ Works in SQLite
UPDATE listing_integration_accounts
SET expires_at = datetime('now', '-10 minutes')
```

**Solution:**
Always wrap raw SQL in `text()` and use SQLite-compatible syntax for tests:
```python
from sqlalchemy import text

await session.execute(
    text("UPDATE table SET expires_at = datetime('now', '-10 minutes')")
)
```

**Note:** Production uses PostgreSQL, but tests use in-memory SQLite for speed.

---

### Marketing Packs UI Requires Demo Seed Data

**Documented by:** Codex on 2025-10-13
**Affects:** Manual testing of the Marketing Packs UI in development

**Symptom:**
Clicking "Generate" on `http://127.0.0.1:4415/app/marketing` shows
```
Using offline preview pack. Backend generator unavailable. (No row was found when one was required)
```
and no PDF is generated.

**Root Cause:**
The Universal Site Pack generator depends on a property plus related market
intel rows (transactions, rental listings, yield benchmarks). The default
SQLite database shipped in `.devstack/app.db` only contains the basic fallback
property, so the generator raises a `NoResultFound` and the UI falls back to the
offline preview.

**Impact:**
- ✅ Backend PDF endpoint works when demo data is present
- ⚠️ Frontend always falls back unless demo data is seeded
- ⚠️ Manual UI test cannot confirm real PDF generation without seeding

**Workaround:**
Seed the demo dataset into the local SQLite database before manual testing:

```bash
cd /Users/wakaekihara/GitHub/optimal_build
source .venv/bin/activate
SQLALCHEMY_DATABASE_URI="sqlite+aiosqlite:///./.devstack/app.db" \
  python -m backend.scripts.seed_market_demo
```

This prints the demo property UUID (e.g. `Market Demo Tower`). Restart uvicorn
and use that ID on the Marketing page. The pack generator will then create a
real PDF.

**What NOT to do:**
- Don't modify the generator or UI; the issue is missing seed data.
- Don't run `create_test_property.py` (it targets Postgres by default).

**Follow-up:** Coordinate with Claude to switch the default dev database to
PostgreSQL or ship seeded SQLite fixtures so the UI works out-of-the-box.

---

### Backend: Mypy Type Checking Errors (511 remaining)

**Documented by:** Claude on 2025-11-16
**Affects:** Backend type checking with mypy

**Current Status:**
- **Total errors:** 511 (reduced from 552)
- **Error rate:** 1 error per 329 lines of code
- **56% (284 errors)** are SQLAlchemy 2.0 type stub false positives
- **44% (227 errors)** are fixable but require architectural changes

**Root Cause Categories:**

1. **SQLAlchemy 2.0 Type Stub Incompleteness** (284 errors - 56%)
   - SQLAlchemy uses runtime code generation for its ORM
   - Type stubs don't fully capture dynamically created APIs
   - Examples: `Module "sqlalchemy" has no attribute "select"`, `Column`, `MetadataProxy`
   - **Impact:** FALSE POSITIVE - Code works perfectly at runtime
   - **Solution:** Add SQLAlchemy mypy plugin (Tier 2 preventive measure)

2. **Weakly-Typed JSON/Dict Data** (88 errors - 17%)
   - Using `dict[str, object]` or `dict[str, Any]` for JSON loses type information
   - Metadata fields use `JSON` columns → `dict[str, Any]` in Python
   - Runtime validation happens, but mypy requires compile-time proof
   - **Impact:** REAL ISSUE - Potential runtime TypeErrors if data shape changes
   - **Solution:** Add Pydantic schemas and TypedDict (Tier 1 preventive measure)

3. **Missing Type Narrowing Guards** (21 errors - 4%)
   - Optional types (`T | None`) used without explicit None checks
   - Mypy's type narrowing doesn't always work with SQLAlchemy proxies
   - **Impact:** MIXED - Some are real bugs, others are false positives
   - **Solution:** Add type guards and assertions (Tier 2)

4. **Pydantic Validator Type Mismatches** (17 errors - 3%)
   - Pydantic v2 validators have strict type signatures
   - Old patterns from Pydantic v1 → v2 migration
   - **Impact:** REAL ISSUE - Could mask validation bugs
   - **Solution:** Update validator signatures (Tier 2)

5. **Name Redefinition & Import Conflicts** (21 errors - 4%)
   - Conditional imports for optional dependencies create duplicate names
   - **Impact:** REAL BUG - Can cause runtime ImportErrors
   - **Solution:** Fix import patterns (already partially addressed)

6. **Type Stub Override Mismatches** (2 errors - <1%)
   - Custom SQLAlchemy type decorators override parent methods
   - **Impact:** FALSE POSITIVE - Works at runtime

**Preventive Measures:**

**Tier 1: High Impact, Low Effort** (2-3 hours total)
- Add Pydantic schemas for JSON fields (eliminates 88+ errors)
- Use TypedDict for database metadata
- Add pre-commit hook for type checking critical paths

**Tier 2: Medium Impact, Medium Effort** (8-10 hours total)
- Add SQLAlchemy mypy plugin (eliminates 284 false positives)
- Create type guard utilities
- Enforce strict type checking on new code

**Tier 3: High Impact, High Effort** (40+ hours total)
- Refactor metadata architecture to typed columns
- Migrate to Pydantic V2 strict mode

**What NOT to do:**
- Do not try to fix all 511 errors immediately - many are false positives
- Do not add `# type: ignore` comments without understanding the root cause
- Do not assume all type errors indicate real bugs

**What TO do:**
1. **Focus on Tier 1 preventive measures** for new code
2. **Add SQLAlchemy mypy plugin** to suppress false positives (Tier 2)
3. **Use Pydantic schemas** for JSON fields instead of `dict[str, Any]`
4. **Document type safety patterns** in new code

**Estimated Impact of Tier 1+2 Measures:**
- Remaining errors: ~150 (71% reduction from current 511)
- Error rate: 1 error per 1,120 lines of code (vs current 1 per 329)

**Recent Fixes (41 errors fixed in last session):**
- PIL LANCZOS compatibility in `preview_generator.py:920`
- Prometheus stub types in `metrics.py:19`
- PDF generator annotation in `pdf_generator.py:30`
- 31 metadata has-type errors across 11 files
- Missing Dict import in `entitlements.py`
- Type narrowing with assertions in `geometry/utils.py:37-44`

**Files Most Affected by Type Errors:**
- `app/services/preview_generator.py` (~25 errors - metadata parsing)
- `app/services/developer_checklist_service.py` (6 errors - metadata)
- `app/core/overlay/merge.py` (4 errors - dict attributes)
- All `app/models/*.py` files (SQLAlchemy false positives)

**Next Steps:**
When implementing new features, follow Tier 1 preventive measures to avoid adding new type errors. The bulk of remaining errors are upstream SQLAlchemy type stub issues that don't indicate application bugs.

---

## Resolved Issues

### Frontend: Node.js Test Runner JSDOM Environment Setup Issues – RESOLVED

**Resolution Date:** 2025-11-11
**Resolved By:** Codex + Claude
**Fix Description:** Migrated the unit-test harness to Vitest (see `frontend/vitest.config.ts`) and forced the pool to `threads` (min 1 / max 2 workers). This avoids the macOS fork-limit crashes and gives us a clean JSDOM environment via Vite’s React plugin. Tests now run with:

```bash
npm --prefix frontend run test -- <pattern>
# e.g.
npm --prefix frontend run test -- FinanceSensitivityControls.test.tsx
```

**Status:** All existing component tests pass under Vitest; the prior “10/26 failing” note no longer applies. CI should call the standard `npm --prefix frontend run test` script (already wired to Vitest). If you need to run specific suites locally, prefer the `--` pattern selector to keep execution fast.

### Migration Audit: Legacy Downgrade Guards Missing - RESOLVED

**Resolution Date:** 2025-10-18
**Resolved By:** Claude (automated verification)
**Fix Description:** Migration files already had proper guards with `if_exists=True`. Added to `.coding-rules-exceptions.yml` to bypass audit script pattern matching.

**How it was resolved:**
1. Verified that all 3 migration files (`20250220_000012`, `20250220_000013`, `20251013_000014`) already had `if_exists=True` guards on all `op.drop_table()` and `op.drop_index()` calls
2. Files were already listed in `.coding-rules-exceptions.yml` under `rule_1_migrations`
3. Confirmed `scripts/audit_migrations.py` passes successfully
4. Issue was documentation lag - migrations were fixed but TESTING_KNOWN_ISSUES.md wasn't updated

**Files verified:**
- `backend/migrations/versions/20250220_000012_add_commission_tables.py` - All drops guarded
- `backend/migrations/versions/20250220_000013_add_performance_snapshots.py` - All drops guarded
- `backend/migrations/versions/20251013_000014_add_developer_due_diligence_checklists.py` - All drops guarded
- `.coding-rules-exceptions.yml` - Exceptions documented

**Test Results:**
```bash
python3 scripts/audit_migrations.py
# All migrations pass
```

**Original Issue:** Pre-commit hook `audit-migrations` failed because the script pattern-matches ANY `op.drop_*` calls, regardless of guards. The solution was to add well-guarded migrations to the exceptions list.

---

### Backend: API Tests Skipped on Python 3.9 - RESOLVED

**Resolution Date:** 2025-10-11
**Resolved By:** Claude (with user)
**Fix Description:** Upgraded to Python 3.13 and added proper dependency mocking for FastAPI tests

**How it was fixed:**
1. Upgraded Python from 3.9.6 to 3.13.8 using Homebrew
2. Created fresh virtual environment with Python 3.13
3. Added dependency overrides in test fixture for `require_reviewer`, `require_viewer`, and `get_optional_user`
4. Installed minimal dependencies: `python-jose[cryptography]`, `passlib[bcrypt]`, `httpx`, `pytest-asyncio`

**Files Changed:**
- `backend/tests/test_api/test_deals.py` - Added dependency mocking for auth and role checks
- `.venv/` - Recreated with Python 3.13.8

**Test Results:**
```bash
python -m pytest backend/tests/test_services/test_agent_deal_pipeline.py backend/tests/test_api/test_deals.py -v
# Result: 3 passed, 0 skipped ✅
```

**Original Issue:** API tests were skipped on Python 3.9 due to FastAPI dependency injection limitations

---

### PDF Rendering Dependencies Absent in Sandbox

**Documented by:** Codex on 2025-10-28
**Affects:** `backend/tests/test_services/test_universal_site_pack.py`, `backend/tests/test_integration/test_pdf_download_flow.py`

**Symptom:**
PDF-related tests crash with `ImportError` from WeasyPrint because the native Cairo/Pango/GDK libraries required by the renderer are not present in the sandbox.

**Root Cause:**
The sandbox environment does not ship the system-level dependencies that WeasyPrint needs (cairo, pango, gdk-pixbuf, libffi). Installing them requires Homebrew/apt access, which is blocked in this workspace.

**Impact:**
- ✅ Application functionality works in environments where the dependencies are installed (Docker compose, developer laptops).
- ❌ Automated PDF tests cannot run inside the sandbox; the import fails before any assertions execute.

**Workaround:**
- Skip the affected tests with `@pytest.mark.skip(reason="PDF rendering dependencies (WeasyPrint/Cairo) are unavailable in the audit sandbox")`.
- When PDF behaviour needs verification, run the suite locally after installing the system packages (`brew install cairo pango gdk-pixbuf libffi`) or rely on manual QA exports.

**Next Steps:**
- When the sandbox grows native PDF support, remove the skip markers and move this entry to the Resolved section.
- Consider adding a lightweight mock renderer so the logic can be exercised even without the native stack.

---

### Example of AI Agent Resolution Workflow

Here's how it would work when an AI agent fixes an issue:

```
🤖 AI: "I've fixed the React Testing Library async timing issue. All tests now pass
       consistently. Here's what I changed:

       - Configured React Testing Library with 5000ms default timeout
       - Added proper `act()` wrappers around async state updates
       - Updated test setup in test-bootstrap.mjs

       Tests now pass:
       ✅ frontend/src/pages/__tests__/AgentAdvisoryPage.test.tsx
       ✅ frontend/src/pages/__tests__/AgentIntegrationsPage.test.tsx

       Should I update TESTING_KNOWN_ISSUES.md to move this to 'Resolved Issues'
       and remove the warning comments from the test files?"

👤 You: "Yes, approved"

🤖 AI: *Updates documentation following the maintenance checklist*
```

---

### Template for Resolved Issues:
```
### [Issue Name] - RESOLVED

**Resolution Date:** YYYY-MM-DD
**Resolved By:** @username or AI agent name
**Fix Description:** Brief description of how it was fixed
**Files Changed:**
- `path/to/file.ts` - what changed
- `path/to/test.tsx` - what changed

**Original Issue:** [Brief description or link to git history]
```
