# Codex Instructions

You are Codex, an AI coding assistant working alongside Claude inside the `optimal_build` repository.
Follow these guardrails when you implement features and changes.

## 🚀 MANDATORY: Read This First

**Before starting any work:**

1. **Read [`START_HERE.md`](START_HERE.md)** - Contains:
   - Reading order for all documentation
   - **COMPLETE inventory of all 20 instruction files** (if asked "list all docs", this is the answer)
   - Project context and testing guidelines

2. **Then read [`docs/handoff_playbook.md`](docs/handoff_playbook.md)** - Contains:
   - Current project status snapshot (Phase 1 100% complete, Phase 2 10% complete)
   - Links to all authoritative sources (all_steps_to_product_completion.md, [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work), NEXT_STEPS, CODING_RULES, etc.)
   - Immediate actions to carry forward from previous session

**⚠️ IMPORTANT:** If asked to "list all instruction files" or "list all documentation", do NOT use grep/find. Instead, read the "Complete Documentation Inventory" section in START_HERE.md - it's the authoritative list.

This ensures you pick up exactly where the previous agent left off.

---

## 1. Environment

- **Repository root**: `/Users/wakaekihara/Documents/GitHub/optimal_build`
- **Sandbox**: `workspace-write` (you may edit files within the repo)
- **Network**: `restricted` — assume outbound requests will be blocked unless explicitly approved
- **Approval policy**: `on-request`; ask for escalation when a command needs it

---

## 2. Coding Rules Enforcement (MANDATORY - NO EXCEPTIONS)

- **BEFORE writing code:** Run `make ai-preflight` to verify the current codebase state passes all checks
- **Read [CODING_RULES.md](CODING_RULES.md)** - All 11 rules apply to AI-generated code
- **AFTER writing code:**
  1. Run `make verify` (checks all rules)
  2. Fix ALL violations before committing
  3. Commit your changes (pre-commit hooks will auto-format)
  4. **NEVER use `git commit --no-verify`** - this bypasses quality checks and is FORBIDDEN
- **If `make verify` fails:**
  - You MUST fix the violations
  - You CANNOT commit until all checks pass
  - You CANNOT ask the user to commit broken code
- **Formatting is Automatic:**
  - Pre-commit hooks automatically run black, ruff, and prettier on commit
  - You don't need to run `make format` manually
  - If you want to format before committing: `pre-commit run --all-files`

Key rules for AI agents:
- Rule 1: Never edit existing migration files
- Rule 2: Use async/await for all database/API operations
- Rule 3: Pre-commit hooks handle formatting automatically
- Import ordering (Python): stdlib → third-party → local (see `CODING_RULES.md` “Python Import Ordering and Formatting”)
- Rule 7: No unused variables, proper exception chaining
- **Rule 8: MANDATORY testing instructions** - After completing ANY feature, provide backend tests, frontend tests, AND UI manual test steps to the user
- Rule 9: Index all foreign keys and frequently queried columns
- Rule 10: All new features MUST have automated tests (>80% coverage for critical paths)
- Rule 11: Security practices (authentication, input validation, no SQL injection)

---

## 3. MANDATORY TESTING CHECKLIST ⚠️ CRITICAL

**After completing ANY feature implementation, you MUST run AND report test results.**

### Rule: ALWAYS Run Tests Matching Your Changes

**If you changed backend files** → Run backend tests
**If you changed frontend files** → Run frontend tests
**If you changed BOTH** → Run BOTH test suites

### Backend Test Commands

**When you modify ANY backend file** (models, services, API, migrations):

```bash
# Run tests for the specific feature you changed
/Users/wakaekihara/GitHub/optimal_build/.venv/bin/python -m pytest \
  backend/tests/test_api/test_[your_feature].py \
  backend/tests/test_services/test_[your_feature].py \
  -v

# Example: If you changed developer condition reports
/Users/wakaekihara/GitHub/optimal_build/.venv/bin/python -m pytest \
  backend/tests/test_api/test_developer_condition_report.py \
  backend/tests/test_services/test_developer_condition_service.py \
  -v
```

**When you add a database migration:**

```bash
# Test migration up/down
/Users/wakaekihara/GitHub/optimal_build/.venv/bin/python -m alembic upgrade head
/Users/wakaekihara/GitHub/optimal_build/.venv/bin/python -m alembic downgrade -1
/Users/wakaekihara/GitHub/optimal_build/.venv/bin/python -m alembic upgrade head
```

### Frontend Test Commands

**When you modify ANY frontend file** (components, pages, API clients):

```bash
# Always run linting
npm --prefix frontend run lint

# Run type checking
npm --prefix frontend run type-check

# Run unit tests (if they exist for the component)
NODE_ENV=test node --test --import tsx --import ./scripts/test-bootstrap.mjs \
  frontend/src/app/pages/__tests__/[YourPage].test.tsx
```

### UI Manual Testing Instructions (MANDATORY for UI changes)

