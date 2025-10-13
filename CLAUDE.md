# Claude Instructions

You are Claude, a coding assistant working alongside Codex inside the `optimal_build` repository.
Follow these guardrails when you take over the keyboard:

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

3. **Editing guidelines**
   - Default to ASCII; introduce non-ASCII only if already present and necessary.
   - Add comments sparingly—only to clarify complex logic.
   - Never undo or overwrite user changes you did not make; if unexpected edits appear, pause and ask.
   - Ensure new files are saved within the repo (respect writable roots).
   - Follow Python import ordering: stdlib → third-party → local; `import X` before `from X import Y`; alphabetical within groups; combine imports from same module (see [CODING_RULES.md](CODING_RULES.md#6-python-import-ordering-and-formatting)).

4. **Code & review etiquette**
   - Be precise about file paths (use inline `path:line` references).
   - When reviewing, lead with findings (bugs, regressions, missing tests) before summaries.
   - Validate work with focused tests or commands whenever practical; mention any gaps.
   - **MANDATORY:** After completing ANY feature, ALWAYS provide test commands to the user (backend tests, frontend tests, manual UI testing steps). See `docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md` section "MANDATORY TESTING CHECKLIST" for the template.
   - **MANDATORY:** When you fix a known testing issue, update `TESTING_KNOWN_ISSUES.md` to move it from "Active Issues" to "Resolved Issues" with resolution details. When you discover a test harness limitation (not a real bug), propose adding it to "Active Issues" for future AI agents to avoid wasting time on it.

5. **Collaboration**
   - Mirror the user's tone: concise, helpful, engineering-focused.
   - Offer next steps only when they add value (tests to run, possible follow-up tasks).
   - Summaries should be short and actionable; avoid unnecessary formatting.

6. **Project workflows**
   - `make dev` boots Docker (if available) and launches backend (`:9400`), frontend (`:4400`), and admin (`:4401`) services; use `make status` to confirm PIDs.
   - `make stop` tears down local process supervisors; `make down` stops Docker Compose; `make reset` rebuilds the stack and reseeds data.
   - `make verify` chains format, lint, and `pytest`; use `make test` for a quick backend-only run or `make test-aec` to exercise the AEC integration (requires frontend npm tests).
   - Set `REGSTACK_DB` before `make regstack-ingest` or call `python -m scripts.ingest --jurisdiction sg_bca --since 2025-01-01 --store <url>` directly for ingestion experiments.
   - Frontend E2E lives under `frontend/`; run `pnpm --dir frontend test:e2e` (with `PLAYWRIGHT_SKIP_BROWSER_INSTALL=1` when offline).

Keep these notes handy so you can jump in quickly when the user swaps you in.
