# NEXT STEPS GUIDE FOR AI AGENTS AND DEVELOPERS

> **⚠️ IMPORTANT:** This is a **DECISION GUIDE**, not a status tracker.
>
> **For current project status:** See [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) — start with the "📊 Current Progress Snapshot" section
>
> **Last Updated:** 2025-10-23

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

**4. Review mandatory testing guides**
- Locate the phase-specific testing notes in:
  - [`TESTING_KNOWN_ISSUES.md`](../TESTING_KNOWN_ISSUES.md) – search for the phase name (e.g., "Phase 2A") to see manual flows that must be re-run
  - [`UI_STATUS.md`](../UI_STATUS.md) – confirm which UI surfaces require verification
  - [`TESTING_DOCUMENTATION_SUMMARY.md`](../TESTING_DOCUMENTATION_SUMMARY.md) – find the "minimum coverage" smoke or regression suites
  - [`README.md`](../README.md) – the `make dev` section explains how to monitor `.devstack/backend.log` while testing
- Keep those checklists open so your "Next steps" always match the documented expectations

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

Find your phase and update the percentage + remaining items.

**For Backend Work:**
```diff
Example for Phase 1D after completing ROI Analytics backend:

- **Phase 1D: Business Performance Management** - Backend 45%, UI 30%
+ **Phase 1D: Business Performance Management** - Backend 60%, UI 30%
- Backend: Deal Pipeline API ✅, Remaining: ROI Analytics, Commission Protection
+ Backend: Deal Pipeline API ✅, ROI Analytics ✅, Remaining: Commission Protection
```

**For UI/UX Work:**
```diff
Example for Phase 1D after completing Pipeline Kanban UI:

- **Phase 1D: Business Performance Management** - Backend 60%, UI 30%
+ **Phase 1D: Business Performance Management** - Backend 60%, UI 50%
- UI: Production shell ✅, Remaining: Pipeline Kanban, Analytics panels
+ UI: Production shell ✅, Pipeline Kanban ✅, Remaining: Analytics panels
```

**How to calculate percentage:**
- Count total milestones in phase (e.g., 3 milestones: Deal Pipeline, ROI Analytics, Commission Protection)
- Divide completed by total (e.g., 2/3 = 66%, round to 60-65%)
- **Track Backend and UI separately** - they progress independently

✅ **Step 2: Update detailed phase section (find "Phase X:" heading)**

**For Backend Work:**
Add to "Delivered (Milestone MX)" section:
```diff
+ **Delivered (Milestone M4 - ROI Analytics):**
+ - ✅ ROI metrics aggregation in performance snapshots
+ - ✅ compute_project_roi() integration from app.core.metrics
+ - ✅ Snapshot context derivation (pipeline metadata)
+ - ✅ Tests: test_agent_performance.py passing (4/4)
```

**For UI/UX Work:**
Add to "UI/UX Status" section (comes after Test Status, before Requirements):
```diff
+ **UI/UX Status (Production Customer-Facing Interface):**
+
+ **Delivered:**
+ - ✅ Pipeline Kanban board component
+ - ✅ Deal detail drawer with timeline/commissions
+
+ **In Progress (YYYY-MM-DD):**
+ - 🔄 Analytics panel
+ - 🔄 ROI panel
+
+ **UI Files:**
+ - frontend/src/app/pages/business-performance/PipelineBoard.tsx
+ - frontend/src/app/pages/business-performance/DealDrawer.tsx
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

**7d. Manual Testing (REQUIRED for UI/UX work)** ⚠️ BLOCKING STEP

🛑 **For UI/UX work: Do not proceed to commit until user completes manual testing**

When implementing customer-facing UI components, you MUST:
1. **Open the browser** to the UI page for the user to test (use `open "http://localhost:4400/#/[route]"`)
2. Provide a detailed manual test script (see template below)
3. Wait for user confirmation before proceeding to commit

**When manual testing is REQUIRED:**
- ✅ ANY customer-facing UI component (buttons, forms, cards, lists, etc.)
- ✅ New pages or navigation changes
- ✅ Form submissions or data entry
- ✅ Charts, visualizations, or dashboards
- ✅ Modals, drawers, popovers, or overlays
- ✅ Interactive widgets (drag-drop, filters, sorting, pagination)
- ✅ Any visual changes (styling, layout, colors, spacing)

**When manual testing is OPTIONAL:**
- ⚠️ Backend-only changes (no UI impact)
- ⚠️ Documentation updates
- ⚠️ Configuration or infrastructure changes

**Template for Manual Test Script:**

Provide this to the user:
```markdown
## Manual Testing Required: [Component/Feature Name]

