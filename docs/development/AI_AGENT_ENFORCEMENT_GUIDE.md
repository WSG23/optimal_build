# AI Agent Enforcement Guide for Solo Founders

**Created:** 2025-11-02
**Purpose:** Automated enforcement mechanisms to ensure AI agents complete documentation workflows without human oversight

---

## Problem Statement

As a solo founder with AI agents building your product, you face a critical challenge:

**You cannot remember every documentation step, and AI agents may skip cleanup tasks.**

### Real Example: Phase 1D Manual QA (Nov 2025)

- **Nov 1:** Phase 1D marked `✅ COMPLETE` in [all_steps_to_product_completion.md](../all_steps_to_product_completion.md)
- **Nov 2:** Manual QA checklist executed (4/12 tests passed)
- **Nov 2:** Work moved to next phase (Phase 2B)
- **Problem:** Checklist status never updated from `READY FOR QA` to `COMPLETED`
- **Root cause:** No automated enforcement to verify completion workflow

---

## Solution: Multi-Layer Enforcement

### Layer 1: Pre-Commit Hooks (Automated)

**File:** `.pre-commit-config.yaml`
**Hook:** `phase-gate` (line 24-28)
**Script:** `scripts/check_coding_rules.py`

**What it checks:**

1. ✅ Manual QA checklist file exists for all COMPLETE phases
2. ✅ Checklist has execution summary (Tester, Date, Result filled)
3. ✅ **NEW:** Checklist status is NOT "READY FOR QA" when phase is COMPLETE
4. ✅ **NEW:** "Next Steps" section has at least one checkbox checked

**When it runs:** Every `git commit`

**Example output when violated:**
```
RULE VIOLATION: Phase 1D marked '✅ COMPLETE' but QA checklist status incomplete.
  -> Current status: '✅ READY FOR QA'
  -> Must be: '✅ QA COMPLETE (YYYY-MM-DD)' or '✅ ARCHIVED (YYYY-MM-DD)'
  -> Rule 12.4: Complete the QA checklist workflow
  -> Update phase-1d-manual-qa-checklist.md status header (line ~5)
  -> See CODING_RULES.md section 12.4
```

### Layer 2: CODING_RULES.md Instructions (AI Agent Guidance)

**File:** `CODING_RULES.md` Section 12.4
**Audience:** AI Agents (read during task planning)

**Mandatory workflow steps:**

1. Before starting QA: Checklist status = `✅ READY FOR QA`
2. During QA: Update test results (Pass/Fail/Not Run)
3. **After QA execution (CRITICAL - AI agents often skip this):**
   - a. Update checklist status header to `✅ QA COMPLETE (YYYY-MM-DD)`
   - b. Complete "Next Steps" section (check relevant boxes)
   - c. Update [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) (move to Completed section)
   - d. Update [all_steps_to_product_completion.md](../all_steps_to_product_completion.md) (verify phase marked COMPLETE)
   - e. Git commit with message referencing QA completion

**Why this works:**
- AI agents read CODING_RULES.md at the start of every task
- Explicit step-by-step instructions reduce ambiguity
- "MANDATORY" and "CRITICAL" keywords trigger agent attention

### Layer 3: Work Queue Checklist (Task Tracking)

**File:** `docs/all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work`
**Section:** "Operating Instructions for AI Agents" (lines 77-86)

**Instructions for AI agents:**

- After completing work, move item to "Completed" section with completion date
- Update [all_steps_to_product_completion.md](../all_steps_to_product_completion.md) only when phase status changes (e.g., READY → COMPLETE)
- For UI phases, execute manual UI walkthrough and include results before review

---

## How to Use This System (For Solo Founders)

### Step 1: Trust the Pre-Commit Hooks

You don't need to remember the steps. Just:

```bash
git add .
git commit -m "your message"
```

If the agent skipped a step, the commit will **FAIL** with a clear error message.

### Step 2: Point AI Agents to the Error

When a commit fails, copy the error message and tell the AI agent:

```
The commit failed with this error:
[paste error message]

Please fix the violations according to CODING_RULES.md section 12.4
```

### Step 3: Verify Fix

After the agent fixes the issues:

```bash
git add .
git commit -m "docs: complete Phase 1D manual QA checklist"
```

If it passes, you're done!

---

## Testing the Enforcement

To manually test if enforcement is working:

```bash
# Run the coding rules checker
python3 scripts/check_coding_rules.py

# Look for Rule 12.4 violations
python3 scripts/check_coding_rules.py 2>&1 | grep -A 5 "Phase.*COMPLETE"
```

