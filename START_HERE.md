# 🚀 START HERE FOR AI AGENTS

**New to this project? Read these files IN ORDER:**

1. **docs/planning/features.md** - What we're building (full feature specification)
2. **docs/feature_delivery_plan_v2.md** - Current status (**START with "📊 Current Progress Snapshot"**)
3. **docs/audits/PRE-PHASE-2D-AUDIT.MD** - 🚨 **CRITICAL** - 2-week audit before Phase 2D (prevents startup failure)
4. **docs/WORK_QUEUE.MD** - ⚠️ **IMPORTANT** - Active task list & technical debt follow-ups
5. **docs/ai-agents/next_steps.md** - How to choose your next task (decision tree)
6. **docs/development/testing/known-issues.md** - Known test issues (read BEFORE testing to avoid wasting time)
7. **docs/ai-agents/claude.md** - Coding guidelines and mandatory workflows

---

## ⚠️ CRITICAL: When You Complete Work

🛑 **MANDATORY: Update `docs/WORK_QUEUE.MD` and `docs/feature_delivery_plan_v2.md` BEFORE asking user to commit**

`docs/WORK_QUEUE.MD` is the **single source of truth** for active tasks; `docs/feature_delivery_plan_v2.md` captures strategic status.

**Every time you complete a feature/milestone:**
1. ✅ Update `docs/WORK_QUEUE.MD` (move item to Completed, capture commits, add follow-ups)
2. ✅ Refresh `docs/feature_delivery_plan_v2.md` phase summary if status changed
3. ✅ Stage docs with code: `git add docs/WORK_QUEUE.MD docs/feature_delivery_plan_v2.md`
4. ✅ Include in same commit as your code changes

**See Step 7c in [docs/ai-agents/next_steps.md](docs/ai-agents/next_steps.md) for detailed instructions.**

---

## 🎯 Quick Context

- **Project:** Singapore commercial real estate development platform
- **Users:** Agents, Developers, Architects, Engineers (B2B platform)
- **Current Phase:** Phase 1D - Business Performance Management (~75% complete)
- **Tech Stack:** Python 3.13 backend (FastAPI), React frontend, PostgreSQL
- **Repository:** `/Users/wakaekihara/GitHub/optimal_build`

---

## 📍 Key Directories

- `backend/` - FastAPI application, models, services, tests
- `frontend/` - React application
- `docs/` - Design documents and delivery plans
- `backend/tests/` - Pytest test suite (service + API tests)

---

## 🧪 Testing

**Before claiming work is done, suggest test commands:**

```bash
# Backend service tests
python3 -m pytest backend/tests/test_services/test_*.py -v

# Backend API tests (requires Python >= 3.10)
python3 -m pytest backend/tests/test_api/test_*.py -v
```

See `docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md` section "MANDATORY TESTING CHECKLIST" for full template.

---

## 🔄 Session Handoff

**Returning to work or starting a new session?**

Read [`docs/handoff_playbook.md`](docs/handoff_playbook.md) for:
- Quick project status snapshot (updated 2025-10-17)
- Immediate actions to carry forward
- Phase 2 build targets and priorities
- Workflow guardrails and quality gates

This ensures continuity between sessions and alignment with previous work.

---

**Ready to start? Go read `docs/feature_delivery_plan_v2.md` first!** 📊

---

## 📚 Complete Documentation Inventory

**⚠️ If asked "list all instruction/documentation files", this is the COMPLETE answer:**

This section lists ALL 20 instruction and reference files in this repository. This prevents AI agents from using heuristics/grep to discover files (which leads to gaps).

### 🎯 Core AI Agent Instructions (Must Read - Listed Above)
1. ✅ **START_HERE.md** (this file) - Entry point and reading order
2. ✅ **docs/planning/features.md** - Complete feature specifications
3. ✅ **docs/feature_delivery_plan_v2.md** - Project roadmap and current status
4. ✅ **docs/ai-agents/next_steps.md** - Task decision guide
5. ✅ **docs/development/testing/known-issues.md** - Known test harness issues (not bugs)
6. ✅ **docs/ai-agents/claude.md** - Claude-specific instructions and workflows
7. ✅ **docs/ai-agents/codex.md** - Codex-specific instructions and mandatory testing checklist

### 📋 Additional Reference Files (Read When Relevant)
8. **docs/WORK_QUEUE.MD** - AI agent work queue (active tasks only)
9. **docs/archive/TECHNICAL_DEBT.MD** - Historical technical debt inventory (for context only)
10. **docs/handoff_playbook.md** - Session handoff guide and status snapshot
11. **CODING_RULES.md** - Mandatory coding rules (enforced by CI)
12. **CONTRIBUTING.md** - Git workflow, PR process, code review
13. **docs/development/testing/advisory.md** - Testing best practices
14. **docs/development/testing/summary.md** - Testing strategy overview
15. **docs/PDF_TESTING_CHECKLIST.md** - Manual PDF testing requirements
16. **docs/validation/live_testing_guide.md** - Manual/UAT testing procedures
17. **docs/development/testing/overview.md** - Feature testing checklist
18. **docs/planning/roadmap.md** - High-level project roadmap
19. **frontend/README_AI_AGENTS.md** - Frontend development guidelines
20. **docs/SOLO_FOUNDER_GUIDE.md** - Solo founder workflow with AI agents
21. **docs/reviewer_sop.md** - Code review procedures

### 📖 Supporting Documentation (Not Instructions)
- **README.md** - General project overview
- **API_ENDPOINTS.md** - API documentation
- **docs/architecture.md** - System architecture
- **docs/finance_api.md**, **docs/entitlements_api.md**, etc. - API references
- Various feature-specific docs in `docs/`

**Last Updated:** 2025-10-19 (Update this date when adding/removing instruction files)
