# 🚀 START HERE FOR AI AGENTS

**New to this project? Read these files IN ORDER:**

1. **FEATURES.md** - What we're building (full feature specification)
2. **docs/feature_delivery_plan_v2.md** - Current status (**START with "📊 Current Progress Snapshot"**)
3. **docs/NEXT_STEPS_FOR_CODEX.md** - How to choose your next task (decision tree)
4. **TESTING_KNOWN_ISSUES.md** - Known test issues (read BEFORE testing to avoid wasting time)
5. **CLAUDE.md** - Coding guidelines and mandatory workflows

---

## ⚠️ CRITICAL: When You Complete Work

**Update `docs/feature_delivery_plan_v2.md`** - Move items from "In Progress" to "Complete"

This is the **SINGLE SOURCE OF TRUTH** for project status. All AI agents reference this file.

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

See `docs/NEXT_STEPS_FOR_CODEX.md` section "MANDATORY TESTING CHECKLIST" for full template.

---

**Ready to start? Go read `docs/feature_delivery_plan_v2.md` first!** 📊