**Expected output if Phase 1D checklist incomplete:**
```
RULE VIOLATION: Phase 1D marked '✅ COMPLETE' but QA checklist status incomplete.
  -> Current status: '✅ READY FOR QA'
  -> Must be: '✅ QA COMPLETE (YYYY-MM-DD)' or '✅ ARCHIVED (YYYY-MM-DD)'
```

---

## What Gets Blocked

### ❌ Blocked: Incomplete QA Checklist Status

**Scenario:** Phase marked COMPLETE, but checklist status still says "READY FOR QA"

**Fix:** Update checklist status header:
```markdown
**Status:** ✅ QA COMPLETE (2025-11-02)
```

### ❌ Blocked: Empty "Next Steps" Section

**Scenario:** Phase marked COMPLETE, but no checkboxes checked in "Next Steps"

**Fix:** Check at least one box in the "Next Steps" section:
```markdown
## 📝 Next Steps

**If PASS:**
- [x] Update [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) - mark Phase 1D as QA complete
- [x] Update [all_steps_to_product_completion.md](../all_steps_to_product_completion.md) Phase 1D gate checkbox
- [x] Archive this checklist with completion date
```

### ❌ Blocked: Missing Execution Summary

**Scenario:** Phase marked COMPLETE, but QA checklist has template placeholders

**Fix:** Fill in execution summary:
```markdown
**Tester:** Codex (with user walkthrough)
**Date:** 2025-11-02
**Overall Result:** [x] PARTIAL
```

---

## Enforcement Levels

| Level | What | How | When |
|-------|------|-----|------|
| **MUST** | QA checklist exists | Pre-commit hook | Every commit |
| **MUST** | Execution summary filled | Pre-commit hook | Every commit |
| **MUST** | Status not "READY FOR QA" | Pre-commit hook | Every commit |
| **MUST** | Next Steps addressed | Pre-commit hook | Every commit |
| **SHOULD** | Follow step-by-step workflow | CODING_RULES.md guidance | AI agent reads at task start |
| **SHOULD** | Update [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) | [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) instructions | AI agent reads during phase work |

---

## Benefits for Solo Founders

✅ **No mental overhead:** You don't need to remember to ask "did you update the checklist?"

✅ **Fail fast:** Problems are caught at commit time, not weeks later

✅ **Self-documenting:** Error messages tell AI agents exactly what to fix

✅ **Audit trail:** Git history shows when QA was completed

✅ **Consistency:** Same workflow for every phase (1A, 1B, 1C, 1D, 2B, 2C)

✅ **Scalable:** Works whether you have 1 AI agent or 10

---

## Troubleshooting

### Pre-commit hook not running?

```bash
# Install/reinstall hooks
pre-commit install

# Test manually
pre-commit run phase-gate --all-files
```

### Want to bypass enforcement temporarily?

```bash
# Skip pre-commit hooks (NOT RECOMMENDED)
SKIP=phase-gate git commit -m "message"

# Or skip all hooks
git commit --no-verify -m "message"
```

**Warning:** Only use this for emergencies. Fix violations properly instead.

### False positive?

If the enforcement script has a bug, you can add an exception:

**File:** `.coding-rules-exceptions.yml`

```yaml
exceptions:
  rule_12_manual_qa:
    - "docs/development/testing/phase-1d-manual-qa-checklist.md"  # Reason: [explain why]
```

---

## Future Enhancements

Potential improvements for this enforcement system:

1. **Auto-fix mode:** Script that automatically updates checklist status
2. **Slack notifications:** Alert when QA checklist is executed
3. **Dashboard:** Visual status of all phase checklists
4. **AI agent reminder:** Bot that comments on PRs with incomplete checklists

---

## Related Documentation

- [CODING_RULES.md Section 12.4](../../CODING_RULES.md#124-qa-checklist-completion-workflow-mandatory---ai-agents-read-this) - Mandatory workflow steps
- [check_coding_rules.py](../../scripts/check_coding_rules.py) - Enforcement script
- [.pre-commit-config.yaml](../../.pre-commit-config.yaml) - Pre-commit hook configuration
- [Phase 1D Manual QA Checklist](testing/phase-1d-manual-qa-checklist.md) - Example checklist

---

**Last Updated:** 2025-11-02
**Maintained by:** Codex + Solo Founder
**Status:** ✅ ACTIVE ENFORCEMENT
