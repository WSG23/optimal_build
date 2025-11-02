# ⚠️ FRONTEND README FOR AI AGENTS

## 🚨 CRITICAL: Production UI Expectations

**ALL frontend UI in Phase 1 and Phase 2 is PRODUCTION-QUALITY B2B SOFTWARE.**

### Critical Facts

1. **This is a B2B platform for commercial real estate professionals**
2. **Users are Agents, Developers, Architects, and Engineers**
3. **UI must be professional, polished, and user-friendly**
4. **Manual QA testing is MANDATORY before marking phases complete** (see CODING_RULES.md Rule 12.1)

### What This Means

```
┌────────────────────────────────────────────────────────┐
│  PRODUCTION-QUALITY UI REQUIREMENTS:                   │
│                                                         │
│  ✅ Professional error handling                        │
│  ✅ User-friendly UX                                   │
│  ✅ Responsive design (desktop focus)                  │
│  ✅ Material-UI consistency                            │
│  ✅ Proper loading states                              │
│  ✅ Form validation                                    │
└────────────────────────────────────────────────────────┘
```

### Purpose of frontend/

**Purpose:** Provide production B2B interfaces for commercial real estate workflows

**Quality bar:** Professional software that users will rely on for their business operations

### What To Do If You See Frontend Errors

**Option A:** Fix bugs and verify with manual testing

**Option B:** Document in TESTING_KNOWN_ISSUES.md if it's a test framework limitation (not app bug)

**Option C:** Ask product owner for UX/design guidance if requirements are unclear

### Before Marking UI Work Complete

**MANDATORY:** Execute manual QA checklist (see `docs/development/testing/phase-*-manual-qa-checklist.md`)

Rule 12.1 in CODING_RULES.md enforces this requirement.

---

## File List

Production UI components and infrastructure:

- `src/pages/*.tsx` - Production UI pages for B2B workflows
- `src/api/*.ts` - API client wrappers
- `src/components/*.tsx` - Reusable UI components
- `src/hooks/*.ts` - React hooks
- `src/i18n/*.json` - Internationalization (English/Japanese)
- `*.css` - Production styling

**All code should meet production quality standards.**

---

## Remember

**Both backend and frontend work have business value.**

All UI must be professional, polished, and user-friendly for B2B users (see CODING_RULES.md Rule 12.2).
