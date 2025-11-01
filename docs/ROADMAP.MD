# Optimal Build Strategic Roadmap

**Purpose:** High-level strategic phases, gate criteria, and business outcomes for Optimal Build. This file replaces `docs/feature_delivery_plan_v2.md` as the stakeholder-facing source of truth.

**Primary Audience:** Product managers, stakeholders, onboarding engineers.

**Update Cadence:** Review monthly or whenever a phase status changes. For daily execution updates, see [`docs/WORK_QUEUE.MD`](WORK_QUEUE.MD).

---

## 📈 Phase Overview

| Phase | Objective | Status |
| --- | --- | --- |
| Phase 1A | GPS capture, quick analysis, marketing pack foundations | ✅ COMPLETE |
| Phase 1B | Automated geometry ingestion & validation | ✅ COMPLETE |
| Phase 1C | Core finance services live for early adopters | ✅ COMPLETE |
| Phase 1D | Business performance dashboards shipped and QA signed off | ✅ COMPLETE |
| Phase 2A | Advanced data ingestion stabilised across jurisdictions | ⚠️ IN PROGRESS |
| Phase 2B | 3D visualisation stack + GLB renderer | ❌ NOT STARTED |
| Phase 2C | Finance automation v2 (lending + cash flow) | ✅ COMPLETE |
| Phase 2D | Infrastructure resilience, audit & launch-readiness sprint | ❌ NOT STARTED |

> **Implementation detail:** Tactical task ordering, assignments, and acceptance criteria live in [`docs/WORK_QUEUE.MD`](WORK_QUEUE.MD).

---

## ✅ Phase Gate Checklist (Pre-Phase 2D Readiness)

> Update these checkboxes only after the corresponding work is fully complete and documented in the relevant execution docs.

- [ ] Phase 2D Gate: Pre-Phase 2D Infrastructure Audit & Quality Sprint complete (`PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.MD`)
- [x] Phase 2D Gate: Phase 1D Business Performance UI backlog delivered & QA signed off (see Phase 1D summary below)
- [ ] Phase 2D Gate: Phase 2B visualisation residual work delivered (see Phase 2B summary below)
- [ ] Phase 2D Gate: Expansion Window 1 (HK, NZ, Seattle, Toronto) complete (`docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md`)

Scripts such as `scripts/check_phase_gate.py` rely on these exact checklist labels to enforce compliance before Phase 2D work can be merged.

---

## Strategic Milestones

1. **North Star Activation:** All Phase 1 capabilities (A–D) provide full self-serve reporting for pilot cities.
2. **Expansion Window 1:** Jurisdictions listed above ready for onboarding by the end of Phase 2C.
3. **Investor Readiness:** Audited infrastructure (Phase 2D) with observability KPIs published to stakeholders.
4. **Automation Wave:** Finance automation (Phase 2C) feeds marketing ROI dashboards without manual reconciliation.

---

## Phase Summaries

### Phase 1D – Business Performance Dashboards
- **Goal:** Deliver the full business performance UI backlog and connect to finance APIs for live metrics.
- **Current Status:** ✅ COMPLETE – pipeline Kanban, insights, analytics, and ROI panels live with responsive design & QA sign-off.
- **Key Outcomes Achieved:** Material-UI implementation, drag-and-drop stage progression, analytics visualisation, ROI reporting, manual QA checklist complete.

### Phase 2A – Advanced Data Ingestion
- **Goal:** Harden ingestion for late-joining jurisdictions and high-volume clients.
- **Current Status:** ⚠️ IN PROGRESS – pending completion of database resilience work from the infrastructure audit.
- **Key Outcomes Required:** Retry orchestration, schema drift alerts, jurisdiction rollout playbook updates.

### Phase 2B – Visualisation Platform
- **Goal:** Ship 3D GLB renderer and context-aware overlays for portfolio reviews.
- **Current Status:** ❌ NOT STARTED – blocked on Phase 2D gate readiness.
- **Key Outcomes Required:** Renderer performance benchmarking, asset tagging pipeline, UI integration plan.

### Phase 2C – Finance Automation v2
- **Goal:** Close the loop between finance data ingestion and business performance dashboards.
- **Current Status:** ✅ COMPLETE – verify no regressions during the infrastructure audit.
- **Key Outcomes Required:** Maintain finance regression suite, monitor cross-border compliance updates.

### Phase 2D – Infrastructure Audit & Launch Sprint
- **Goal:** Complete resilience audit, observability rollout, and go-live rehearsal.
- **Current Status:** ❌ NOT STARTED – prerequisites listed in the phase gate checklist remain outstanding.
- **Key Outcomes Required:** Close audit findings, certify backup/restore runbooks, publish launch readiness report.

---

## How to Use This Document

1. **Stakeholders:** Review the phase overview table and milestone list to understand strategic positioning.
2. **Product & Delivery Leads:** Update status rows when a phase materially progresses or completes.
3. **AI Agents & Developers:** Before coding, check [`docs/WORK_QUEUE.MD`](WORK_QUEUE.MD) for actionable tasks, then reflect status changes here.

For historical context and detailed execution logs, see the archived roadmap in [`docs/archive/FEATURE_DELIVERY_PLAN_V2.MD`](archive/FEATURE_DELIVERY_PLAN_V2.MD).
