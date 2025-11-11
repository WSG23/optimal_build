# Phase 2C Finance Delivery Plan (v0.1)

Roadmap for evolving the finance workspace from the current generic feasibility snapshot into a developer-private modelling suite that satisfies Phase 2C acceptance criteria (asset-specific models, enhanced financing views, sensitivities, and data privacy).

---

## Changelog

- **v0.2 (2025-11-10)** – Enforced finance privacy guard now requires developer
  identity headers, logs denied attempts, and increments the new
  `finance_privacy_denials_total` metric for auditability.
- **v0.1 (2025-10-22)** – Captured current-state audit and implementation track for backend models, frontend workspace, sensitivity tooling, and privacy hardening.

---

## 1. Objectives

- Convert optimiser outputs (asset mix, heritage context, finance blueprint) into asset-specific pro formas covering office, retail, residential, industrial, and mixed-use segments.
- Extend finance pipeline with construction loan modelling, drawdown + interest carry, and sensitivity bands sourced from the Phase 2B blueprint.
- Deliver developer-only UI with equity/debt visualisations, scenario sensitivities, and asset breakdowns while keeping financial data private from other roles.
- Provide advanced metrics (IRR, MOIC, DSCR, NPV, loan-to-cost, cap rates) with clear provenance and downloadable artefacts.
- Instrument services so long-running finance runs and sensitivity batches are observable (metrics, logs, alerts).

---

## 2. Current Baseline

### 2.1 Backend

- `POST /api/v1/finance/feasibility` escalates costs, computes NPV/IRR, optional DSCR timelines, capital stack, and drawdown schedules (see `backend/app/api/v1/finance.py`).
- Asset optimiser (`app/services/asset_mix.py`) now emits estimated revenue, capex, risk, and confidence metrics per asset type; feasibility engine consolidates totals in `AssetFinancialSummarySchema`.
- Finance results persist to `fin_scenarios`, `fin_capital_stacks`, and `fin_results` tables; drawdowns stored via JSON metadata.
- Finance blueprint (capital stack targets, sensitivity bands) is attached to developer GPS capture responses (`DeveloperFinancialSummary`).
- Role guard uses `require_reviewer` for mutations and `require_viewer` for reads—no project-specific privacy yet.

### 2.2 Frontend

- `frontend/src/modules/finance/FinanceWorkspace.tsx` lists scenarios (static project id 401) and renders:
  - Scenario table (escalated cost, NPV, IRR, min DSCR, loan-to-cost).
  - Capital stack cards with progress bars.
  - Drawdown schedule table.
- No asset-level panels, no sensitivity toggles, no privacy messaging, and no link back to captured optimisation data.

### 2.3 Data & Security

- Finance API accepts `project_id` as UUID/int but does not verify caller ownership.
- Role header defaults to `admin`/`viewer`; any viewer-level role can read scenarios.
- Finance payloads lack asset-specific metadata (`asset_mix_summary` placeholder unused).
- No end-to-end sensitivity pipeline (only blueprint bands exist).

---

## 3. Gap Analysis

| Requirement | Gap |
|-------------|-----|
| Asset-specific financial modelling | Optimiser produces revenue/capex per asset, but finance API neither stores nor exposes breakdowns. No NOI, cap rate, or cash-flow projections per asset. |
| Financing architecture (equity/debt breakdown, loan modelling) | Capital stack summary exists but lacks tranche metadata surfaced in UI; construction loan interest carry and facility terms are not modelled. |
| Sensitivity analysis | Blueprint bands delivered, yet no API/UI layer to run +/- scenarios or visualise results. |
| Privacy controls | Finance scenarios readable by any viewer; need developer-only scope (owner-based) and logging. |
| Advanced analytics | IRR/NPV present; MOIC, equity multiple, payback, DSCR heat maps, and price/volume sensitivities absent. |
| Observability/testing | Metrics counters exist, but no asset-level validation or regression suite ensuring per-asset figures align with optimiser outputs. |

---

## 4. Target Data Flow

