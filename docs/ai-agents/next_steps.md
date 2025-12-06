# NEXT STEPS GUIDE FOR AI AGENTS AND DEVELOPERS

> **⚠️ IMPORTANT:** This is a **DECISION GUIDE**, not a status tracker.
>
> **For strategic status:** See [all_steps_to_product_completion.md](all_steps_to_product_completion.md) — start with the "📊 Current Progress Snapshot" section
> **For actionable tasks:** Check [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) before coding
>
> **Last Updated:** 2025-12-06 (Phase 1 complete, Phase 2B complete, Phase 2C complete, Phase 2D complete, Expansion Window 1 complete)

---

## 🎯 Quick Start (20 Minutes)

**New to this project? Follow these steps:**

### Step 0: Understand Frontend UI Status (3 min) 🚨 CRITICAL
→ Read [ui-status.md](../planning/ui-status.md) FIRST

**This prevents massive waste of time:**
- ❌ Polishing test UI that will be replaced
- ❌ Treating test harness as production code
- ❌ Adding offline fallback / professional error handling to temporary scaffolding
- ❌ Applying B2B professional tool standards to development tools

**CRITICAL FACT:** All frontend UI was created by AI agents as test harnesses. Product owner was NOT involved in UI design. DO NOT polish it.

**Before touching ANY frontend file, read UI_STATUS.md.**

### Step 1: Check Current Status (5 min)
→ Read [all_steps_to_product_completion.md](all_steps_to_product_completion.md), beginning with the "📊 Current Progress Snapshot" section

Look for:
- ✅ What's complete
- ⏸️ What's in progress
- ❌ What's not started

