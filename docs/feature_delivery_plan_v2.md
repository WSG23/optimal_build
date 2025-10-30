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
> **Last Updated:** 2025-10-23 (reflects status from detailed sections)
>
> **🤖 AI AGENTS:** Read [docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md](NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md) for guidance on choosing your next task.

---

### ✅ Phase Gate Checklist (Pre-Phase 2D Readiness)

> Update these checkboxes only after the corresponding work is fully complete and documented.
> `scripts/check_phase_gate.py` enforces these gates for any Phase 2D commits.

- [ ] Phase 2D Gate: Pre-Phase 2D Infrastructure Audit & Quality Sprint complete (`PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.md`)
- [ ] Phase 2D Gate: Phase 1D Business Performance UI backlog delivered & QA signed off (see lines 274‑392)
- [ ] Phase 2D Gate: Phase 2B visualisation residual work delivered (see lines 455‑508)
- [ ] Phase 2D Gate: Expansion Window 1 (HK, NZ, Seattle, Toronto) complete (`docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md`)

---

### ✅ Complete Phases

**[Phase 1A: GPS Capture & Quick Analysis](#phase-1a-gps-capture--quick-analysis)** ✅ COMPLETE
- **Backend:** 100% | **UI:** 100%
- **Status source:** Detailed section confirms "✅ COMPLETE"
- GPS Capture, Quick Analysis, Marketing Pack Generator all shipped
- [Jump to details ↓](#phase-1a-gps-capture--quick-analysis)

**[Phase 1B: Agent Advisory Services](#phase-1b-agent-advisory-services)** ✅ COMPLETE
- **Backend:** 100% | **UI:** 100%
- **Status source:** Detailed section confirms "✅ COMPLETE"
- Asset Mix Strategy, Market Positioning, Absorption Forecasting, Feedback Loop
- [Jump to details ↓](#phase-1b-agent-advisory-services)

**[Phase 1C: Listing Integrations (Mocks)](#phase-1c-listing-integrations-mocks)** ✅ COMPLETE
- **Backend:** 100% | **UI:** 100%
- **Status source:** Detailed section confirms "✅ COMPLETE (Mocks)"
- PropertyGuru mock, EdgeProp mock, Zoho CRM mock, Token encryption
- Note: Real OAuth pending API credentials (future work, not blocking)
- [Jump to details ↓](#phase-1c-listing-integrations-mocks)

**[Phase 2A: Universal GPS Site Acquisition](#phase-2a-universal-gps-site-acquisition)** ✅ COMPLETE
- **Backend:** 100% | **UI:** 100%
- **Status source:** Detailed section confirms "✅ COMPLETE"
- Site Acquisition workspace, due diligence checklists, manual inspection capture
- [Jump to details ↓](#phase-2a-universal-gps-site-acquisition)

---

### ⏸️ In Progress Phases

**[Phase 1D: Business Performance Management](#phase-1d-business-performance-management)** ⚠️ IN PROGRESS
- **Backend:** 100% | **UI:** 20%
- **Status source:** [Line 268](#phase-1d-business-performance-management) says "⚠️ IN PROGRESS - 60%"
- **Completed:** Deal Pipeline API ✅, Commission ledger ✅, ROI Analytics backend ✅, Performance Snapshots ✅
- **Missing:** Pipeline Kanban UI, Deal insights panel, Analytics panel, ROI panel, Manual UI testing (0/8 checks done)
- [Jump to details ↓](#phase-1d-business-performance-management)

**[Phase 2B: Asset-Specific Feasibility](#phase-2b-asset-specific-feasibility)** ⚠️ IN PROGRESS
- **Backend:** 100% | **UI:** 85%
- **Status source:** [Line 416](#phase-2b-asset-specific-feasibility) says "⚠️ IN PROGRESS"
- **Completed:** Asset optimizer ✅, Heritage overlay backend ✅, Preview job infrastructure ✅
- **Missing:** 3D preview UI renderer (GLB generation + interactive viewer) - See [phase2b_visualisation_stub.md](phase2b_visualisation_stub.md)
- [Jump to details ↓](#phase-2b-asset-specific-feasibility)

**[Phase 2C: Complete Financial Control & Modeling](#phase-2c-complete-financial-control--modeling)** ⚠️ IN PROGRESS
- **Backend:** 80% | **UI:** 40%
- **Status source:** [Line 472](#phase-2c-complete-financial-control--modeling)
- **Completed:** Asset finance engine ✅, Construction loan interest ✅
- **Missing:** Sensitivity analysis UI, async batching, tranche editing
- [Jump to details ↓](#phase-2c-complete-financial-control--modeling)

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
- Looking for next task? → [NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md](NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md)
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

## 📋 PHASE 1: AGENT FOUNDATION (100% Complete) ✅

**Goal:** Complete all 6 Agent tools so agents can work entire development lifecycle

### Phase 1A: GPS Capture & Quick Analysis ✅ COMPLETE
**Status:** 100% - Backend + UI Complete, Ready for validation

**Backend Deliverables:**
- ✅ Mobile GPS Logger with Singapore coordinate capture
- ✅ Multi-scenario quick analysis (raw land, existing, heritage, underused)
- ✅ Photo documentation with GPS tagging
- ✅ Quick 3D visualization (basic massing)
- ✅ Market intelligence integration
- ✅ Marketing pack generation (4 types: Universal, Investment, Sales, Lease)
- ✅ PDF download endpoint with absolute URLs
- ✅ Documentation & demo scripts

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

### Phase 1B: Development Advisory Services ✅ COMPLETE
**Status:** 100% - Backend + UI Complete (2025-10-13)

**Backend Deliverables (from FEATURES.md lines 49-54):**
- ✅ Asset Mix Strategy tool (mixed-use optimizer)
- ✅ Market Positioning calculator (pricing, tenant mix)
- ✅ Absorption Forecasting engine (velocity predictions)
- ✅ Buyer/Tenant Feedback Loop system

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

### Phase 1C: Listing Integrations ✅ COMPLETE (Mocks)
**Status:** 100% - Backend + UI Complete (2025-10-13)

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

### Phase 1D: Business Performance Management ⚠️ IN PROGRESS
**Status:** 60% - Deal pipeline + commission ledger + ROI analytics (October 2025)

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
- 🔄 Pipeline Kanban board component
- 🔄 Deal insights panel
- 🔄 Analytics panel
- 🔄 ROI panel

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
- [ ] Component contracts defined (TypeScript interfaces in `src/types`)
- [ ] API client hooks production-ready (no offline fallbacks)
- [ ] Storybook/visual tests for key components
- [ ] Accessibility review (keyboard nav, focus management)
- [ ] Manual QA completed (see NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md Step 7d):
  - [ ] Happy path: Primary user journey works end-to-end
  - [ ] Empty states: Render with clear messaging and CTAs
  - [ ] Error states: User-friendly error messages display
  - [ ] Loading states: No UI flash or layout shift
  - [ ] Complete flow: All interactions chain correctly
  - [ ] Edge cases: Long text, large numbers, missing data handled
  - [ ] Visual quality: Alignment, spacing, colors, responsive design
  - [ ] Accessibility: Keyboard nav, screen reader, focus management
- [ ] Browser opened to UI page for user testing
- [ ] Manual test script provided to user with specific scenarios
- [ ] User confirmed: "✅ All manual tests passing"
- [ ] Merge to main and mark ✅ complete

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

### Phase 2A: Universal GPS Site Acquisition ✅ COMPLETE
**Status:** 100% - Developer Site Acquisition workspace live end-to-end; GPS capture currently reuses the shared agent `POST /api/v1/agents/commercial-property/properties/log-gps` endpoint while a developer-specific route is tracked as backlog

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
- [`Testing Known Issues`](development/testing/known-issues.md) — "Phase 2A" section lists mandatory manual walkthroughs (capture, checklist, assessment, PDF export)
- [`ui-status.md`](planning/ui-status.md) — details the developer workspace components that must render after changes
- [`TESTING_DOCUMENTATION_SUMMARY.md`](../TESTING_DOCUMENTATION_SUMMARY.md) — outlines the smoke/coverage expectations for developer exports
- [`README.md`](../README.md) — see the `make dev` guidance for monitoring `.devstack/backend.log` during verification

**Estimated Effort:** 2-3 weeks (mostly frontend, reuse Agent backend)

---

### Phase 2B: Asset-Specific Feasibility ⚠️ IN PROGRESS
**Status:** 15% - Developer capture enriched with Phase 2B asset + finance baselines; optimisation wiring ongoing

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

**What's Missing (Next Focus):**
- ✅ Asset-specific feasibility optimizers (office, retail, industrial, residential, mixed-use) with scoring engine, constraint logging, and scenario variants
- ⏭️ Scenario-aware 3D preview generation and UI integration (deferred - see [Phase 2B Visualisation Delivery Plan](phase2b_visualisation_stub.md))
- ⏭️ Automate NHB dataset refresh (Monuments/Trails) + add override management for future conservation updates

**Kickoff Deliverables (Planned):**
- ✅ Stand up developer-specific GPS logging endpoint and API client so Site Acquisition no longer proxies through the agent route
- ✅ Extend capture response with zoning envelope + max buildable metrics (baseline commercial template)
- ✅ Complete asset-specific optimisation models (beyond baseline heuristics) and link to 3D preview shell (office/commercial first)
- Update developer UI to surface the dedicated capture flow and enriched feasibility snapshots

---

### Phase 2C: Complete Financial Control & Modeling ✅ BACKEND / UI VERIFIED
**Status:** Asset finance engine wired to developer capture, finance API gated by role, and construction loan interest now modelled with multi-facility carry + reviewer UI. ORM models now align with UUID-backed finance tables, and the smoke runner has a static asset-mix fallback so finance execution proceeds even when GPS capture is offline. Synchronous sensitivity loads are capped via `FINANCE_SENSITIVITY_MAX_SYNC_BANDS`; remaining work covers async batching, caching, and tranche editing (see [Phase 2C Finance Delivery Plan](phase2c_finance_delivery_plan.md)).

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

**What Exists:**
- ✅ NPV/IRR backend calculations
- ✅ Capital stack visualization (basic)
- ✅ Drawdown schedule tracking
- ✅ Asset-level finance breakdowns exposed via `/finance/feasibility` and surfaced in the developer finance UI
- ✅ Finance scenario access restricted to reviewer/admin roles; Site Acquisition returns finance-ready asset mix payloads
- ✅ Construction loan interest carry calculated (capitalised vs expensed) with UI summary/table
- ✅ Sensitivity engine returns rent / construction cost / interest variants; finance workspace now includes toggles + CSV/JSON export controls
- ⚠️ Finance dashboard (partial)

**What's Missing:**
- 🟡 Enhanced financing UI (equity/debt tranche details & sensitivity explorer)
- ✅ Construction loan detailed modelling (fees, multiple facilities, facility editor)
- ❌ Scenario sensitivity analysis UI / batch runners

**Acceptance Criteria:**
- Developer creates private financial models
- Equity/debt breakdown with visual charts
- Construction financing integrated with drawdowns
- Sensitivity analysis across scenarios
- No other role can access financial data

**Estimated Effort:** 6-8 weeks (complex financial logic + UI)

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

**Solution:** Add 4 new jurisdictions after Phase 2C (when we have MVP: Agent + Developer GPS/Feasibility/Finance), then build Phase 2D-6 for ALL 5 jurisdictions simultaneously.

---

### Expansion Window 1: After Phase 2C (Dec 2025 - Jan 2026)

**Status:** ❌ NOT STARTED (Blocked: Waiting for Phase 2C completion)

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
- 🇭🇰 Hong Kong: ❌ NOT STARTED (Target: Dec 2025)
- 🇳🇿 New Zealand: ❌ NOT STARTED (Target: Jan 2026)
- 🇺🇸 Washington State: ❌ NOT STARTED (Target: Jan 2026)
- 🇨🇦 Ontario: ❌ NOT STARTED (Target: Feb 2026)

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