```
Developer capture → optimiser plans + finance blueprint
          │
          ▼
 Finance pipeline ingests:
   • escalated base cost
   • asset mix plans (per asset)
   • capital stack blueprint & sensitivity bands
          │
          ▼
 Finance calculator produces:
   • global metrics (NPV, IRR, DSCR timeline, drawdown)
   • per-asset pro forma (NOI, rent roll, opex, absorption, capex)
   • scenario sensitivities (rent, cost, rate pivots)
          │
          ▼
 Persistence + entitlements layer restricts to project owner
          │
          ▼
 Frontend finance workspace renders developer-only dashboard,
 downloads, and sensitivity toggles.
```

---

## 5. Backend Implementation Plan

1. **Asset Finance Engine**
   - Introduce `app/services/finance/asset_models.py` to translate optimiser outcomes into per-asset cash-flow models using helpers in `re_metrics.py`.
   - Extend `AssetFinancialSummarySchema` and `FinResult` metadata with per-asset NOI, capex, payback, and risk notes.
   - Persist structured asset results (new table `fin_asset_breakdowns` or JSON metadata) for scenario exports.
2. **Construction Loan & Interest Carry**
   - Enhance `calculator.drawdown_schedule` usage to compute interest carry and outstanding balance costs; store results in `FinResult` metadata.
   - Support facility terms (rate, fees, interest reserve) from blueprint or request payload.
3. **Sensitivity Batching**
   - Add optional `sensitivity` flag to feasibility request that spawns +/- scenarios (rent, cost, rate) using blueprint bands, summarising deltas (NPV, IRR, loan-to-cost).
   - Persist sensitivity runs as child scenarios or embed in metadata (`finance_sensitivity` result).
4. **Privacy Enforcement**
   - Create `require_developer_owner` dependency that validates JWT/project association.
   - Restrict `/finance/scenarios` and `/finance/export` to project owners (fallback to 404 for non-owners) and audit access.
   - Store scenario visibility flags (private, shared) for future collaboration features.
5. **API Schema Updates**
   - Populate existing `asset_mix_summary` field.
   - Add `asset_breakdowns`, `sensitivity_summary`, and `privacy_scope` to `FinanceFeasibilityResponse`.
   - Update OpenAPI + schema tests.
6. **Testing**
   - Service unit tests for new asset finance calculators.
   - API tests verifying privacy checks, asset breakdown structure, sensitivity delta correctness.
   - Fixture covering each asset type with deterministic optimiser output (tie into `backend/tests/test_services/test_feasibility_engine.py`).

---

## 6. Frontend Implementation Plan

1. **Workspace Layout**
   - Replace static project id with selection from captured developer properties (pass via route params/state).
   - Gate finance module behind developer role; display privacy banner when data is private.
2. **Asset Breakdown Panel**
   - New component summarising per-asset NOI, capex, risk, absorption (stacked bar + tabular detail).
   - Link back to optimiser constraints/notes for context.
3. **Financing Architecture**
   - Expand capital stack section with tranche table (rate, fees, maturity) and interest carry summary.
   - Surface loan-to-cost, weighted debt rate, equity multiple.
4. **Sensitivity Explorer**
   - UI to toggle rent/cost/rate bands; render results (sparkline or delta cards) from API sensitivity payload.
   - Provide CSV/JSON download for sensitivity runs.
5. **Scenario Management**
   - Allow marking scenario primary/private; show last run timestamp and reviewer log.
     - **Update (Nov 2025):** Workspace now exposes a “Make primary” action backed by `PATCH /api/v1/finance/scenarios/{id}`, automatically demoting sibling scenarios so reviewers can designate the canonical run.
   - Add refresh + duplicate controls (calls to new backend endpoints when implemented).
6. **Testing**
   - Component tests for new panels (mock API data).
   - Cypress or RTL tests ensuring privacy banner appears for non-developer roles.

---

## 7. Privacy & Entitlements

