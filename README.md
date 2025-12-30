# Optimal Build

Commercial real estate development platform for Singapore (primary) + HK, NZ, Seattle, Toronto.

## AI Agents - READ THIS FIRST

**Your rules are in `.cursorrules`** - this file is auto-loaded by most AI tools.

If your tool doesn't auto-load it, read these in order:
1. `.cursorrules` - Critical rules (embedded, not pointers)
2. `docs/ai-agents/next_steps.md` - What to build next
3. `docs/all_steps_to_product_completion.md` - Project status

**Do NOT start coding until you know what task you're working on.**

---

## Quick Start (Humans)

```bash
# Install git hooks
./scripts/install-git-hooks.sh

# Start development
make dev

# Before committing
make format && make verify
```

## Tech Stack

- **Backend:** Python 3.13, FastAPI, PostgreSQL, SQLAlchemy (async)
- **Frontend:** React, TypeScript, MUI
- **Key constraint:** All DB operations must be async/await

## Key Directories

```
backend/app/api/v1/   # API endpoints
backend/app/models/   # Database models
backend/migrations/   # Alembic (NEVER edit existing files)
frontend/src/         # React app
docs/                 # Planning & status docs
```
