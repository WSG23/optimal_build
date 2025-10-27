# Claude Instructions

You are Claude, a coding assistant working alongside Codex inside the `optimal_build` repository.
Follow these guardrails when you take over the keyboard:

## 🚀 MANDATORY: Read This First

**Before starting any work:**

1. **Read [`START_HERE.md`](START_HERE.md)** - Contains:
   - Reading order for all documentation
   - **COMPLETE inventory of all 20 instruction files** (if asked "list all docs", this is the answer)
   - Project context and testing guidelines

2. **Then read [`docs/handoff_playbook.md`](docs/handoff_playbook.md)** - Contains:
   - Current project status snapshot (Phase 1 100% complete, Phase 2 10% complete)
   - Links to all authoritative sources (feature_delivery_plan_v2.md, NEXT_STEPS, CODING_RULES, etc.)
   - Immediate actions to carry forward from previous session

**⚠️ IMPORTANT:** If asked to "list all instruction files" or "list all documentation", do NOT use grep/find. Instead, read the "Complete Documentation Inventory" section in START_HERE.md - it's the authoritative list.

This ensures you pick up exactly where the previous agent left off.

1. **Environment**
   - Repository root: `/Users/wakaekihara/Documents/GitHub/optimal_build`.
   - Sandbox: `workspace-write` (you may edit files within the repo).
   - Network: `restricted` — assume outbound requests will be blocked unless explicitly approved.
   - Approval policy: `on-request`; ask for escalation when a command needs it (e.g., writing outside the repo, network access, destructive actions).

2. **Shell usage**
   - Invoke commands through the harness (e.g. `bash -lc "<cmd>"`).
   - Always set the `workdir` parameter; avoid `cd` unless required.
   - Prefer `rg`/`rg --files` for search; fall back only if they are unavailable.
   - Keep commands reproducible and concise; note when you skip a step (missing deps, no access, etc.).

3. **Coding Rules Enforcement (MANDATORY - NO EXCEPTIONS)**
   - **BEFORE writing code:** Run `make ai-preflight` to verify the current codebase state passes all checks.
   - **Read [CODING_RULES.md](CODING_RULES.md)** - All 7 rules apply to AI-generated code.
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
   - **CI/CD Enforcement:**
     - All PRs are automatically checked by GitHub Actions
     - Code that fails `make verify` will be REJECTED by CI
   - Key rules for AI agents:
     - Rule 1: Never edit existing migration files
     - Rule 2: Use async/await for all database/API operations
     - Rule 3: Pre-commit hooks handle formatting automatically
     - Rule 6: Follow import ordering (stdlib → third-party → local)
     - Rule 7: No unused variables, proper exception chaining
     - Rule 8: **MANDATORY testing instructions** after completing ANY feature (backend tests, frontend tests, UI manual steps)
     - Rule 9: Index all foreign keys and frequently queried columns
     - Rule 10: All new features MUST have automated tests (>80% coverage for critical paths)
     - Rule 11: Security practices (authentication, input validation, no SQL injection)

4. **Editing guidelines**
   - Default to ASCII; introduce non-ASCII only if already present and necessary.
   - Add comments sparingly—only to clarify complex logic.
   - Never undo or overwrite user changes you did not make; if unexpected edits appear, pause and ask.
   - Ensure new files are saved within the repo (respect writable roots).
   - Follow Python import ordering: stdlib → third-party → local; `import X` before `from X import Y`; alphabetical within groups; combine imports from same module (see [CODING_RULES.md](CODING_RULES.md#6-python-import-ordering-and-formatting)).

5. **Code & review etiquette**
   - Be precise about file paths (use inline `path:line` references).
   - When reviewing, lead with findings (bugs, regressions, missing tests) before summaries.
   - Validate work with focused tests or commands whenever practical; mention any gaps.
   - **MANDATORY:** After completing ANY feature, ALWAYS provide test commands to the user (backend tests, frontend tests, manual UI testing steps). See `docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md` section "MANDATORY TESTING CHECKLIST" for the template.
   - **MANDATORY:** When you fix a known testing issue, update `TESTING_KNOWN_ISSUES.md` to move it from "Active Issues" to "Resolved Issues" with resolution details. When you discover a test harness limitation (not a real bug), propose adding it to "Active Issues" for future AI agents to avoid wasting time on it.

6. **Collaboration**
   - Mirror the user's tone: concise, helpful, engineering-focused.
   - Offer next steps only when they add value (tests to run, possible follow-up tasks).
   - Summaries should be short and actionable; avoid unnecessary formatting.

7. **Project workflows**
   - `make dev` boots Docker (if available) and launches backend (`:9400`), frontend (`:4400`), and admin (`:4401`) services; use `make status` to confirm PIDs.
   - `make stop` tears down local process supervisors; `make down` stops Docker Compose; `make reset` rebuilds the stack and reseeds data.
   - `make verify` chains format, lint, and `pytest`; use `make test` for a quick backend-only run or `make test-aec` to exercise the AEC integration (requires frontend npm tests).
   - Set `REGSTACK_DB` before `make regstack-ingest` or call `python -m scripts.ingest --jurisdiction sg_bca --since 2025-01-01 --store <url>` directly for ingestion experiments.
   - Frontend E2E lives under `frontend/`; run `pnpm --dir frontend test:e2e` (with `PLAYWRIGHT_SKIP_BROWSER_INSTALL=1` when offline).

Keep these notes handy so you can jump in quickly when the user swaps you in.
