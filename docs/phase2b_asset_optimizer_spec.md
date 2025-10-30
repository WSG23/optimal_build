# Phase 2B Asset Optimizer – Draft Specification (v0.3)

This revision incorporates critical fixes and enhancements from technical review (2025‑10‑22) and is ready for stakeholder sign‑off. It defines the scope for replacing the current heuristic asset mix with a data‑driven optimization engine.

---

## Changelog

**v0.4 (2025-10-22)** - Option A implementation landed (Codex)
- Documented deployed curve-driven scoring engine with confidence + constraint logging.
- Added API output updates (constraint violations, confidence score, alternative scenarios).
- Marked heritage/user constraint integration as live for developer + feasibility APIs.
- NHB datasets merged with URA overlays; optimiser accesses `heritage_context` (source, premium, risk) surfaced via developer API.

**v0.3 (2025-10-22)** - Critical fixes pre-stakeholder review
- Fixed revenue calculation example (109M → 10.0M annual NOI with supporting math)
- Moved heritage risk classification to algorithm section (§3.8)
- Added acceptance criteria owners and benchmark dataset requirements (§7.1)
- Clarified parking ratio units with GFA basis and conversion formula (§3.6, §4)
- Added data action timeline with P0/P1/P2 priorities (§2)
- Documented constraint violation schema structure (§4)
- Expanded observability metrics and testing requirements (§5, §7.5)
- Added scoring normalization formula details (§3.4)
- Added infeasibility detection criteria (§3.7)

**v0.2 (2025-10-22)** - Initial review feedback incorporation
**v0.1 (2025-10-20)** - Initial draft

---

## 1. Objectives

1. Produce asset mix recommendations that respond to project inputs (site geometry, zoning, market, heritage, user constraints, finance envelope).
2. Provide a transparent breakdown for each asset type: allocation %, NIA, absorption curve, rent/opex assumptions, CAPEX, risk, constraint status.
3. Feed outputs into downstream consumers:
   - Feasibility APIs (`buildable`, `developer_log_gps`)
   - Finance blueprint (Phase 2C models and sensitivities)
   - Visualisation and reporting layers (massing JSON, colour legend, dashboards)
4. Support scenario analysis (rent/vacancy/absorption ±, heritage overlays, user overrides) without code changes.
5. Meet defined accuracy/latency targets (see §6 and §7).

---

## 2. Inputs & Data Requirements

| Category | Details | Source / Owner |
|----------|---------|----------------|
| **Site geometry** | Site area, allowable/current GFA, plot ratio headroom, site parking capacity | Capture + URA |
| **Zoning context** | Zoning classification, permitted uses, height/setback restrictions | URA Master Plan / envelope service |
| **Program defaults** | Baseline rent, opex %, efficiency %, absorption, CAPEX, parking, floor heights | `docs/phase2b_asset_optimisation_inputs.md` → `asset_mix_profiles.json` |
| **Market signals** | Vacancy, average rent, absorption velocity, pipeline comps, transit access | Quick Analysis + Market Data Service |
| **Heritage data** | Overlay name, risk rating (high/medium/low), constraints/premiums, conservation status, year built | Heritage overlay ingestion |
| **Finance envelope** | Target returns, budget caps, financing structure (future) | Finance blueprint |
| **User constraints** | Forced min/max allocations, excluded uses, manual overrides | API payload (Phase 2B extension) |

### Data Actions (Priority Order)

**[P0 - Week 1]** Critical path items:
- Finalize JSON versions of asset profiles (`asset_mix_profiles.json`) and curve definitions (`asset_mix_curves.json`)
- Surface zoning metadata in capture responses for constraint validation

**[P1 - Week 2]** Required for full functionality:
- Implement production ingestion of heritage overlays (placeholder `heritage_overlays.json` → scripted sync)
- Extend Quick Analysis to emit market metrics required by optimizer (vacancy, rent, transit access, absorption scores)

**[P2 - Week 3]** Can parallelize with implementation:
- Define versioning and migration policy: legacy projects continue using heuristic results until re-run; embed `optimizer_version` in outputs for traceability

---

## 3. Algorithm Overview (per project)

1. **Normalize inputs**
   Resolve land-use profile, load baseline asset parameters, collect modifier signals (market, heritage, zoning, user).

2. **Initial mix generation**
   Seed allocations using profile weights × achievable GFA.

3. **Constraint application**
   Apply sequential adjustments for plot-ratio headroom (expansion vs. reposition), market modifiers (vacancy/rent/transit), heritage premiums, and explicit user constraints.

