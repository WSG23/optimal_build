# ⚠️ FRONTEND README FOR AI AGENTS

## 🚨 STOP - Read This Before Touching Any Frontend Code

**ALL files in `frontend/` are TEMPORARY TEST HARNESSES.**

### Critical Facts

1. **These UIs were created by AI agents (Claude/Codex) for manual testing**
2. **Product owner was NOT involved in any UI design decisions**
3. **These are NOT production interfaces for customers**
4. **These WILL be replaced when actual product UI design happens**

### What This Means

```
┌────────────────────────────────────────────────────────┐
│  DO NOT POLISH ANYTHING IN frontend/                  │
│                                                         │
│  - No offline fallback logic                           │
│  - No professional error handling                      │
│  - No UX improvements                                  │
│  - No accessibility work                               │
│  - No responsive design                                │
│  - No performance optimizations                        │
└────────────────────────────────────────────────────────┘
```

### Purpose of frontend/

**Only purpose:** Let product owner manually test that backend APIs work

**That's it. Nothing more.**

### What To Do If You See Frontend Errors

**Option A (Preferred):** Document in TESTING_KNOWN_ISSUES.md and move on

**Option B:** Ask product owner if they want minimal fix

**Option C (NEVER):** Apply professional tool standards, add offline modes, implement graceful degradation

### Before ANY Frontend Work

**Read [ui-status.md](../docs/planning/ui-status.md) at repository root.**

That document explains in detail why polishing test UI wastes time.

---

## File List

All files in this directory are temporary test harnesses:

- `src/pages/*.tsx` - Test pages for manual API verification
- `src/api/*.ts` - API client wrappers (may be reused)
- `src/components/*.tsx` - UI components (temporary)
- `src/hooks/*.ts` - React hooks (may be reused)
- `src/i18n/*.json` - Translations (temporary)
- `*.css` - Styling (temporary)

**Only `src/api/*.ts` and `src/hooks/*.ts` might survive to production. Everything else is throwaway code.**

---

## Remember

**Backend work has business value. Test UI polish does not.**

Focus on Phase 1D backend work (see [docs/ROADMAP.MD](../docs/ROADMAP.MD) and task priority in [docs/WORK_QUEUE.MD](../docs/WORK_QUEUE.MD)).