### Setup
1. Start server: `make dev`
2. Navigate to: `http://localhost:4400/#/[route]`
3. Test as user role: [Agent/Developer/Architect]
4. Prerequisites: [Any data setup needed]

### Test Scenarios

**1. Happy Path (Primary User Journey)**
- **Action:** [e.g., Click "Create Deal" button]
- **Expected:** [e.g., Modal opens with form fields for deal details]
- **Verify:**
  - [ ] UI renders correctly (no layout breaks)
  - [ ] All interactive elements work
  - [ ] Data submits successfully
  - [ ] Success feedback shown

**2. Empty State**
- **Action:** [e.g., Load page with no existing deals]
- **Expected:** [e.g., Empty state message with CTA to create first deal]
- **Verify:**
  - [ ] Message is clear and user-friendly
  - [ ] CTA button is prominent and actionable
  - [ ] No broken UI or console errors

**3. Error State**
- **Action:** [e.g., Submit form with invalid data / trigger API error]
- **Expected:** [e.g., Validation errors display inline OR error message shows]
- **Verify:**
  - [ ] Error messages are user-friendly (not technical jargon)
  - [ ] Errors point to specific fields/issues
  - [ ] User knows how to fix the problem
  - [ ] UI remains functional after error

**4. Loading State**
- **Action:** [e.g., Trigger API call (may need network throttling)]
- **Expected:** [e.g., Loading spinner/skeleton appears while fetching]
- **Verify:**
  - [ ] Loading indicator is visible
  - [ ] UI doesn't flash or jump when data loads
  - [ ] Layout is stable (no content shift)
  - [ ] User can't trigger duplicate actions

**5. Complete Interaction Flow**
- **Action:** [e.g., Create deal → view in pipeline → update stage → see analytics]
- **Expected:** [e.g., User completes entire workflow without confusion]
- **Verify:**
  - [ ] Navigation between steps is clear
  - [ ] User feedback at each step
  - [ ] No dead ends or confusing states
  - [ ] User achieves their goal successfully

**6. Edge Cases**
- **Long text:** [e.g., Deal name with 100+ characters]
  - [ ] Text truncates gracefully with ellipsis or wraps properly
- **Large numbers:** [e.g., Values over $1,000,000,000]
  - [ ] Numbers format correctly with commas/currency
- **Missing optional data:** [e.g., Deal without description]
  - [ ] UI handles gracefully (shows "—" or hides field)
- **Slow network:** [Throttle to Fast 3G in DevTools]
  - [ ] Loading states work correctly
  - [ ] No timeouts or hanging requests
- **Browser compatibility:** [Test in Chrome, Safari, Firefox]
  - [ ] UI works consistently across browsers

**7. Visual Quality**
- [ ] No alignment issues (elements properly aligned)
- [ ] Consistent spacing (padding/margins follow design system)
- [ ] Colors match design (no random colors)
- [ ] Typography correct (font sizes, weights, line heights)
- [ ] Icons render properly (no broken images)
- [ ] Responsive design works (test mobile viewport 375px width)

**8. Accessibility**
- [ ] **Keyboard navigation:** Tab through all interactive elements
- [ ] **Focus indicators:** Clear visual focus on active element
- [ ] **Screen reader:** Test with VoiceOver (Mac) or NVDA (Windows)
  - [ ] All buttons/links have descriptive labels
  - [ ] Form fields have associated labels
  - [ ] Error messages are announced
