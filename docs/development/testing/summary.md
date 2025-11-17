# Testing Documentation Summary

This file explains the testing documentation system for both humans and AI agents.

## Key Documents

### 1. [Testing Known Issues](../../all_steps_to_product_completion.md#-known-testing-issues)
Tracks test harness issues that are **not bugs** in the application code.

**Purpose:**
- Prevents wasted time investigating non-issues
- **Critical for AI agents** who have no memory between sessions
- Provides institutional knowledge

**When to use:**
- Test fails but feature works correctly
- Known limitation of test environment (JSDOM, SQLite, etc.)
- Timing/race condition in test harness

**When NOT to use:**
- Actual bugs in application code
- Tests that fail because feature is broken
- Temporary failures that need fixing

---

### 2. [Phase 2B Manual UI QA Checklist](../archive/phase2b/PHASE2B_VISUALISATION_STUB_archived_2025-11-12.md#10-manual-ui-qa-checklist-preview-payload-builder)
Defines the required manual walkthrough for the developer preview harness before closing Phase 2B renderer tasks.

**Purpose:**
- Ensures agents actually launch the preview UI and validate the structured payload after backend changes.
- Captures screenshots/logs for audit so regressions are visible to the product owner.
- Restores parity with Phase 1D, where manual UI QA was already mandated.

**When to use:**
- Any change that touches `backend/app/services/preview_generator.py`, renderer orchestration, or frontend preview consumption.
- Before marking a Phase 2B work queue item complete or requesting PR review.

**When NOT to use:**
- Non-visual backend refactors that do not impact preview payloads (document rationale in the PR if skipping).
- Infrastructure audit tasks unrelated to renderer output.

---

## Workflows

### Adding a New Known Issue

#### AI Agent discovers issue:
1. 🤖 AI explains issue and proposes documenting it
2. 👤 **Human decides**: "Document it" / "No, fix it" / "Document until Phase X"
3. 🤖 AI adds to `../../all_steps_to_product_completion.md#-known-testing-issues`
4. 🤖 AI adds code comments pointing to documentation
5. 📝 AI notes "Documented by [name] on [date]"

#### Human discovers issue:
1. Add to `../../all_steps_to_product_completion.md#-known-testing-issues` "Active Issues" section
2. Add code comments in affected files
3. Note discovery date
4. OR ask AI agent to document it for you

---

### Resolving a Known Issue

#### AI Agent fixes issue:
1. 🤖 AI fixes the issue and verifies tests pass
2. 🤖 AI proposes documentation updates:
   - Move from "Active Issues" to "Resolved Issues"
   - Add resolution details (date, who, how)
   - Remove/update code comments
   - Remove test workarounds
3. 👤 **Human reviews**: "Approved" / "Modify" / "Not actually fixed"
4. 🤖 AI updates all documentation

#### Human fixes issue:
1. Fix the issue, verify tests pass
2. Follow maintenance checklist in `../../all_steps_to_product_completion.md#-known-testing-issues`
3. OR ask AI agent to update documentation for you

---

## Why This Matters

### For Human Developers
- ✅ Clear guidance on what's a bug vs test limitation
- ✅ Saves debugging time
- ✅ Institutional knowledge preserved

### For AI Agents (Claude, Codex)
- ✅ **Critical** - AI has no memory between sessions
- ✅ Prevents investigating same issue repeatedly
- ✅ Prevents "fixing" working code
- ✅ Provides accurate status reports to users

---

## Example Scenario

**Without documentation:**
```
User: "Run tests"
AI: "Tests failing, investigating..."
AI: *spends 20 minutes debugging*
AI: "I think I found the bug, let me fix it..."
AI: *changes working code*
```

**With documentation:**
```
User: "Run tests"
AI: "Tests failing. Checking ../../all_steps_to_product_completion.md#-known-testing-issues..."
AI: "This is documented as known test harness timing issue.
     HTML dump shows page renders correctly. Feature works.
     Backend tests pass. Status: ✅ Feature complete, ⚠️ Test harness issue."
```

---

## Current Known Issues

As of 2025-10-11:

1. **Frontend: React Testing Library Async Timing**
   - Affects: Phase 1B, Phase 1C
   - Status: Known limitation, feature works correctly
   - Workaround: Verify HTML dump and manual testing

2. **SQLite vs PostgreSQL SQL Compatibility**
   - Affects: Backend tests with raw SQL
   - Status: Fixed in Phase 1C
   - Solution: Use SQLite-compatible syntax in tests

See [../../all_steps_to_product_completion.md#-known-testing-issues](../../all_steps_to_product_completion.md#-known-testing-issues) for full details.
