# Project Documentation

## 🚨 New to This Project?

**👉 Read [../START_HERE.md](../START_HERE.md) for the authoritative reading order.**

That file provides the exact sequence for AI agents and developers to onboard efficiently.

---

## 📋 Documentation Index

This is a comprehensive index of all documentation in the `docs/` directory.

### Core Planning Documents:
- [all_steps_to_product_completion.md](all_steps_to_product_completion.md) - Complete roadmap and current status
- [Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) - Tactical task list and technical debt actions
- [ai-agents/next_steps.md](ai-agents/next_steps.md) - What to build next
- [handoff_playbook.md](handoff_playbook.md) - Session handoff guide

### Feature-Specific Guides:
- [agents/marketing_pack_quickstart.md](agents/marketing_pack_quickstart.md) - Agent user guide
- [frontend/agents_site_capture.md](frontend/agents_site_capture.md) - Developer implementation guide
- [demos/agents_capture_demo.md](demos/agents_capture_demo.md) - Demo script

### Testing & Quality:
- [all_steps_to_product_completion.md#-known-testing-issues](all_steps_to_product_completion.md#-known-testing-issues) - **Known test harness issues** (critical for AI agents)
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
→ Check [Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) for Active/Ready tasks, then confirm context in [ai-agents/next_steps.md](ai-agents/next_steps.md)

**Question:** "Is this feature in scope?"
→ Check [planning/features.md](planning/features.md)

**Question:** "What phase are we in?"
→ Check [all_steps_to_product_completion.md](all_steps_to_product_completion.md)

**Question:** "How do I write this code?"
→ Check [CODING_RULES.md](../CODING_RULES.md)

**Question:** "How do users use this feature?"
→ Check feature-specific guides in `agents/` or `frontend/`

**Question:** "Test is failing - is this a known issue?"
→ Check [all_steps_to_product_completion.md#-known-testing-issues](all_steps_to_product_completion.md#-known-testing-issues)

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
- Always check [ai-agents/next_steps.md](ai-agents/next_steps.md) before starting
- Follow the phase order in all_steps_to_product_completion.md
- Get validation feedback between phases
- Update progress in all_steps_to_product_completion.md and [Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) as you go
- Ask questions if requirements are unclear

---

## 📊 Current Project Status

See [all_steps_to_product_completion.md](all_steps_to_product_completion.md) for the latest status snapshot and [Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) for current execution priorities.

---

## 🤝 Getting Help

**For strategic questions:** Review `planning/features.md` and `all_steps_to_product_completion.md`
**For technical questions:** Check CODING_RULES.md and existing code
**For priority questions:** Check [Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) and [ai-agents/next_steps.md](ai-agents/next_steps.md)
**For user questions:** Check feature-specific guides

**Still unclear?** Ask the project owner before proceeding.

---

## 🔄 Keeping Documentation Current

**After completing a feature:**
1. Update `[Unified Execution Backlog](all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work)` (move item, add commits, document follow-ups)
2. Update status in `all_steps_to_product_completion.md` (❌ → ✅)
3. Update [ai-agents/next_steps.md](ai-agents/next_steps.md) with new priorities
4. Add user guide if customer-facing feature
5. Update this README if major milestone reached

**After validation session:**
1. Document feedback in `validation/` directory
2. Update delivery plan with any scope changes
3. Revise estimates if needed

---

**Remember:** FEATURES.md is the source of truth. Everything else supports delivering it.
