# Work Queue (AI Agent Task List)

**Last Updated:** 2025-11-02
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

### 3. Phase 2B: Implement 3D GLB renderer
- **Status:** READY (blocked by Infrastructure Audit completion)
- **Estimate:** 2-3 weeks
- **Documentation:** Align with [`docs/ROADMAP.MD`](ROADMAP.MD) Phase 2B objectives.

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

### 2025-11-02: Phase 1D Business Performance UI shipped
- **Completed by:** AI Agents crew
- **Commits:** 46780e7, 7c97757
- **Highlights:** Pipeline Kanban drag-and-drop, deal insights timeline, analytics & ROI panels, manual QA checklist ✅

### 2025-11-02: Infrastructure Audit - Option 10: Pre-commit hook fixes
- **Completed by:** Claude
- **Commits:** 3766d08
- **Impact:** Resolved lint failures in conftest.py, all critical pre-commit hooks now pass cleanly

---

## Operating Instructions for AI Agents

1. **Before starting work**, review the Active section to confirm priority.
2. Cross-check context docs: [`docs/development/testing/known-issues.md`](development/testing/known-issues.md), [`docs/planning/ui-status.md`](planning/ui-status.md), [`docs/development/testing/summary.md`](development/testing/summary.md), and the repository [`README.md`](../README.md).
3. If a task is unclear, consult the linked documentation or add clarifying notes in this file.
4. After completing work, move the item to the Completed section with the completion date and relevant commit IDs.
5. Update [`docs/ROADMAP.MD`](ROADMAP.MD) only when phase status changes (e.g., READY → COMPLETE).
6. For infrastructure audit tasks, update `docs/audits/PRE-PHASE-2D-AUDIT.MD` checklists in parallel.