- [ ] **Color contrast:** Text readable (use browser DevTools)

---

**Document the current status so the next builder isn’t guessing:**
- After sharing the script, update [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) for that phase with the manual-testing status (**Pending**, **In Progress**, or **Complete**) and list any blockers.
- Capture the active environment context (for example, “Backend reset running”, “Using fallback propertyId”, “Waiting on Claude seed script”). When the situation changes, update the note.
- If manual tests are blocked, call it out in the plan doc and in your handoff message so the next agent knows exactly what remains.

### Test Results

Please complete the above tests and reply:

**"✅ Manual testing complete - all scenarios passing"**

OR if issues found:

**"❌ Manual testing found issues: [describe problems]"**

---

**I will wait for your test confirmation before proceeding to commit.**
```

**Example for Phase 1D Pipeline Kanban:**
```markdown
## Manual Testing Required: Pipeline Kanban Board

### Setup
1. Start server: `make dev`
2. Navigate to: `http://localhost:4400/#/app/performance`
3. Test as: Agent Team Lead
4. Prerequisites: Ensure backend has test deals in database

### Test Scenarios

**1. Happy Path: View and Move Deals**
- **Action:** View pipeline board with deals in various stages
- **Expected:** Kanban columns show deals grouped by stage
- **Verify:**
  - [ ] All deals render in correct stage columns
  - [ ] Deal cards show: title, asset type, value, confidence %
  - [ ] Can drag deal card to different stage
  - [ ] Card updates position and backend updates stage

**2. Empty State**
- **Action:** View pipeline with no deals (clear DB or filter to empty result)
- **Expected:** Empty state message: "No deals yet. Create your first deal to get started."
- **Verify:**
  - [ ] Message is centered and clear
  - [ ] "Create Deal" CTA button is prominent
  - [ ] No broken Kanban layout

**3. Error State**
- **Action:** Disconnect network, try to move deal to new stage
- **Expected:** Error toast/message: "Failed to update deal stage. Please try again."
- **Verify:**
  - [ ] Error message appears
  - [ ] Deal reverts to original position
  - [ ] User can retry action

**4. Loading State**
- **Action:** Load page (throttle network to Fast 3G)
- **Expected:** Loading skeletons appear in each column
- **Verify:**
  - [ ] Skeleton cards visible while loading
  - [ ] No layout shift when real data loads
  - [ ] Smooth transition from skeleton to cards

**5. Complete Flow: Create → Move → View**
- **Action:** Create new deal → appears in "Lead captured" → drag to "Qualified" → view timeline
- **Expected:** Deal moves through pipeline and timeline shows stage history
- **Verify:**
  - [ ] New deal appears immediately in correct column
  - [ ] Drag-and-drop feels smooth
  - [ ] Timeline shows stage transition with timestamp
  - [ ] Audit metadata visible (hash, changed by)

**6. Edge Cases**
- **Long deal name:** "Very Long Commercial Property Name That Exceeds Normal Length at Marina Bay Waterfront District"
  - [ ] Truncates with ellipsis, full name in tooltip
- **Large value:** $1,234,567,890
  - [ ] Formats as "$1.2B" or "$1,234,567,890" with commas
- **100+ deals:** Populate DB with many deals
  - [ ] Performance acceptable (no lag when scrolling)
  - [ ] Columns scroll independently if needed

**7. Visual Quality**
- [ ] Card spacing consistent within columns
- [ ] Column widths equal
- [ ] Deal cards have subtle shadow/border
- [ ] Confidence % shows as colored badge (green high, yellow medium, red low)
- [ ] Asset type icons render correctly

**8. Accessibility**
- [ ] Tab to each deal card
- [ ] Enter key opens deal details
- [ ] Arrow keys navigate between cards
- [ ] Screen reader announces: "Deal card: [name], [stage], [value]"