- Introduce developer ownership checks using project membership (owner email/user id).
- Log access events with `log_event` including `scenario_id`, `user_id`, `role`.
- Update CLA (`docs/ROADMAP.MD` acceptance) to note finance data is developer-private and add follow-up tasks in `docs/WORK_QUEUE.MD`.
- Coordinate with `ui-admin` for admin override tooling (view-only with explicit grant).

**Update (Nov 2025):** `_ensure_project_owner` now enforces owner-only access for
all finance endpoints. Requests must include `X-User-Email` or `X-User-Id`
headers matching the `Project` owner (admins bypass via `X-Role: admin`). Every
denial emits a `finance_privacy_denied` log entry and increments the
`finance_privacy_denials_total{reason="<cause>"}` counter so privacy regressions
surface in Grafana/alerts.

---

## 8. Observability & Testing Strategy

- **Metrics:** `finance.asset_model.duration_ms`, `finance.asset_model.failures`, `finance.sensitivity.runs`, `finance.privacy.denied_requests`.
- **Logs:** Structured entries for sensitivity batches, loan carry calculations, privacy denials.
- **Alerts:** Trigger when finance run errors exceed 5% or duration > 3 s P95.
- **Regression Suite:** Expand `backend/tests/test_api` coverage; ensure `pytest` fixtures seeded with asset mix data.
- **Frontend QA:** Manual checklist (per `TESTING_ADVISORY.md`) covering scenario selection, sensitivity toggles, downloads.
- **Test Harness Caveat (Nov 2025):** Frontend unit tests are currently blocked by known infrastructure issues (Vitest vs. node runner resolution, `tsx` IPC `EPERM`, and JSDOM misconfiguration). Retest once the harness is fixed before Phase 2C sign-off.

---

## 9. Known Issues / QA Findings

- **Finance workspace viewport clipping (Phase 2C UI):** ✅ **RESOLVED** - The shared `AppShell` layout now supports horizontal scrolling on viewports ≤1440px via `overflow-x: auto`. Added responsive media queries at 1280px and 1024px breakpoints to optimize padding and sidebar width. The fix maintains the gradient background and rounded corners while ensuring all finance workspace content (capital stack, drawdown cards) is accessible on MacBook Air-sized displays (~1280px) without zoom tricks. Changes applied to `frontend/src/index.css` lines 2987-3032.

---

## 10. Timeline & Dependencies

| Week | Deliverable | Owners | Dependencies |
|------|-------------|--------|--------------|
| Week 1 | Asset finance engine + schema updates | Backend | Stable optimiser outputs, heritage ingestion complete |
| Week 2 | Privacy enforcement + construction loan modelling | Backend | Owner/project lookup service |
| Week 3 | Frontend asset panels + capital stack enhancements | Frontend | Week 1–2 APIs |
| Week 4 | Sensitivity explorer + analytics instrumentation | Backend + Frontend | Blueprint finalisation |
| Week 5 (buffer) | QA, docs, rollout checklist | Platform | All prior weeks |

Dependencies: completed heritage ingestion (Phase 2B), finance blueprint validation, access to owner entitlements service (`TokenData`), and Prefect job runner for async sensitivities (optional).

---

## 11. Outstanding Decisions

1. Where to persist per-asset financials (dedicated table vs. JSON metadata)? **Owner:** Backend lead.
2. Do we compute sensitivities synchronously or via background jobs? **Owner:** Platform.
3. Default currency handling for multi-market expansion? **Owner:** Finance/Product.
4. Privacy fallback: should non-owners see scenario existence (redacted metadata) or receive 404? **Owner:** Product + Legal.
5. Export scope – single CSV with all assets vs. multi-tab workbook? **Owner:** Finance ops.

---

## 12. Next Steps Checklist

- [ ] Finalise per-asset result schema and storage approach.
- [ ] Confirm project ownership lookup mechanism (user ↔ project mapping).
- [ ] Draft API contract updates for frontend (asset breakdowns, sensitivities, privacy).
- [ ] Align on sensitivity batching process (sync vs async, caching).
- [ ] Prepare test fixtures mirroring Phase 2B optimiser outputs for finance QA.
