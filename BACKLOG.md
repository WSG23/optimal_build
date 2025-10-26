# Technical Debt Backlog

**Last updated:** 2025-10-27
**Maintained by:** Human (you) with help from Claude/Codex

---

## How to Use This File

**For AI Agents (Claude, Codex):**
1. Always read this file at the start of each session
2. Check "Active" section for next task
3. When task is complete, move it to "Completed" with date
4. Update "Last updated" date at top

**For Human (Program Manager):**
1. Review this weekly
2. Move tasks between sections as priorities change
3. AI agents will follow this as their work queue

---

## Active (Do Next)

**Nothing - finish Phase 2C Finance work first**

---

## Blocked (Waiting)

### Phase 1D: Business Performance Management UI
**Status:** BLOCKED - waiting for Phase 2C Finance to complete
**Priority:** HIGH (60% complete, UI missing)
**Estimate:** 3-4 weeks
**Risk:** Blocks Phase 1 completion

**What's Done:**
- ✅ Backend 100% complete (deal pipeline, commission ledger, ROI analytics)
- ✅ Production shell + navigation configured
- ✅ Page scaffold created

**What's Missing (UI Implementation):**
- ❌ Pipeline Kanban board component (columns per stage, drag-drop)
- ❌ Deal insights panel (timeline, audit metadata)
- ❌ Analytics panel (KPI cards, trend charts, benchmarks)
- ❌ ROI panel (project-level ROI tracking)
- ❌ Manual QA checklist (8 items in feature_delivery_plan_v2.md lines 351-363)

**Documentation:**
- Requirements: [feature_delivery_plan_v2.md](docs/feature_delivery_plan_v2.md) lines 274-392
- UI specs: Lines 315-343 (primary persona: Agent Team Leads)
- API endpoints: Lines 330 (deals, timeline, commissions, performance)

**After Phase 2C completes:**
1. Read Phase 1D UI Design Specifications (lines 328-335)
2. Build 4 UI components (Kanban, Insights, Analytics, ROI panels)
3. Run manual QA checklist (lines 351-363)
4. Mark Phase 1D ✅ COMPLETE

---

### Phase 2B: Asset-Specific Feasibility - 3D Visualization
**Status:** BLOCKED - waiting for Phase 2C Finance to complete
**Priority:** HIGH (85% complete, 3D preview missing)
**Estimate:** 2-3 weeks
**Risk:** Blocks Phase 2B completion

**What's Done:**
- ✅ Asset optimizer (curve-driven scoring, constraint logging)
- ✅ Heritage overlay backend (NHB Historic Sites, National Monuments)
- ✅ Preview job pipeline (background renders, polling endpoints)
- ✅ Visualization stub (per-asset massing layers, color legend)

**What's Missing (Backend - 40% of remaining work):**
- ❌ Renderer service (Blender/Three.js for GLB generation)
- ❌ Asset storage & versioning (S3/local with versions)
- ❌ Geometry builder enhancements (floor plates, podiums, setbacks)
- ❌ Prefect flow orchestration (`developer_preview_flow`)

**What's Missing (Frontend UI - 60% of remaining work):**
- ❌ Preview status polling hook (GET every 5s with backoff)
- ❌ "Rendering" banner during generation
- ❌ GLB viewer integration + JSON stub fallback
- ❌ Retry CTA on failed renders
- ❌ Status chip on scenario tabs
- ❌ Thumbnail loading placeholders
- ❌ WebGL 2 detection with graceful fallback

**Documentation:**
- Requirements: [feature_delivery_plan_v2.md](docs/feature_delivery_plan_v2.md) lines 455-508
- Detailed plan: [docs/phase2b_visualisation_stub.md](docs/phase2b_visualisation_stub.md)

**After Phase 2C completes:**
1. Read phase2b_visualisation_stub.md for implementation details
2. Implement GLB generation with scenario variants
3. Wire frontend 3D viewer component
4. Mark Phase 2B ✅ COMPLETE