### Step 2: Check for Known Issues (5 min)
→ Read [Testing Known Issues](../all_steps_to_product_completion.md#-known-testing-issues)

This prevents you from:
- ❌ Investigating known test harness issues
- ❌ Trying to fix documented limitations
- ❌ Wasting time on non-problems

**⚠️ IMPORTANT:** When you fix a known issue or discover a new test limitation, you MUST update this file. See step 7b below for the workflow.

### Step 3: Understand the Codebase (5 min)
→ Read [features.md](../planning/features.md) (just scan headers)
→ Read [CODING_RULES.md](../CODING_RULES.md) (reference while coding)

### Step 4: Choose Your Task (5 min)
→ Review [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) and follow the decision tree below

### Step 5: After Implementation - ALWAYS Suggest Tests ⚠️
→ When you complete ANY feature, you MUST provide test commands to the user
→ See "MANDATORY TESTING CHECKLIST" section below (step 7)

**Non-negotiable:** Every implementation ends with test suggestions, even if you can't run them yourself.

---

## 🌳 Decision Tree: What Should I Build?

### Question 1: Is there a ❌ NOT STARTED task in current phase?

**Check:** [all_steps_to_product_completion.md](all_steps_to_product_completion.md) — confirm phase priority, then cross-check [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) Active items

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

**Check:** [all_steps_to_product_completion.md](all_steps_to_product_completion.md) for phase sequencing, then ensure the task appears in [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work)

**Look for:**
- Phase marked ❌ NOT STARTED
- No dependency blockers
- No external requirements

**Found one?** Build that (skip to "How to Start")

**All phases blocked?** Ask the user for direction

---

## ✅ Expansion Window 1 (Hong Kong / New Zealand / Seattle / Toronto) — COMPLETE

> **Status:** ✅ COMPLETE (2025-12-06) — All 4 jurisdictions implemented with property models, compliance utilities, seed scripts, and test suites.

**Completed Jurisdictions:**
- 🇭🇰 **Hong Kong:** `HongKongProperty` model, `hong_kong_compliance.py`, `seed_hong_kong_rules.py`, tests
- 🇳🇿 **New Zealand:** `NewZealandProperty` model, `new_zealand_compliance.py`, `seed_new_zealand_rules.py`, tests
- 🇺🇸 **Seattle/Washington:** `SeattleProperty` model, `seattle_compliance.py`, `seed_seattle_rules.py`, tests
- 🇨🇦 **Toronto/Ontario:** `TorontoProperty` model, `toronto_compliance.py`, `seed_toronto_rules.py`, tests

**Files Delivered (per jurisdiction):**
- Property model: `backend/app/models/<jurisdiction>_property.py`
- Compliance utils: `backend/app/utils/<jurisdiction>_compliance.py`
- Seed script: `backend/scripts/seed_<jurisdiction>_rules.py`
- Test suite: `backend/tests/test_utils/test_<jurisdiction>_compliance.py`
- Relationships: Added to `backend/app/models/projects.py`
- Registration: Added to `backend/app/models/__init__.py`

**Next:** Phase 2D-2I can now proceed with multi-jurisdiction support built-in from the start.
---

## 📚 How to Start a New Phase

### Before Writing Code:

**1. Read the phase requirements**
- Strategic context: [all_steps_to_product_completion.md](all_steps_to_product_completion.md)
- Execution details: [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work)
- Find your phase section
- Note: Requirements, Acceptance Criteria, Estimated Effort

**2. Check features for details**
- The plan will reference section headers (e.g., "Phase 1D: Business Performance Management")
- Read those sections in [features.md](../planning/features.md)
- This is the detailed specification

**3. Verify dependencies**
- Check "Dependencies" section in the phase
- Ensure prerequisite phases are ✅ COMPLETE
- If blocked, choose a different phase

**4. Review mandatory testing guides**
- Locate the phase-specific testing notes in:
  - [`Testing Known Issues`](../all_steps_to_product_completion.md#-known-testing-issues) – search for the phase name (e.g., "Phase 2A") to see manual flows that must be re-run
  - [`ui-status.md`](../planning/ui-status.md) – confirm which UI surfaces require verification
  - [`Testing Documentation Summary`](../development/testing/summary.md) – find the "minimum coverage" smoke or regression suites
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

**7b. Update Known Testing Issues section (docs/all_steps_to_product_completion.md#-known-testing-issues) if needed** (CRITICAL)

When you encounter test issues, you MUST check and update Known Testing Issues section (docs/all_steps_to_product_completion.md#-known-testing-issues):

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
- Do NOT add to Known Testing Issues section (docs/all_steps_to_product_completion.md#-known-testing-issues)
- Fix the bug instead

**Why this matters:**
- Prevents future AI agents from wasting time on known issues
- Documents test infrastructure limitations vs real bugs
- Builds institutional knowledge across sessions

---

**7c. Update all_steps_to_product_completion.md (backlog + phase summary) BEFORE asking user to commit** ⚠️ BLOCKING STEP

🛑 **STOP: Do not proceed to commit until you complete this step.**

When you finish implementing a feature/milestone, you MUST update the backlog + phase sections **in the same commit** as your code changes.

**Why this is mandatory:**
- The [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) is the **single source of truth** for active tasks and technical debt follow-ups
- `all_steps_to_product_completion.md` communicates strategic status to stakeholders and future agents
- Outdated docs create duplicate work, conflicting priorities, and failed gate checks

---

**Required updates:**

✅ **Step 1: Update the Unified Execution Backlog (execution log)**
- Move items between **Active → Completed** or **Ready → Active** as work progresses
- Add completion date, commit hashes, and impact summary for finished items
- Record new blockers or follow-up actions under the appropriate section

✅ **Step 2: Update docs/all_steps_to_product_completion.md (strategic snapshot)**
- Adjust the phase status table if progress or completion changed
- Update the relevant phase summary bullets with what shipped and remaining risks
- Tick Phase 2D gate checkboxes when prerequisites are satisfied (e.g., audit complete)
- Mention dependencies, regressions, or testing insights in plain language

✅ **Step 3: Stage the documentation with your code changes**
```bash
git add docs/all_steps_to_product_completion.md
# These go in the SAME commit as your feature code
```

✅ **Step 4: Mention documentation update in commit message**
```bash
git commit -m "feat: close audit hook action for Phase 2D gate"

Backend changes:
- Stabilise phase gate script for schema migrations
- Add regression tests for hook execution

Tests: pytest passing (12/12)

Updated docs/all_steps_to_product_completion.md:
- Unified backlog: Moved "Infrastructure Audit - Option 10" to Completed with commit hashes
- Unified backlog: Logged new follow-up task for hook telemetry
- Phase 1D summary: noted audit blocker resolved
- Phase 2D gate checkbox: Pre-Phase 2D Infrastructure Audit marked [x]
```

**When to update:**
- ✅ After tests pass (Step 7a-7b complete)
- ✅ Before asking user to commit
- ✅ Every time you complete a milestone/feature
- ✅ Even for partial progress (e.g., backend done, frontend pending)

---

### 🚫 Common Mistakes to Avoid

**❌ MISTAKE #1: Leaving tasks in Active after completion**
```markdown
## 🚀 Active (Do Now - Priority Order)
1. Infrastructure Audit - Option 10: Fix pre-commit hook failures  ← STILL LISTED HERE

## ✅ Completed
(nothing logged)
```
**Fix:** Move the task to Completed with date + commits.

**❌ MISTAKE #2: Forgetting to update Phase 2D gate checklist**
```markdown
- [ ] Phase 2D Gate: Pre-Phase 2D Infrastructure Audit & Quality Sprint complete
```
**Fix:** Change to `[x]` when the prerequisite work is finished.

**❌ MISTAKE #3: Marking a phase complete while the Unified Execution Backlog still has open items**
```markdown
| Phase | Status |
| Phase 1D | ✅ COMPLETE |

## 🚀 Active
1. Phase 1D: Build Pipeline Kanban UI component
```
**Fix:** Clear the task or move it to Completed before flipping the phase status.

---

### 🚫 Common Mistakes to Avoid

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
- After sharing the script, update [all_steps_to_product_completion.md](all_steps_to_product_completion.md) for that phase with the manual-testing status (**Pending**, **In Progress**, or **Complete**) and list any blockers.
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

Updated all_steps_to_product_completion.md:
- Phase X progress: Y% → Z%
- Added [Feature Name] to delivered milestones

See all_steps_to_product_completion.md for full details."
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
For current status, see the "📊 Current Progress Snapshot" section in all_steps_to_product_completion.md
```

---

### ❌ Don't Skip the Delivery Plan

**WRONG:** Just ask user "what should I build?"

**RIGHT:**
1. Check delivery plan for current phase
2. If unclear or blocked, THEN ask user

---

### ✅ Phase 1 Complete (2025-12-06)

**Phase 1 Completion Gate:** ✅ ALL PASSED
- ✅ All 6 Agent tools implemented (GPS Capture, Quick Analysis, Marketing Pack, Advisory, Integrations, Performance)
- ✅ v2 enhancements complete (Sales Velocity Model, Zillow, LoopNet, Salesforce, HubSpot mocks)
- ✅ Multi-jurisdiction support (SG, HK, NZ, Seattle, Toronto)

**Phase 2 is now unblocked** - proceed with Phase 2D-2I.

---

## 🎯 Common Scenarios

### Scenario 1: "I'm starting fresh on this project"

**Do this:**
1. Read the "📊 Current Progress Snapshot" section in all_steps_to_product_completion.md (5 min)
2. Read Known Testing Issues section (docs/all_steps_to_product_completion.md#-known-testing-issues) (5 min)
3. Find first ❌ NOT STARTED task without blockers
4. Read that phase's requirements
5. Start building

**Time to first code:** ~20 minutes

---

### Scenario 2: "Previous AI agent just finished Phase X"

**Do this:**
1. Verify Phase X shows ✅ COMPLETE in all_steps_to_product_completion.md
2. Look for next ❌ NOT STARTED phase
3. Check for blockers
4. If blocked, find next unblocked phase
5. Start building

**Time to continue:** ~10 minutes

---

### Scenario 3: "Tests are failing - is this a bug?"

**Do this:**
1. Check Known Testing Issues section (docs/all_steps_to_product_completion.md#-known-testing-issues) first
2. Is it listed there? → Not a bug, skip it
3. Not listed? → Investigate as real bug
4. If new issue found → Document it (see workflow in Known Testing Issues section (docs/all_steps_to_product_completion.md#-known-testing-issues))

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
1. Read the "📊 Current Progress Snapshot" section in all_steps_to_product_completion.md
2. Find the most recent ✅ COMPLETE phase
3. Look for next ❌ NOT STARTED
4. That's where you left off
5. Confirm with user if unclear

---

## 📊 Understanding Phase Dependencies

### Phase Order (from delivery plan):

```
Phase 1: Agent Foundation ✅ COMPLETE (2025-12-06)
  ├─ 1A: GPS Capture ✅ COMPLETE (v1 + v2)
  ├─ 1B: Advisory ✅ COMPLETE (v1 + v2, includes Sales Velocity Model)
  ├─ 1C: Integrations ✅ COMPLETE (v1 + v2 mocks: Zillow, LoopNet, Salesforce, HubSpot)
  └─ 1D: Performance ✅ COMPLETE

Expansion Window 1 ✅ COMPLETE (2025-12-06)
  ├─ 🇭🇰 Hong Kong ✅
  ├─ 🇳🇿 New Zealand ✅
  ├─ 🇺🇸 Seattle/Washington ✅
  └─ 🇨🇦 Toronto/Ontario ✅

Phase 2: Developer Foundation (2A-2C complete, 2D-2I ready to start)
  ├─ 2A: Site Acquisition ✅ COMPLETE
  ├─ 2B: Feasibility Analysis ✅ COMPLETE
  ├─ 2C: Finance Engine ✅ COMPLETE
  ├─ 2D: Land Acquisition Workflow ❌ NOT STARTED ← NEXT
  ├─ 2E: Team Coordination ❌ NOT STARTED
  ├─ 2F: Regulatory Navigation ❌ NOT STARTED
  ├─ 2G: Construction Management ❌ NOT STARTED
  ├─ 2H: Disposal Management ❌ NOT STARTED
  └─ 2I: Portfolio Dashboard ❌ NOT STARTED

Phase 3+: Later phases (depend on Phase 2)
```

**Current focus:** Phase 2D-2I with multi-jurisdiction support built-in.

---

## ✅ JURISDICTION EXPANSION WINDOW 1: COMPLETE (2025-12-06)

### All 4 Jurisdictions Implemented

**Expansion Window 1 is DONE. Phase 2D-2I can now proceed.**

**Completed Jurisdictions:**
1. 🇭🇰 **Hong Kong** ✅ `HongKongProperty`, `hong_kong_compliance.py`, `seed_hong_kong_rules.py`
2. 🇳🇿 **New Zealand** ✅ `NewZealandProperty`, `new_zealand_compliance.py`, `seed_new_zealand_rules.py`
3. 🇺🇸 **Seattle/Washington** ✅ `SeattleProperty`, `seattle_compliance.py`, `seed_seattle_rules.py`
4. 🇨🇦 **Toronto/Ontario** ✅ `TorontoProperty`, `toronto_compliance.py`, `seed_toronto_rules.py`

**Why this was important:**
- Phase 2D-6 features will now be built multi-jurisdiction from start
- No Singapore-only assumptions to refactor later
- All 5 jurisdictions (SG + 4 new) ready for Phase 2D-6 development

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
- [ ] all_steps_to_product_completion.md updated with expansion status
- [ ] Known Testing Issues section (docs/all_steps_to_product_completion.md#-known-testing-issues) updated if new issues found

**Once all checks pass:** Proceed to Phase 2D with multi-jurisdiction support in place.

---

### ✅ Expansion Window 1 Complete - Phase 2D Now Unblocked

**Expansion Window 1 was completed on 2025-12-06.** All 4 jurisdictions (Hong Kong, New Zealand, Seattle, Toronto) have been implemented.

**Phase 2D-2I can now proceed** with multi-jurisdiction support built-in from the start.

---

### Where to Find Detailed Instructions

**For PM:** [`docs/jurisdiction_expansion_playbook.md`](jurisdiction_expansion_playbook.md) — Complete guide with checklists

**For Codex:** [`docs/jurisdiction_expansion_playbook.md`](jurisdiction_expansion_playbook.md) → Section 4 "Codex Workflow"

**For Claude:** [`docs/jurisdiction_expansion_playbook.md`](jurisdiction_expansion_playbook.md) → Section 5 "Claude Workflow"

**For Strategy/Rationale:** [`docs/all_steps_to_product_completion.md`](docs/all_steps_to_product_completion.md) → Section "JURISDICTION EXPANSION WINDOWS"

---

## 🤝 When to Ask the User

### ASK when:
- ✅ Current phase is blocked and ALL phases are blocked
- ✅ Requirements are ambiguous or contradictory
- ✅ You need external credentials/API access
- ✅ Major architectural decision needed
- ✅ Validation results change priorities

### DON'T ASK when:
- ❌ Status is clear in all_steps_to_product_completion.md
- ❌ Test failure is in Known Testing Issues section (docs/all_steps_to_product_completion.md#-known-testing-issues)
- ❌ Coding pattern exists in codebase
- ❌ Answer is in FEATURES.md or CODING_RULES.md

**Be autonomous** - most answers are in the docs.

---

## 🔄 Update Workflow

### When You Complete a Phase:

**1. Update all_steps_to_product_completion.md (Required)**
- Change ❌ NOT STARTED → ✅ COMPLETE
- Add completion date
- Add test status
- List key files delivered

**2. Do NOT Update This File**
- This file is a guide, not a status tracker
- Status lives in all_steps_to_product_completion.md only

**3. Update Known Testing Issues section (docs/all_steps_to_product_completion.md#-known-testing-issues) (If Applicable)**
- Add new issues to "Active Issues"
- Move resolved issues to "Resolved Issues"
- Follow the workflow in that document

---

## 📞 Quick Reference

| Question | Answer |
|----------|--------|
| **"What's the current status?"** | [all_steps_to_product_completion.md](all_steps_to_product_completion.md) — see "📊 Current Progress Snapshot" |
| **"What should I build next?"** | Use decision tree above |
| **"Phase 2C is done - what's next?"** | ✅ Expansion Window 1 complete - proceed to Phase 2D |
| **"How do I add a jurisdiction?"** | [jurisdiction_expansion_playbook.md](jurisdiction_expansion_playbook.md) |
| **"Are there known test issues?"** | [Testing Known Issues](../all_steps_to_product_completion.md#-known-testing-issues) |
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
- [ ] ✅ all_steps_to_product_completion.md updated (status → ✅ COMPLETE)
- [ ] ✅ Commit message describes what was delivered
- [ ] ✅ Known issues documented (if any)

---

## 🚀 Ready to Start?

**Go to:** the "📊 Current Progress Snapshot" section in [all_steps_to_product_completion.md](all_steps_to_product_completion.md)

Find your next task and start building! 💪
