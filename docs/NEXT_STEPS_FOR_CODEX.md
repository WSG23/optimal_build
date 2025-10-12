# NEXT STEPS GUIDE FOR CODEX (AND OTHER AI AGENTS)

> **⚠️ IMPORTANT:** This is a **DECISION GUIDE**, not a status tracker.
>
> **For current project status:** See [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) — start with the "📊 Current Progress Snapshot" section
>
> **Last Updated:** 2025-10-11

---

## 🎯 Quick Start (20 Minutes)

**New to this project? Follow these steps:**

### Step 0: Understand Frontend UI Status (3 min) 🚨 CRITICAL
→ Read [UI_STATUS.md](../UI_STATUS.md) FIRST

**This prevents massive waste of time:**
- ❌ Polishing test UI that will be replaced
- ❌ Treating test harness as production code
- ❌ Adding offline fallback / professional error handling to temporary scaffolding
- ❌ Applying B2B professional tool standards to development tools

**CRITICAL FACT:** All frontend UI was created by AI agents as test harnesses. Product owner was NOT involved in UI design. DO NOT polish it.

**Before touching ANY frontend file, read UI_STATUS.md.**

### Step 1: Check Current Status (5 min)
→ Read [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md), beginning with the "📊 Current Progress Snapshot" section

Look for:
- ✅ What's complete
- ⏸️ What's in progress
- ❌ What's not started

### Step 2: Check for Known Issues (5 min)
→ Read [TESTING_KNOWN_ISSUES.md](../TESTING_KNOWN_ISSUES.md)

This prevents you from:
- ❌ Investigating known test harness issues
- ❌ Trying to fix documented limitations
- ❌ Wasting time on non-problems

**⚠️ IMPORTANT:** When you fix a known issue or discover a new test limitation, you MUST update this file. See step 7b below for the workflow.

### Step 3: Understand the Codebase (5 min)
→ Read [FEATURES.md](../FEATURES.md) (just scan headers)
→ Read [CODING_RULES.md](../CODING_RULES.md) (reference while coding)

### Step 4: Choose Your Task (5 min)
→ Use the decision tree below

### Step 5: After Implementation - ALWAYS Suggest Tests ⚠️
→ When you complete ANY feature, you MUST provide test commands to the user
→ See "MANDATORY TESTING CHECKLIST" section below (step 7)

**Non-negotiable:** Every implementation ends with test suggestions, even if you can't run them yourself.

---

## 🌳 Decision Tree: What Should I Build?

### Question 1: Is there a ❌ NOT STARTED task in current phase?

**Check:** [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) — use the current phase callout in "📊 Current Progress Snapshot"

**If YES:** Build that task (skip to "How to Start")

**If NO:** Go to Question 2

---

### Question 2: Is current phase blocked?

**Common blockers:**
- "Waiting for API credentials"
- "Waiting for user validation"
- "Depends on Phase X completion"

**If BLOCKED:** Go to Question 3

**If NOT BLOCKED:** Something's wrong - ask the user

---

### Question 3: What's the next unblocked phase?

**Check:** [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) — review the "Phase 1D: Business Performance Management" section and the phases that follow

**Look for:**
- Phase marked ❌ NOT STARTED
- No dependency blockers
- No external requirements

**Found one?** Build that (skip to "How to Start")

**All phases blocked?** Ask the user for direction

---

## 📚 How to Start a New Phase

### Before Writing Code:

**1. Read the phase requirements**
- Location: [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md)
- Find your phase section
- Note: Requirements, Acceptance Criteria, Estimated Effort

**2. Check FEATURES.md for details**
- The plan will reference section headers (e.g., "Phase 1D: Business Performance Management")
- Read those sections in [FEATURES.md](../FEATURES.md)
- This is the detailed specification

**3. Verify dependencies**
- Check "Dependencies" section in the phase
- Ensure prerequisite phases are ✅ COMPLETE
- If blocked, choose a different phase

### While Building:

**4. Follow CODING_RULES.md**
- [CODING_RULES.md](../CODING_RULES.md) has:
  - Migration patterns
  - Async/await standards
  - Import ordering rules
  - Singapore compliance requirements