Please test and confirm: ✅ All scenarios passing
```

**Why this step is critical:**
- Automated tests don't catch visual bugs (alignment, colors, spacing)
- UX flow issues require human judgment (is it confusing? intuitive?)
- Accessibility problems need manual verification (keyboard nav, screen reader)
- User experience quality depends on manual testing
- Frontend tests don't validate actual browser rendering
- Edge cases often slip through without manual verification

**What happens next:**
1. You provide test script (above template)
2. User completes manual testing
3. User confirms: "✅ All scenarios passing" OR reports issues
4. If passing → proceed to Step 8 (commit)
5. If issues → fix them, ask user to retest

---

**8. Commit with descriptive message** (after docs updated AND manual testing complete)
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

## 🌍 JURISDICTION EXPANSION WINDOW 1: After Phase 2C (BLOCKING)

### ⚠️ CRITICAL: Do NOT Start Phase 2D Until This Is Complete

**When Phase 2C shows ✅ COMPLETE in feature_delivery_plan_v2.md:**

🛑 **STOP** - Do NOT immediately start Phase 2D.

**Instead:** Begin **Expansion Window 1** to add 4 new jurisdictions:
1. 🇭🇰 **Hong Kong** (Week 1-2)
2. 🇳🇿 **New Zealand** (Week 3)
3. 🇺🇸 **Washington State (Seattle)** (Week 4)
4. 🇨🇦 **Toronto (Ontario)** (Week 5)

**Why this timing matters:**
- Adding jurisdictions AFTER Phase 6 requires 6-12 months refactoring
- Singapore-only assumptions will harden in Phase 3-6 (Architect/Engineer tools)
- This prevents 18 months of missed revenue and late market entry
- Phase 2D-6 features will be built multi-jurisdiction from start

---

### Expansion Workflow for Each Jurisdiction

**For detailed step-by-step instructions, see:** [`jurisdiction_expansion_playbook.md`](jurisdiction_expansion_playbook.md)

#### Quick Workflow Summary:

**1. PM Preparation (BEFORE Codex starts coding):**
- ✅ Secure API access (government planning/zoning APIs)
- ✅ Collect sample regulations (5-10 sample zoning rules)
- ✅ Gather market data (build costs, land prices, ROI benchmarks)
- ✅ Identify heritage data sources (conservation areas, protected buildings)
- ✅ Prepare validation data (known sites to test compliance)

**2. Codex Implementation (6-10 days per jurisdiction):**
- ✅ Create jurisdiction structure: `jurisdictions/{code}/`
- ✅ Implement `fetch.py` (API integration)
- ✅ Implement `parse.py` (transform to CanonicalReg)
- ✅ Refactor services to accept jurisdiction parameter
- ✅ Seed RefRule database with zoning rules
- ✅ Add heritage data (conservation areas)
- ✅ Update tests (compliance, buildable, geocoding)
- ✅ Document configuration (README.md, ENV vars)

**3. Claude Testing & Validation (2-3 days):**
- ✅ Run backend tests (pytest)
- ✅ Fix test failures
- ✅ Integration test (GPS → Feasibility → Finance for new jurisdiction)
- ✅ Regression test (ensure Singapore still works)
- ✅ Validation test (test with known sites in new jurisdiction)

**4. PM Manual Validation:**
- ✅ Test GPS capture for new jurisdiction
- ✅ Verify compliance checks (zoning rules)
- ✅ Check buildable calculations (FAR, coverage, height)
- ✅ Validate finance modeling (market data)
- ✅ Test heritage overlay (conservation areas)

---

### Sequential Rollout Schedule

**🇭🇰 Week 1-2: Hong Kong (First - Establishes Pattern)**
- Most similar to Singapore (95% similarity)
- APIs: DATA.GOV.HK (Land Registry, Buildings Dept, Planning Dept)
- Cost: HK$0/month (free government APIs)
- Effort: 10-14 days (includes refactoring)
- **Goal:** Refactor services to be jurisdiction-agnostic, establish plugin pattern

**🇳🇿 Week 3: New Zealand (Second - Validates Pattern)**
- Apply patterns learned from Hong Kong
- APIs: LINZ Data Service, Auckland Council API
- Cost: NZ$0/month (free government APIs)
- Effort: 6-8 days (faster - pattern established)

**🇺🇸 Week 4: Washington State (Third - Different Structure)**
- Tests plugin flexibility (different zoning structure than SG/HK)
- APIs: King County Parcel Viewer, Seattle Open Data
- Cost: $0/month (free government APIs)
- Effort: 6-8 days

**🇨🇦 Week 5: Toronto (Fourth - Final Validation)**
- Confirms multi-jurisdiction architecture is robust
- APIs: Toronto Open Data, Ontario Land Registry Connect
- Cost: CA$0/month (free government APIs)
- Effort: 6-8 days

**Total Expansion Window 1 Duration:** 5-6 weeks (not 5 months)

---

### Completion Gate (Before Starting Phase 2D)

**All 5 jurisdictions (SG + 4 new) must pass:**

✅ **Technical Validation:**
- [ ] All backend tests passing (pytest)
- [ ] All frontend tests passing (or documented exceptions)
- [ ] Integration tests pass (GPS → Feasibility → Finance)
- [ ] Regression tests pass (Singapore functionality unchanged)

✅ **PM Validation:**
- [ ] GPS capture works in all 5 jurisdictions
- [ ] Compliance checks correct for all 5 jurisdictions
- [ ] Buildable calculations accurate for all 5 jurisdictions
- [ ] Finance modeling uses correct market data for each jurisdiction
- [ ] Heritage overlays load correctly for each jurisdiction

✅ **Documentation:**
- [ ] Each jurisdiction has README.md with ENV vars
- [ ] Each jurisdiction has map_overrides.yaml
- [ ] feature_delivery_plan_v2.md updated with expansion status
- [ ] TESTING_KNOWN_ISSUES.md updated if new issues found

**Once all checks pass:** Proceed to Phase 2D with multi-jurisdiction support in place.

---

### What If Expansion Window 1 Is Skipped?

**If you see Phase 2D in progress WITHOUT Expansion Window 1 complete:**

🚨 **ALERT THE USER IMMEDIATELY:**

> "⚠️ WARNING: Phase 2D has started but Expansion Window 1 (4 new jurisdictions) is not complete.
>
> According to feature_delivery_plan_v2.md, all 4 jurisdictions (Hong Kong, New Zealand, Seattle, Toronto) should be added BEFORE Phase 2D starts.
>
> **Risk:** Phase 2D-6 code will be built with Singapore-only assumptions, requiring 6-12 months refactoring later.
>
> **Recommendation:** Pause Phase 2D and complete Expansion Window 1 first (5-6 weeks).
>
> See docs/feature_delivery_plan_v2.md section 'JURISDICTION EXPANSION WINDOWS' for full rationale."

**Don't proceed with Phase 2D** until user explicitly confirms to skip expansion or complete it.

---

### Where to Find Detailed Instructions

**For PM:** [`docs/jurisdiction_expansion_playbook.md`](jurisdiction_expansion_playbook.md) — Complete guide with checklists

**For Codex:** [`docs/jurisdiction_expansion_playbook.md`](jurisdiction_expansion_playbook.md) → Section 4 "Codex Workflow"

**For Claude:** [`docs/jurisdiction_expansion_playbook.md`](jurisdiction_expansion_playbook.md) → Section 5 "Claude Workflow"

**For Strategy/Rationale:** [`docs/feature_delivery_plan_v2.md`](feature_delivery_plan_v2.md) → Section "JURISDICTION EXPANSION WINDOWS"

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
| **"Phase 2C is done - what's next?"** | 🛑 STOP - Do Expansion Window 1 (add 4 jurisdictions) BEFORE Phase 2D |
| **"How do I add a jurisdiction?"** | [jurisdiction_expansion_playbook.md](jurisdiction_expansion_playbook.md) |
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
