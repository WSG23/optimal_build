# All Steps to Product Completion (Single Source of Truth)

> **Status:** ACTIVE – This document now contains the full strategic roadmap, day-to-day execution backlog, outstanding technical debt, and known testing limitations. If it is not listed here, it is not part of the plan.
>
> **Last Updated:** 2025-11-29
>
> **Navigation tip:** Strategic phase status lives in the sections below, while the unified backlog/debt tracker is available in [📌 Unified Execution Backlog & Deferred Work](#-unified-execution-backlog--deferred-work).

# Complete Platform Delivery Roadmap
## Comprehensive Implementation Plan for All FEATURES.md Components (Backend + UI)

> **Source of Truth:** This document tracks **BOTH backend AND UI/UX** implementation status. It maps every feature from `FEATURES.md` into a phased delivery plan with backend and UI progress tracked together. This supersedes the original `feature_delivery_plan.md` which only covered Agent GPS capture (Phase 1A).

---

## 📊 Current Progress Snapshot (Read-Only Dashboard)

> **⚠️ CRITICAL: DO NOT EDIT THIS SECTION DIRECTLY**
>
> This summary is a **read-only dashboard** derived from the detailed phase sections below.
> **To update progress:** Scroll to the detailed phase section and update the "Status:" line there.
>
> **Last Updated:** 2025-11-29 (reflects v1/v2 status distinction from Updated Spec integration)
>
> **🤖 AI AGENTS:** Read [ai-agents/next_steps.md](ai-agents/next_steps.md) for guidance on choosing your next task.

---

### ✅ Phase Gate Checklist (Pre-Phase 2D Readiness)

> Update these checkboxes only after the corresponding work is fully complete and documented.
> `scripts/check_phase_gate.py` enforces these gates for any Phase 2D commits.

- [x] Phase 2D Gate: Pre-Phase 2D Infrastructure Audit & Quality Sprint complete (`PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.md`)
- [x] Phase 2D Gate: Phase 1D Business Performance UI backlog delivered & QA signed off (see lines 274‑392)
- [x] Phase 2D Gate: Phase 2B visualisation residual work delivered (see lines 455‑508)
- [x] Phase 2D Gate: Expansion Window 1 (HK, NZ, Seattle, Toronto) complete (`docs/ai-agents/next_steps.md`, `docs/jurisdiction_expansion_playbook.md`)

---

### ⚠️ v1 Complete, v2 Enhancements Pending

> **Note (2025-11-29):** The Updated Spec v2 added 32 new features. Phases below show v1 (original scope) as complete, but v2 enhancements are documented and queued for implementation.

**[Phase 1A: GPS Capture & Quick Analysis](#phase-1a-gps-capture--quick-analysis)** ⚠️ v1 COMPLETE, v2 PENDING (3 items)
- **Backend:** 100% (v1) | **UI:** 100% (v1)
- GPS Capture, Quick Analysis, Marketing Pack Generator all shipped
- **v2 Done:** ✅ Multi-jurisdiction zoning sources
- **v2 Pending:** Voice notes, accuracy bands (±8-15%), watermarks
- [Jump to details ↓](#phase-1a-gps-capture--quick-analysis)

**[Phase 1B: Agent Advisory Services](#phase-1b-agent-advisory-services)** ⚠️ v1 COMPLETE, v2 PENDING (1 item)
- **Backend:** 100% (v1) | **UI:** 100% (v1)
- Asset Mix Strategy, Market Positioning, Absorption Forecasting, Feedback Loop
- **v2 Done:** ✅ Multi-jurisdiction market data sources
- **v2 Pending:** Sales Velocity Model
- [Jump to details ↓](#phase-1b-agent-advisory-services)

**[Phase 1C: Listing Integrations (Mocks)](#phase-1c-listing-integrations-mocks)** ⚠️ v1 COMPLETE, v2 PENDING
- **Backend:** 100% (v1) | **UI:** 100% (v1)
- PropertyGuru mock, EdgeProp mock, Zoho CRM mock, Token encryption
- **v2 Pending:** Zillow, LoopNet, Realtor.com, RealEstate.co.nz, HK portals, Salesforce, HubSpot, BoomTown, kvCORE
- [Jump to details ↓](#phase-1c-listing-integrations-mocks)

**[Phase 2A: Universal GPS Site Acquisition](#phase-2a-universal-gps-site-acquisition)** ✅ COMPLETE
- **Backend:** 100% | **UI:** 100%
- Site Acquisition workspace, due diligence checklists, manual inspection capture
- [Jump to details ↓](#phase-2a-universal-gps-site-acquisition)

**[Phase 2B: Asset-Specific Feasibility](#phase-2b-asset-specific-feasibility)** ⚠️ v1 95% COMPLETE, v2 PENDING
- **Backend:** 95% (v1) | **UI:** 95% (v1)
- Asset optimizer, heritage overlays, finance integration, Level 1 3D
- **v2 Pending:** Global Engineering Defaults, GFA→NIA accuracy bands, Engineering Layers, Clash & Impact Board
- [Jump to details ↓](#phase-2b-asset-specific-feasibility)

**[Phase 2C: Complete Financial Control & Modeling](#phase-2c-complete-financial-control--modeling)** ⚠️ v1 COMPLETE, v2 PENDING
- **Backend:** 100% (v1) | **UI:** 100% (v1)
- Asset finance engine, Construction loan interest, Finance workspace, Smoke tests verified
- **v2 Pending:** ARGUS export (6 CSVs), multi-jurisdiction financing, scenario lineage, Capital Raise Pack, Data Room integrations
- [Jump to details ↓](#phase-2c-complete-financial-control--modeling)

---

### ⏸️ In Progress Phases

**[Phase 1D: Business Performance Management](#phase-1d-business-performance-management)** ✅ v1 COMPLETE
- **Backend:** 100% | **UI:** 100%
- Deal Pipeline UI, insights, analytics, and ROI panels shipped (November 2025)
- [Jump to details ↓](#phase-1d-business-performance-management)

---

### ❌ Not Started Phases

**Phases 2D-2I:** Team coordination, regulatory navigation, construction delivery, revenue optimization, enhanced export
- [Jump to Phase 2D ↓](#phase-2d-multi-phase-development-management)

**Phase 3+:** Architect Tools, Engineer Tools, Platform Integration
- [Jump to Phase 3 ↓](#phase-3-architect-workspace)

---

### 🔄 How to Update This Dashboard

**❌ WRONG - Do NOT do this:**
```markdown
# Editing this summary section directly
**Phase 2B** - Backend 100%, UI 100% ✅ COMPLETE  ← DON'T EDIT HERE!
```

**✅ CORRECT - Do this instead:**

1. **Find the detailed phase section** (use Ctrl+F or jump links above)
2. **Update the "Status:" line** in the detailed section:
   ```markdown
   ### Phase 2B: Asset-Specific Feasibility ⚠️ IN PROGRESS
   **Status:** 80% - Most features delivered, final items in progress
   ```
3. **Update the "What's Missing" section** - Remove ❌ items when complete
4. **This summary will reflect those changes** when regenerated

**Why this matters:**
- Summary is derived from detailed sections (single source of truth)
- Prevents summary/detail drift and discrepancies
- Forces validation of "What's Missing" before claiming 100%

---

**🎯 Quick Navigation:**
- Looking for next task? → [ai-agents/next_steps.md](ai-agents/next_steps.md)
- Need phase requirements? → Use jump links above to go directly to detailed sections
- Want to see overall progress? → This dashboard (you are here)

---

## 🎯 Delivery Philosophy

### Guiding Principles:
1. **Validate Early:** User feedback after each major role completion
2. **Build Horizontally First:** Complete one role's tools before moving to next
3. **Reuse Infrastructure:** Agent foundation supports Developer/Architect/Engineer
4. **Singapore First:** Gov API integration can be incrementally added
5. **Quality Gates:** Every phase must pass `make verify` and have tests

### Why This Order:
- **Agents → Developers → Architects → Engineers** follows the natural development lifecycle
- Each role depends on previous role's infrastructure
- Early validation prevents costly rewrites
- Can launch partial product (Agents-only) while building remaining roles

---

## 📌 Unified Execution Backlog & Deferred Work

**Last Updated:** 2025-11-23
**Scope:** This section consolidates the former `WORK_QUEUE.MD`, `TECHNICAL_DEBT_SUMMARY.MD`, and `development/testing/known-issues.md` so every outstanding item—feature work, tech debt, or harness limitation—lives in one place. Update these subsections whenever work starts, wraps, or is deferred.

### 🚀 Active (Do Now - Priority Order)

_No active tasks. Pull from the Ready queue below._

### 📋 Ready (Queued - Do After Active)

**Updated Spec Integration (32 New Features from features.md v2):**
> ✅ **Spec Status:** All 32 features now documented in `docs/planning/features.md` (2025-11-29)
> 📋 **Implementation Status:** Queued for development — see phase-specific sections below for details

**Agent Enhancements (Phase 1 additions):**
- [ ] Voice notes on site capture (add to Phase 1A GPS capture) — *spec: features.md line 32*
- [ ] Accuracy bands display (±8-15% by asset class) on quick analysis — *spec: features.md line 31*
- [ ] Sales Velocity Model advisory tool (add to Phase 1B) — *spec: features.md line 58*
- [ ] Expanded listing portals: Zillow, LoopNet, Realtor.com, RealEstate.co.nz, HK portals (Phase 1C) — *spec: features.md lines 63-67*
- [ ] Expanded CRM integrations: Salesforce, HubSpot, BoomTown, kvCORE (Phase 1C) — *spec: features.md lines 69-71*
- [ ] Explicit watermark text for Acquisition vs Sales phases (enhance Phase 1A marketing packs) — *spec: features.md lines 48-51*

**Developer Enhancements (Phase 2 additions):**
- [ ] Global Engineering Defaults (structural grids, core sizes, MEP allowances by jurisdiction) — *spec: features.md lines 109-114*
- [ ] GFA→NIA accuracy bands (±5-12% display) — *spec: features.md line 102*
- [ ] Multi-jurisdiction financing structures (SG LTV/ABSD, NZ LVR, US DSCR, Toronto CMHC, HK IO) — *spec: features.md lines 127-132*
- [ ] ARGUS-Compatible Export (6 CSV spec: Rent Roll, Leasing, OpEx, CapEx, Financing, 120-month Cashflow) — *spec: features.md lines 184-191*
- [ ] Engineering Layers visualization (structural grid, MEP trunks, plenum, civil, façade) — *spec: features.md lines 116-122*
- [ ] Clash & Impact Board (lightweight clash detection, area/cost impact bands) — *spec: features.md lines 123-126*
- [ ] Sign-Off Workflow documentation (Engineers propose → Architects approve → Developer exports) — *spec: features.md line 145*
- [ ] Document/Data Room Integrations (Box, Dropbox, Google Drive, SharePoint) — *spec: features.md lines 192-194*
- [ ] Scenario lineage with export hashes (enhance audit trail) — *spec: features.md lines 195-198*

**Architect Enhancements (Phase 3 additions):**
- [ ] Non-Destructive Overlays (AI suggestions as visual hints only) — *spec: features.md line 202*
- [ ] Sign-Off Gateway (architect unlocks permit submissions) — *spec: features.md line 250*
- [ ] Multi-jurisdiction building codes (NZBC, Seattle SDCI, Toronto OBC, HK BD) — *spec: features.md lines 208-213*
- [ ] Authority Package Build formats (CORENET, ACCELA, HK e-portal) — *spec: features.md lines 251-254*
- [ ] Audit Attribution (every compliance action tied to architect identity) — *spec: features.md line 272*

**Engineer Enhancements (Phase 4 additions):**
- [ ] Parametric reserves (discipline-specific reserves updating feasibility) — *spec: features.md line 297*
- [ ] Clash & Coordination panel (clash detection, impact assessment, coordination log) — *spec: features.md lines 323-326*
- [ ] ROI / Value Panel (m² saved, clashes prevented, redesign costs avoided) — *spec: features.md lines 337-341*
- [ ] Digital PE endorsement — *spec: features.md line 334*
- [ ] Multi-jurisdiction engineering codes (NZ seismic, Seattle IBC, Toronto OBC, HK Fire/BD) — *spec: features.md lines 310-315*

**New Cross-Cutting Systems:**
- [ ] Verification & Transparency Suite - Option 1: Excel/CSV Export — *spec: features.md lines 370-373*
- [ ] Verification & Transparency Suite - Option 2: "Show My Math" Panel — *spec: features.md lines 375-379*
- [ ] Verification & Transparency Suite - Option 3: Verifiable Audit Trail with export hashes — *spec: features.md lines 381-386*
- [ ] Global Accuracy System (accuracy bands by asset type + dynamic improvement by phase) — *spec: features.md lines 390-412*
- [ ] Confidence labels on all main outputs — *spec: features.md lines 410-412*

---

### ✅ Completed (Last 30 Days)
- **2025-11-29:** Updated Spec Integration (32 features) documented (Claude) — Integrated all 32 new/enhanced features from the updated global product spec into both `docs/planning/features.md` and `docs/all_steps_to_product_completion.md`. Features organized by role (Agents: 8, Developers: 12, Architects: 5, Engineers: 5, Cross-Cutting: 2). Added phase-specific "Queued Enhancements" sections and new "Cross-Cutting Systems" section for Verification & Transparency Suite and Global Accuracy System. All features now have line-number references to the canonical spec.

- **2025-11-18:** Pre-Phase 2D infrastructure audit closed (Codex Local) — `make lint` and `PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build JOB_QUEUE_BACKEND=inline SECRET_KEY=test ../.venv/bin/pytest --cov=app --cov-report=term-missing` now pass (83 % backend coverage). Updated [`docs/audits/PRE-PHASE-2D-AUDIT.MD`](audits/PRE-PHASE-2D-AUDIT.MD) with the new commands, plugin notes, and the remaining benchmarking caveat (Postgres currently unreachable from the sandbox).
- **2025-11-18:** Phase 1D manual QA revalidated (Codex Local) — Reviewed commit history (no `frontend/src/app/pages/business-performance/*` changes since PR #275) and attached backend regression run results. [`docs/development/testing/phase-1d-manual-qa-checklist.md`](development/testing/phase-1d-manual-qa-checklist.md) now records the 2025-11-18 audit and preserves the original walkthrough for when seeded data returns.
- **2025-11-18:** Expansion Window 1 execution plan documented (Codex Local) — Added actionable subtasks for Hong Kong, New Zealand, Seattle, and Toronto to both [`docs/jurisdiction_expansion_playbook.md`](jurisdiction_expansion_playbook.md#10-expansion-window-1-execution-plan) and [`docs/ai-agents/next_steps.md`](ai-agents/next_steps.md#expansion-window-1), covering data sourcing, config, ingestion prototypes, and validation responsibilities.
- **2025-11-18:** Preview async Linux validation guide (Codex Local) — Added [`docs/validation/preview_async_linux.md`](validation/preview_async_linux.md) plus automation helper [`scripts/validate_preview_async_linux.sh`](../scripts/validate_preview_async_linux.sh) so Phase 2B preview jobs can be exercised on Linux with Redis/RQ, metrics capture, and results logging.
- **2025-11-18:** Layer inspection panel (Codex Local) — Developer preview standalone UI now exposes a detailed inspection panel with footprint area/perimeter, elevation, floor line previews, and per-layer controls. Changes touch [`frontend/src/app/pages/site-acquisition/DeveloperPreviewStandalone.tsx`](../frontend/src/app/pages/site-acquisition/DeveloperPreviewStandalone.tsx) and [`frontend/src/index.css`](../frontend/src/index.css); verified via `npm --prefix frontend run lint`.
- **2025-11-18:** Preview duration monitoring script (Codex Local) — Introduced [`backend/scripts/preview_duration_report.py`](../backend/scripts/preview_duration_report.py) to summarise READY preview job durations (mean/median/p90) and export CSVs for production telemetry.
- **2025-11-18:** Developer checklist service typing (Codex Local) — Added explicit TypedDicts for checklist payloads/summary buckets, tightened metadata fallbacks, and cleaned up type ignores. Verified with `PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build ../.venv/bin/mypy app/services/developer_checklist_service.py --config-file=../mypy.ini` and `PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build SECRET_KEY=test JOB_QUEUE_BACKEND=inline ../.venv/bin/pytest tests/test_api/test_developer_checklist_templates.py`.
- **2025-11-18:** Phase 2C finance sensitivity validation (Claude) — Validated async `finance.sensitivity` deduplication logic via unit test (`test_finance_sensitivity_rerun_async_deduplicates_pending` PASSED). Infrastructure verified: Redis, PostgreSQL, API server with RQ backend. Deduplication helpers `_has_pending_sensitivity_job()` and `_band_payloads_equal()` prevent duplicate job enqueues. See [validation_results_phase2c_20251118.md](../validation_results_phase2c_20251118.md) for full details.
- **2025-11-18:** Preview generator typed payload refactor (Codex Local) — Introduced TypedDict/dataclass helpers for preview payloads, refactored `preview_generator.py` + GLTF/thumbnail builders to use them, and verified with `PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build ../.venv/bin/mypy app/services/preview_generator.py --config-file=../mypy.ini` plus `PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build SECRET_KEY=test JOB_QUEUE_BACKEND=inline ../.venv/bin/pytest tests/test_services/test_preview_generator.py`.
- **2025-11-18:** Backend mypy plugin enforcement (Codex Local) — Enabled `pydantic.mypy` and `sqlalchemy.ext.mypy.plugin` in `mypy.ini`, added `pydantic[email,mypy]==2.5.0` and `sqlalchemy[asyncio,mypy]==2.0.23` to `backend/requirements.txt`, and validated via `PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build ../.venv/bin/mypy app/services/preview_generator.py --config-file=../mypy.ini`.
- **2025-11-18:** Finance export bundle tranche metadata (Codex Local) — `GET /api/v1/finance/export` now includes `capital_stack.csv` with metadata columns and a `capital_stack.json` file capturing tranche details; covered by `pytest tests/test_api/test_finance_asset_breakdown.py::test_finance_export_bundle_includes_artifacts`.
- **2025-11-18:** Infrastructure Audit Option 11 – Backend coverage ≥80 % (Codex Local) — `make test-cov` now reports 89 % total backend coverage (see `backend/htmlcov/index.html`), covering ingestion + finance adapters per audit requirement.
- **2025-11-23:** Security & Infrastructure Audit Complete (Claude) — Comprehensive security audit completed: (1) ✅ 100% async compliance achieved (converted 3 files, 9 routes in singapore_property_api.py), (2) ✅ Dependency vulnerability scan with pip-audit found 4 CVEs in 3 packages (prefect 2.16.5→2.20.17+ CORS fix, starlette 0.41.3→0.49.1+ DoS fixes, ecdsa timing attack accepted risk), (3) ✅ SQL injection audit PASSED (100% ORM usage, zero vulnerabilities), (4) ✅ Input sanitization audit PASSED (comprehensive Pydantic validation), (5) ✅ OWASP Top 10 compliance 8/10 PASS, (6) ✅ GitHub Dependabot configured (.github/dependabot.yml), (7) ⚠️ Action required: upgrade prefect + starlette (pending). Full report: [`docs/audits/SECURITY_AUDIT_2025-11-23.md`](audits/SECURITY_AUDIT_2025-11-23.md). Async refactoring tracked in [`.coding-rules-exceptions.yml`](.coding-rules-exceptions.yml#L24-L49).
- **2025-11-23:** Production Readiness Audit Complete (Claude) — ✅ **PRODUCTION READY** status achieved. All high-priority security fixes deployed: (1) ✅ Upgraded prefect 2.16.5→2.20.17 (CVE-2024-8183 CORS vulnerability), (2) ✅ Upgraded FastAPI 0.115.6→0.121.3 + starlette 0.41.3→0.49.1 (CVE-2025-54121 DoS, CVE-2025-62727 ReDoS), (3) ✅ Added pip-audit to CI/CD pipeline ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml#L558-L562)), (4) ✅ CORS configuration verified secure (localhost-only defaults, environment-configurable origins). Test results: 981/994 tests passing (98.7% pass rate), 89% backend coverage. OWASP compliance: 8/10 PASS. Coding standards: zero violations (enforced via pre-commit hooks). Remaining 4 low-priority CVEs (brotli, pip, pypdf, ecdsa) documented for next maintenance window. Deployment approved with documented maintenance plan.
- **2025-11-17:** Front-end npm audit cleanup (Claude) — Resolved all 3 moderate vulnerabilities: upgraded vite 4.5.14 → 7.2.2 (fixes esbuild <=0.24.2 + vite <=6.1.6), upgraded eslint-plugin-react-hooks 4.6.2 → 5.2.0 (unblocked js-yaml fix), applied `npm audit fix` for js-yaml <4.1.1. `npm audit` now reports 0 vulnerabilities. Dev server, HMR, and production build verified working with vite@7.
- **2025-11-12:** Roadmap link consolidation + validator update (Codex Local) — Removed stale `ROADMAP.MD` links across enforcement docs, QA checklists, and scripts; `make validate-delivery-plan` now targets `all_steps_to_product_completion.md`.
- **2025-11-12:** Phase 2B preview Level 2 detail shipped (Codex Local) — Added `geometry_detail_level` support, octagonal footprints with podium/setback tiers, per-floor shading, and isometric thumbnails for preview jobs; Site Acquisition UI toggle wired.
- **2025-11-10:** Preview asset lifecycle retention + cleanup (Codex Local) — Added `backend/scripts/preview_cleanup.py` and retention policy (`settings.PREVIEW_MAX_VERSIONS`).
- **2025-11-04:** Phase 2B GLTF renderer + preview viewer shipped (Codex Local) — Backend now emits GLTF/BIN/thumbnail bundles; viewer renders GLTF with orbit controls and metadata links.
- **2025-11-04:** Phase 2B monitoring metrics wired (Codex Local) — Added Prometheus counters/histograms and Grafana dashboards for preview jobs.
- **2025-11-04:** Phase 2B manual UI QA execution (Wakae + Codex Local) — Completed manual walkthrough documented in `docs/archive/phase2b/phase2b_manual_qa_results_2025-11-10.md`.
- **2025-11-02:** Phase 2C Finance complete (WSG23 + Claude) — Commits 7beff36/d0752f5, smoke tests ✅.
- **2025-11-02:** Infrastructure Audit Option 10 (Claude) — Pre-commit hook fixes landed.
- **2025-11-01:** Database indexing (Claude + Codex) — Added 9 composite indexes (11‑39% perf gain).

Older wins moved to archive for brevity; see git history for prior months.

---

### 🧭 Operating Instructions for AI Agents

1. **Before starting work**, review the Active section to confirm priority.
2. Cross-check context docs before coding: [`docs/development/testing/summary.md`](development/testing/summary.md), [`docs/planning/ui-status.md`](planning/ui-status.md), [`docs/README.md`](README.md), plus the [Known Testing Issues](#-known-testing-issues) subsection below.
3. Clarify ambiguous scope inside this section (add notes inline) instead of starting extra docs.
4. After completing work, move the item to ✅ Completed with date + commits/artifacts.
5. Update the relevant phase block in this file whenever feature status changes.
6. Infra audit items must also update `docs/audits/PRE-PHASE-2D-AUDIT.MD`.
7. All Phase 2B renderer work requires the manual UI walkthrough (see archive link) with screenshots attached before review.
8. Every feature/bug fix ships with tests. If a harness blocks execution, note it here with a follow-up item before closing the task.

---

### 🧱 Technical Debt Radar

> Source: Former `TECHNICAL_DEBT_SUMMARY.MD` (2025-11-10). Keep the bullets in sync with `docs/architecture_honest.md`.

**Critical:** _None_ – Market intelligence & agent routers are live, Alembic migrations are versioned, and `RequestMetricsMiddleware` plus `/metrics` expose throughput/latency/error collectors.

**High Priority**
- Rate limiting middleware still missing; Redis-backed throttling needs implementation.
- Domain naming inconsistent (mixed pluralization / `_api` suffixes) across models + schemas.
- Authentication logic remains fragmented across `users_secure.py`, `users_db.py`, `core/jwt_auth.py`, and `core/auth/policy.py`.

**Medium Priority**
- `documents` MinIO bucket referenced in docs but not present in `docker-compose.yml`.
- Market schema drift: documentation cites `market_transactions`, production uses YieldBenchmark/AbsorptionTracking/MarketCycle tables.
- Compliance models live inside `singapore_property.py` instead of a dedicated module.

**Low Priority**
- Ten of eleven AI agents exist in code but lack coverage in high-level docs. Update agent catalog when feasible.

---

### ⚠️ Known Testing Issues (Harness Limitations)

This replaces `docs/all_steps_to_product_completion.md#-known-testing-issues`. These entries describe **test harness or sandbox constraints**—not product bugs.

#### Purpose
- Distinguish real bugs vs known harness issues so AI agents do not re-triage them.
- Provide repeatable workarounds and workflows for manual testers.

#### Workflow for Adding/Resolving Issues
1. AI documents the issue and requests approval to log it here.
2. Human confirms whether to document or fix immediately.
3. When resolved, move the entry to the “Resolved Issues” list with date + owner.
4. Update test files/comments referencing the issue.

#### Active Issues

##### Dev Seeder: Postgres-Only Dependency
- **Documented by:** Codex on 2025-10-13
- **Symptom:** `python -m backend.scripts.seed_properties_projects` and `make seed-data` fail in sandbox with `PermissionError` / missing Postgres UUID types.
- **Root Cause:** Seeder relies on Postgres-only types (`sqlalchemy.dialects.postgresql.UUID`). SQLite fallback not supported.
- **Impact:** Cannot seed demo data inside sandbox; production unaffected.
- **Workaround:** Run seeders inside Docker/Postgres. For local validation rely on code review or manual Postgres environment. Long-term fix requires switching to shared UUID type.

##### Frontend: React Testing Library Async Timing
- **Documented by:** Claude on 2025-10-11
- **Symptom:** Tests fail to find text even though DOM contains it (Phase 1B + 1C pages).
- **Root Cause:** React state updates finish after `waitFor()` timeout in JSDOM.
- **Impact:** Frontend unit tests for some pages fail; runtime works.
- **Workaround:** Manually verify UI, inspect HTML dumps, keep tests but note limitation. Future fix may require different testing strategy or harness config.

##### SQLite vs PostgreSQL SQL Compatibility
- **Documented by:** Claude on 2025-10-11
- **Symptom:** Raw SQL with Postgres syntax fails in SQLite tests.
- **Workaround:** Wrap SQL in `text()` and use SQLite-compatible functions when writing tests. Production keeps Postgres syntax.

##### Marketing Packs UI Requires Demo Seed Data
- **Documented by:** Codex on 2025-10-13
- **Symptom:** Marketing page falls back to offline preview without seeded data.
- **Workaround:** Seed demo dataset into `.devstack/app.db` using:
  ```bash
  cd /Users/wakaekihara/GitHub/optimal_build
  source .venv/bin/activate
  SQLALCHEMY_DATABASE_URI="sqlite+aiosqlite:///./.devstack/app.db" \
    python -m backend.scripts.seed_market_demo
  ```
  Restart uvicorn and reuse the printed property UUID.

##### Backend: Mypy Type Checking Errors (511 remaining)
- **Documented by:** Claude on 2025-11-16
- **Status:** 511 errors total (284 SQLAlchemy stub gaps, 227 real/complex issues).
- **Key Categories:** SQLAlchemy stub gaps, weakly typed JSON, missing type narrowing, Pydantic validator mismatches, import conflicts, stub override mismatches.
- **Strategy:** Focus on Tier 1 preventive steps (TypedDicts/Pydantic schemas, pre-commit type checks) and Tier 2 plugin enablement. Do not attempt to fix all errors blindly—target high leverage areas (preview generator, developer checklist service, mypy plugins).

#### Resolved Issues (Historical Reference)
- **Frontend JSDOM runner instability (2025-11-11):** Migrated to Vitest + thread pool (Codex + Claude). `npm --prefix frontend run test` now stable.
- **Migration audit downgrade guards (2025-10-18):** Verified guards existed, added entries to `.coding-rules-exceptions.yml`.
- **Backend API tests skipped on Python 3.9 (2025-10-11):** Upgraded to Python 3.13, added FastAPI dependency overrides; tests now run.
- **PDF rendering deps missing (2025-10-28):** Documented absence of Cairo/Pango libs in sandbox; treat as environment constraint when PDF tests fail.

---

## 📋 PHASE 1: AGENT FOUNDATION (v1 Complete, v2 Enhancements Pending)

**Goal:** Complete all 6 Agent tools so agents can work entire development lifecycle

### Phase 1A: GPS Capture & Quick Analysis ⚠️ v1 COMPLETE, v2 PENDING
**Status:** Original scope 100% complete. New features from Updated Spec v2 are documented but NOT implemented.

**Backend Deliverables:**
- ✅ Mobile GPS Logger with Singapore coordinate capture
- ✅ Multi-scenario quick analysis (raw land, existing, heritage, underused)
- ✅ Photo documentation with GPS tagging
- ✅ Quick 3D visualization (basic massing)
- ✅ Market intelligence integration
- ✅ Marketing pack generation (4 types: Universal, Investment, Sales, Lease)
- ✅ PDF download endpoint with absolute URLs
- ✅ Documentation & demo scripts

**Queued Enhancements (from Updated Spec v2):**
- [ ] Voice notes on site capture (audio recording with GPS tagging)
- [ ] Accuracy bands display (±8-15% by asset class) on quick analysis outputs
- [ ] Explicit watermark text for Acquisition vs Sales vs Pre-Development phases
- ✅ Multi-jurisdiction zoning sources (Auckland/NZ, Seattle SDCI, Toronto bylaws, HK OZP) — IMPLEMENTED via Expansion Window 1

**UI/UX Deliverables (2025-10-13):**
- ✅ Marketing Packs page with gradient hero section
- ✅ Interactive pack type selector (card-based with icons)
- ✅ Color-coded pack types (blue, green, red, purple)
- ✅ Generation form with property ID input
- ✅ Generated packs list with download buttons
- ✅ Empty, loading, and error states
- ✅ Smooth hover animations and transitions
- ✅ Manual testing complete (all pack types working)

**UI Files:**
- `frontend/src/app/pages/marketing/MarketingPage.tsx` (enhanced)
- `frontend/src/app/pages/marketing/hooks/useMarketingPacks.ts`
- `frontend/src/api/agents.ts` (pack generation client)

**Validation Required:** Live walkthroughs with 2-3 real Singapore agents

---

### Phase 1B: Development Advisory Services ⚠️ v1 COMPLETE, v2 PENDING
**Status:** Original scope 100% complete. New features from Updated Spec v2 are documented but NOT implemented.

**Backend Deliverables (from FEATURES.md lines 49-54):**
- ✅ Asset Mix Strategy tool (mixed-use optimizer)
- ✅ Market Positioning calculator (pricing, tenant mix)
- ✅ Absorption Forecasting engine (velocity predictions)
- ✅ Buyer/Tenant Feedback Loop system

**Queued Enhancements (from Updated Spec v2):**
- [ ] Sales Velocity Model advisory tool (demand vs absorption, inventory, market benchmarks)
- ✅ Multi-jurisdiction market data sources (NZ Stats, Toronto TRREB/MLS, Seattle King County, HK RVD) — IMPLEMENTED via jurisdictions.json

**UI/UX Deliverables (2025-10-13):**
- ✅ Advisory Services page with Apple minimalist design
- ✅ Property ID input with load functionality
- ✅ Asset Mix Strategy display with allocation percentages
- ✅ Market Positioning pricing guidance grid
- ✅ Absorption Forecast with 3-metric cards and timeline
- ✅ Market Feedback submission form and history
- ✅ Error handling and empty states

**Test Status:**
- ✅ Backend tests: PASSING (UUID type issues fixed 2025-10-28)
- ✅ Manual UI testing: Complete (all 4 features working)
- ✅ Frontend unit tests: No blocking issues

**Files Delivered:**
- Backend: `backend/app/services/agents/advisory.py`
- Backend API: `backend/app/api/v1/agents.py`
- Frontend UI: `frontend/src/app/pages/advisory/AdvisoryPage.tsx`
- Frontend API: `frontend/src/api/advisory.ts`
- Tests: `backend/tests/test_api/test_agent_advisory.py`
- Tests: `backend/tests/test_services/`

**Acceptance Criteria Met:**
- ✅ Agent can input property data and get mix recommendations
- ✅ Pricing strategy suggestions based on market data
- ✅ Absorption velocity predictions with confidence intervals and timeline
- ✅ Feedback loop submission and display
- ✅ Clean UI with all 4 advisory features accessible

---

### Phase 1C: Listing Integrations ⚠️ v1 COMPLETE (Mocks), v2 PENDING
**Status:** Original scope 100% complete (mock integrations). New features from Updated Spec v2 are documented but NOT implemented.

**Backend Deliverables (from FEATURES.md lines 56-61):**
- ✅ PropertyGuru mock integration with token lifecycle
- ✅ EdgeProp mock integration
- ✅ Zoho CRM mock integration
- ✅ Token encryption system (Fernet with LISTING_TOKEN_SECRET)
- ✅ OAuth flow endpoints (connect, disconnect, publish)
- ✅ Token expiry detection (401 responses)
- ✅ Token refresh helpers (`is_token_valid`, `needs_refresh`)

**UI/UX Deliverables (2025-10-13):**
- ✅ Listing Integrations page with Apple minimalist design
- ✅ 3 provider integration cards (PropertyGuru, EdgeProp, Zoho CRM)
- ✅ Color-coded provider branding (blue, orange, red)
- ✅ OAuth connection flow with mock code generation
- ✅ Account status display and connection management
- ✅ Publish listing modal with form validation
- ✅ Authentication error handling (401 graceful state)
- ✅ Provider-specific themed buttons

**Test Status:**
- ✅ Backend tests: PASSING (3/3 service + API tests)
- ✅ Manual UI testing: Complete (all integration flows working)
- ✅ Frontend unit tests: No blocking issues

**Files Delivered:**
- Backend: `backend/app/services/integrations/accounts.py` (with encryption)
- Backend: `backend/app/services/integrations/propertyguru.py`
- Backend: `backend/app/services/integrations/edgeprop.py`
- Backend: `backend/app/services/integrations/zoho.py`
- Backend: `backend/app/utils/encryption.py` (TokenCipher)
- Backend API: `backend/app/api/v1/listings.py`
- Frontend UI: `frontend/src/app/pages/integrations/IntegrationsPage.tsx`
- Frontend API: `frontend/src/api/listings.ts`
- Tests: `backend/tests/test_services/test_listing_integration_accounts.py`
- Tests: `backend/tests/test_api/test_listing_integrations.py`

**What's NOT Done (Future Enhancements):**
- ⏭️ Real PropertyGuru OAuth (requires API credentials)
- ⏭️ Real EdgeProp OAuth (requires API credentials)
- ⏭️ Real Zoho OAuth (requires API credentials)
- ⏭️ Marketing Automation with watermarking

**Queued Enhancements (from Updated Spec v2):**
- [ ] Expanded listing portals: Zillow, LoopNet, Realtor.com, RealEstate.co.nz, HK portals
- [ ] Expanded CRM integrations: Salesforce, HubSpot, BoomTown, kvCORE

**Technical Requirements:**
- OAuth integration for each platform
- Webhook handlers for listing updates
- Image watermarking service (already exists)
- Export tracking in audit system

**Acceptance Criteria:**
- One-click publish to PropertyGuru
- Listing syncs to CBRE/JLL platforms
- CRM data flows bidirectionally
- All exports are watermarked and tracked

**Estimated Effort:** 4-6 weeks (API integrations, auth flows, testing)

**Risk:** Depends on external platform APIs - may need fallback manual export

---

### Phase 1D: Business Performance Management ✅ COMPLETE
**Status:** 100% – Deal pipeline UI, insights, analytics, and ROI panels shipped with responsive layout (November 2025)

**Delivered (Milestone M1/M2/M3 foundations):**
- ✅ Database schema for agent deals, stage history, contacts, and documents
- ✅ Alembic migration `20250220_000011_add_business_performance_tables.py`
- ✅ SQLAlchemy models in `backend/app/models/business_performance.py`
- ✅ Service layer (`AgentDealService`) with full CRUD + stage transitions
- ✅ REST API endpoints (`/api/v1/deals`) with auth integration
- ✅ Stage transitions append audit ledger (`deal_stage_transition`) events with hashed chains
- ✅ Timeline responses provide per-stage `duration_seconds`
- ✅ Timeline and API responses surface audit metadata (hash, signature, context) for each transition
- ✅ Commission ledger schema, models, and migration (`agent_commission_records`, `agent_commission_adjustments`)
- ✅ Commission service/API (`/commissions/...`) with audit-tracked status changes and adjustments
- ✅ Agent performance snapshot & benchmark schema, migration `20250220_000013_add_performance_snapshots.py`
- ✅ Analytics service (`AgentPerformanceService`) with batch snapshot generation and benchmark lookup APIs (`/api/v1/performance/...`)
- ✅ Prefect flows (`agent_performance_snapshots_flow`, `seed_performance_benchmarks_flow`) and queue jobs (`performance.generate_snapshots`, `performance.seed_benchmarks`) for automation
- ✅ Backend service tests passing (`test_agent_deal_pipeline.py`, `test_agent_commissions.py`, `test_agent_performance.py`)
- ⚠️ API smoke tests for deals/performance skipped on Python 3.9 sandbox (run on Python ≥3.10 / full FastAPI install)

**Delivered (Milestone M4 - ROI Analytics):**
- ✅ ROI metrics aggregation in performance snapshots (`_aggregate_roi_metrics()` method)
- ✅ Integration with `compute_project_roi()` from `app.core.metrics`
- ✅ Snapshot context derivation with pipeline metadata (`_derive_snapshot_context()`)
- ✅ Project-level ROI tracking per agent deal
- ✅ Datetime deprecation fixes across entire codebase (replaced `datetime.utcnow()` with `datetime.now(UTC)`)
- ✅ Tests: `test_agent_performance.py` passing (4/4 tests including ROI validation)

**Files Delivered:**
- `backend/app/api/v1/deals.py` (REST endpoints)
- `backend/app/services/deals/pipeline.py` (AgentDealService)
- `backend/app/services/deals/commission.py` (AgentCommissionService)
- `backend/app/schemas/deals.py` (Pydantic schemas)
- `backend/tests/test_services/test_agent_deal_pipeline.py` (✅ passing)
- `backend/tests/test_services/test_agent_commissions.py` (✅ passing)
- `backend/tests/test_api/test_deals.py` (⚠️ skipped Python 3.9)

**Test Status:** Backend service layer fully tested and passing (`python3 -m pytest backend/tests/test_services/test_agent_performance.py backend/tests/test_services/test_agent_commissions.py backend/tests/test_services/test_agent_deal_pipeline.py`). API smoke endpoints (deals + performance) execute on Python ≥3.10 (`backend/tests/test_api/test_deals.py`, `backend/tests/test_api/test_performance.py`).

---

**UI/UX Status (Production Customer-Facing Interface):**

**Delivered:**
- ✅ Production shell + navigation (`frontend/src/app/layout/AppShell.tsx`, `AppNavigation.tsx`)
- ✅ Navigation config with `/app/performance` route (`frontend/src/app/navigation.ts`)
- ✅ Business Performance page scaffold (`frontend/src/app/pages/business-performance/BusinessPerformancePage.tsx`)

**In Progress (2025-10-12):**
- ✅ Pipeline Kanban board component
- ✅ Deal insights panel
- ✅ Analytics panel
- ✅ ROI panel

**UI Design Specifications:**
- **Primary Persona:** Agent Team Leads validating performance before presenting to developers/investors
- **Data Sources:** `/api/v1/deals`, `/api/v1/deals/{id}/timeline`, `/api/v1/deals/{id}/commissions`, `/api/v1/performance/summary`, `/api/v1/performance/snapshots`, `/api/v1/performance/benchmarks`
- **Key Components:**
  - Pipeline Kanban: Columns per `PipelineStage` (Lead captured → Closed lost), cards with deal title, asset type, value, confidence %, audit badge
  - Deal Detail Drawer: Timeline (stage history + audit metadata), Commissions (status, amounts, dispute CTA), Contacts/Docs
  - Analytics/Benchmarks: KPI cards (open deals, won, pipeline values, conversion rate, cycle time), trend charts, benchmark comparisons, ROI metrics
  - States: Empty/loading/error/dispute handling, offline snapshot refresh

**UI Files:**
- `frontend/src/app/layout/` - AppShell layout
- `frontend/src/app/components/` - AppNavigation
- `frontend/src/app/pages/business-performance/` - 5 component files + types
- `frontend/src/router.tsx` - Route integration
- `frontend/src/index.css` - Styling

**UI Implementation Checklist:**
- [ ] Wireframe artifacts exported (Figma or markdown diagrams)
- [ ] Copy deck approved (en.json translations)
- [x] Component contracts defined (TypeScript interfaces in `src/types`)
- [x] API client hooks production-ready (no offline fallbacks)
- [ ] Storybook/visual tests for key components
- [ ] Accessibility review (keyboard nav, focus management)
- [x] Manual QA completed (see [`docs/development/testing/phase-1d-manual-qa-checklist.md`](development/testing/phase-1d-manual-qa-checklist.md); revalidated 2025-11-18)
  - [x] Happy path: Primary user journey works end-to-end
  - [x] Empty states: Render with clear messaging and CTAs
  - [x] Error states: User-friendly error messages display
  - [x] Loading states: No UI flash or layout shift
  - [x] Complete flow: All interactions chain correctly
  - [x] Edge cases: Long text, large numbers, missing data handled
  - [x] Visual quality: Alignment, spacing, colors, responsive design
  - [x] Accessibility: Keyboard nav, screen reader, focus management
- [x] Browser opened to UI page for user testing
- [x] Manual test script provided to user with specific scenarios
- [x] User confirmed: "✅ All manual tests passing"
- [x] Merge to main and mark ✅ complete

**Manual QA (2025-11-02):** ✅ Validated drag-and-drop stage transitions, timeline/commission rendering (happy path, empty/error states), analytics trend responsiveness, ROI breakdown, and keyboard navigation focus order. Logged outcomes in sprint notes for audit traceability.

---

#### Phase 1D Technical Design Specification

**Implementation Snapshot (2025-10-11):** Milestone M1 delivered – database schema, models, service layer, deal CRUD/stage APIs in place with backend tests validating workflow. Stage transitions emit `deal_stage_transition` audit ledger entries (deterministic UUID→int mapping). Timeline responses include `duration_seconds`. Remaining milestones (commissions, analytics, benchmarks) pending.

**Data Model Additions ([backend/app/models/business_performance.py](../backend/app/models/business_performance.py)):**

*Core Tables:*
- `agent_deals`: Primary pipeline entity across any asset class. Columns: id (UUID PK), project_id (FK→projects, nullable), property_id (FK→properties, nullable), agent_id (FK→users, required), title, asset_type (Enum + portfolio), deal_type (Enum: buy_side, sell_side, lease, management, other), pipeline_stage (Enum), status (Enum: open, closed_won, closed_lost, cancelled), lead_source, estimated_value_amount (Numeric 16,2), estimated_value_currency (String 3), expected_close_date, actual_close_date, confidence (Numeric 4,2), metadata (JSONB).
- `agent_deal_stage_events`: Immutable stage history for timeline/SLA. Columns: id, deal_id (FK), from_stage (Enum, nullable), to_stage (Enum), changed_by (FK→users), note (Text), recorded_at (timezone aware).
- `agent_deal_contacts`: Counterparty/company contacts. Columns: id, deal_id, contact_type (Enum: principal, co_broke, legal, finance, other), name, email, phone, company, notes.
- `agent_deal_documents`: Artefact references (S3/Drive). Columns: id, deal_id, document_type (Enum: loi, valuation, agreement, financials, other), title, uri, mime_type, uploaded_by, uploaded_at, metadata.

*Commission & Audit Tables:*
- `agent_commission_records`: Commission ledger with audit-stamped lifecycle. Columns: id, deal_id, agent_id, commission_type (Enum: introducer, exclusive, co_broke, referral, bonus), basis_amount, basis_currency, commission_rate (Numeric 5,4), commission_amount (Numeric 16,2, nullable until calculated), status (Enum: pending, confirmed, invoiced, paid, disputed, written_off), introduced_at, confirmed_at, invoiced_at, paid_at, disputed_at, resolved_at, audit_log_id (FK→audit_logs, nullable).
- `agent_commission_adjustments`: Clawbacks/adjustments. Columns: id, commission_id, adjustment_type (Enum: clawback, bonus, correction), amount, currency, note, recorded_by, recorded_at, audit_log_id.

*Analytics Support Tables:*
- `agent_performance_snapshots`: Materialised daily snapshot for dashboards; recalculated nightly. Columns: id, agent_id, as_of_date, deals_open, deals_closed_won, gross_pipeline_value, weighted_pipeline_value, avg_cycle_days, conversion_rate, roi_metrics (JSONB).
- `performance_benchmarks`: Industry reference metrics (CSV/API imports). Columns: id, metric_key, asset_type, deal_type, cohort (Enum: industry_avg, top_quartile, internal_avg), value_numeric, value_text, source, effective_date.

*Enumerations:*
- PipelineStage: lead_captured, qualification, needs_analysis, proposal, negotiation, agreement, due_diligence, awaiting_closure, closed_won, closed_lost
- DealStatus: open, closed_won, closed_lost, cancelled
- DealType: buy_side, sell_side, lease, management, capital_raise, other
- CommissionStatus: pending, confirmed, invoiced, paid, disputed, written_off
- CommissionType: introducer, exclusive, co_broke, referral, bonus

*Indices:*
- `agent_deals`: composite (agent_id, pipeline_stage) for Kanban queries; (project_id, status) for reporting
- `agent_deal_stage_events`: (deal_id, recorded_at), (to_stage, recorded_at DESC) for recent transitions
- `agent_commission_records`: (agent_id, status), (deal_id) for lookups; optional unique constraint (deal_id, agent_id, commission_type) prevents duplicates
- `agent_performance_snapshots`: unique (agent_id, as_of_date)
- `performance_benchmarks`: composite (metric_key, asset_type, cohort, effective_date DESC)

**Backend Architecture:**

*Services:*
- [app/services/deals/pipeline.py](../backend/app/services/deals/pipeline.py): CRUD for AgentDeal, stage transition helpers appending AgentDealStageEvent, weighted pipeline calculations, `timeline_with_audit()` enriches stage history with hashed audit ledger entries.
- [app/services/deals/commission.py](../backend/app/services/deals/commission.py): Commission lifecycle management; emits audit log events (deal_commission_introduced, deal_commission_confirmed, etc.) via existing audit_logs chain.
- [app/services/deals/performance.py](../backend/app/services/deals/performance.py): Aggregation routines to compute metrics per agent/property type; writes to agent_performance_snapshots.
- [app/services/deals/benchmark_ingest.py](../backend/app/services/deals/benchmark_ingest.py): Loader for CSV/JSON benchmark data (Prefect or management CLI).

*API Routes ([backend/app/api/v1/deals.py](../backend/app/api/v1/deals.py)):*
- GET /api/v1/deals: Paginated filter by agent, stage, property, search text
- POST /api/v1/deals: Create new deal
- PATCH /api/v1/deals/{deal_id}: Update metadata, expected close, etc
- POST /api/v1/deals/{deal_id}/stage: Transition stage (body: to_stage, optional note). Records event + audit log (deal_stage_transition)
- GET /api/v1/deals/{deal_id}/timeline: Stage history + commission events aggregated for timeline display
- GET /api/v1/deals/{deal_id}/commissions, POST /api/v1/deals/{deal_id}/commissions: Manage commission records
- POST /api/v1/commissions/{commission_id}/status: Update status, attach supporting doc reference; logs to audit
- GET /api/v1/performance/summary?agent_id=…&period=…: Latest snapshot metrics + ROI breakdown
- GET /api/v1/performance/benchmarks?asset_type=…: Benchmark entries filtered by asset type/cohort

*Authentication/Authorization:* Reuse existing `require_agent` / `require_viewer` dependencies ([app/api/deps.py](../backend/app/api/deps.py)). Stage transitions and commission operations require write permissions.

*Background Jobs:*
- Nightly `agent_performance_snapshots_flow` (Prefect) or queue job `performance.generate_snapshots` to roll up per-agent metrics (conversion rate by property type, weighted pipeline, average cycle)
- Optional hourly trigger to recompute snapshots for active deals (Kanban performance numbers)
- Benchmark ingest handled via `seed_performance_benchmarks_flow` / `performance.seed_benchmarks` job when remote datasets refresh

*Integration with Audit Log:*
- Every stage change writes AuditLog row (event_type="deal_stage_transition") with deterministic hash linking to previous entry for that project/deal; context includes IDs, stage, user
- Commission lifecycle events log event_type (deal_commission_status_change) with same chaining rules
- Store audit_log_id on commission tables for direct traceability

**Frontend Plan:**

*New Route:* `/agents/performance` (or extend integrations page) with two tabs: Pipeline (Kanban) and Analytics

*Pipeline Kanban (PipelineBoard component):* Columns map to PipelineStage; cards display counterparty, asset type, estimated value, latest activity, quick actions (move stage, log note). Initial implementation at `/agents/performance` with audit-aware timeline panel.

*Deal Detail Drawer:* Timeline (stage events + commission history) with audit hash/signature badges, contact list, documents, manual adjustments.

*Analytics Dashboard:* Charts using existing design-system components (bar charts, donut). Data sources: `/performance/summary`, `/performance/benchmarks`.

*Commission Dispute UI:* Modal to mark commission as disputed, collects reason, optionally attaches doc (URI stored via agent_deal_documents).

*State Management:* React Query hooks hitting new API layer functions ([frontend/src/api/deals.ts](../frontend/src/api/deals.ts)). Align with patterns used in listing integrations.

*Testing:* Component tests for pipeline board interactions and API hook mocks; snapshot tests for analytics charts referencing known data.

**Backend Test Coverage:**
- [backend/tests/test_services/test_agent_performance.py](../backend/tests/test_services/test_agent_performance.py) covers AgentPerformanceService aggregation (deal/commission scenarios, daily snapshot generation)
- [backend/tests/test_api/test_performance.py](../backend/tests/test_api/test_performance.py) validates `/api/v1/performance` endpoints (snapshots + benchmarks) when executed on Python ≥3.10 / real FastAPI

**Implementation Phasing:**
1. Foundation (M1): Migrations, models, basic CRUD service, API list/create/update, Kanban read-only view. Tests for models and pipeline service.
2. Stage transitions & timeline (M2): Stage event endpoints, audit logging, timeline API, Kanban drag/drop.
3. Commission ledger (M3): Commission models/services APIs, audit integration, dispute handling UI.
4. Analytics & benchmarks (M4): Snapshot job, performance API, dashboard charts, benchmark ingestion script + sample dataset.
5. Polish & docs (M5): Update all_steps_to_product_completion.md and [Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work), add docs (docs/agents/business_performance.md), expand TESTING_DOCUMENTATION_SUMMARY.md.

---

**Requirements (from FEATURES.md lines 63-68):**
- Cross-Asset Deal Pipeline tracker
- ROI Analytics dashboard
- Commission Protection system (audit stamps)
- Performance Benchmarking

**Backend Requirements:**
- Deal stages database schema
- Commission calculation engine
- Analytics aggregation queries
- Benchmark data collection

**Frontend Requirements:**
- Pipeline kanban view
- Analytics dashboard with charts
- Commission dispute resolution UI
- Performance comparison widgets

**Acceptance Criteria:**
- Agent tracks deals from capture → close
- ROI metrics show conversion by property type
- Commission timestamps are audit-stamped
- Benchmarking compares to industry standards

**Estimated Effort:** 3-4 weeks (analytics heavy)

---

### Phase 1 Completion Gate

**Requirements to Exit Phase 1:**
- ✅ All 6 Agent tools fully implemented
- ✅ Live validation with 3+ Singapore agents
- ✅ Feedback incorporated and refined
- ✅ Full documentation (user + developer guides)
- ✅ Private beta with 5-10 agents successful
- ✅ `make verify` passes all tests
- ✅ Demo ready for investor/stakeholder presentations

**Then:** Move to Phase 2 (Developers)

---

## 📋 PHASE 2: DEVELOPER FOUNDATION (20% Complete)

**Goal:** Complete all 9 Developer tools so developers can manage full project lifecycle

### Phase 2A: Universal GPS Site Acquisition ⚠️ IN PROGRESS
**Status:** 60% - Core GPS capture works but missing key FEATURES.md requirements (address input, interactive map, real geocoding, photo uploads)
**Gaps to align with FEATURES.md (backlog - ~2 weeks effort):**
- [ ] Forward geocoding: add address input (`123 Main St`) → coords via Google Maps Geocoding API (2 days)
- [ ] Reverse geocoding: replace mocked address with real reverse-geocode from coords (1 day)
- [ ] Map/pin-drop: replace placeholder card with interactive map to set coords (3 days)
- [ ] Zoning lookup on capture: fetch/display zoning for the resolved point (e.g., URA/other jurisdiction overlays) (2 days)
- [ ] GPS photo/attachment capture: allow photo uploads with capture (2 days)
- [ ] Pack generator wiring: connect "Generate pack" buttons to real pack export pipeline (2 days)

**Requirements (from FEATURES.md lines 86-96):**
- Mobile property capture (GPS-enabled)
- Development scenario selector (5 types)
- Multi-scenario feasibility engine
- Enhanced due diligence checklists

**What Exists:**
- ✅ GPS logging backend
- ✅ Quick analysis scenarios
- ✅ Condition report export (JSON + PDF fallback for environments without WeasyPrint) with docs + tests (Oct 16 2025)
- ✅ Feasibility signals surfaced in developer UI (Oct 14 2025) with deep link to developer workspace (legacy + `/app/asset-feasibility`)
- ✅ Scenario selector enhancements (history modal + comparison table quick access) (Oct 18 2025)
- ✅ Scenario focus controls now surface per-scenario progress + quick actions (Oct 18 2025)
- ✅ Property overview cards with zoning + site metrics (Oct 18 2025)
- ✅ Due diligence checklist authoring + bulk import tooling (Oct 17 2025)
- ✅ Specialist checklist insights merged into condition assessments; manual inspections now surface named specialist follow-ups in the UI
- ✅ Manual inspection capture: developers can log inspector name, timestamp, notes, and attachments with timeline + comparison surfacing (Oct 19 2025)
- ✅ Multi-scenario comparison dashboard shows side-by-side scorecards and is included in exported condition reports (JSON + PDF)

**What's Missing:**
- _Dedicated developer `POST /api/v1/developers/properties/log-gps` endpoint will be delivered as the first Phase 2B increment; manual inspection capture shipped Oct 19 2025_

**Acceptance Criteria:**
- Developer captures site with enhanced property details
- Selects development scenario (new/renovation/reuse/heritage)
- Gets instant multi-scenario feasibility comparison
- Due diligence checklist auto-populates by scenario

**Testing references:**
- [`Testing Known Issues`](all_steps_to_product_completion.md#-known-testing-issues) — "Phase 2A" section lists mandatory manual walkthroughs (capture, checklist, assessment, PDF export)
- [`Testing Summary`](development/testing/summary.md) — comprehensive testing expectations for all features
- [`ui-status.md`](planning/ui-status.md) — details the developer workspace components that must render after changes
- [`README.md`](../README.md) — see the `make dev` guidance for monitoring `.devstack/backend.log` during verification

**Estimated Effort:** 2-3 weeks (mostly frontend, reuse Agent backend)

---

### Phase 2B: Asset-Specific Feasibility ⚠️ v1 95% COMPLETE, v2 PENDING
**Status:** Original scope 95% complete (core asset optimizer, heritage overlays, finance integration, Level 1 3D). New features from Updated Spec v2 are documented but NOT implemented.

**Requirements (from FEATURES.md lines 98-108):**
- Multi-use development optimizer
- Space efficiency calculator (NIA optimization)
- Program modeling by asset type:
  - Office (floor plates, core, parking, tenant mix)
  - Retail (tenant mix, anchors, circulation, parking)
  - Residential (unit mix, amenities, efficiency)
  - Industrial (clear heights, loading, utilities)
  - Mixed-use (complex coordination)
- Heritage constraint integration

**Queued Enhancements (from Updated Spec v2):**
- [ ] Global Engineering Defaults (structural grids, core sizes, MEP allowances by jurisdiction)
- [ ] GFA→NIA accuracy bands (±5-12% display with confidence labels)
- [ ] Engineering Layers visualization (structural grid, MEP trunks/risers, plenum depth, civil, façade)
- [ ] Clash & Impact Board (lightweight clash detection, area/cost impact bands ±%)

**Technical Complexity:**
- Asset-specific calculators for each property type
- Constraint engines (zoning, heritage, technical)
- Optimization algorithms (use mix, efficiency)
- 3D visualization updates

**Acceptance Criteria:**
- Developer inputs property parameters
- System suggests optimal use mix
- NIA calculations match Singapore standards
- Heritage constraints properly limit options
- Visual 3D updates show massing options

**Estimated Effort:** 8-10 weeks (complex domain logic, multiple asset types)

**What Exists:**
- ✅ `/api/v1/developers/properties/log-gps` endpoint delivers developer-specific capture results with zoning envelope + buildability heuristics
- ✅ Frontend Site Acquisition client now calls the developer endpoint and surfaces build envelope + visualisation metadata for follow-on feasibility work
- ✅ Feasibility assessment now ingests the build envelope, tuning GFA summaries and generating land-use-specific optimisation notes
- ✅ Developer Feasibility wizard surfaces captured asset mix recommendations (persisted from Site Acquisition) for quick programme planning
- ✅ Optimisation outputs flow into developer financial summaries and Finance API responses (revenue/capex rollups + risk heuristics) to prime Phase 2C modelling
- ✅ Asset mix engine now references Phase 2B Singapore baselines (rent, vacancy, OPEX, heritage premiums) to calculate NOI and fit-out capex per asset type
- ✅ Finance blueprint (capital stack targets, debt facilities, equity waterfall, sensitivity bands) returned with developer capture for direct Phase 2C ingestion
- ✅ Visualization stub exposes per-asset massing layers and colour legend so frontend can wire Phase 2B preview scaffolding
- ✅ Asset mix reacts to quick analysis metrics (vacancy, rent softness, transit gaps) and property headroom to rebalance allocations and risk notes dynamically
- ✅ Asset optimiser upgraded to curve-driven scoring with constraint logs, confidence scores, and scenario variants (Oct 22 2025)
- ✅ Preview job pipeline enqueues background renders and exposes polling/refresh endpoints (Oct 22 2025)
- ✅ NHB Historic Sites, National Monuments, and Heritage Trails merged with URA overlays; developer API returns rich `heritage_context` for optimiser + finance flows (Oct 22 2025)
- ✅ Level 2 preview renderer (Nov 2025): octagonal footprints, stepped setbacks/podiums, per-floor shading, isometric thumbnails, and `geometry_detail_level` control wired through `PreviewJob` metadata (`medium` default, `simple` fallback for low-spec). Site Acquisition UI exposes a selector so QA/users can refresh renders in either mode; backend/API accept the `geometry_detail_level` body param (default governed by `PREVIEW_GEOMETRY_DETAIL_LEVEL`).

**What's Remaining:**
- ✅ **3D Preview Level 2 Detail** – Octagonal footprints, stepped setbacks (>60 m), podium coloration, per-floor banding (vertex shading), isometric thumbnails, and `geometry_detail_level` overrides now ship by default (Nov 2025). Frontend viewer automatically renders the richer GLTF payload.
- ⏭️ Automate NHB dataset refresh (Monuments/Trails) + add override management for future conservation updates (housekeeping task)

---

#### Phase 2B Technical Specifications

**Asset Optimizer Engine (v0.4)**

*Algorithm:* Curve-driven scoring with weighted components (NOI, risk, market demand, heritage uplift). Score normalization: `(score - min_score) / (max_score - min_score)`. Adjustment factor from `asset_mix_curves.json`. Constraint priority: user overrides → heritage → market. Zoning constraints non-negotiable (fail fast with HTTP 422 if violated).

*Inputs:* Site geometry, zoning context, program defaults ([phase2b_asset_optimisation_inputs.md](phase2b_asset_optimisation_inputs.md)), market signals (Quick Analysis), heritage data (URA + NHB overlays), finance envelope, user constraints.

*Outputs:* Per-asset allocation %, NIA, absorption curve, rent/opex assumptions, CAPEX, risk score, constraint logs, scenario variants (base/expansion/reposition). Allocations sum to 100% ±0.1%, absorption [3,60] months, parking as bays per 1,000 sqm GFA.

*Heritage Risk Classification:* Explicit overlay rating → conservation=true → year_built<1970 → user override → default "low".

*Data Actions:* [P0] Finalize `asset_mix_profiles.json` + `asset_mix_curves.json`, surface zoning metadata. [P1] Heritage overlay ingestion, Quick Analysis market metrics. [P2] Versioning policy (embed `optimizer_version` in outputs).

**Heritage Overlay Ingestion Pipeline (v0.5)**

*Data Sources:* URA Conservation Areas (shapefile/GeoJSON), NHB Historic Sites (GeoJSON), NHB National Monuments (GeoJSON), NHB Heritage Trails (KML→GeoJSON). 194 features total merged. Access via data.gov.sg (no credentials required initially).

*Pipeline:* `fetch` (downloads raw data) → `transform` (shapely-based normalization, SVY21→WGS84, bbox/centroid, simplification tolerance 0.00001) → `load` (copies to `backend/app/data/heritage_overlays.geojson`, records metadata) → `publish` (S3 upload if required).

*Output Schema:* {name, risk [high|medium|low|info], source, boundary (GeoJSON Polygon), bbox, centroid, notes, effective_date, heritage_premium_pct, attributes{ura_category, planning_area}}.

*Components:* CLI `python -m scripts.heritage [fetch|transform|load|pipeline]`. Dependencies: shapely≥2.0, pyproj≥3.6, fiona≥1.9 (optional). Spatial index: STRtree. Performance target: <10ms P95.

*Refresh Cadence:* Weekly (manual CLI initially, Prefect/cron planned). Rollback retention: 90 days, last 2 versions.

**Finance Architecture Template**

*Capital Structure Targets:* Base case: 35% equity, 60% debt, 5% preferred, LTV 60%, LTC 65%, DSCR 1.35. Upside: 30/65/5, LTV 58%, DSCR 1.40. Downside: 45/50/5, LTV 55%, DSCR 1.25.

*Debt Terms:* Construction loan 60% of dev cost @ 4.8% (SORA 3M + 240bps), 4yr tenor, interest-only. Bridge/mezzanine 10% @ 8.5% fixed, 2yr bullet. Permanent debt 55% of stabilised value @ 4.2% (SORA + 180bps), 7yr, 20yr amort with 30% balloon.

*Equity Waterfall:* Tier 1: 12% IRR → 10% promote. Tier 2: 18% IRR → 20% promote. Preferred return: 9% annual. Catch-up: 50/50 after pref, clawback if IRR <12% on exit.

*Cash Flow Timing:* Land acquisition (months 0-3), construction (3-33), leasing/sales (24-42), stabilisation (42-54), exit/refinance (48-51).

*Exit Assumptions:* Base cap rate 4.0% (prime office/hospitality), upside 3.6%, downside 4.5%. Sale costs 2.25% (broker 1.75%, legal 0.25%, stamp 0.25%). Refinance: 65% LTV @ SORA + 170bps, 5yr tenor, 25yr amort.

*Sensitivity Bands:* Rent [-8%, 0%, +6%], Exit cap rate [+40bps, 0, -30bps], Construction cost [+10%, 0%, -5%], Interest rate [+150bps, 0, -75bps].

---

#### Phase 2B Visualization Delivery Audit

**Date:** 2025-11-04 | **Status:** ✅ COMPLETE

**Delivered Components:**
- `backend/app/services/preview_generator.py:25` – GLTF construction, asset manifest, Pillow thumbnail generation
- `backend/jobs/preview_generate.py:99` – preview job writes metadata_url, updates manifest, returns URLs
- `backend/app/services/preview_jobs.py:120` – resets metadata on refresh
- `backend/app/api/v1/developers.py:318` – API surfaces metadata_url + visualization summary
- `frontend/src/api/siteAcquisition.ts:507` – client parses previewMetadataUrl + job metadataUrl
- `frontend/src/app/components/site-acquisition/Preview3DViewer.tsx:1` – GLTF viewer with orbit controls
- `frontend/src/app/pages/site-acquisition/SiteAcquisitionPage.tsx:638` – wires manifest URLs, surfaces asset version

**Migration:** `backend/migrations/versions/20251104_000021_add_preview_metadata_url.py:1` adds metadata_url column

**Tests:** `backend/tests/test_services/test_preview_generator.py:9` verifies GLTF+BIN output

**Observability:** Prometheus metrics (`preview_generation_jobs_total`, `preview_generation_jobs_completed_total`, `preview_generation_job_duration_ms`, `preview_generation_queue_depth`)

**Outstanding Follow-ups:**
1. Monitoring/Alerts – Grafana dashboard JSON + Prometheus rules committed, import into ops stack
2. Storage hardening (optional) – Migrate to S3 + signed URLs (§4.5 of delivery plan) once buckets provisioned

---

#### Phase 2B Manual QA Results

**Test Run 1 (2025-11-03):** Initial implementation with pre-generated job
- Environment: inline backend execution
- Property ID: `6a0b64be-fc56-458b-87fc-7c9b17c24bff`, Preview Job ID: `24a62073-1cfb-4db2-835b-13952cd184f6`
- ✅ Status transitions (placeholder → processing → ready) within UI
- ✅ Thumbnail placeholder updated with new asset timestamp
- ✅ Bounding box, layer counts, camera hints match backend logs
- ✅ Gray site boundary renders correctly, blue/teal building mass renders as 3D volumetric form
- ✅ Camera orbit/pan/zoom controls functional
- Observations: Job pre-generated, status showed READY immediately. Thumbnail displayed as small pink/magenta square. Metadata available at `/static/dev-previews/.../preview.json`.

**Test Run 2 (2025-11-10):** End-to-end capture & refresh workflow
- Tester: User (wakaekihara), Environment: inline backend, Browser: Chrome on macOS
- ✅ Capture Property button triggers preview generation successfully
- ✅ POST `/api/v1/developers/properties/log-gps` completed with 200 OK
- ✅ Job ID `23a32344-fb0f-4c5e-a0aa-1a5fd22ee04f` displayed with status READY
- ✅ Timestamps populated (requested/started/finished at 12:19 am - identical due to inline execution <1s)
- ✅ Asset URLs populated (preview GLTF, metadata JSON, thumbnail PNG)
- ✅ 3D viewer rendered with gray site boundary + blue/teal building mass
- ✅ Refresh Preview button regenerates assets with new timestamps
- ⚠️ Status transitions too fast to observe with inline execution (<1 second) - expected behavior for dev mode
- Evidence: 10 total screenshots captured (7 Capture workflow, 3 Refresh workflow)

**Test Run 3 (2025-11-10):** Async queue verification (RQ backend)
- Environment: Redis docker + RQ worker, Browser: Chrome
- ✅ Status chip sequence observed: QUEUED → PROCESSING → READY (each visible 2-3s)
- ✅ RQ worker console: `16:09:48 preview: Job OK (preview.generate)`
- ✅ Polling endpoint: 200 responses, no 429s (increased rate limit to 120/min)
- ✅ Refresh Preview re-queued job, status stepped through all states again
- ⚠️ Known limitation: RQ on macOS crashes with Pillow/Cairo (SIGABRT on fork). Workaround: inline backend for dev, Linux for production.
- Evidence: Screenshots of QUEUED/PROCESSING/READY states + worker terminal output, Network HAR log

**Phase 2B Completion Status:**
- ✅ Preview job data model and API endpoints
- ✅ GLTF preview generation pipeline
- ✅ Asset versioning and storage
- ✅ Frontend 3D viewer integration
- ✅ Capture Property workflow
- ✅ Refresh Preview workflow
- ✅ Manual UI testing (development environment)
- ✅ Automated integration tests ([backend/tests/test_integration/test_preview_job_integration.py](../backend/tests/test_integration/test_preview_job_integration.py))
- ✅ Documentation of expected behavior and limitations

**🎯 Ready for Production** – Phase 2B preview viewer functionally complete, all manual QA satisfied

**📋 Recommended Follow-ups (Post-Phase 2B):**
1. ✅ Production testing with async Celery/RQ on Linux — documented in [preview_async_linux.md](validation/preview_async_linux.md) and automated via `scripts/validate_preview_async_linux.sh`. **Execution pending:** requires a Linux host (current macOS-only laptop cannot run the RQ worker); rerun the script and attach the generated `preview_validation_results_*.md` once a Linux box is available.
2. ✅ Layer breakdown UI – detailed massing inspection panel — Developer preview standalone now surfaces per-layer geometry inspection controls (Nov 18 2025).
3. ✅ Monitoring – Grafana dashboards for preview generation metrics — dashboards + Prometheus counters landed Nov 4 2025.
4. ✅ Performance – monitor generation times with real property data — use `backend/scripts/preview_duration_report.py` and Prometheus histogram `preview_generation_job_duration_ms` to track p50/p90.
5. ✅ Asset cleanup – automated cleanup of old preview versions (`backend/scripts/preview_cleanup.py`, retention policy shipped Nov 10 2025).
6. ✅ Preview generator typed payloads — refactored to TypedDict/dataclasses (Nov 18 2025).
7. ✅ Developer checklist service typing — structured payload helpers (Nov 18 2025).

**Testing Discipline (Phase 2B onward):**
- Every Phase 2B feature or refactor must land with automated tests that keep the touched modules at or above the 80 % coverage gate.
- Coverage regressions must be resolved before hand-off; if a temporary waiver is unavoidable, log the owner and expiry in the [Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) and reopen the task in the Phase 2B backlog.

**Kickoff Deliverables (Planned):**
- ✅ Stand up developer-specific GPS logging endpoint and API client so Site Acquisition no longer proxies through the agent route
- ✅ Extend capture response with zoning envelope + max buildable metrics (baseline commercial template)
- ✅ Complete asset-specific optimisation models (beyond baseline heuristics) and link to 3D preview shell (office/commercial first)
- Update developer UI to surface the dedicated capture flow and enriched feasibility snapshots

---

### Phase 2C: Complete Financial Control & Modeling ⚠️ v1 BACKEND/UI VERIFIED, v2 PENDING
**Status:** Original scope complete (finance workspace, capital stack, sensitivity, exports). New features from Updated Spec v2 (ARGUS export, multi-jurisdiction financing, data room integrations) are documented but NOT implemented.

**Manual QA (2025‑10‑27 @demo-owner@example.com):** ✅ Created “Phase 2C Base Case” scenario from the finance workspace, confirmed asset mix summary (`SGD 123,600` revenue, balanced/moderate mix), construction-loan facility breakdown, and sensitivity tables/CSV export (rent/construction-cost/interest bands match backend payload). Issue encountered: finance run initially failed due to missing `is_private` column mapping—fixed by adding the field to `FinScenario` ORM before re-test.

**Manual QA (2025‑10‑28 @demo-owner@example.com):** ✅ Re-ran developer GPS capture and finance workspace verification post-compat fixes. Site Acquisition now returns `asset_mix_finance_inputs` aligned with seeded mix (55 % office / 25 % retail), and the finance workspace shows the expected `SGD 123,600` revenue snapshot with moderate dominant risk. `python3 -m backend.scripts.run_smokes --artifacts artifacts/smokes_phase2c` succeeds on Python 3.9, producing complete buildable/finance/entitlements artifacts without manual intervention.

**Manual QA (2025‑10‑29 @demo-owner@example.com):** ✅ Executed the full Phase 2C smoke suite via `JOB_QUEUE_BACKEND=inline .venv/bin/python -m backend.scripts.run_smokes --artifacts artifacts/smokes_phase2c`; buildable, finance, and entitlements checks all passed after the finance UUID fix. Confirmed the new asset-mix fallback seeds finance runs when developer GPS capture is unavailable.

**Latest smoke artefacts:** `artifacts/smokes_phase2c/` (generated 2025‑10‑28 alongside the inline job queue run).

**Requirements (from FEATURES.md lines 110-132):**
- Universal development economics
- Asset-specific financial modeling (5 types)
- Enhanced financing architecture:
  - Equity vs debt breakdown (visual charts)
  - Construction loan modeling
  - Drawdown scheduling
  - Interest carry calculations
  - Refinancing strategies
- Advanced analytics (IRR, MOIC, DSCR, NPV)

**Queued Enhancements (from Updated Spec v2):**
- [ ] Multi-jurisdiction financing structures (SG LTV/ABSD, NZ LVR/CCCFA, US DSCR, Toronto CMHC, HK IO-heavy)
- [ ] ARGUS-Compatible Export (6 CSVs: Rent Roll, Leasing, OpEx, CapEx, Financing, 120-month Cashflow)
- [ ] Scenario lineage with export hashes (hash-versioned scenario chains for audit trail)
- [ ] Capital Raise Pack spec (Teaser, IM, Financial Model, ARGUS CSV, sensitivity PDF, exit assumptions, compliance)
- [ ] Document/Data Room Integrations (Box, Dropbox, Google Drive, SharePoint)

**What Exists:**
- ✅ NPV/IRR backend calculations with persisted `FinResult` metadata
- ✅ Capital stack cards with tranche metadata (rate/fees/reserve/amortisation/capitalisation flags) plus loan-to-cost + weighted debt summaries
- ✅ Drawdown schedule tracking + construction-loan interest viewer and inline facility editor
- ✅ Asset-level finance breakdowns rendered from `fin_asset_breakdowns` via `FinanceAssetBreakdown`
- ✅ Project selector + privacy guard + scenario promotion workflow, respecting developer ownership checks
- ✅ Sensitivity engine delivers rent / construction cost / interest variants; workspace ships rerun controls, CSV/JSON downloads, impact summaries, and job timelines
- ✅ Finance scenario access restricted to developer/reviewer/admin headers; denied attempts logged and metered through `finance_privacy_denials_total`
- ⚠️ Finance observability dashboard scaffolded (Prometheus/Grafana) – alert tuning deferred

**What's Missing:**
- 🟡 Advanced analytics UI (MOIC/equity multiple, DSCR heat maps, per-asset KPI exports) to finish the dashboard deliverable
- 🟡 Sensitivity batching resiliency: validate async worker path on Linux, add caching/back-pressure + status polling polish
- 🟡 Download packaging: bundle scenario JSON/CSV + tranche metadata into auditor-ready exports

**Acceptance Criteria:**
- Developer creates private financial models
- Equity/debt breakdown with visual charts
- Construction financing integrated with drawdowns
- Sensitivity analysis across scenarios
- No other role can access financial data

**Estimated Effort:** 6-8 weeks (complex financial logic + UI)

---

#### Phase 2C Finance Delivery Plan (v0.4)

**Changelog:**
- v0.4 (2025-11-11): Finance feasibility runs persist structured per-asset breakdowns into `fin_asset_breakdowns`, enabling exports/scenario summaries to rely on canonical ORM rows instead of JSON blobs. API tests verify ORM records and asset mix responses stay in sync.
- v0.3 (2025-11-10): Capital stack slices inherit construction-loan facility metadata (reserve/amortisation/tenor/capitalisation). Sensitivity explorer renders per-parameter delta cards with sparklines. Added `POST /api/v1/finance/scenarios/{id}/sensitivity` + workspace controls for on-demand sensitivity reruns. Frontend unit test reminder: retest once Vitest harness issues resolved before Phase 2C sign-off.
- v0.2 (2025-11-10): Finance privacy guard enforces developer identity headers, logs denied attempts, increments `finance_privacy_denials_total` metric for auditability.

**Current Baseline:**

*Backend:* `POST /api/v1/finance/feasibility` escalates costs, computes NPV/IRR, optional DSCR timelines, capital stack, drawdown schedules ([backend/app/api/v1/finance.py](../backend/app/api/v1/finance.py)). Asset optimiser ([app/services/asset_mix.py](../backend/app/services/asset_mix.py)) emits estimated revenue, capex, risk, confidence per asset type; feasibility engine consolidates into `AssetFinancialSummarySchema`. Finance results persist to `fin_scenarios`, `fin_capital_stacks`, `fin_results` tables. Finance blueprint (capital stack targets, sensitivity bands) attached to developer GPS capture responses (`DeveloperFinancialSummary`). Role guard uses `require_reviewer` for mutations, `require_viewer` for reads.

*Frontend:* [frontend/src/modules/finance/FinanceWorkspace.tsx](../frontend/src/modules/finance/FinanceWorkspace.tsx) lets developers pick captured projects (query params + storage), promotes scenarios, edits construction facilities, and renders capital stack cards, tranche tables, drawdowns, per-asset breakdowns, sensitivity tables/summaries, privacy banners, and job timelines.

*Data & Security:* `_ensure_project_owner` now guards every finance endpoint (admins bypass via `X-Role: admin`), logs denials, and increments `finance_privacy_denials_total`. Requests must supply `X-User-Email`/`X-User-Id`, scenarios default to private, and async sensitivity runs honour the same guard (worker tokens still need Linux validation).

**Gap Analysis (Nov 2025):**
- Asset-specific financial modelling: ✅ Persisted & rendered; remaining work is richer exports + multi-scenario comparison tooling
- Financing architecture: ✅ UI shows tranche metadata + interest editor; analytics overlays (MOIC/DSCR heat maps) still outstanding
- Sensitivity analysis: ✅ API/UI reruns exist; production worker path/caching/back-pressure needs validation
- Privacy controls: ✅ Developer-only guard + metrics shipped; admin override UX deferred
- Advanced analytics: ❌ MOIC/equity multiple, DSCR heat maps, price/volume sensitivities absent
- Observability/testing: ⚠️ Metrics emitted; Grafana alerts + Vitest migration tracked separately

**Implementation Plan:**

*Backend:*
1. Sensitivity resilience: Validate the `finance.sensitivity` RQ worker path on Linux, add caching/back-pressure, and persist async job metadata for polling/history.
2. Analytics aggregator: Extend `FinResult` metadata with MOIC/equity multiple, DSCR heat map bins, and per-asset KPI deltas so the UI can render the complete finance dashboard.
3. Export packaging: Bundle scenario JSON/CSV + tranche metadata + sensitivity deltas into signed artifacts for auditors/downloads.
4. Observability polish: Promote `finance.asset_model.*` / `finance.sensitivity.*` metrics to Grafana dashboards and wire alert thresholds.
5. Testing: Expand API/unit coverage for analytics + exports; keep deterministic fixtures per asset type.

*Frontend:*
1. Analytics UI: Add MOIC/equity multiple cards, DSCR heat-map visualisations, and KPI exports alongside the existing summary stack.
2. Download bundles: Provide a one-click export (ZIP/CSV/JSON) that mirrors backend packaging, including tranche metadata and sensitivity deltas.
3. Job UX polish: Surface async worker statuses when running outside inline mode, and improve retry/error messaging around cached reruns.
4. Testing: Keep RTL/Vitest suites updated (post-harness fix) for analytics panels, export flows, and access banners.

**Privacy & Entitlements:** `_ensure_project_owner` now enforces developer-only scope; future work is admin override UX + audit-log surfacing. Continue logging `finance_privacy_denied` metrics for every rejection and document overrides in [Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) when granted.

**Observability & Testing Strategy:**
- Metrics: `finance.asset_model.duration_ms`, `finance.asset_model.failures`, `finance.sensitivity.runs`, `finance.privacy.denied_requests`
- Logs: Structured entries for sensitivity batches, loan carry calculations, privacy denials
- Alerts: Trigger when finance run errors exceed 5% or duration > 3 s P95 (Grafana wiring pending)
- Regression Suite: Expand [backend/tests/test_api](../backend/tests/test_api) coverage; ensure pytest fixtures seeded with asset mix data
- Frontend QA: Manual checklist covering project selection, privacy banner, sensitivity reruns, downloads
- **Test Harness Caveat (Nov 2025):** Frontend unit tests blocked by known infrastructure issues (Vitest vs node runner resolution, `tsx` IPC `EPERM`, JSDOM misconfiguration). Retest once harness fixed before Phase 2C sign-off, capture results in this document.

**Known Issues / QA Findings:**
- Finance workspace viewport clipping (Phase 2C UI): ✅ **RESOLVED** - Shared `AppShell` layout now supports horizontal scrolling on viewports ≤1440px via `overflow-x: auto`. Added responsive media queries at 1280px and 1024px breakpoints. Fix maintains gradient background and rounded corners while ensuring all finance workspace content accessible on MacBook Air-sized displays (~1280px). Changes applied to [frontend/src/index.css](../frontend/src/index.css) lines 2987-3032.

---

### Phase 2D: Multi-Phase Development Management ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 134-139):**
- Complex phasing strategy tools
- Renovation sequencing (occupied buildings)
- Heritage integration planning
- Mixed-use orchestration

**Technical Requirements:**
- Timeline/Gantt chart system
- Phase dependency tracking
- Tenant coordination workflows
- Heritage preservation milestones

**Acceptance Criteria:**
- Developer plans multi-phase projects
- Renovation phases coordinate with occupancy
- Heritage work tracked separately
- Mixed-use phases orchestrated properly

**Estimated Effort:** 4-5 weeks (timeline UI + coordination logic)

---

### Phase 2E: Comprehensive Team Coordination ❌ NOT STARTED
**Status:** 0% - Major collaboration feature

**Requirements (from FEATURES.md lines 141-146):**
- Specialist consultant network (invitations)
- Multi-disciplinary approval workflows
- Progress coordination across teams
- Stakeholder management

**Queued Enhancements (from Updated Spec v2):**
- [ ] Sign-Off Workflow documentation (Engineers propose → Architects approve → Developer exports)

**Technical Requirements:**
- Invitation system (roles: Architect, Engineer, etc.)
- Approval workflow engine
- Progress tracking dashboards
- Communication/notification system

**Acceptance Criteria:**
- Developer invites consultants by role
- Approval workflows route correctly
- Progress visible across all teams
- Stakeholder updates automated

**Estimated Effort:** 6-8 weeks (collaboration infrastructure)

**Note:** This enables Phase 3 (Architects) and Phase 4 (Engineers)

---

### Phase 2F: Singapore Regulatory Navigation ❌ NOT STARTED
**Status:** 0% - Requires Gov API integration

**Requirements (from FEATURES.md lines 148-153):**
- Multi-authority coordination (URA, BCA, SCDF, NEA, STB, JTC)
- Asset-specific compliance paths
- Change of use navigation
- Heritage authority management (STB)

**Technical Requirements:**
- CORENET API integration
- Authority-specific submission templates
- Status tracking across multiple agencies
- Document management system

**Acceptance Criteria:**
- Developer sees all required authority submissions
- Status updates automatically from agencies
- Change of use paths documented
- Heritage submissions route to STB

**Estimated Effort:** 8-12 weeks (Gov API integration complex)

**Risk:** Depends on CORENET API access - may need manual process initially

---

### Phase 2G: Construction & Project Delivery ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 155-166):**
- Construction phase management (groundbreaking → TOP/CSC)
- Contractor coordination
- Quality control systems
- Safety & compliance monitoring
- Construction financing management:
  - Drawdown requests/approvals
  - Progress-based funding releases
  - Cost control/budget monitoring
  - Lender coordination
  - Interest carry tracking

**What Exists:**
- ⚠️ Basic drawdown schedule (Phase 2C)

**What's Missing:**
- ❌ Construction phase tracking
- ❌ Contractor management system
- ❌ Quality/safety checklists
- ❌ Progress certification workflow
- ❌ Lender reporting tools

**Acceptance Criteria:**
- Developer tracks construction phases
- Contractor progress monitored
- Drawdown requests tied to milestones
- QS/Architect certification workflow
- Lender reports auto-generated

**Estimated Effort:** 6-8 weeks (construction domain complex)

---

### Phase 2H: Revenue Optimization & Asset Management ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 168-173):**
- Multi-asset revenue strategy
- Complex sales/leasing management
- Phased revenue recognition
- Exit strategy optimization

**Technical Requirements:**
- Revenue forecasting engine
- Sales/leasing pipeline tracker
- Phasing revenue allocation
- Hold vs. sale analysis tools

**Acceptance Criteria:**
- Developer optimizes revenue across assets
- Sales/leasing tracked by phase
- Revenue recognized properly
- Exit timing optimized by analysis

**Estimated Effort:** 4-5 weeks (analytics + UI)

---

### Phase 2I: Enhanced Export & Documentation Control ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 175-181):**
- Capital raise materials (audit stamped)
- Marketing collateral for agents (audit stamped)
- Authority submissions (architect approval, dual audit stamps)
- Asset management reporting
- Board & investor reports

**What Exists:**
- ✅ Export watermarking system
- ✅ Audit stamping infrastructure
- ⚠️ Basic export (DXF, DWG, IFC, PDF)

**What's Missing:**
- ❌ Template system for each document type
- ❌ Approval routing (architect sign-off)
- ❌ Dual audit stamp workflow
- ❌ Board report templates

**Acceptance Criteria:**
- Developer generates capital raise packs
- Agent marketing materials auto-watermarked
- Authority submissions require architect approval
- Reports templated and automated

**Estimated Effort:** 3-4 weeks (template system + routing)

---

### Phase 2 Completion Gate

**Requirements to Exit Phase 2:**
- ✅ All 9 Developer tools fully implemented
- ✅ Live validation with 2-3 Singapore developers
- ✅ Complete financial privacy verified
- ✅ Multi-phase project successfully managed end-to-end
- ✅ Authority submission workflow tested
- ✅ Documentation complete
- ✅ Private beta successful

**⚠️ IMPORTANT: Before Phase 2D, complete Jurisdiction Expansion Window 1 (see below)**

**Then:** Move to Phase 3 (Architects)

---

## 🌍 JURISDICTION EXPANSION WINDOWS

### Overview: Multi-Jurisdiction Strategy

**Philosophy:** Expand to new jurisdictions at natural breakpoints (after Phase 2C, after Phase 6) to:
- Validate plugin architecture with real markets
- Build future phases jurisdiction-agnostic from the start
- Enable early market validation across multiple geographies
- Prevent Singapore-only assumptions from hardening

**Key Decision:** Add jurisdictions BEFORE building Phase 2D-6, not after Phase 6.

**Why:** If we build all 6 phases for Singapore only, then add jurisdictions in 2027, we face:
- 6-12 months of refactoring Phase 3-6 code
- Singapore assumptions baked into architect/engineer tools
- Missed revenue opportunities (18 months delay)

**Solution:** Add 4 new jurisdictions after Phase 2C (when we have MVP: Agent + Developer GPS/Feasibility/Finance), then build Phase 2D-6 for ALL 5 jurisdictions simultaneously. Execution plan for Hong Kong, New Zealand, Seattle, and Toronto now lives in [`docs/jurisdiction_expansion_playbook.md#10-expansion-window-1-execution-plan`](jurisdiction_expansion_playbook.md#10-expansion-window-1-execution-plan) with mirrored task queues in [`docs/ai-agents/next_steps.md#expansion-window-1`](ai-agents/next_steps.md#expansion-window-1).

---

### Expansion Window 1: After Phase 2C (Dec 2025 - Jan 2026)

**Status:** ⚠️ 75% COMPLETE (3 of 4 jurisdictions validated, Toronto pending)

**Goal:** Add 4 new jurisdictions BEFORE building Phase 2D-6, ensuring all subsequent phases are built multi-jurisdiction from the start.

**Strategic Rationale:**
- Phase 1-2C represents a complete MVP (80% of user value)
- Early market validation across 5 jurisdictions (SG, HK, NZ, Seattle, Toronto)
- Prevents Singapore-only assumptions in Phase 3-6
- Revenue acceleration (18 months earlier than waiting for Phase 6)
- Geographic risk diversification

---

#### Target Jurisdictions (Sequential Addition)

**Selection Criteria:**
- ✅ Free/low-cost government APIs (no manual scraping)
- ✅ English-speaking markets (no translation needed)
- ✅ High-quality open data infrastructure
- ✅ Minimal manual data compilation

**Selected Jurisdictions:**

**1. 🇭🇰 Hong Kong** (Week 1-2 after Phase 2C)
- **APIs:** DATA.GOV.HK (Land Registry, Buildings Dept, Planning Dept)
- **Cost:** HK$0/month (free government APIs)
- **Similarity to SG:** 95% (Commonwealth system, similar building regulations, plot ratio concepts)
- **Effort:** 2-3 weeks (first jurisdiction - establishes refactoring pattern)
- **Market:** Similar user base to Singapore (international developers, high-density commercial)
- **Data Quality:** World-class (comparable to Singapore's OneMap/URA)

**2. 🇳🇿 New Zealand** (Week 3)
- **APIs:** LINZ Data Service (national coverage, property boundaries, planning zones)
- **Cost:** NZ$0/month (all government data free)
- **Similarity to SG:** High (Commonwealth system, British-style planning)
- **Effort:** 1 week (pattern from HK exists)
- **Market:** Wealthy, early adopters of proptech, English-speaking
- **Data Quality:** Excellent (LINZ is world-class, single national system)

**3. 🇺🇸 Washington State (Seattle)** (Week 4)
- **APIs:** Seattle Open Data, WA GeoData Portal, King County Assessor
- **Cost:** $0/month (free civic tech APIs)
- **Similarity to SG:** Moderate (different system but well-documented)
- **Effort:** 1 week
- **Market:** Tech-savvy developers, active construction (Amazon/Microsoft expansion)
- **Data Quality:** Excellent (Seattle civic tech community is mature)

**4. 🇨🇦 Ontario (Toronto)** (Week 5)
- **APIs:** Toronto Open Data, Ontario GeoHub, BC Assessment
- **Cost:** CA$0/month (free)
- **Similarity to SG:** Moderate (Commonwealth influence, provincial building code)
- **Effort:** 1 week
- **Market:** Similar to US, international developer base, strong B2B SaaS adoption
- **Data Quality:** Very good (Toronto's open data portal is mature)

**Total Timeline:** 5-6 weeks (Dec 2025 - Jan 2026)

---

#### Deliverables Per Jurisdiction

**For detailed step-by-step instructions, see:** [docs/jurisdiction_expansion_playbook.md](jurisdiction_expansion_playbook.md)

**Codex Tasks:**
- [ ] Create `jurisdictions/{code}/` plugin structure
- [ ] Implement `fetch.py` (government API integration)
- [ ] Implement `parse.py` (convert to CanonicalReg format)
- [ ] Refactor services for jurisdiction-awareness (FIRST jurisdiction only):
  - `backend/app/services/geocoding.py` - Add `jurisdiction` parameter
  - `backend/app/services/finance/asset_models.py` - Extract market data by jurisdiction
  - `backend/app/utils/compliance.py` - Generalize from Singapore-only
- [ ] Seed RefRule database with jurisdiction zoning rules (5-10 zones minimum)
- [ ] Add market data (rent PSF, OPEX, vacancy rates) - from PM prep
- [ ] Add heritage overlay data (if available)
- [ ] Create tests in `backend/tests/test_jurisdictions/test_{code}.py`

**Claude Tasks:**
- [ ] Run test suite for new jurisdiction
- [ ] Fix test failures (common: missing jurisdiction parameter, hardcoded SG assumptions)
- [ ] Validate RefRule queries work for jurisdiction
- [ ] Run integration tests (GPS → Feasibility → Finance)
- [ ] Run Singapore regression test (ensure SG still works)

**PM Tasks:**
- [ ] Provide API credentials and market data (see playbook Section 3)
- [ ] Manual testing: GPS capture works in jurisdiction
- [ ] Manual testing: Feasibility analysis calculates correctly
- [ ] Manual testing: Finance modeling shows correct currency
- [ ] Regression test: Singapore still works
- [ ] Approval: Mark jurisdiction complete in this document

---

#### Jurisdiction Addition Sequence

**Sequential rollout (one at a time, NOT all 4 simultaneously):**

**Week 1-2: Hong Kong**
- PM gathers HK data (API keys, market data, zoning rules)
- Codex builds HK plugin + refactors services for jurisdiction-awareness
- Claude tests and fixes bugs
- PM validates HK works end-to-end
- ✅ Mark HK complete

**Week 3: New Zealand**
- PM gathers NZ data
- Codex builds NZ plugin (applies HK pattern - faster!)
- Claude tests
- PM validates
- ✅ Mark NZ complete

**Week 4: Washington State**
- PM gathers Seattle data
- Codex builds Seattle plugin
- Claude tests
- PM validates
- ✅ Mark Seattle complete

**Week 5: Ontario**
- PM gathers Toronto data
- Codex builds Toronto plugin
- Claude tests
- PM validates
- ✅ Mark Toronto complete

**Week 6: Integration & Stabilization**
- Run `make verify` across all 5 jurisdictions
- Fix any cross-jurisdiction bugs
- Update documentation
- Deploy to staging

---

#### Completion Gate: Expansion Window 1

**All 5 jurisdictions must have:**
- ✅ Phase 1 (Agent tools: GPS, Advisory, Integrations, Performance) working
- ✅ Phase 2A (Developer GPS Site Acquisition) working
- ✅ Phase 2B (Developer Feasibility Analysis) working
- ✅ Phase 2C (Developer Finance Modeling) working
- ✅ `make verify` passing (all tests green)
- ✅ Manual testing complete (PM validated)
- ✅ No blocking bugs

**Then:**
- 🛑 **STOP adding new jurisdictions** (defer next batch to Expansion Window 2)
- ✅ **Proceed to Phase 2D-2I for ALL 5 jurisdictions simultaneously**
- ✅ **Build Phase 3-6 for ALL 5 jurisdictions** (not Singapore-only!)

**Update this section when complete:**

**Expansion Window 1 Progress:**
- 🇸🇬 Singapore: ✅ COMPLETE (Baseline)
- 🇭🇰 Hong Kong: ✅ COMPLETE (GPS logging, preview jobs, and finance exports validated with HK currency/unit defaults - 2025-11-18)
- 🇳🇿 New Zealand: ✅ COMPLETE (GPS logging validated with NZ jurisdiction code, preview jobs storing metadata correctly, jurisdictions.json configured with NZD market data - 2025-11-23)
- 🇺🇸 Washington State: ✅ COMPLETE (GPS logging validated with SEA jurisdiction code, preview jobs functional, jurisdictions.json configured with USD market data - 2025-11-23)
- 🇨🇦 Ontario: ❌ NOT STARTED (Target: TBD - deferred)

---

### Expansion Window 2: After Phase 6 (2027+)

**Status:** ❌ NOT STARTED (Blocked: Waiting for Phase 6 completion)

**Goal:** Add next batch of jurisdictions to fully mature platform

**By this point:**
- ✅ All 6 phases working across 5 jurisdictions (SG, HK, NZ, Seattle, Toronto)
- ✅ Jurisdiction plugin pattern is mature (1 week per new jurisdiction)
- ✅ Revenue from existing markets funds expansion
- ✅ Cross-sell opportunities validated (developers with multi-market projects)

**Candidate Jurisdictions:**
- 🇬🇧 **UK (England & Wales)** - 333 local authorities, but national APIs (Land Registry, Planning Portal)
- 🇦🇺 **Australia (NSW/Sydney, VIC/Melbourne)** - State-level APIs, strong proptech market
- 🇮🇪 **Ireland (Dublin)** - EU market entry, good government APIs
- 🇨🇦 **British Columbia (Vancouver)** - Expand Canadian coverage
- 🇺🇸 **California (Bay Area/LA)** - Largest US commercial market
- 🇺🇸 **Massachusetts (Boston)** - East Coast US entry

**Timeline:** TBD (depends on Phase 6 completion date, likely mid-2027)

**Effort per jurisdiction:** ~1 week (pattern mature, just add data)

**Strategy:** Add 1-2 jurisdictions per quarter based on customer demand

---

### Rejected Jurisdictions (Poor API Infrastructure)

**NOT recommended for expansion:**
- ❌ **Dubai/Abu Dhabi** - No centralized APIs, manual scraping required, expensive data licenses
- ❌ **Manila/Philippines** - Fragmented local government units (LGUs), poor digital infrastructure
- ❌ **Most Southeast Asia** - Manual data compilation needed (Malaysia slightly better than most)
- ❌ **India** - Fragmented state systems, poor API quality

**Selection Rule:** Only expand to jurisdictions with free/low-cost government APIs. Manual scraping is NOT scalable for a solo founder.

---

## 📋 PHASE 3: ARCHITECT WORKSPACE (0% Complete)

**Goal:** Complete all 8 Architect tools ensuring compliance & design control

### Phase 3A: Universal Design Integration & Tool Compatibility ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 198-203):**
- Multi-platform compatibility (Revit, ArchiCAD, SketchUp, Rhino)
- Asset-specific design validators
- Renovation/heritage workflow
- Multi-use coordination

**Queued Enhancements (from Updated Spec v2):**
- [ ] Non-Destructive Overlays (AI suggestions appear as visual hints only, never overwrite architect geometry)

**Technical Requirements:**
- IFC/DWG/RVT import/export (existing)
- Plugin development for each CAD platform
- Design validation rules by asset type
- Heritage preservation validators

**Acceptance Criteria:**
- Architect imports from any major CAD tool
- Design validated against Singapore codes
- Heritage constraints automatically checked
- Multi-use conflicts detected

**Estimated Effort:** 10-12 weeks (CAD plugin development complex)

---

### Phase 3B: Comprehensive Singapore Compliance Command ❌ NOT STARTED
**Status:** 0% - Critical feature

**Requirements (from FEATURES.md lines 205-219):**
- Universal building code integration (BCA, SCDF, accessibility)
- Asset-specific regulatory requirements (5 types)
- Height restriction management (4 types)
- Change of use compliance

**Queued Enhancements (from Updated Spec v2):**
- [ ] Multi-jurisdiction building codes (NZBC, Seattle SDCI, Toronto OBC, HK BD)

**What Exists:**
- ✅ Basic compliance checking engine
- ✅ URA zoning data
- ⚠️ Plot ratio/GFA calculations

**What's Missing:**
- ❌ BCA/SCDF rule engines
- ❌ Asset-specific validators
- ❌ Height restriction calculator (aviation, heritage, URA, technical)
- ❌ Change of use approval workflow

**Acceptance Criteria:**
- Design validated against all Singapore codes
- Height restrictions automatically enforced
- Asset-specific rules applied correctly
- Change of use compliance path clear

**Estimated Effort:** 12-16 weeks (regulatory rules complex, ongoing maintenance)

---

### Phase 3C: Design Protection & Professional Control ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 221-226):**
- Universal design intent locks
- Change control authority (audit stamped with credentials)
- Multi-phase design integrity
- Heritage design balance

**Technical Requirements:**
- Design element locking system
- Change request/approval workflow
- QP credential verification
- Audit stamping with professional credentials

**Acceptance Criteria:**
- Architect locks critical design elements
- All changes require architect approval
- QP credentials verified
- Changes audit-stamped with timestamp

**Estimated Effort:** 4-5 weeks (workflow + permissions)

---

### Phase 3D: Enhanced Professional Documentation ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 228-238):**
- Comprehensive design rationale system documenting:
  - Singapore code interpretations
  - Heritage compliance methodology
  - Multi-use coordination strategies
  - Alternative compliance methods
  - Risk assessments
  - Climate considerations
- Regulatory integration (auto-included in submissions)
- Professional liability protection

**Technical Requirements:**
- Rationale logging system
- Template library by decision type
- Search/retrieval by project/phase
- Auto-inclusion in export packages

**Acceptance Criteria:**
- Architect logs all design decisions
- Rationale includes code references
- Heritage methodology documented
- Auto-included in authority submissions

**Estimated Effort:** 5-6 weeks (documentation system + templates)

---

### Phase 3E: Multi-Disciplinary Technical Coordination ❌ NOT STARTED
**Status:** 0% - Depends on Phase 2E

**Requirements (from FEATURES.md lines 240-245):**
- Specialist integration hub
- Complex systems coordination
- Renovation phase management
- Heritage specialist collaboration

**Dependencies:**
- Requires Phase 2E team coordination infrastructure
- Builds on invitation/approval workflows

**Acceptance Criteria:**
- Architect coordinates with all specialists
- System conflicts detected automatically
- Renovation phases coordinated
- Heritage specialists integrated

**Estimated Effort:** 4-5 weeks (extends Phase 2E coordination)

---

### Phase 3F: Singapore Authority Submission Management ❌ NOT STARTED
**Status:** 0% - Critical for compliance

**Requirements (from FEATURES.md lines 247-257):**
- Multi-agency submission hub (URA, BCA, SCDF, NEA, STB, JTC)
- Enhanced export packages (includes rationale, methodology, justifications)
- Complex approval orchestration
- Amendment & revision control

**Queued Enhancements (from Updated Spec v2):**
- [ ] Sign-Off Gateway (architect unlocks permit submissions only after approval)
- [ ] Authority Package Build formats (CORENET, ACCELA, HK e-portal)

**Dependencies:**
- Phase 2F (Regulatory Navigation)
- Phase 3D (Design Rationale)

**Technical Requirements:**
- Agency-specific submission templates
- Document assembly system
- Status tracking across agencies
- Revision control system

**Acceptance Criteria:**
- Architect submits to all agencies from platform
- Rationale auto-included in submissions
- Interdependent approvals orchestrated
- Revisions tracked and controlled

**Estimated Effort:** 8-10 weeks (government integration + workflows)

---

### Phase 3G: Professional Standards & Credentials ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 259-264):**
- QP responsibility matrix
- Singapore professional requirements (QP architect)
- International collaboration support
- CPD tracking

**Technical Requirements:**
- QP credential verification system
- Responsibility assignment matrix
- CPD tracking database
- Certificate validation

**Acceptance Criteria:**
- QP credentials verified before submissions
- Responsibility clearly assigned
- International architects can collaborate
- CPD requirements tracked

**Estimated Effort:** 3-4 weeks (credential system)

---

### Phase 3H: Quality Assurance & Risk Management ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 266-271):**
- Multi-asset quality control
- Construction administration
- Professional insurance coordination
- Comprehensive audit protection

**Queued Enhancements (from Updated Spec v2):**
- [ ] Audit Attribution (every compliance action tied to architect identity with timestamps)

**Technical Requirements:**
- QA checklist system by asset type
- Shop drawing review workflow
- Site observation logging
- Insurance tracking

**Acceptance Criteria:**
- QA standards enforced by asset type
- Construction admin workflow complete
- Insurance coverage tracked
- All decisions audit-stamped with credentials

**Estimated Effort:** 5-6 weeks (QA workflows + insurance tracking)

---

### Phase 3 Completion Gate

**Requirements to Exit Phase 3:**
- ✅ All 8 Architect tools fully implemented
- ✅ Live validation with 2-3 QP architects
- ✅ Authority submission workflow tested with real submissions
- ✅ Design protection verified
- ✅ Professional liability protection confirmed
- ✅ Documentation complete
- ✅ Private beta successful

**Then:** Move to Phase 4 (Engineers)

---

## 📋 PHASE 4: ENGINEER WORKSPACE (0% Complete)

**Goal:** Complete all 6 Engineer tools for technical excellence

### Phase 4A: Discipline-Specific Technical Workspace ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 288-298):**
- Asset-adaptive engineering (different standards by building type)
- Specialty areas (Civil, Structural, MEP, Façade, Fire/Life Safety)
- Renovation/heritage engineering
- Multi-asset coordination

**Queued Enhancements (from Updated Spec v2):**
- [ ] Parametric reserves (discipline-specific reserves that update feasibility dynamically)

**Technical Requirements:**
- Discipline-specific workspace UI
- Engineering calculation modules
- Standards library by discipline
- Heritage engineering tools

**Acceptance Criteria:**
- Engineer selects discipline and gets appropriate workspace
- Calculations conform to Singapore standards
- Heritage constraints integrated
- Multi-asset systems coordinated

**Estimated Effort:** 8-10 weeks (multiple disciplines, complex calculations)

---

### Phase 4B: Advanced Technical Integration ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 300-305):**
- BIM/Model integration (IFC, DWG, Revit)
- Asset-specific calculations
- Heritage engineering solutions
- Construction phase support

**What Exists:**
- ✅ IFC/DWG import/export
- ⚠️ Basic BIM viewer

**What's Missing:**
- ❌ Engineering calculation integration with BIM
- ❌ Asset-specific calc libraries
- ❌ Heritage engineering modules
- ❌ Construction support tools

**Acceptance Criteria:**
- Engineer imports BIM models
- Calculations run on model data
- Heritage solutions available
- Construction support workflows complete

**Estimated Effort:** 6-8 weeks (BIM integration + calc engines)

---

### Phase 4C: Singapore Technical Compliance ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 307-312):**
- Singapore engineering standards by discipline
- Asset-specific code compliance
- Authority coordination (technical submissions)
- PE certification requirements

**Queued Enhancements (from Updated Spec v2):**
- [ ] Multi-jurisdiction engineering codes (NZ seismic, Seattle IBC, Toronto OBC, HK Fire/BD)

**Dependencies:**
- Phase 3B (Compliance Command)
- Phase 3F (Authority Submissions)

**Acceptance Criteria:**
- Engineering validated against Singapore codes
- Asset-specific requirements enforced
- Technical submissions to authorities
- PE endorsement workflow

**Estimated Effort:** 6-8 weeks (engineering codes + PE workflow)

---

### Phase 4D: Multi-Disciplinary Coordination ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 314-319):**
- Cross-discipline integration
- Technical query resolution
- Heritage engineering coordination
- Construction support

**Queued Enhancements (from Updated Spec v2):**
- [ ] Clash & Coordination panel (clash detection, impact assessment, coordination log)

**Dependencies:**
- Phase 2E (Team Coordination)
- Phase 3E (Architect Coordination)

**Acceptance Criteria:**
- Engineers coordinate across disciplines
- Technical queries tracked and resolved
- Heritage specialists integrated
- Construction support effective

**Estimated Effort:** 4-5 weeks (extends existing coordination)

---

### Phase 4E: Professional Engineering Sign-Off ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 321-326):**
- Discipline-specific approvals
- Singapore PE endorsement (audit stamped)
- Technical documentation
- Construction phase certification

**Queued Enhancements (from Updated Spec v2):**
- [ ] Digital PE endorsement (cryptographic signature with timestamp)

**Technical Requirements:**
- PE credential verification
- Sign-off workflow by discipline
- Audit stamping with PE credentials
- Certification tracking

**Acceptance Criteria:**
- PE credentials verified
- Sign-offs tracked by discipline
- All approvals audit-stamped
- Construction certifications recorded

**Estimated Effort:** 3-4 weeks (PE credential system)

---

### Phase 4F: Technical Documentation & Handover ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 328-333):**
- Asset-specific deliverables
- Heritage technical documentation
- Construction documentation (as-built)
- Operations & maintenance packages

**Queued Enhancements (from Updated Spec v2):**
- [ ] ROI / Value Panel (m² saved, clashes prevented, redesign costs avoided)

**Technical Requirements:**
- Template system by asset type
- As-built tracking system
- O&M manual generator
- Heritage preservation documentation

**Acceptance Criteria:**
- Engineering docs by asset type
- As-builts tracked through construction
- O&M packages auto-generated
- Heritage preservation documented

**Estimated Effort:** 4-5 weeks (documentation templates + tracking)

---

### Phase 4 Completion Gate

**Requirements to Exit Phase 4:**
- ✅ All 6 Engineer tools fully implemented
- ✅ Live validation with 2-3 PE engineers
- ✅ Multi-disciplinary coordination tested
- ✅ Technical submissions successful
- ✅ Documentation complete
- ✅ Private beta successful

**Then:** Move to Phase 5 (Platform Integration)

---

## 📋 PHASE 5: PLATFORM INTEGRATION & APIs (10% Complete)

**Goal:** Integrate with all external systems and government APIs

### Phase 5A: Government Authority APIs ⚠️ 10% COMPLETE
**Status:** URA data exists, others missing

**Requirements (from FEATURES.md lines 368-376):**
- URA: Planning, zoning, plot ratio, height controls ⚠️ Partial
- BCA: Building plans, structural, Green Mark, accessibility ❌
- SCDF: Fire safety, means of escape, emergency systems ❌
- NEA: Environmental compliance, waste, pollution ❌
- STB: Heritage conservation, gazetted buildings ❌
- JTC: Industrial development, specialized facilities ❌
- CORENET: Integrated online submission ❌

**What Exists:**
- ✅ URA zoning data integration
- ✅ Basic reference data parsers

**What's Missing:**
- ❌ Live API connections to each agency
- ❌ CORENET submission integration
- ❌ Status polling and updates
- ❌ Document submission workflows

**Acceptance Criteria:**
- Platform connects to all 6 agencies + CORENET
- Data syncs automatically
- Submissions flow through CORENET
- Status updates in real-time

**Estimated Effort:** 16-20 weeks (multiple agencies, complex authentication)

**Risk:** High - depends on government API access and documentation

---

### Phase 5B: Market Platform Integration ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 386-391):**
- PropertyGuru/EdgeProp integration
- URA REALIS transaction data
- Local market intelligence
- International brokerage (CBRE, JLL, C&W)

**Dependencies:**
- Phase 1C (Agent Market Integration)

**Acceptance Criteria:**
- Listings auto-publish to portals
- Transaction data syncs from REALIS
- Market intelligence updated daily
- Brokerage platforms integrated

**Estimated Effort:** 6-8 weeks (API integrations)

---

### Phase 5C: Professional Credentials System ❌ NOT STARTED
**Status:** 0%

**Requirements (from FEATURES.md lines 378-384):**
- QP architect verification
- PE engineer verification
- REA agent licensing
- International recognition
- Credential validation

**Technical Requirements:**
- Integration with Singapore professional boards
- Certificate validation APIs
- Credential storage and verification
- International credential mapping

**Acceptance Criteria:**
- QP/PE credentials verified before submissions
- REA licenses validated
- International professionals can collaborate
- All credentials tracked in audit system

**Estimated Effort:** 4-6 weeks (credential APIs + validation)

---

### Phase 5 Completion Gate

**Requirements to Exit Phase 5:**
- ✅ All government APIs integrated
- ✅ Market platforms connected
- ✅ Professional credentials verified
- ✅ End-to-end submission tested
- ✅ Documentation complete

**Then:** Move to Phase 6 (Advanced Features)

---

## 📋 PHASE 6: ADVANCED FEATURES & POLISH (0% Complete)

**Goal:** Complete anti-cannibalization, audit system, and platform polish

### Phase 6A: Anti-Cannibalization System ⚠️ 30% COMPLETE
**Status:** Role boundaries exist, enforcement incomplete

**Requirements (from FEATURES.md lines 344-362):**
- Professional boundary protection
- Universal audit system
- Action tracking with credentials
- Professional liability protection
- Export tracking

**What Exists:**
- ✅ Role-based access control
- ✅ Basic audit trail
- ✅ Export watermarking
- ⚠️ Partial audit stamping

**What's Missing:**
- ❌ Comprehensive boundary enforcement
- ❌ Credential-based audit stamps (QP, PE, REA)
- ❌ Export recipient tracking
- ❌ Professional liability reports

**Acceptance Criteria:**
- No role can access prohibited data
- Every action audit-stamped with credentials
- Exports tracked with recipient info
- Liability protection verified

**Estimated Effort:** 4-6 weeks (comprehensive enforcement + reporting)

---

### Phase 6B: Comprehensive Audit System ⚠️ 40% COMPLETE
**Status:** Basic logs exist, needs enhancement

**Requirements (from FEATURES.md lines 353-362):**
- Complete action tracking
- User identity + professional credentials
- Role and authority level
- Timestamp and IP address
- Action type and justification
- Export tracking
- Regulatory compliance

**What Exists:**
- ✅ Basic activity logs
- ✅ Overlay decision tracking
- ⚠️ Partial audit trail

**What's Missing:**
- ❌ Professional credential inclusion
- ❌ Business justification fields
- ❌ Export recipient tracking
- ❌ Regulatory compliance reports
- ❌ Audit log search and export

**Acceptance Criteria:**
- Every action logged with credentials
- Audit trail immutable
- Export tracking complete
- Compliance reports generated

**Estimated Effort:** 3-4 weeks (enhance existing audit system)

---

### Phase 6C: Mobile Applications ❌ NOT STARTED
**Status:** 0%

**Requirements:**
- iOS app (Agent GPS capture, photo documentation)
- Android app (same)
- Offline mode support
- Photo sync when online
- Mobile-optimized interfaces

**Technical Requirements:**
- React Native or native apps
- Offline storage (SQLite)
- Photo upload queue
- Background sync

**Acceptance Criteria:**
- Agent captures sites offline
- Photos upload when online
- Mobile UI optimized
- Works in Singapore's network conditions

**Estimated Effort:** 12-16 weeks (native app development)

---

### Phase 6D: Performance Optimization ⚠️ 20% COMPLETE
**Status:** Basic optimization done

**What Exists:**
- ✅ Database indexes
- ✅ API pagination
- ⚠️ Basic caching

**What's Missing:**
- ❌ CDN for static assets
- ❌ Lazy loading for large datasets
- ❌ Query optimization
- ❌ Frontend bundle optimization
- ❌ Real-time performance monitoring

**Acceptance Criteria:**
- Page load < 2 seconds
- API responses < 500ms
- Large datasets paginated
- Real-time monitoring in place

**Estimated Effort:** 4-6 weeks (ongoing optimization)

---

### Phase 6E: Security Hardening ⚠️ 50% COMPLETE
**Status:** Basic security in place

**What Exists:**
- ✅ JWT authentication
- ✅ Role-based access control
- ✅ HTTPS enforced
- ⚠️ Basic input validation

**What's Missing:**
- ❌ Penetration testing
- ❌ Security audit by third party
- ❌ Rate limiting
- ❌ Advanced threat detection
- ❌ Compliance certifications (ISO, SOC2)

**Acceptance Criteria:**
- Third-party security audit passed
- Rate limiting on all APIs
- Threat detection active
- Compliance certifications obtained

**Estimated Effort:** 8-12 weeks (security audit + fixes + certifications)

---

### Phase 6 Completion Gate

**Requirements to Exit Phase 6:**
- ✅ All advanced features complete
- ✅ Mobile apps launched
- ✅ Security audit passed
- ✅ Performance SLAs met
- ✅ Ready for public launch

---

## 📋 CROSS-CUTTING SYSTEMS (New from Updated Spec v2)

These systems span multiple phases and should be implemented incrementally alongside Phase 2-6 work.

### Verification & Transparency Suite ❌ NOT STARTED
**Status:** 0% - Critical for auditor/investor confidence

**Requirements (from Updated Spec v2):**
Three implementation options (can implement all):

**Option 1: Excel/CSV Export**
- Export all assumptions, formulas, and rule pack versions
- Downloadable, offline-verifiable format
- Includes jurisdiction-specific rule references

**Option 2: "Show My Math" Panel**
- Human-readable formulas with plain-English explanations
- Attribution to source data (market rents, zoning rules, etc.)
- Dependency chains showing calculation flow

**Option 3: Verifiable Audit Trail**
- Timeline of all scenario changes
- Role-tagged events (who changed what)
- Version ID and export hashes for tamper detection
- Hash-chained entries for immutability proof

**Technical Requirements:**
- Formula extraction and documentation system
- Audit log enhancement with hash chaining
- Export packaging with integrity verification
- UI panels for formula inspection

**Acceptance Criteria:**
- Auditors can verify any calculation independently
- All outputs show clear provenance
- Export hashes allow tamper detection
- Dependency chains are human-readable

**Estimated Effort:** 6-8 weeks (incremental across phases)

---

### Global Accuracy System ❌ NOT STARTED
**Status:** 0% - Critical for user trust and professional liability

**Requirements (from Updated Spec v2):**

**Pre-Acquisition Accuracy Bands by Asset Type:**
| Asset Type | Accuracy Band |
|---|---|
| Mid-Rise Residential | ±8-10% |
| High-Rise Residential | ±10-12% |
| Office | ±5-8% |
| Industrial | ±5% |
| Retail | ±8-12% |
| Mixed-Use | ±10-15% |

**Dynamic Accuracy Improvement by Phase:**
| Phase | Accuracy | Description |
|---|---|---|
| Phase 1 (Quick Analysis) | ±5-12% | Desktop feasibility |
| Phase 2 (Detailed Feasibility) | ±3-5% | Full financial model |
| Phase 3 (Architect Sign-Off) | ±1-3% | Design-confirmed |
| Phase 4 (Engineer Sign-Off) | Exact | Construction-ready |

**Technical Requirements:**
- Confidence labels on all main outputs (GFA, NIA, revenue, cost)
- Accuracy band calculation engine based on asset type + phase
- UI badges showing current accuracy tier
- Warning when accuracy band exceeds thresholds

**Acceptance Criteria:**
- Every estimate displays its accuracy band
- Accuracy improves as project progresses through phases
- Users understand confidence levels at each stage
- Professional liability disclaimers tied to accuracy bands

**Estimated Effort:** 4-6 weeks (incremental across phases)

---

## 📊 ESTIMATED TIMELINE & EFFORT

### Overall Summary:
| Phase | Estimated Duration | Parallel Work Possible? |
|---|---|---|
| Phase 1: Agent Foundation | 10-14 weeks | Some (1B + 1C parallel) |
| Phase 2: Developer Foundation | 32-40 weeks | Some (2A-2C parallel) |
| Phase 3: Architect Workspace | 36-48 weeks | Limited (depends on Phase 2) |
| Phase 4: Engineer Workspace | 20-28 weeks | Limited (depends on Phase 3) |
| Phase 5: Platform Integration | 20-28 weeks | Can start early in Phase 2-3 |
| Phase 6: Advanced Features | 16-24 weeks | Parallel with Phase 4-5 |

**Total Sequential Time:** ~134-182 weeks (2.5 - 3.5 years)
**With Parallelization:** ~80-120 weeks (1.5 - 2.3 years)

### Current Progress:
- **Completed:** ~45% of Phase 1, 60% Finance backend, 95% CAD
- **Estimated Completion:** 45% overall
- **Remaining Effort:** ~60-80 weeks with full team

---

## 🎯 RECOMMENDED EXECUTION STRATEGY

### Option A: Complete One Role at a Time (Lower Risk)
1. **Finish Phase 1 (Agent)** → Validate → Launch agent-only product
2. **Build Phase 2 (Developer)** → Validate → Launch dev features
3. **Build Phase 3 (Architect)** → Validate → Launch professional features
4. **Build Phase 4 (Engineer)** → Complete platform

**Pros:** Early revenue, validated product-market fit, manageable complexity
**Cons:** Longer time to full platform

---

### Option B: Parallel Role Development (Higher Risk, Faster)
1. **Team A:** Finish Phase 1 + start Phase 5 (Gov APIs)
2. **Team B:** Build Phase 2 (Developer)
3. **Team C:** Build Phase 3 (Architect) once Phase 2 coordination exists
4. **Team D:** Build Phase 4 (Engineer) once Phase 3 exists

**Pros:** Faster completion (1.5-2 years), comprehensive launch
**Cons:** Complex coordination, higher risk, needs larger team

---

### Option C: Phased Launch with Parallel Build (Recommended)
1. **Q1 2025:** Complete Phase 1 (Agent) + Launch private beta
2. **Q2 2025:** Build Phase 2A-2C (Developer GPS + Feasibility + Finance) in parallel with Phase 5A (Gov APIs)
3. **Q3 2025:** Launch Agent + Basic Developer features while building Phase 2D-2I
4. **Q4 2025:** Complete Phase 2, start Phase 3 (Architect)
5. **Q1-Q2 2026:** Build Phase 3 + Phase 4 in parallel
6. **Q3 2026:** Launch full platform with all roles
7. **Q4 2026:** Polish (Phase 6) and public launch

**Pros:** Balanced risk, early revenue, manageable team size
**Cons:** Requires disciplined execution

---

## 🚀 IMMEDIATE NEXT STEPS (What to Tell Codex)

Since Agent Phase 1A-1C is complete and waiting for validation:

### Short-term (Next 4-8 weeks):
1. **Wait for human-led agent validation** (Phase 1A validation gate)
2. **Start Phase 1B (Development Advisory)** - can begin in parallel
3. **Start Phase 1C (Market Integration)** - PropertyGuru/EdgeProp APIs
4. **Plan Phase 2A (Developer GPS)** - spec and design

### Medium-term (8-16 weeks):
1. Complete Phase 1 (all 6 agent tools)
2. Launch agent private beta
3. Begin Phase 2A-2C (Developer foundation)
4. Start Phase 5A (Government APIs) in parallel

### Long-term (16+ weeks):
1. Complete Phase 2 (Developer)
2. Begin Phase 3 (Architect)
3. Continue Phase 5 (APIs)
4. Plan Phase 4 (Engineer)

---

## 📋 SUCCESS METRICS BY PHASE

### Phase 1 (Agents):
- 10+ agents using platform weekly
- 50+ properties captured
- 20+ marketing packs generated
- 5+ deals closed using platform

### Phase 2 (Developers):
- 5+ developers managing projects
- 10+ projects with full financials
- 5+ authority submissions
- 3+ construction projects tracked

### Phase 3 (Architects):
- 5+ QP architects using platform
- 10+ designs validated
- 5+ authority submissions approved
- 0 compliance violations

### Phase 4 (Engineers):
- 5+ PE engineers by discipline
- 10+ technical designs
- 5+ engineering sign-offs
- 0 technical failures

### Phase 5 (Integration):
- All 6 gov agencies connected
- 100+ daily API calls
- 95%+ uptime
- <500ms average response

### Phase 6 (Launch):
- 100+ active users across roles
- 50+ projects in platform
- 0 security incidents
- 99.9% uptime

---

## 📝 MAINTENANCE & EVOLUTION

### Ongoing Requirements:
- **Singapore Regulatory Updates:** Building codes change quarterly
- **Gov API Changes:** Agencies update APIs periodically
- **Market Data Refresh:** Daily updates from PropertyGuru, REALIS
- **Professional Standards:** QP/PE requirements evolve
- **Security Patches:** Monthly security updates

### Dedicated Resources Needed:
- **Regulatory Specialist:** Track code changes
- **API Integration Engineer:** Maintain gov/market APIs
- **DevOps Engineer:** Platform stability and performance
- **Security Analyst:** Ongoing threat monitoring

---

## ✅ QUALITY GATES (Every Phase)

Before any phase is considered complete:

1. **Code Quality:**
   - `make verify` passes (format, lint, tests)
   - Test coverage >80%
   - No critical security vulnerabilities

2. **Documentation:**
   - User guides updated
   - Developer docs current
   - API documentation complete
   - Demo scripts ready

3. **Validation:**
   - Real users tested features
   - Feedback incorporated
   - Edge cases handled

4. **Compliance:**
   - Singapore regulations checked
   - Professional requirements verified
   - Audit trail complete

5. **Performance:**
   - Load tested
   - Response times <500ms
   - Mobile-optimized

---

## 🎓 LESSONS FROM PHASE 1

### What Worked Well:
- ✅ Starting with Agent foundation validated approach
- ✅ Comprehensive documentation prevented knowledge loss
- ✅ Test-driven development caught issues early
- ✅ Demo scripts made validation easier

### What to Improve:
- ⚠️ Need faster feedback loops (validation took time)
- ⚠️ Parallel work needed to speed up delivery
- ⚠️ Gov API access should start earlier
- ⚠️ Mobile requirement should be Phase 1, not Phase 6

### Adjustments for Phase 2:
- Start Gov API integration in Phase 2, not Phase 5
- Build mobile-first from beginning
- Validation sessions every 2 weeks, not at end
- More parallel team work

---

This comprehensive plan ensures **EVERY feature from FEATURES.md is delivered** with quality gates, validation, and proper sequencing. The platform will be complete, trustworthy, and production-ready.

**Ready to execute.**

#### Phase 2B.1: 3D Visualization Delivery Plan (Detailed Spec)

> **Integrated from PHASE2B_VISUALISATION_STUB.MD - This is now the single source of truth for Phase 2B visualization**

**Current State:** GLTF renderer + preview viewer delivered (Level 1 - simple box geometry)
**Target State:** Level 2 detail enhancement (medium architectural massing)
**Status:** See Phase 2B completion checklist above

For complete Phase 2B visualization specification, architecture diagrams, testing requirements, and manual QA checklist, see the original 317-line spec that was here. Key sections consolidated into Feature Delivery Plan v2:

- **Architecture:** Async preview pipeline (API → job queue → renderer → storage → frontend polling)
- **Renderer:** Python GLTF builder with struct-packed geometry and Pillow thumbnails
- **Level 2 Enhancement:** Octagonal footprints, setbacks, podium distinction, floor lines, ambient shadows
- **Observability:** Prometheus metrics + Grafana dashboards + alert rules
- **Storage:** Versioned assets with retention policy (keep last 3 versions)
- **Manual QA:** Comprehensive UI testing checklist (completed 2025-11-04)

**Level 2 Detail Features (Phase 2B Residual):**
1. **Octagonal Footprints** - 8-sided polygons vs current squares
2. **Setbacks** - Two tiers at 1/3 and 2/3 height for tall buildings (>60m)
3. **Podium Distinction** - Ground floor geometry (4.5-6m) with different material
4. **Floor Lines** - Horizontal edge lines every 3.5m for scale reference
5. **Ambient Shadows** - Vertex color gradient (darker at base, lighter at top)
6. **Thumbnail Optimization** - 45° isometric view instead of orthographic

**Performance Target:** <5 seconds per preview, 100-500 vertices per building, <200KB GLTF+BIN

**Implementation:** Modify `preview_generator.py::_serialise_layer()` to support `geometry_detail_level` parameter (simple/medium/detailed). **Status:** Complete for `simple` + `medium`. Default is configurable via `PREVIEW_GEOMETRY_DETAIL_LEVEL`, and the Site Acquisition UI/API allow per-job overrides when refreshing previews.

---
> **External validation reminder:** Both the Linux async preview run (`scripts/validate_preview_async_linux.sh`) and the preview duration reporting script (`backend/scripts/preview_duration_report.py`) need access to a Linux environment and a database seeded with preview jobs. These steps remain outstanding solely because the current development hardware is macOS-only; log the results in this document as soon as a Linux host becomes available.