**5. Write tests as you go**
- Backend tests: Always write and make them pass
- Frontend tests: Write them, but known JSDOM timing issues exist
- Document test status in commit message

**6. Check for existing patterns**
- Look at completed phases for patterns
- Reuse service/API/frontend structures
- Keep consistency

### After Completing Work:

**⚠️ MANDATORY TESTING CHECKLIST**

**7. Run tests and provide user with test commands** (CRITICAL - DO NOT SKIP)

When you complete ANY feature implementation, you MUST:

✅ **a) Run backend tests locally (if you can):**
```bash
python -m pytest backend/tests/test_[your_feature].py -v
```

✅ **b) ALWAYS suggest test commands to the user:**
```markdown
"I've completed [feature name]. Please run these tests locally to verify:

Backend tests:
python -m pytest backend/tests/test_services/test_[feature].py -v
python -m pytest backend/tests/test_api/test_[feature].py -v

Frontend tests (if applicable):
npm run lint
NODE_ENV=test node --test --import tsx --import ./scripts/test-bootstrap.mjs frontend/src/pages/__tests__/[Feature]Page.test.tsx

Manual UI testing:
1. Start the server: make dev
2. Navigate to: http://localhost:4400/#/[route]
3. Test: [specific actions to verify]"
```

✅ **c) Document test results in your message:**
- If tests pass: "✅ All tests passing"
- If tests skip: "⚠️ Test skipped because [reason]"
- If tests fail: "❌ Tests failing - needs debugging"

**Why this matters:**
- User needs to verify your work locally
- Test results inform commit message
- Prevents shipping broken code
- Gives user confidence in the implementation

---

**7b. Update TESTING_KNOWN_ISSUES.md if needed** (CRITICAL)

When you encounter test issues, you MUST check and update TESTING_KNOWN_ISSUES.md:

✅ **If you FIX a known issue:**
- Move it from "Active Issues" to "Resolved Issues"
- Add resolution date, who fixed it, and how
- Update the "Files Changed" section
- Example: "Backend: API Tests Skipped on Python 3.9 - RESOLVED"

✅ **If you DISCOVER a test harness limitation (not a real bug):**
- Check if it's already in "Active Issues"
- If NEW, propose adding it to the user
- Include: symptom, root cause, impact, workaround
- Example: "Frontend tests timeout but app works correctly"

✅ **If tests fail due to REAL bugs:**
- Do NOT add to TESTING_KNOWN_ISSUES.md
- Fix the bug instead

**Why this matters:**
- Prevents future AI agents from wasting time on known issues
- Documents test infrastructure limitations vs real bugs
- Builds institutional knowledge across sessions

---

**7c. Update feature_delivery_plan_v2.md BEFORE asking user to commit** ⚠️ BLOCKING STEP

🛑 **STOP: Do not proceed to commit until you complete this step.**

When you finish implementing a feature/milestone, you MUST update the status document **in the same commit** as your code changes.

**Why this is mandatory:**
- `feature_delivery_plan_v2.md` is the **SINGLE SOURCE OF TRUTH** for project status
- Other AI agents in new chat windows rely on it to know what's done
- User relies on it to track progress across sessions
- Outdated status creates confusion and duplicate work
- This document will be referenced for 6-12 months during pre-launch development

**Required updates:**

✅ **Step 1: Update "📊 Current Progress Snapshot" section (lines 7-59)**

Find your phase and update the percentage + remaining items:
```diff
Example for Phase 1D after completing ROI Analytics:

- **Phase 1D: Business Performance Management** - 45%
+ **Phase 1D: Business Performance Management** - 60%
- Remaining: ROI Analytics, Commission Protection, Performance Benchmarking
+ Remaining: Commission Protection, Performance Benchmarking
```

**How to calculate percentage:**
- Count total milestones in phase (e.g., 3 milestones: Deal Pipeline, ROI Analytics, Commission Protection)
- Divide completed by total (e.g., 2/3 = 66%, round to 60-65%)

✅ **Step 2: Update detailed phase section (find "Phase X:" heading)**

