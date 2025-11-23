# Technical Debt – Canonical Tracker

Last updated: 2025-11-22
Purpose: Single, maintained view of debt, how overrides are approved, and the active cleanup roadmap.

---

## 1) Governance / Overrides
- Deviations from coding rules require an explicit note in this file with scope, owner, and expiry.
- Default stance: fix debt instead of adding exceptions; use overrides only when the fix would block higher-priority delivery.
- When granting an override:
  - Capture: why the rule is bypassed, affected files, and a sunset date.
  - Revisit: at the next monthly review, either remove the override or extend it with justification.

Current overrides:
- None recorded here. See section 3 for temporary type-ignore allowances.

---

## 2) Current High-Impact Debt
- Type-check gaps: 20+ `# type: ignore` instances (see roadmap below).
- Infrastructure/observability items listed historically in `docs/archive/TECHNICAL_DEBT.MD` remain open unless marked completed there.

---

## 3) Type Ignore Cleanup (Active)
Scope: Reduce unannotated `# type: ignore` usage and document the necessary ones.

Phases:
- **Phase 1 – Quick wins (2 hours):** Remove or justify test fixture ignores; install missing stubs (`types-python-jose`, `types-passlib`). Target: drop ~6 ignores.
- **Phase 2 – ASGI/uvicorn typing (3-4 hours):** Re-evaluate ignores in `backend/uvicorn_app`; update stubs or add Protocol types to eliminate `ignore[misc]` calls.
- **Phase 3 – Document remaining legitimate ignores (1 hour):** For optional deps or monkey-patching, keep the ignore with an inline justification comment. Add a pre-commit check to flag new unjustified ignores.

Metrics:
- Baseline: ~30 ignores across ~20 files.
- Target: 15–18 ignores with 100% inline justification.

Review cadence:
- Monthly check to ensure new ignores are justified and to retire temporary ones.

---

## 4) Maintenance Cadence
- Monthly: review this file, close completed items, and renew/retire overrides.
- Quarterly: sync with the archived backlog in `docs/archive/TECHNICAL_DEBT.MD` (historical context only).

---

## 5) How to Add Debt Items
Use this structure:
- Item: <short title>
- Impact: <why it matters>
- Plan: <steps or phase>
- Owner / ETA: <name or role, timeframe>
- Notes: <links to PRs, docs>
