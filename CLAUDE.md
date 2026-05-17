# optimal_build — Claude Agent Guide

## Critical rules (build will fail if violated)

**1. Never edit existing migrations.** Create new ones with `cd backend && alembic revision -m "..."`. Use `sa.String()` for ENUM columns, not `sa.Enum()`. SQL enum values must match Python enum `.value` exactly (case-sensitive).

**2. All database and API code is async.** `async def`, `AsyncSession`, `await db.execute(select(...))`. Never `db.query(...).first()`.

**3. Before every commit, run `make format && make verify`.** Both must pass. `make hooks` runs pre-commit locally if you want to check first.

**4. Frontend uses design tokens, never hardcoded values.** `var(--ob-space-100)`, `var(--ob-radius-sm)`, theme palette colors. No `px`, no hex codes, no MUI `spacing={2}`. Cards use `--ob-radius-sm` (4px), buttons `--ob-radius-xs` (2px), modals `--ob-radius-lg` (8px). See [frontend/UI_STANDARDS.md](frontend/UI_STANDARDS.md) and [frontend/UX_ARCHITECTURE.md](frontend/UX_ARCHITECTURE.md).

**5. After finishing a feature, give the user runnable test commands** — backend pytest path, frontend test path (if applicable), and numbered manual UI steps. Don't just say "done."

**6. Single-writer per branch — acquire the agent lock before editing.** This repo is also worked on by Codex and IDE-side linters; concurrent writes silently overwrite each other. Before opening any write tool, run `python3 scripts/agent_session.py start claude --intent "<short description>"`. If it exits non-zero, another agent owns the branch — stop, surface the lock contents to the user, and wait for an explicit handoff. Run `stop` when done. Full rules and patterns in [docs/ai-agents/multi_agent_coordination.md](docs/ai-agents/multi_agent_coordination.md).

The full ruleset is in [CODING_RULES.md](CODING_RULES.md) (12 rules). Pre-commit hooks enforce most of them; read it when a hook fails or before non-trivial work.

## Project orientation

| Question | File |
|----------|------|
| What should I build next? | [docs/ai-agents/next_steps.md](docs/ai-agents/next_steps.md) |
| What's already shipped? | [docs/all_steps_to_product_completion.md](docs/all_steps_to_product_completion.md) |
| What's the product? | [docs/planning/features.md](docs/planning/features.md) |
| Known test failures (not bugs) | [docs/all_steps_to_product_completion.md#-known-testing-issues](docs/all_steps_to_product_completion.md#-known-testing-issues) |

## Working style

**Default role on shared branches: reviewer and committer.** This repo also has Codex running. The intended division of labour is *Codex implements; Claude reviews, runs verification, and commits* (see [docs/ai-agents/codex.md §7](docs/ai-agents/codex.md)). When the user hands you a feature, default to the review/commit role: pull up Codex's diff, run `make verify`, tighten types, fix anything in scope per the rule below, then commit. Take the implementer role only when the user gives it to you explicitly, or when no Codex session is active. Two general-purpose writers on the same branch will collide — see [docs/ai-agents/multi_agent_coordination.md](docs/ai-agents/multi_agent_coordination.md).

**Scope expansion is good — silent scope expansion is not.** If you spot an out-of-scope bug, typo, dead import, missing `await`, or stale doc reference, fix it. Then mention it in your summary. Exception: anything architectural, behavior-changing, or risky — surface first.

**Checkpoint before large or irreversible work.** Examples: refactors touching >5 files, schema changes, anything that breaks an API contract, scope creep you discovered mid-task. State the plan, list the files, ask to proceed.

**Phase completion gates (Rule 12).** Don't mark a phase `✅ COMPLETE` in `docs/all_steps_to_product_completion.md` while it still has `[ ]`, `🔄`, or `❌` markers, missing "Files Delivered" files, or non-✅ test status. Ask the user before flipping the marker. The `check_phase_gate.py` pre-commit hook catches violations.

## Code quality bar

After implementing, scan for and fix:
- Functions >30 lines (likely doing too much)
- Logic duplicated 3+ times (extract)
- TypeScript `any` (replace with real types)
- Components with >3 loose props (group into an object)
- Missing error handling on `async` operations
- Foreign keys without indexes (Rule 9)
- Endpoints without `Depends(get_current_user)` or authorization checks (Rule 11)

Run `/simplify` before presenting non-trivial changes.

## Communication

- Reference code with clickable links: `[finance.py:142](backend/app/api/v1/finance.py#L142)`.
- Commit messages: imperative + why. "Add compliance scoring to surface regulatory violations" — not "Added compliance_score field."
- No apology filler. No trailing recap of what the diff already shows.

## Design context

**Users.** Commercial real estate professionals — agents marketing properties, developers running feasibility and finance workflows. Data-literate, long sessions, high-stakes decisions. Singapore, Hong Kong, NZ, Seattle, Toronto. They respect density and distrust tools that oversimplify.

**Brand.** Sharp, assured, technical. Engineering-grade precision with institutional gravitas. A command surface for experts — Bloomberg Terminal, not generic SaaS.

**Aesthetic.** Mission-control density. Dark and light both first-class. Custom display font for headings, system fonts for body. "Square Cyber-Minimalism" — Obsidian & Sapphire palette, `--ob-*` tokens, sharp radii (2–4px). Anti-references: government portals, crypto neon, soft rounded UIs.

**Principles.**
1. Density over decoration — every pixel earns its place.
2. Earned complexity — show the full picture; progressive disclosure is for onboarding, not hiding capability.
3. Structured authority — hierarchy through typography, spacing, color restraint.
4. Institutional trust — timeless, no trends.
5. Dual-mode parity — neither theme is degraded.
