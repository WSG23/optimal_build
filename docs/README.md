# Project Documentation

## 🚨 New to This Project?

**👉 Read [../START_HERE.md](../START_HERE.md) for the authoritative reading order.**

That file provides the exact sequence for AI agents and developers to onboard efficiently.

---

## 📋 Documentation Index

This is a comprehensive index of all documentation in the `docs/` directory.

### Core Planning Documents:
- [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) - Complete roadmap and current status
- [ai-agents/next_steps.md](ai-agents/next_steps.md) - What to build next
- [handoff_playbook.md](handoff_playbook.md) - Session handoff guide

### Feature-Specific Guides:
- [agents/marketing_pack_quickstart.md](agents/marketing_pack_quickstart.md) - Agent user guide
- [frontend/agents_site_capture.md](frontend/agents_site_capture.md) - Developer implementation guide
- [demos/agents_capture_demo.md](demos/agents_capture_demo.md) - Demo script

### Testing & Quality:
- [development/testing/known-issues.md](development/testing/known-issues.md) - **Known test harness issues** (critical for AI agents)
- [development/testing/summary.md](development/testing/summary.md) - Overview of testing workflows
- [development/testing/advisory.md](development/testing/advisory.md) - Phase 1B testing guide

### Validation & User Research:
- [validation/live_testing_guide.md](validation/live_testing_guide.md) - Manual UAT testing procedures (Finance & Intelligence pages)
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
- [feature_delivery_plan_v1_deprecated.md](archive/feature_delivery_plan_v1_deprecated.md) - Original Phase 1 plan (now part of v2)

---

## 🎯 Quick Decision Tree

**Question:** "What should I build next?"
→ Check [ai-agents/next_steps.md](ai-agents/next_steps.md)

**Question:** "Is this feature in scope?"
→ Check [planning/features.md](planning/features.md)

**Question:** "What phase are we in?"
→ Check [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md)

**Question:** "How do I write this code?"
→ Check [CODING_RULES.md](../CODING_RULES.md)

**Question:** "How do users use this feature?"
→ Check feature-specific guides in `agents/` or `frontend/`

**Question:** "Test is failing - is this a known issue?"
→ Check [development/testing/known-issues.md](development/testing/known-issues.md)

**Question:** "I fixed a test issue - how do I update docs?"
→ Check [development/testing/summary.md](development/testing/summary.md)

---

## ⚠️ Common Mistakes to Avoid

### ❌ DON'T:
- Start building without reading FEATURES.md
- Jump to Phase 2+ before Phase 1 is validated
- Build features not listed in FEATURES.md
- Ignore the delivery plan dependencies
- Skip validation gates

### ✅ DO:
- Always check NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md before starting
- Follow the phase order in feature_delivery_plan_v2.md
- Get validation feedback between phases
- Update progress in the delivery plan as you go
- Ask questions if requirements are unclear

---

## 📊 Current Project Status

See [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) for the latest status snapshot.

---

## 🤝 Getting Help

**For strategic questions:** Review `planning/features.md` and `feature_delivery_plan_v2.md`
**For technical questions:** Check CODING_RULES.md and existing code
**For priority questions:** Check NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md
**For user questions:** Check feature-specific guides

**Still unclear?** Ask the project owner before proceeding.

---

## 🔄 Keeping Documentation Current

**After completing a feature:**
1. Update status in `feature_delivery_plan_v2.md` (❌ → ✅)
2. Update `NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md` with new priorities
3. Add user guide if customer-facing feature
4. Update this README if major milestone reached

**After validation session:**
1. Document feedback in `validation/` directory
2. Update delivery plan with any scope changes
3. Revise estimates if needed

---

**Remember:** FEATURES.md is the source of truth. Everything else supports delivering it.
