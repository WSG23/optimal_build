# Phase 2B Visualization Delivery Audit

**Date:** 2025-11-02
**Auditor:** Claude Code (requested by user)
**Commits Reviewed:** 83efa81, d71fd78, and related Phase 2B work
**Status:** ⚠️ **PARTIALLY COMPLETE** - Backend infrastructure delivered, frontend 3D viewer **NOT delivered**

---

## Executive Summary

Codex Cloud delivered valuable Phase 2B backend infrastructure but **did not complete the visualization feature**. The work is approximately **70% complete** (backend only).

### What Was Delivered ✅

1. **Backend Preview Job Infrastructure** (83efa81)
   - `preview_jobs` table and `PreviewJob` model
   - Preview job API endpoints (`POST`, `GET` for job status)
   - Job queuing and status tracking (`queued`, `processing`, `ready`, `failed`)
   - Integration with site acquisition workflow

2. **Geometry Payload Builder** (d71fd78)
   - Enhanced `backend/app/services/preview_generator.py` (+173 lines)
   - Massing layer generation from optimizer outputs
   - Camera hints and bounding box calculations
   - Tests: `backend/tests/test_services/test_preview_generator.py` (+86 lines)

3. **Frontend Preview Job Polling** (83efa81)
   - `frontend/src/api/siteAcquisition.ts` API client methods:
     - `fetchPreviewJob()`, `refreshPreviewJob()`, `listPreviewJobs()`
   - `SiteAcquisitionPage.tsx` preview job state management (+187 lines)
   - Status polling logic (5s interval with exponential backoff)
   - "Rendering..." status banner

4. **Documentation** (d71fd78)
   - `docs/PHASE2B_VISUALISATION_STUB.MD` v0.4 with manual QA checklist
   - Manual UI QA guardrails documented (Section 10)
   - Updated WORK_QUEUE.MD with renderer bootstrap task

### What Is Missing ❌

1. **3D Renderer Service** (Section 4.4 of PHASE2B_VISUALISATION_STUB.MD)
   - **NO** Blender/Three.js renderer implementation
   - **NO** GLB mesh generation
   - **NO** thumbnail PNG generation
   - **NO** headless rendering infrastructure

2. **Frontend 3D Viewer Component**
   - **NO** WebGL/Three.js viewer component
   - **NO** GLB loader
   - **NO** camera controls
   - **NO** preview display UI
   - Grep search confirmed: `frontend/src/` contains **ZERO** mentions of:
     - `GLB`, `three`, `Three`, `WebGL`, `canvas`, `renderer`, `Viewer`

3. **Storage & Asset Management** (Section 4.5)
   - **NO** S3 upload helper
   - **NO** asset versioning system
   - **NO** GLB file serving endpoints
   - Only stub JSON preview files in `static/dev-previews/`

4. **Manual UI QA Execution** (Section 10)
   - Checklist created but **NOT executed** (all items unchecked `[ ]`)
   - **NO** tester name, date, or results
   - **NO** screenshots or console logs attached

---

## Detailed File Analysis

### Backend Files Delivered

| File | Lines Changed | Purpose | Status |
|------|---------------|---------|--------|
| `backend/app/models/preview.py` | New | PreviewJob model | ✅ Complete |
| `backend/app/services/preview_jobs.py` | New | Job CRUD operations | ✅ Complete |
| `backend/app/api/v1/developers.py` | Modified | Preview job endpoints | ✅ Complete |
| `backend/jobs/preview_generate.py` | Modified (+12) | Job worker stub | ⚠️ Incomplete (no renderer call) |
| `backend/app/services/preview_generator.py` | +173 lines | Geometry builder | ✅ Complete |
| `backend/migrations/versions/20251022_000017_add_preview_jobs.py` | New | Database schema | ✅ Complete |

### Frontend Files Delivered

| File | Lines Changed | Purpose | Status |
|------|---------------|---------|--------|
| `frontend/src/api/siteAcquisition.ts` | +187 | Preview job API client | ✅ Complete |
| `frontend/src/app/pages/site-acquisition/SiteAcquisitionPage.tsx` | +344 | Preview job polling | ⚠️ Incomplete (no viewer) |

**Missing:** Entire 3D viewer component tree (viewer, controls, materials, lighting, camera)

### Documentation Files

| File | Status | Notes |
|------|--------|-------|
| `docs/PHASE2B_VISUALISATION_STUB.MD` | ✅ Updated | Section 10 checklist NOT executed |
| `docs/WORK_QUEUE.MD` | ✅ Correct | Lists "Renderer pipeline bootstrap" as READY |
| `docs/ROADMAP.MD` | ✅ Correct | Phase 2B marked "⚠️ IN PROGRESS" (not COMPLETE) |

---

## Comparison: Promised vs Delivered

### Promised (per PHASE2B_VISUALISATION_STUB.MD)

**Section 1: Objectives**
- Asynchronous preview generation ✅ (backend only)
- Status lifecycle (`queued → processing → ready/failed`) ✅
- Scenario-aware previews ❌ (no viewer)
- Durable storage with cache-friendly URLs ❌ (no S3, no GLB)
- Metrics and observability ❌ (not implemented)

