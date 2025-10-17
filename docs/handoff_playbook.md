# Optimal Build Handoff Playbook

## Purpose
- Give new owners and AI agents an immediate snapshot of where to resume work and how to execute within the documented process.
- Points to the authoritative sources so status stays consistent with `docs/feature_delivery_plan_v2.md`.

## Mandatory Orientation (Read Before Planning)
1. `UI_STATUS.md` – understand the test-harness UI constraints and avoid polishing scaffolding.
2. `START_HERE.md` – confirms the official reading order and reinforces the single source of truth workflow.
3. `README.md` – onboarding note that requires `feature_delivery_plan_v2.md` and `NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md`.
4. `docs/feature_delivery_plan_v2.md` – project status, acceptance criteria, progress ledger.
5. `docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md` – decision guide for picking the next task.
6. `CODING_RULES.md` and `CONTRIBUTING.md` – quality gates, coding standards, and testing workflow.

## Project Snapshot (updated 2025-10-17)
- Phase 1 (Agent Foundation) – 100% complete; live agent validation is the remaining loop before wider rollout.
- Phase 2 (Developer Foundation) – 10% complete overall; Phase 2A partially delivered, Phase 2C backend underway, other sub-phases not started.
- Phases 3+ (Architect, Engineer, Integrations, Mobile) – scoped, dependent on Phase 2 infrastructure, not started.

## Immediate Actions (Carry Over)
- Run and complete the agent live walkthroughs, capture findings in `docs/feature_delivery_plan_v2.md`, and file follow-up tickets with `agent-validation` label.
- Keep `docs/feature_delivery_plan_v2.md` as the live status log—update the snapshot and relevant phase sections with every change.
- Maintain `TESTING_KNOWN_ISSUES.md` when tests are skipped or harness limits surface during validation or development.

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
- Provide explicit backend/frontend test commands and manual walkthrough steps with every delivery (see the mandatory testing checklist in `docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md`).

## When You Finish Work
- Update `docs/feature_delivery_plan_v2.md` immediately—snapshot, detailed phase section, and any dependency notes.
- Note resolved or new limitations in `TESTING_KNOWN_ISSUES.md`.
- Reference this playbook in handoff notes so future contributors know the orientation path and current targets.