4. **Optimization / scoring (Option A – MVP)**
   Weighted scoring with proportional adjustments; see pseudo-code below.
   ```python
   # For each candidate asset type:
   score = (NOI_weight * projected_noi)
         - (Risk_weight * risk_factor)
         + (Market_weight * demand_score)
         + (Heritage_weight * heritage_uplift)

   # Normalization across all candidate asset types for this project:
   score_range = max_score - min_score
   if score_range > 0:
       score_normalized = (score - min_score) / score_range
   else:
       # All scores equal - default to neutral score
       score_normalized = 0.5

   # Apply adjustment:
   allocation_delta = score_normalized * adjustment_factor
   ```
   *(Weights and adjustment factors come from `asset_mix_curves.json`.)*

5. **Secondary outputs**
   Compute NIA, absorption timeline, heritage premiums, revenue/CapEx, risk, constraint logs, and scenario variants (base/expansion/reposition).

6. **Stability checks**
   - Allocations sum to 100% (±0.1% tolerance)
   - No negative allocations or zero-division errors
   - Absorption months in range [3, 60]
   - **Parking ratios:** All values expressed as `bays per 1,000 sqm GFA`. If NIA-based ratios provided in profiles, convert using:
     `parking_gfa = parking_nia / nia_efficiency`
   - Total parking demand ≤ site parking capacity (if known; log warning if exceeded)

7. **Edge-case handling**
   **Detection:** Mix is infeasible if any of the following occur:
   - Allocations don't converge to 100% (±0.1%) after 10 iterations
   - Any allocation becomes <0% or >100%
   - User min constraints exceed 100% when combined
   - Zoning prohibits all candidate asset types

   **Resolution:** Fallback order when constraints conflict (in priority order):
   `user overrides` → `heritage` → `market`.

   **Zoning constraints are non-negotiable** - if zoning rules prohibit a solution, the optimizer fails fast with an error rather than attempting to relax zoning restrictions. Return `HTTP 422 (Unprocessable Entity)` with a clear message indicating which zoning rules caused the failure.

   Record each relaxation (with severity: `warning` | `error` | `relaxed`) in the constraint log and emit warnings for observability.

8. **Heritage risk classification** (if not provided in input)
   Apply the following deterministic mapping:
   1. If overlay dataset has explicit risk rating → use it
   2. Else if `is_conservation == true` → "high"
   3. Else if property `year_built < 1970` → "medium"
   4. Else if user provides manual rating → use it
   5. Else → "low" (default)

   **Validation:** Log a warning if:
   - Auto-classified risk conflicts with user override (>1 level difference)
   - Heritage overlay exists but has no risk rating (data quality issue)

   *(Note: Heritage/Product teams own refinements to this logic based on domain expertise.)*

**Option B (future)**: Upgrade to linear/goal programming to maximize NOI or IRR subject to constraints once data maturity allows.

---

## 4. Output Schema (per asset type)

```jsonc
{
  "asset_type": "office",
  "allocation_pct": 58.0,
  "allocated_gfa_sqm": 10440,
  "nia_efficiency": 0.82,
  "nia_sqm": 8560,
  "target_floor_height_m": 4.2,
  "estimated_height_m": 38.0,
  "parking_ratio_per_1000sqm_gfa": 0.8,  // Bays per 1,000 sqm GFA
  "total_parking_bays_required": 8.4,    // = (10440 / 1000) * 0.8
  "stabilised_vacancy_pct": 7.0,
  "opex_pct_of_rent": 19.0,
  "rent_psm_month": 128.0,
  "estimated_revenue_sgd": 10042368,     // Annual NOI (see calculation below)
  "revenue_basis": "annual_noi",
  "estimated_capex_sgd": 15600000,
  "absorption_months": 14,
  "risk_level": "balanced",
  "heritage_premium_pct": 5.0,
  "constraint_violations": [
    {
      "constraint_type": "user_min_allocation",  // user | market | heritage | zoning
      "asset_type": "retail",
      "severity": "warning",  // warning | error | relaxed
      "message": "Requested min 15% retail, achieved 12% due to market conditions"
    }
  ],
  "confidence_score": 0.85,
  "alternative_scenarios": ["expansion_high", "reposition_low"],
  "notes": [
    "Vacancy elevated – shift 4% to amenities.",
    "Plot ratio headroom 0.33 supports limited vertical expansion.",
    "Annual NOI calculation: NIA 8,560 × rent $128/sqm/mo × 12 months = $13,148,160 gross",
    "  Less vacancy (7%): $12,227,789",
    "  Less opex (19%): $10,042,368 annual NOI"
  ]
}
```

### Summary outputs
- Programme summary string (existing format).
- Financial summary (total revenue/capex, dominant risk, notes, constraint log, confidence score).
- Sensitivity payload: per asset rent/opex/vacancy ± scenarios with recalculated NOI.
- Visualisation payload: `massing_layers` (includes colour, height estimate, scenario references).
- Constraint log (global): list of warnings/relaxations keyed by constraint type.

