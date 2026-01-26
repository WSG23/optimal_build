# Optimal Build - Shared AI Instructions

> **Single source of truth** for all AI assistants (Claude, Gemini, Codex)
>
> Last Updated: 2026-01-26

This document contains the core instructions that apply to ALL AI assistants working on this codebase. AI-specific entry points (CLAUDE.md, MCP.md) should reference this file.

---

## 1. Critical Rules (Build Will FAIL)

### Rule 1: Database Migrations - NEVER EDIT EXISTING FILES

```bash
# CORRECT - Create new migration
cd backend && alembic revision -m "add_column"

# WRONG - Never edit files in backend/migrations/versions/
```

- Use `sa.String()` for ENUM columns, NOT `sa.Enum()`
- Match Python enum VALUES exactly in SQL

### Rule 2: Async/Await - ALL Database Operations

```python
# CORRECT
async def get_item(db: AsyncSession, id: int):
    result = await db.execute(select(Item).where(Item.id == id))
    return result.scalar_one_or_none()

# WRONG - Missing async/await
def get_item(db: Session, id: int):
    return db.query(Item).filter(Item.id == id).first()
```

### Rule 3: Before Committing - MUST RUN

```bash
make format   # Auto-fix formatting
make verify   # MUST PASS before commit
```

### Rule 4: Frontend UI - Use Design Tokens

```tsx
// CORRECT
<Box sx={{ p: 'var(--ob-space-100)', borderRadius: 'var(--ob-radius-sm)' }}>

// WRONG
<Box sx={{ p: '16px', borderRadius: '12px' }}>
```

### Rule 5: Testing - Always Provide Commands

After completing ANY feature, provide:

```bash
pytest backend/tests/test_api/test_[feature].py -v
```

---

## 2. Tech Stack

### Backend

- **Python 3.12+** with FastAPI, Pydantic v2, SQLAlchemy (async), Alembic
- **PostgreSQL** database with PostGIS for geospatial
- **Testing:** Pytest with `@pytest.mark.unit`, `@pytest.mark.integration`
- **Formatting:** Black (88 chars), Ruff for linting
- **Type checking:** mypy (run `make typecheck-backend`)

### Frontend

- **TypeScript 5+** with strict mode
- **React 18+** with Vite, MUI
- **Testing:** Vitest for unit tests
- **Formatting:** Prettier, ESLint
- **Type checking:** Must be 0 errors (`npm run lint`)

---

## 3. Design System (Square Cyber-Minimalism)

### Color Tokens

Use semantic tokens, never hardcoded colors:

| Token                | Usage                    |
| -------------------- | ------------------------ |
| `--ob-color-primary` | Brand identity, key CTAs |
| `--ob-color-surface` | Card backgrounds         |
| `--ob-color-text`    | Primary text             |
| `--ob-color-muted`   | Secondary text           |

### Border Radius Standards

| Element        | Token            | Value |
| -------------- | ---------------- | ----- |
| Buttons        | `--ob-radius-xs` | 2px   |
| Cards/Panels   | `--ob-radius-sm` | 4px   |
| Modals/Dialogs | `--ob-radius-lg` | 8px   |

### Spacing

Use spacing tokens, never hardcoded pixels:

- `--ob-space-100` (4px)
- `--ob-space-200` (8px)
- `--ob-space-300` (12px)
- `--ob-space-400` (16px)

---

## 4. Test-First Development (RECOMMENDED)

### Workflow

1. **CREATE TEST FILE FIRST**

   - Backend: `tests/test_api/test_[feature].py` or `tests/test_services/test_[feature].py`
   - Frontend: Colocated `__tests__/*.test.tsx` files

2. **WRITE TEST CASES** covering:

   - Happy path (valid inputs -> expected outputs)
   - Error cases (401, 403, 404, 422)
   - Edge cases (empty, null, boundary values)

3. **RUN TESTS** - they should FAIL initially

   ```bash
   pytest backend/tests/test_api/test_[feature].py -v
   ```

4. **ONLY THEN** write implementation code

5. **RUN TESTS AGAIN** - they should PASS

### Coverage Requirements

- Backend critical paths: **>80%**
- Backend overall: **>70%**
- Frontend critical paths: **Covered**

---

## 5. Quick Start Commands

```bash
# Pre-flight checks
make ai-preflight           # Run before starting work

# Development
make dev                    # Start backend + frontend
make format                 # Auto-format code
make verify                 # Run all quality checks

# Testing
make test                   # Run backend tests
pytest backend/tests/ -v    # Verbose test output

# Type checking
make typecheck-backend      # Backend type checking
cd frontend && npm run lint # Frontend linting
```

---

## 6. Key File Locations

| Purpose           | Location                                  |
| ----------------- | ----------------------------------------- |
| Technical rules   | `CODING_RULES.md`                         |
| Current roadmap   | `docs/all_steps_to_product_completion.md` |
| Next priorities   | `docs/ai-agents/next_steps.md`            |
| UI standards      | `frontend/UI_STANDARDS.md`                |
| UX architecture   | `frontend/UX_ARCHITECTURE.md`             |
| Rules reference   | `docs/mcp/MCP_RULES.md`                   |
| Security/perf     | `docs/mcp/MCP_GUARDRAILS.md`              |
| Persona playbooks | `docs/ai-agents/`                         |

---

## 7. AI-Specific Code Generation Rules

### [OB-AI-001] Read Before Writing

- NEVER propose changes to code you haven't read
- Use the Read tool first to understand existing patterns

### [OB-AI-002] Verify Changes Immediately

After editing, run:

```bash
make format   # Auto-format
make verify   # Check all rules
```

### [OB-AI-003] Use Checkpoint Protocol

Before large changes (>3 files, architectural), ask:

```markdown
I've identified N files that need updates for [FEATURE].

**Scope:**

- [List of changes]

**Should I proceed?**
```

### [OB-AI-004] Format-Stage-Commit Workflow

```bash
make format                 # Format all files
git add [specific files]    # Stage changes
make hooks                  # Run pre-commit
git commit -m "message"     # Commit
```

### [OB-AI-005] Pre-commit Rejections Are Intentional

- Never say "the linter reverted my changes"
- Pre-commit **REJECTS** (commit fails) or **MODIFIES** (auto-format)
- Read the error message and fix the underlying issue

---

## 8. Handoff Protocol

When switching between personas or completing a task, provide:

```markdown
**Handoff Packet**

- From -> To persona(s): [e.g., Architect -> QA Engineer]
- Context & scope: [What was being worked on]
- Decisions made: [Key choices with rationale]
- Risks / blockers: [Known issues]
- Test status: [What's passing/failing]
- Next steps: [Recommended follow-up actions]
```

---

## 9. Conflict Resolution Hierarchy

When personas disagree, priority order:

1. **Security & Compliance** (highest)
2. **Quality & Testing**
3. **Reliability & Availability**
4. **Performance & Scalability**
5. **User Value & UX**
6. **Cost Optimization**
7. **Speed of Delivery** (lowest)

---

## 10. Related Documentation

- **Full Rules:** [docs/mcp/MCP_RULES.md](../mcp/MCP_RULES.md)
- **Guardrails:** [docs/mcp/MCP_GUARDRAILS.md](../mcp/MCP_GUARDRAILS.md)
- **Persona Index:** [docs/ai-agents/README.md](../ai-agents/README.md)
- **Claude-Specific:** [CLAUDE.md](../../CLAUDE.md)
- **MCP (Gemini):** [MCP.md](../../MCP.md)

---

**Document Version:** 1.0
**Synced from:** CLAUDE.md, MCP.md (2026-01-26)