**When you modify ANY UI component, page, or user-facing feature, you MUST provide manual testing steps to the user:**

```markdown
Manual UI testing steps:
1. Start the dev server: make dev
2. Navigate to: http://localhost:4400/#/[route]
3. Test action: [specific interaction, e.g., "Click 'Add Scenario' button"]
4. Verify: [expected outcome, e.g., "Modal opens with empty form"]
5. Test edge case: [e.g., "Submit form with empty name field"]
6. Verify: [expected validation, e.g., "Error message 'Name is required' appears"]
```

**Example:**
```markdown
Manual UI testing steps for finance scenario privacy:
1. Start dev server: make dev
2. Navigate to: http://localhost:4400/#/finance/scenarios
3. Create new scenario with name "Test Private Scenario"
4. Toggle "Make Private" checkbox ON
5. Click "Save" button
6. Verify: Scenario appears in list with lock icon 🔒
7. Logout and login as different user (user2@example.com)
8. Navigate to: http://localhost:4400/#/finance/scenarios
9. Verify: "Test Private Scenario" does NOT appear in list (privacy working)
```

**Why this matters:** Automated tests don't catch UI/UX issues, accessibility problems, or visual regressions. The user needs specific steps to verify your UI changes work correctly.

### Example Test Report Format

After running tests, ALWAYS report results like this:

```
Tests: Backend ✅, Frontend ✅, UI Manual ⚠️ (user to verify)

Backend tests:
$ pytest backend/tests/test_api/test_developer_condition_report.py -v
✅ test_create_condition_report_with_inspector ... PASSED
✅ test_create_condition_report_with_attachments ... PASSED
✅ test_get_condition_report_includes_metadata ... PASSED
All 3 tests passing

Frontend tests:
$ npm --prefix frontend run lint
✅ No new linting errors (existing warnings only)

$ npm --prefix frontend run type-check
✅ No type errors

UI Manual testing steps (for user to verify):
1. Start dev server: make dev
2. Navigate to http://localhost:4400/#/site-acquisition
3. Click "Add Condition Report" button
4. Fill in "Inspector Name" field with "John Doe"
5. Verify: Inspector name appears in report summary
6. Save report and reload page
7. Verify: Inspector name persists after reload
```

### When Tests Fail

**If tests fail:**
1. ❌ DO NOT report "tests complete" - report the failure
2. Fix the failing tests
3. Re-run tests until they pass
4. ONLY THEN report success

---

## 4. File Change Tracking

**When you modify files, ALWAYS specify which files changed:**

```
Files changed:
- backend/app/models/developer_condition.py (added inspector_name field)
- backend/app/services/developer_condition_service.py (added validation logic)
- backend/tests/test_services/test_developer_condition_service.py (added test coverage)
- frontend/src/app/pages/site-acquisition/SiteAcquisitionPage.tsx (UI updates)
```

This helps Claude know what to commit and what tests to verify.

---

## 5. Testing Decision Tree

Use this to decide what tests to run:

```
Did I change files in backend/app/models/ ?
└─> YES → Run pytest backend/tests/test_services/test_[model]*.py

Did I change files in backend/app/services/ ?
└─> YES → Run pytest backend/tests/test_services/test_[service]*.py

Did I change files in backend/app/api/ ?
└─> YES → Run pytest backend/tests/test_api/test_[endpoint]*.py

Did I add a migration in backend/migrations/versions/ ?
└─> YES → Run alembic upgrade head (test it applies)

Did I change files in frontend/src/ ?
└─> YES → Run npm --prefix frontend run lint
         AND npm --prefix frontend run type-check

Did I change files in frontend/src/app/pages/ ?
└─> YES → Check for frontend/src/app/pages/__tests__/[Page].test.tsx
         If exists, run: NODE_ENV=test node --test ...
```

---

## 6. Common Mistakes to Avoid

### ❌ WRONG: Only running frontend tests for backend+frontend changes
```
Tests: npm --prefix frontend run lint
✅ No new linting errors
```

**Problem:** You changed backend files but didn't test them!

### ✅ RIGHT: Run BOTH test suites
```
Tests: Backend ✅, Frontend ✅

Backend:
$ pytest backend/tests/test_services/test_developer_condition_service.py -v
✅ All 5 tests passing

Frontend:
$ npm --prefix frontend run lint
✅ No new linting errors
```

---

## 7. Integration with Claude

When you finish implementing a feature:
1. Run all applicable tests (backend + frontend)
2. Report test results with command output
3. List all files you changed
4. Claude will verify and commit the changes

**Claude relies on YOUR test reports to know if the code works!**

If you skip tests or run the wrong tests, Claude might commit broken code.

### 7.1 Single-Writer Rule (MANDATORY)

This repo is regularly worked on by both Codex and Claude at the same time. Concurrent writes to the same branch silently overwrite each other — we've watched it happen, and the recovery is expensive. **Only one AI agent edits a given branch at a time. The other reads, reviews, or runs tests but does not write.**

