# Work Queue (AI Agent Task List)

**Last Updated:** 2025-11-04
**Current Sprint:** Pre-Phase 2D Infrastructure Audit (Week 1)

Legend: `IN PROGRESS` = actively being worked, `READY` = unblocked and next in line, `BLOCKED` = awaiting dependency listed inline.

---

## 🚀 Active (Do Now - Priority Order)

### 1. Infrastructure Audit - Option 11: Backend test coverage 68% → 80%
- **Status:** IN PROGRESS (Codex Local)
- **Assigned:** Codex Local
- **Estimate:** 8 hours
- **Description:** Expand unit and integration coverage for audit-critical services (ingestion pipelines, finance adapters).
- **Acceptance Criteria:** Coverage report ≥ 80% on critical paths, flaky tests resolved, audit checklist updated.
- **Files:** `backend/`, `tests/`, `docs/audits/PRE-PHASE-2D-AUDIT.MD`.


---

## 📋 Ready (Queued - Do After Active)

### Front-end npm audit cleanup
- **Status:** READY
- **Assigned:** Frontend
- **Estimate:** 0.5 day
- **Description:** Follow up on the two moderate vulnerabilities flagged after `npm install --legacy-peer-deps` (2025-11-02). Run `npm audit` locally, attempt `npm audit fix` (without `--force`), and document any remaining vulnerable packages plus remediation plan if upgrades require breaking changes.
- **Acceptance Criteria:** Audit report captured, fixes applied where safe, unresolved items logged with owner/action.
- **Files:** `frontend/package-lock.json`, `frontend/package.json`.

---

## ✅ Completed (Last 30 Days)

### 2025-11-01: Database indexing (9 composite indexes)
- **Completed by:** Claude + Codex
- **Commits:** 1d11b6d, ...
- **Impact:** 11-39% query performance improvement

### 2025-10-28: Phase 2C Finance complete
- **Completed by:** WSG23 + Claude
- **Commits:** 7beff36, d0752f5
- **Smoke tests:** ✅ All passed

### 2025-11-04: Phase 2B GLTF renderer + preview viewer shipped
- **Completed by:** Codex Local
- **Commits:** (pending merge)
- **Highlights:** Backend now emits GLTF/BIN/thumbnail assets with manifests; preview jobs expose `metadata_url`/`asset_version`; Three.js viewer renders GLTF with orbit controls and thumbnails; documentation and roadmap updated to mark Phase 2B complete.

### 2025-11-04: Phase 2B monitoring metrics wired
- **Completed by:** Codex Local
- **Commits:** (pending merge)
- **Highlights:** Prometheus counters/histograms (`preview_generation_jobs_total`, `preview_generation_jobs_completed_total`, `preview_generation_job_duration_ms`, `preview_generation_queue_depth`) added; queue depth and duration recorded during enqueue/worker execution. Dashboards/alerts now need to hook into these series—see `docs/observability/preview_generation_monitoring.md`.

### 2025-11-02: Phase 1D Business Performance UI shipped
- **Completed by:** AI Agents crew
- **Commits:** 46780e7, 7c97757
- **Highlights:** Pipeline Kanban drag-and-drop, deal insights timeline, analytics & ROI panels, manual QA checklist ✅

### 2025-11-02: Infrastructure Audit - Option 10: Pre-commit hook fixes
- **Completed by:** Claude
- **Commits:** 3766d08
- **Impact:** Resolved lint failures in conftest.py, all critical pre-commit hooks now pass cleanly

### 2025-11-04: Phase 2B GLTF renderer + preview viewer shipped
- **Completed by:** Codex Local
- **Commits:** (pending merge)
- **Highlights:** Backend now emits GLTF/BIN/thumbnail assets with manifests; preview jobs expose `metadata_url`/`asset_version`; Three.js viewer renders GLTF with orbit controls and thumbnails; documentation and roadmap updated to mark Phase 2B complete.

### 2025-11-04: Phase 2B manual UI QA execution
- **Completed by:** Wakae + Codex Local
- **Artifacts:** Screenshots (developer preview route), updated checklist in `docs/PHASE2B_VISUALISATION_STUB.MD`
- **Highlights:** Confirmed Three.js viewer renders seeded GLTF assets with orbit controls; metadata links verified, no regressions observed.

### 2025-11-04: Phase 2B Monitoring & Alerts wired
- **Completed by:** Codex Local
- **Artifacts:** `infra/observability/grafana/phase2b_preview_dashboard.json`, `infra/observability/prometheus/preview_generation.rules.yml`
- **Highlights:** Grafana import-ready dashboard plus Prometheus alert rules covering failure rate, latency, and queue depth; documented runbook updated with import instructions.

---

## Operating Instructions for AI Agents

1. **Before starting work**, review the Active section to confirm priority.
2. Cross-check context docs: [`docs/development/testing/known-issues.md`](development/testing/known-issues.md), [`docs/planning/ui-status.md`](planning/ui-status.md), [`docs/development/testing/summary.md`](development/testing/summary.md), and the repository [`README.md`](../README.md).
3. If a task is unclear, consult the linked documentation or add clarifying notes in this file.
4. After completing work, move the item to the Completed section with the completion date and relevant commit IDs.
5. Update [`docs/ROADMAP.MD`](ROADMAP.MD) only when phase status changes (e.g., READY → COMPLETE).
6. For infrastructure audit tasks, update `docs/audits/PRE-PHASE-2D-AUDIT.MD` checklists in parallel.
7. For Phase 2B renderer items, execute the manual UI walkthrough in [`docs/PHASE2B_VISUALISATION_STUB.MD`](PHASE2B_VISUALISATION_STUB.MD#10-manual-ui-qa-checklist-preview-payload-builder) and include results before requesting review.