Add what you delivered to the phase's status:
```diff
Example:

- **Status:** 45% - Deal pipeline + commission ledger API (October 2025)
+ **Status:** 60% - Deal pipeline + commission + ROI analytics (October 2025)

Add to "Delivered" section:
+ - ✅ ROI metrics aggregation in performance snapshots
+ - ✅ compute_project_roi() integration from app.core.metrics
+ - ✅ Snapshot context derivation (pipeline metadata)
+ - ✅ Tests: test_agent_performance.py passing (4/4)

Update "Test Status" if needed:
- Backend service tests passing (test_agent_deal_pipeline.py, test_agent_commissions.py)
+ Backend service tests passing (test_agent_deal_pipeline.py, test_agent_commissions.py, test_agent_performance.py)
```

✅ **Step 3: Stage the documentation with your code changes**
```bash
git add docs/feature_delivery_plan_v2.md
# This goes in the SAME commit as your feature code
```

✅ **Step 4: Mention documentation update in commit message**
```bash
git commit -m "Add Phase 1D ROI Analytics

Backend changes:
- ROI metrics aggregation in performance snapshots
- compute_project_roi() integration
- Snapshot context derivation

Tests: 4/4 passing

Updated docs/feature_delivery_plan_v2.md:
- Phase 1D progress: 45% → 60%
- Added ROI Analytics to delivered milestones
```

**When to update:**
- ✅ After tests pass (Step 7a-7b complete)
- ✅ Before asking user to commit
- ✅ Every time you complete a milestone/feature
- ✅ Even for partial progress (e.g., backend done, frontend pending)

**What if you're not sure what to write?**
- Look at completed phases (1A, 1B, 1C) for examples
- Match the formatting and structure
- Ask user: "I completed X. Should I update feature_delivery_plan_v2.md to show X% progress?"

---

**8. Commit with descriptive message** (after updating docs above)
```bash
git commit -m "Complete Phase X Milestone: Feature Name

Backend/Frontend changes:
- [Key feature 1]
- [Key feature 2]

Tests: [Backend X/X passing, Frontend status]
Files: [Key files created/modified]

Updated feature_delivery_plan_v2.md:
- Phase X progress: Y% → Z%
- Added [Feature Name] to delivered milestones

See feature_delivery_plan_v2.md for full details."
```

---

## 🚫 What NOT to Do

### ❌ Don't Duplicate Status in This File

**WRONG:**
```markdown
Phase 1B: ✅ COMPLETE
Phase 1C: ✅ COMPLETE
Phase 1D: ❌ NOT STARTED ← Do this next
```

**This creates two sources of truth and they WILL get out of sync.**

**RIGHT:**
```markdown
For current status, see the "📊 Current Progress Snapshot" section in feature_delivery_plan_v2.md
```

---

### ❌ Don't Skip the Delivery Plan

**WRONG:** Just ask user "what should I build?"

**RIGHT:**
1. Check delivery plan for current phase
2. If unclear or blocked, THEN ask user

---

### ❌ Don't Start Phase 2 Before Phase 1 Done

**Check:** [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) — look at the "Phase 1 Completion Gate" checklist

**Phase 1 Completion Gate:**
- All 6 Agent tools implemented
- User validation complete
- Feedback incorporated

**Don't jump ahead** - the phases have dependencies.

---

## 🎯 Common Scenarios

### Scenario 1: "I'm starting fresh on this project"

**Do this:**
1. Read the "📊 Current Progress Snapshot" section in feature_delivery_plan_v2.md (5 min)
2. Read TESTING_KNOWN_ISSUES.md (5 min)
3. Find first ❌ NOT STARTED task without blockers
4. Read that phase's requirements
5. Start building

**Time to first code:** ~20 minutes

---

### Scenario 2: "Previous AI agent just finished Phase X"

**Do this:**
1. Verify Phase X shows ✅ COMPLETE in feature_delivery_plan_v2.md
2. Look for next ❌ NOT STARTED phase
3. Check for blockers
4. If blocked, find next unblocked phase
5. Start building