**Section 9: Next Steps Checklist**
- [x] Draft PreviewJob model ✅
- [x] Implement job queue entry point ✅
- [x] Extend geometry builder ✅
- [x] Update frontend to consume status lifecycle ✅ (polling only, no viewer)
- [ ] Finalise renderer selection ❌ **NOT DONE**
- [ ] Define monitoring dashboards ❌ **NOT DONE**

### Delivered

**Backend:** Job infrastructure, geometry payload generation
**Frontend:** API client, status polling
**Renderer:** **NOTHING**
**3D Viewer:** **NOTHING**

---

## Why Manual QA Was Not Suggested

**Root Cause (per PHASE2B_VISUALISATION_STUB.MD line 40-43):**

> **Root cause:** Only Phase 1D deliverables had a manual UI checklist, so the Phase 2B preview payload builder shipped without anyone running the Web preview harness end-to-end. The missing guardrail meant agents relied solely on automated tests and never launched the renderer UI, leaving regressions invisible to the product owner.

**The same gap occurred again:**
1. Codex Cloud added Section 10 manual QA checklist to the doc
2. But never executed it (all checkboxes remain `[ ]`)
3. Codex never built the 3D viewer UI component
4. Without the viewer, there's nothing to manually test
5. Therefore, no manual QA was suggested

**This is circular logic:** "We need manual QA for the viewer, but there's no viewer to test, so we didn't do manual QA."

---

## Residual Work Required

To complete Phase 2B visualization, the following work remains:

### 1. Renderer Service (1-2 weeks)
- **Decision:** Blender CLI vs Three.js node script vs custom renderer
- **Implementation:**
  - Headless rendering infrastructure
  - GLB mesh generation from geometry payload
  - Thumbnail PNG generation
  - Timeout handling (90s default)
- **Integration:**
  - Called by `backend/jobs/preview_generate.py`
  - Outputs written to storage

### 2. Storage & Asset Management (3-5 days)
- S3 upload helper (or local filesystem abstraction)
- Asset versioning (`{optimizer_version}-{preview_schema_version}-{YYYYMMDDHHMM}`)
- GLB serving endpoint
- Asset expiry policy

### 3. Frontend 3D Viewer (1 week)
- **Component tree:**
  - `PreviewViewer.tsx` (main component)
  - `SceneCanvas.tsx` (Three.js WebGL canvas)
  - `CameraControls.tsx` (orbit controls)
  - `MaterialLibrary.ts` (asset type colors)
- **Features:**
  - GLB loading
  - Camera orbit from preview hints
  - Massing layer visualization
  - Loading states
  - WebGL fallback for unsupported browsers

### 4. Manual UI QA (2-4 hours)
- Execute Section 10 checklist in PHASE2B_VISUALISATION_STUB.MD
- Fill out tester, date, result
- Attach screenshots of rendered previews
- Document any visual regressions

**Total Estimate:** 3-4 weeks

---

## Recommendations

### Immediate Actions

1. **Create dedicated work queue item:** "Phase 2B Frontend 3D Viewer" with clear scope
   - Estimated: 1 week
   - Acceptance: Viewer component renders GLB, manual QA executed
   - Blocked by: Renderer service selection

2. **Update PHASE2B_VISUALISATION_STUB.MD Section 9:**
   - Mark "Finalise renderer selection" as next critical decision
   - Add "Build frontend 3D viewer component" as unchecked item

3. **Prevent future gaps:**
   - Implement Rule 12.3: "Frontend file existence check"
   - Enforcement: If phase design doc lists UI components, verify files exist in `frontend/src/`
   - Example: Phase 2B design promises "WebGL viewer" → must find `*Viewer*.tsx` or `*viewer*.tsx`

### Process Improvements

**Add to CODING_RULES.md Rule 12.1:**

> **AI agents MUST NOT claim a phase is "complete" or "done" UNLESS:**
> 1. Manual QA checklist exists AND executed (Tester, Date, Result filled)
> 2. ROADMAP.MD updated to `✅ COMPLETE`
> 3. **ALL frontend UI components listed in phase design doc exist in `frontend/src/`**
> 4. **ALL backend API endpoints listed in phase design doc exist in `backend/app/api/`**

**Add enforcement in `scripts/check_coding_rules.py`:**

```python
# Rule 12.3: Frontend file existence for UI phases
if phase marked COMPLETE and phase_design_doc lists UI components:
    for component in promised_components:
        if not exists(f"frontend/src/**/{component}.tsx"):
            error(f"{component} promised but missing")
```

---

## Conclusion

**Phase 2B Status:** ⚠️ **IN PROGRESS** (correctly tracked)

**Delivered Value:** Backend preview job infrastructure is production-ready and valuable

**Missing Value:** The entire user-facing 3D visualization (renderer + viewer)

**Next Step:** Decide whether to:
- **Option A:** Complete Phase 2B (add renderer + viewer, 3-4 weeks)
- **Option B:** Defer 3D viewer to post-launch backlog (backend is functional)
- **Option C:** Prototype with simple 2D preview images instead of full 3D (1 week pivot)

**User should decide** based on Phase 2D launch timeline pressure.