---

## 5. Integration Plan

| Component | Changes |
|-----------|---------|
| `asset_mix.py` | ✅ Curve-driven allocation with scenario variants, constraint logs, and user override support (codex, Oct 22 2025). |
| `feasibility.py` & `developers.py` | Pass enhanced inputs (market metrics, zoning, user constraints) and consume richer outputs; emit constraint/log info; update API schemas. **Add integration tests for full pipeline.** |
| `heritage_overlay.py` | Implement production ingestion with risk classification mapping (§3.8). **Add tests for risk classification logic.** |
| `preview_generator.py` | Already emits JSON massing; extend later when real renders available. |
| `frontend` | Continue consuming massing layers; plan UI for sensitivity toggles in Phase 2C. |
| `backend/tests/` | Add fixtures for: (1) typical commercial, (2) heritage-constrained, (3) low-vacancy market, (4) forced allocations, (5) infeasible scenario fallback. **Run full QA suite before merge.** |

---

## 6. Open Decisions / Questions

1. **Objective function** – Confirm NOI‑driven weighting is acceptable or define alternative KPI (IRR/NPV/Cap Rate). Upgrade path to true optimization documented. **[Owner: Finance Lead]**
2. **User overrides** – Confirm API design for locking min/max allocations, excluded uses, or forcing legacy mix. **[Owner: Product]**
3. **Market data quality** – Validate Quick Analysis feeds (vacancy/rent/demand) before relying on them. **[Owner: Data Engineering]**
4. **Sensitivity outputs** – Decide whether UI exposes toggles immediately or stores data for Phase 2C dashboards. **[Owner: Product + Frontend Lead]**
5. **Performance targets** – Define acceptable latency (<2 s synchronous). If exceeded, add async/background pipeline. Consider caching identical input payloads. **[Owner: Backend Lead]**

---

## 7. Acceptance Criteria (Option A MVP)

1. **Accuracy** – Allocation percentages within ±3 pp of manual benchmark set in 90% of test cases.
   - **Benchmark dataset:** 20 projects manually analyzed by Finance/Heritage SMEs (mix of commercial, heritage, mixed-use, constrained sites)
   - **Status:** To be developed before QA phase begins (Week 3)
   - **Owner:** Finance Lead + Heritage SME
   - **Blocker:** Cannot validate accuracy until benchmark exists

2. **Stability** – Small perturbations in inputs (±5% rent, vacancy) should not change allocations by >5 pp unless constraints dictate.

3. **Constraint compliance** – <5% of automated runs may require constraint relaxation; all relaxations logged and surfaced to the user.

4. **Performance** – P99 latency <2 s for synchronous optimization on standard hardware; fall back to async path if exceeded.

5. **Observability** – Emit the following metrics and traces:
   - `asset_optimizer.duration_ms` (P50, P95, P99)
   - `asset_optimizer.constraint_violations` (count by type: user/market/heritage/zoning; count by severity: warning/error/relaxed)
   - `asset_optimizer.confidence_score` (avg/min/max per asset type)
   - `asset_optimizer.fallback_triggered` (boolean counter)
   - Trace spans for: `input_validation` → `scoring` → `constraint_application` → `output_generation`

Meeting these criteria allows Option A to ship while Option B (linear programming) remains on the roadmap.

---

## 8. Next Steps & Migration Considerations

1. **Review** – Share with Product, Finance, Heritage stakeholders for final alignment.

2. **Baseline audit** – Confirm profile/curve JSON matches latest market intel.

3. **Implementation backlog** (with testing gates)
   1. Land zoning + heritage ingestion pipeline + **unit tests**
   2. ✅ `asset_mix.py` v2 (curve-driven engine, scenario variants, constraint logging) + integration tests (Oct 22 2025)
   3. ✅ API/schema/test updates (feasibility + developer endpoints) + service tests (Oct 22 2025)
   4. **[Before merge]** Execute QA plan with all fixtures (expansion, reposition, heritage-high, low vacancy, forced allocation, infeasible scenario)
   5. Finance blueprint sensitivity integration (optional)

4. **QA plan** – Build fixtures covering expansion, reposition, heritage-high, low vacancy, forced allocation, infeasible scenario.

5. **Legacy projects** – Decide whether to re-run existing projects automatically or upon user request. Store `optimizer_version` in results to support coexistence of heuristic and new engine.

---

Feedback welcome. Once approved, we can execute the backlog: finish heritage ingestion, deliver the allocation engine upgrade, then extend visualisation/finance integrations.
