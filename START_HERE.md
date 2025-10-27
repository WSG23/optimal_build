# 🚀 START HERE FOR AI AGENTS

**New to this project? Read these files IN ORDER:**

1. **UI_STATUS.md** - ⚠️ **READ FIRST** - Frontend UI status (CRITICAL: prevents wasted work)
2. **FEATURES.md** - What we're building (full feature specification)
3. **docs/feature_delivery_plan_v2.md** - Current status (**START with "📊 Current Progress Snapshot"**)
4. **PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.md** - 🚨 **CRITICAL** - 2-week audit before Phase 2D (prevents startup failure)
5. **TECHNICAL_DEBT.md** - ⚠️ **IMPORTANT** - All known technical debt (prevents forgotten work)
6. **docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md** - How to choose your next task (decision tree)
7. **TESTING_KNOWN_ISSUES.md** - Known test issues (read BEFORE testing to avoid wasting time)
8. **CLAUDE.md** - Coding guidelines and mandatory workflows

---

## ⚠️ CRITICAL: When You Complete Work

🛑 **MANDATORY: Update `docs/feature_delivery_plan_v2.md` BEFORE asking user to commit**

This is the **SINGLE SOURCE OF TRUTH** for project status. All AI agents reference this file.

**Every time you complete a feature/milestone:**
1. ✅ Update "📊 Current Progress Snapshot" (update percentage + remaining items)
2. ✅ Update detailed phase section (add what you delivered)
3. ✅ Stage docs with code: `git add docs/feature_delivery_plan_v2.md`
4. ✅ Include in same commit as your code changes

**See Step 7c in [NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md](docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md) for detailed instructions.**

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
2. ✅ **UI_STATUS.md** - Frontend UI status and warnings
3. ✅ **FEATURES.md** - Complete feature specifications
4. ✅ **docs/feature_delivery_plan_v2.md** - Project roadmap and current status
5. ✅ **docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md** - Task decision guide
6. ✅ **TESTING_KNOWN_ISSUES.md** - Known test harness issues (not bugs)
7. ✅ **CLAUDE.md** - Claude-specific instructions and workflows
8. ✅ **CODEX.md** - Codex-specific instructions and mandatory testing checklist

### 📋 Additional Reference Files (Read When Relevant)
9. **BACKLOG.md** - AI agent work queue (active tasks only)
10. **TECHNICAL_DEBT.md** - Complete technical debt inventory (all known deferred work)
11. **docs/handoff_playbook.md** - Session handoff guide and status snapshot
12. **CODING_RULES.md** - 8 mandatory coding rules (enforced by CI)
13. **CONTRIBUTING.md** - Git workflow, PR process, code review
14. **TESTING_ADVISORY.md** - Testing best practices
15. **TESTING_DOCUMENTATION_SUMMARY.md** - Testing strategy overview
16. **docs/PDF_TESTING_CHECKLIST.md** - Manual PDF testing requirements
17. **docs/validation/live_testing_guide.md** - Manual/UAT testing procedures
18. **TEST_ALL_FEATURES.md** - Feature testing checklist
19. **PROJECT_ROADMAP.md** - High-level project roadmap
20. **frontend/README_AI_AGENTS.md** - ⚠️ Critical warnings about frontend test harnesses
21. **docs/SOLO_FOUNDER_GUIDE.md** - Solo founder workflow with AI agents
22. **docs/reviewer_sop.md** - Code review procedures

### 📖 Supporting Documentation (Not Instructions)
- **README.md** - General project overview
- **API_ENDPOINTS.md** - API documentation
- **docs/architecture.md** - System architecture
- **docs/finance_api.md**, **docs/entitlements_api.md**, etc. - API references
- Various feature-specific docs in `docs/`

**Last Updated:** 2025-10-19 (Update this date when adding/removing instruction files)
