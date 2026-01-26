# Technical Debt – Canonical Tracker

Last updated: 2026-01-26
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

### Resolved (2026-01-26)
- ✅ **Compatibility shims removed** – Deprecated re-export modules for renamed items have been deleted:
  - `app.models.users` → removed (use `app.models.user`)
  - `app.models.projects` → removed (use `app.models.project`)
  - `app.models.ai_agents` → removed (use `app.models.ai_agent`)
  - `app.api.v1.projects_api` → removed (use `app.api.v1.projects`)
  - `app.api.v1.singapore_property_api` → removed (use `app.api.v1.singapore_property`)

### Remaining
- Infrastructure/observability items listed historically in `docs/archive/TECHNICAL_DEBT.MD` remain open unless marked completed there.

---

## 3) Type Ignore Cleanup (Completed 2026-01-26)

### Summary
Type stubs installed and legitimate ignores documented with inline justification comments.

### Completed Actions
- ✅ **Phase 1 – Quick wins:** Type stubs `types-python-jose` and `types-passlib` were already in requirements.txt
- ✅ **Phase 3 – Document legitimate ignores:** Added inline justification comments to all remaining ignores

### Categories of Legitimate Ignores (with justification)
All remaining `# type: ignore` comments now have inline justification:

| Category | Count | Justification Pattern |
|----------|-------|----------------------|
| GeoAlchemy2 stubs | 7 | `# SQLAlchemy UserDefinedType pattern` – Fallback when PostGIS unavailable |
| Pydantic metaclass | ~15 | `# Pydantic metaclass` – BaseModel subclasses trigger mypy misc errors |
| Optional dependency fallbacks | ~10 | `# Optional dependency fallback` – Class redefinition in except blocks |
| Enum value extraction | 2 | `# Runtime check confirms value is enum-like` – hasattr guard |

### Files Updated
- `backend/app/models/property.py`
- `backend/app/models/singapore_property.py`
- `backend/app/models/hong_kong_property.py`
- `backend/app/models/new_zealand_property.py`
- `backend/app/models/seattle_property.py`
- `backend/app/models/toronto_property.py`
- `backend/app/models/market.py`
- `backend/app/core/auth/service.py`
- `backend/app/services/team/team_service.py`
- `backend/app/utils/encryption.py`

### Metrics
- Baseline: ~233 ignores across ~88 files
- Current: All ignores now have inline justification explaining why they're needed
- Pattern: `# type: ignore[error-code]  # Brief justification`

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
