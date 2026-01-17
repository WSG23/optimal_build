# Optimal Build Handoff Playbook

## Purpose
- Give new owners and AI agents an immediate snapshot of where to resume work and how to execute within the documented process.
- Points to the authoritative sources so status stays consistent with `docs/all_steps_to_product_completion.md` (strategic + tactical).

## Mandatory Orientation (Read Before Planning)
1. [ui-status.md](planning/ui-status.md) – understand the UI constraints and standards.
2. `START_HERE.md` – confirms the official reading order and reinforces the single source of truth workflow.
3. `README.md` – onboarding note that requires `all_steps_to_product_completion.md` (including the Unified Execution Backlog) and [ai-agents/next_steps.md](ai-agents/next_steps.md).
4. `docs/all_steps_to_product_completion.md` – project status, acceptance criteria, progress ledger, and tactical backlog.
5. [ai-agents/next_steps.md](ai-agents/next_steps.md) – decision guide for picking the next task.
6. `CODING_RULES.md` and `CONTRIBUTING.md` – quality gates, coding standards, and testing workflow.

## Project Snapshot (updated 2025-10-17)
- Phase 1 (Agent Foundation) – 100% complete; live agent validation is the remaining loop before wider rollout.
- Phase 2 (Developer Foundation) – 10% complete overall; Phase 2A partially delivered, Phase 2C backend underway, other sub-phases not started.
- Phases 3+ (Architect, Engineer, Integrations, Mobile) – scoped, dependent on Phase 2 infrastructure, not started.

## Immediate Actions (Carry Over)
- Run and complete the agent live walkthroughs, capture findings inside the [Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work), and file follow-up tickets with `agent-validation` label.
- Keep `docs/all_steps_to_product_completion.md` as both the live status log and execution log—update the backlog + phase sections with every change.
- Maintain [Known Testing Issues](all_steps_to_product_completion.md#-known-testing-issues) when tests are skipped or harness limits surface during validation or development.

## Build Targets – Phase 2 (Developer Foundation)
- **2A Universal GPS Site Acquisition (20% started):** Backend + developer UI scaffolds exist; remaining work focuses on deeper condition insights, side-by-side scenario comparison, and manual inspection capture.
- **2B Asset-Specific Feasibility (not started):** Requires multi-asset optimizers (office, retail, residential, industrial, mixed-use) with heritage constraints and 3D massing updates.
- **2C Complete Financial Control & Modeling (backend 60% complete):** Needs asset-specific financial models, richer financing UI (equity vs debt, loan modeling, sensitivity), and privacy controls for developer data.
- **2D–2I (Team Coordination through Enhanced Export):** All marked not started; depend on 2A–2C foundations plus coordination infrastructure.

## Roadmap Beyond Phase 2
- **Phase 3 (Architect Workspace):** Requires developer coordination stack; unlocks compliance-first design review.
- **Phase 4 (Engineer Tooling) & Phase 5 (Integrations):** Build after architect workflows stabilize; some government API work can overlap with late Phase 2.
- **Phase 6+:** Collaboration and mobile optimization remain future initiatives once core role-based tooling is live.

## Workflow Guardrails
- Always run `make format` followed by `make verify` before presenting changes.
- Apply every rule in `CODING_RULES.md`; document temporary exceptions in `.coding-rules-exceptions.yml`.
- Provide explicit backend/frontend test commands and manual walkthrough steps with every delivery (see the mandatory testing checklist in [ai-agents/next_steps.md](ai-agents/next_steps.md)).
- **Note:** Pre-commit hooks automatically enforce `make format` and `make verify` checks when you commit. If hooks fail, fix violations before bypassing with `--no-verify`.

## When You Finish Work
- Update the [Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) immediately—move tasks, record blockers, and add completion context—then refresh the surrounding phase snapshot/dependencies in `docs/all_steps_to_product_completion.md`.
- Note resolved or new limitations in [Known Testing Issues](all_steps_to_product_completion.md#-known-testing-issues).
- Reference this playbook in handoff notes so future contributors know the orientation path and current targets.