**Time to continue:** ~10 minutes

---

### Scenario 3: "Tests are failing - is this a bug?"

**Do this:**
1. Check TESTING_KNOWN_ISSUES.md first
2. Is it listed there? → Not a bug, skip it
3. Not listed? → Investigate as real bug
4. If new issue found → Document it (see workflow in TESTING_KNOWN_ISSUES.md)

---

### Scenario 4: "Phase is blocked on API credentials"

**Do this:**
1. Note the blocker in your message to user
2. Find next unblocked phase
3. Build that instead
4. Keep momentum going

**Don't:** Wait around for credentials

---

### Scenario 5: "User says 'continue where we left off'"

**Do this:**
1. Read the "📊 Current Progress Snapshot" section in feature_delivery_plan_v2.md
2. Find the most recent ✅ COMPLETE phase
3. Look for next ❌ NOT STARTED
4. That's where you left off
5. Confirm with user if unclear

---

## 📊 Understanding Phase Dependencies

### Phase Order (from delivery plan):

```
Phase 1: Agent Foundation (A → B → C → D)
  ├─ 1A: GPS Capture ✅ No dependencies
  ├─ 1B: Advisory ⚠️ Can start (uses 1A data)
  ├─ 1C: Integrations ⚠️ Can start (parallel with 1B)
  └─ 1D: Performance ⚠️ Uses data from 1B + 1C

Phase 2: Developer Foundation (depends on Phase 1 complete)
  └─ Can't start until Phase 1 validated

Phase 3+: Later phases (depend on Phase 2)
```

**Key rule:** Don't skip ahead. Validate before moving to next major phase.

---

## 🤝 When to Ask the User

### ASK when:
- ✅ Current phase is blocked and ALL phases are blocked
- ✅ Requirements are ambiguous or contradictory
- ✅ You need external credentials/API access
- ✅ Major architectural decision needed
- ✅ Validation results change priorities

### DON'T ASK when:
- ❌ Status is clear in feature_delivery_plan_v2.md
- ❌ Test failure is in TESTING_KNOWN_ISSUES.md
- ❌ Coding pattern exists in codebase
- ❌ Answer is in FEATURES.md or CODING_RULES.md

**Be autonomous** - most answers are in the docs.

---

## 🔄 Update Workflow

### When You Complete a Phase:

**1. Update feature_delivery_plan_v2.md (Required)**
- Change ❌ NOT STARTED → ✅ COMPLETE
- Add completion date
- Add test status
- List key files delivered

**2. Do NOT Update This File**
- This file is a guide, not a status tracker
- Status lives in feature_delivery_plan_v2.md only

**3. Update TESTING_KNOWN_ISSUES.md (If Applicable)**
- Add new issues to "Active Issues"
- Move resolved issues to "Resolved Issues"
- Follow the workflow in that document

---

## 📞 Quick Reference

| Question | Answer |
|----------|--------|
| **"What's the current status?"** | [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) — see "📊 Current Progress Snapshot" |
| **"What should I build next?"** | Use decision tree above |
| **"Are there known test issues?"** | [TESTING_KNOWN_ISSUES.md](../TESTING_KNOWN_ISSUES.md) |
| **"What are the requirements?"** | [FEATURES.md](../FEATURES.md) + phase section in delivery plan |
| **"How should I write code?"** | [CODING_RULES.md](../CODING_RULES.md) |
| **"How do I update docs?"** | See "Update Workflow" above |

---

## 🎯 Success Checklist

Before saying "I'm done with Phase X":

- [ ] ✅ Feature works as specified in FEATURES.md
- [ ] ✅ Backend tests written and passing
- [ ] ✅ Frontend tests written (even if timing issues exist)
- [ ] ✅ Code follows CODING_RULES.md
- [ ] ✅ feature_delivery_plan_v2.md updated (status → ✅ COMPLETE)
- [ ] ✅ Commit message describes what was delivered
- [ ] ✅ Known issues documented (if any)

---

## 🚀 Ready to Start?

**Go to:** the "📊 Current Progress Snapshot" section in [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md)

Find your next task and start building! 💪