Before you open any write tool on a session:

```bash
python3 scripts/agent_session.py start codex --intent "<short description of what you're about to do>"
```

If it exits non-zero, another agent owns the branch. **Stop. Do not edit any file.** Surface the lock contents to the user (the script prints them) and wait for an explicit handoff. Do not `clear --force` to take a lock you didn't earn — the visible handoff is the entire point.

When you're done editing for the session:

```bash
python3 scripts/agent_session.py stop
```

For Codex → Claude handoffs after a feature is implemented, the recommended sequence is:

1. Codex: `agent_session.py start codex --intent "<feature>"` → edit → tests → `agent_session.py stop`. Codex reports the file list and test output to the user.
2. Claude: `agent_session.py start claude --intent "review and commit <feature>"` → review → commit → `agent_session.py stop`.

Single-writer invariant is preserved across the handoff.

For genuinely parallel streams of work (Codex feature A on one branch, Claude refactor B on another), use git worktrees so each agent has its own filesystem and its own `.agent-active`:

```bash
git worktree add ../optimal_build-codex codex/my-branch
git worktree add ../optimal_build-claude claude/my-branch
```

Full rules, failure modes, and the worktree-per-agent pattern are documented in [multi_agent_coordination.md](multi_agent_coordination.md). This rule is also Core Directive 6 in [MCP.md](../../MCP.md).

---

## 8. Quick Reference

| You Changed | You Must Run |
|-------------|--------------|
| `backend/app/models/*.py` | `pytest backend/tests/test_services/...` |
| `backend/app/services/*.py` | `pytest backend/tests/test_services/...` |
| `backend/app/api/*.py` | `pytest backend/tests/test_api/...` |
| `backend/migrations/versions/*.py` | `alembic upgrade head` |
| `frontend/src/**/*.tsx` | `npm --prefix frontend run lint` + `type-check` |
| Backend + Frontend | ALL OF THE ABOVE |

---

## 9. Example: Full Feature Implementation

**Scenario:** Adding `inspector_name` field to condition reports

**Files Changed:**
- `backend/migrations/versions/20251020_000016_add_inspection_metadata.py` (new)
- `backend/app/models/developer_condition.py`
- `backend/app/services/developer_condition_service.py`
- `backend/app/api/v1/developers.py`
- `backend/tests/test_api/test_developer_condition_report.py`
- `backend/tests/test_services/test_developer_condition_service.py`
- `frontend/src/app/pages/site-acquisition/SiteAcquisitionPage.tsx`
- `frontend/src/api/siteAcquisition.ts`

**Tests You MUST Run:**

```bash
# Backend tests (MANDATORY - you changed backend files)
/Users/wakaekihara/GitHub/optimal_build/.venv/bin/python -m pytest \
  backend/tests/test_api/test_developer_condition_report.py \
  backend/tests/test_services/test_developer_condition_service.py \
  -v

# Migration test (MANDATORY - you added a migration)
/Users/wakaekihara/GitHub/optimal_build/.venv/bin/python -m alembic upgrade head

# Frontend tests (MANDATORY - you changed frontend files)
npm --prefix frontend run lint
npm --prefix frontend run type-check
```

**Report Format:**

```
Tests: Backend ✅, Frontend ✅

Backend tests:
$ pytest backend/tests/test_api/test_developer_condition_report.py -v
✅ test_create_report_with_inspector ... PASSED
✅ test_get_report_includes_inspector ... PASSED
✅ test_update_report_inspector ... PASSED

$ pytest backend/tests/test_services/test_developer_condition_service.py -v
✅ test_validate_inspector_name ... PASSED
✅ test_strip_inspector_whitespace ... PASSED

Migration test:
$ alembic upgrade head
✅ Migration 20251020_000016 applied successfully

Frontend tests:
$ npm --prefix frontend run lint
✅ No new linting errors (existing warnings only: unused type in IntegrationsPage)

$ npm --prefix frontend run type-check
✅ No type errors

Files changed:
- backend/migrations/versions/20251020_000016_add_inspection_metadata.py (new)
- backend/app/models/developer_condition.py
- backend/app/services/developer_condition_service.py
- backend/app/api/v1/developers.py
- backend/tests/test_api/test_developer_condition_report.py
- backend/tests/test_services/test_developer_condition_service.py
- frontend/src/app/pages/site-acquisition/SiteAcquisitionPage.tsx
- frontend/src/api/siteAcquisition.ts
```

---

## 10. Project Workflows

- `make dev` - Boots Docker and launches backend (:9400), frontend (:4400), admin (:4401)
- `make status` - Check service PIDs
- `make test` - Quick backend-only test run
- `make verify` - Chains format, lint, and pytest
- `make stop` - Stop processes
- `make down` - Stop Docker Compose
- `make reset` - Rebuild stack and reseed data

---

**Remember: Testing is NOT optional. It's a requirement for every change you make.**
