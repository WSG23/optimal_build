# Project Documentation

## 🚨 START HERE - Critical Documents

**If you're new to this project (human or AI), read these IN ORDER:**

### 1. [../FEATURES.md](../FEATURES.md) - WHAT we're building
**Read first!** This is the complete product vision.
- All 4 user roles (Agents, Developers, Architects, Engineers)
- All 29+ major features across roles
- Singapore-specific requirements
- Professional boundaries and compliance

**Status:** ✅ Complete and frozen (do not modify without approval)

---

### 2. [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) - HOW we're building it
**Read second!** This maps FEATURES.md into executable phases.
- 6 phases covering 100% of FEATURES.md
- Dependencies and priorities clear
- Acceptance criteria for each feature
- Timeline estimates (1.5-2.3 years)

**Status:** ✅ Current roadmap (update as features complete)

---

### 3. [NEXT_STEPS_FOR_CODEX.md](NEXT_STEPS_FOR_CODEX.md) - WHAT to build next
**Read before starting work!** This tells you current priorities.
- Updated regularly with latest status
- Shows what's complete, in-progress, not-started
- Clear "you are here" indicator
- Specific next tasks with acceptance criteria

**Status:** 🔄 Updated frequently (check before each task)

---

### 4. [../CODING_RULES.md](../CODING_RULES.md) - HOW to write code
**Reference while coding!** Technical standards and patterns.
- Migrations and database rules
- Async/await patterns
- Singapore compliance requirements
- Code organization standards

**Status:** ✅ Active rules (follow strictly)

---

## 📋 Other Documentation

### Feature-Specific Guides:
- [agents/marketing_pack_quickstart.md](agents/marketing_pack_quickstart.md) - Agent user guide
- [frontend/agents_site_capture.md](frontend/agents_site_capture.md) - Developer implementation guide
- [demos/agents_capture_demo.md](demos/agents_capture_demo.md) - Demo script

### Validation & Testing:
- [validation/live_walkthrough_plan.md](validation/live_walkthrough_plan.md) - User validation tracking
- [validation/outreach_drafts.md](validation/outreach_drafts.md) - User outreach templates

### Data Operations (Legacy):
- [data_sources_policy.md](data_sources_policy.md) - Data sourcing standards
- [update_cadence.md](update_cadence.md) - Ingestion frequency
- [reviewer_sop.md](reviewer_sop.md) - Data review checklist
- [export_api.md](export_api.md) - CAD/BIM export reference
- [finance_api.md](finance_api.md) - Finance endpoints
- [feasibility_workflows.md](feasibility_workflows.md) - Feasibility wizard
- [sample_fixtures.md](sample_fixtures.md) - Test fixtures

### Original Plans (Superseded):
- [feature_delivery_plan.md](feature_delivery_plan.md) - Original Phase 1 plan (now part of v2)

---

## 🎯 Quick Decision Tree

**Question:** "What should I build next?"
→ Check [NEXT_STEPS_FOR_CODEX.md](NEXT_STEPS_FOR_CODEX.md)

**Question:** "Is this feature in scope?"
→ Check [FEATURES.md](../FEATURES.md)

**Question:** "What phase are we in?"
→ Check [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md)

**Question:** "How do I write this code?"
→ Check [CODING_RULES.md](../CODING_RULES.md)

**Question:** "How do users use this feature?"
→ Check feature-specific guides in `agents/` or `frontend/`

---

## ⚠️ Common Mistakes to Avoid

### ❌ DON'T:
- Start building without reading FEATURES.md
- Jump to Phase 2+ before Phase 1 is validated
- Build features not listed in FEATURES.md
- Ignore the delivery plan dependencies
- Skip validation gates

### ✅ DO:
- Always check NEXT_STEPS_FOR_CODEX.md before starting
- Follow the phase order in feature_delivery_plan_v2.md
- Get validation feedback between phases
- Update progress in the delivery plan as you go
- Ask questions if requirements are unclear

---

## 📊 Current Project Status

**Overall Progress:** ~45% of total platform

**Completed:**
- ✅ Phase 1A: Agent GPS Capture (100%)
- ✅ Phase 1B: Market Intelligence (100%)
- ✅ Phase 1C: Marketing Packs (100%)
- ✅ CAD Processing Infrastructure (95%)

**In Progress:**
- ⏸️ Phase 1A Validation (waiting for real agents)
- ⚠️ Phase 2A: Developer GPS (5%)

**Next Up:**
- 🎯 Phase 1B: Development Advisory Services ← **START HERE**
- 🎯 Phase 1C: Market Integration (parallel)

**Not Started:**
- Phase 1D, 2B-2I, 3, 4, 5, 6 (see delivery plan)

---

## 🤝 Getting Help

**For strategic questions:** Review FEATURES.md and feature_delivery_plan_v2.md
**For technical questions:** Check CODING_RULES.md and existing code
**For priority questions:** Check NEXT_STEPS_FOR_CODEX.md
**For user questions:** Check feature-specific guides

**Still unclear?** Ask the project owner before proceeding.

---

## 🔄 Keeping Documentation Current

**After completing a feature:**
1. Update status in `feature_delivery_plan_v2.md` (❌ → ✅)
2. Update `NEXT_STEPS_FOR_CODEX.md` with new priorities
3. Add user guide if customer-facing feature
4. Update this README if major milestone reached

**After validation session:**
1. Document feedback in `validation/` directory
2. Update delivery plan with any scope changes
3. Revise estimates if needed

---

**Remember:** FEATURES.md is the source of truth. Everything else supports delivering it.