---

### Tier 2: Dependency Pinning
**Status:** BLOCKED - waiting for Phase 2C Finance to complete AND Phase 1D/2B residual work
**Priority:** Medium
**Estimate:** 1-2 hours
**Risk:** Security, reproducibility

**Problem:**
7 dependencies in `backend/requirements.txt` use `>=` instead of `==`:
- asyncpg>=0.30.0
- shapely>=2.0.6
- pandas>=2.2.3
- numpy>=1.26.0
- statsmodels>=0.14.0
- scikit-learn>=1.3.0
- reportlab>=4.0.0

**Solution:**
Pin to exact versions. Full instructions in:
`.github/ISSUE_TEMPLATE/tier2-dependency-pinning.md`

**Quick steps:**
1. Run: `pip freeze | grep -E "asyncpg|shapely|pandas|numpy|statsmodels|scikit-learn|reportlab"`
2. Update `backend/requirements.txt` with exact versions
3. Run: `make verify` and `pytest backend/tests/`
4. Remove exception from `.coding-rules-exceptions.yml`
5. Commit and push

**Acceptance criteria:**
- [ ] All 7 dependencies use `==` instead of `>=`
- [ ] `make verify` passes
- [ ] All tests pass
- [ ] Exception removed from `.coding-rules-exceptions.yml`

**Related:**
- CODING_RULES.md Rule 4
- Violations found in commit d848b49

---

## Backlog (Later)

### Tier 3: Async/Await Refactoring
**Status:** Deferred - fix when touching those files
**Priority:** Low
**Estimate:** 4-6 hours
**Risk:** Performance (minor)

**Problem:**
3 legacy API files use sync `Session` instead of `AsyncSession`:
- backend/app/api/v1/users_db.py
- backend/app/api/v1/singapore_property_api.py
- backend/app/api/v1/projects_api.py

**Solution:**
Refactor to use AsyncSession. Already documented in exceptions.

**When to fix:**
- When refactoring those modules anyway
- Or as part of async/await consistency sprint

**Related:**
- CODING_RULES.md Rule 2
- Exception documented in `.coding-rules-exceptions.yml`

---

## Completed

### 2025-10-26: Migration Validation Infrastructure (Phases 1-3)
**Completed by:** Claude
**Commits:** 4cf497e, e7a987e, d848b49, d2b98c3

**What was done:**
- ✅ Phase 1: Pre-commit hook for ENUM pattern validation
- ✅ Phase 2: Schema validation tests (8 tests)
- ✅ Phase 3: CI workflow integration
- ✅ Fixed check_coding_rules.py to use venv Python
- ✅ Fixed missing Sequence import in finance.py

**Impact:**
- 90%+ reduction expected in migration issues
- 100% coverage of known migration patterns
- Clear error messages at commit time

**Documentation created:**
- docs/ai-agent-guides/MIGRATION_ISSUES_ROOT_CAUSE_ANALYSIS.md
- docs/ai-agent-guides/MIGRATION_HOOK_CONFLICT_ANALYSIS.md
- docs/ai-agent-guides/PHASE1_IMPLEMENTATION_SUMMARY.md
- docs/ai-agent-guides/PHASE2_PHASE3_IMPLEMENTATION_SUMMARY.md

---

## Notes

**For future AI agents:**
- Before creating migrations, read PHASE1_IMPLEMENTATION_SUMMARY.md
- Before committing, pre-commit hooks will run automatically
- If hooks fail, read the error message - it shows the correct pattern
- Phase 2 tests will catch schema drift during `make verify`
- Phase 3 CI will validate everything before merge

**For human:**
- Migration validation is complete and production-ready
- Monitor success metrics after 1 month:
  - Migration-related commits (baseline: 74/month, target: <10/month)
  - Issues found at commit time vs manual testing
  - Pre-push hook bypass frequency
