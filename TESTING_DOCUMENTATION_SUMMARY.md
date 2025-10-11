# Testing Documentation Summary

This file explains the testing documentation system for both humans and AI agents.

## Key Documents

### 1. [TESTING_KNOWN_ISSUES.md](TESTING_KNOWN_ISSUES.md)
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

## Workflows

### Adding a New Known Issue

#### AI Agent discovers issue:
1. 🤖 AI explains issue and proposes documenting it
2. 👤 **Human decides**: "Document it" / "No, fix it" / "Document until Phase X"
3. 🤖 AI adds to TESTING_KNOWN_ISSUES.md
4. 🤖 AI adds code comments pointing to documentation
5. 📝 AI notes "Documented by [name] on [date]"

#### Human discovers issue:
1. Add to TESTING_KNOWN_ISSUES.md "Active Issues" section
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
2. Follow maintenance checklist in TESTING_KNOWN_ISSUES.md
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
AI: "Tests failing. Checking TESTING_KNOWN_ISSUES.md..."
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

See [TESTING_KNOWN_ISSUES.md](TESTING_KNOWN_ISSUES.md) for full details.
