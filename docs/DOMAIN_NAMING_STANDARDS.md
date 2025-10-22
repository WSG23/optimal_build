# Domain Naming Standards

**Last Updated:** 2025-10-22
**Status:** Living Document

This document defines naming conventions for optimal_build to reduce confusion and improve code maintainability.

---

## Table of Contents

1. [Current State](#current-state)
2. [Recommended Standards](#recommended-standards)
3. [Migration Strategy](#migration-strategy)
4. [Decision Tree](#decision-tree)
5. [Examples](#examples)

---

## Current State

### Problem: Inconsistent Naming

The codebase exhibits **three types of inconsistency**:

#### 1. Plural vs Singular Models

**Plural (21 files):**
- `users.py`, `projects.py`, `ai_agents.py`, `rulesets.py`
- `entitlements.py`, `imports.py`
- `business_performance.py`, `developer_checklists.py`, `developer_condition.py`
- `listing_integration.py`

**Singular (10 files):**
- `property.py`, `market.py`, `finance.py`, `audit.py`, `overlay.py`
- `singapore_property.py`
- `rkp.py`, `types.py`, `base.py`
- `agent_advisory.py`

#### 2. `_api` Suffix Usage

**With `_api` suffix (2 files):**
- `backend/app/api/v1/projects_api.py`
- `backend/app/api/v1/singapore_property_api.py`

**Without `_api` suffix (27 files):**
- `finance.py`, `entitlements.py`, `audit.py`, `export.py`, `overlay.py`
- `market_intelligence.py`, `agents.py`, `deals.py`, `performance.py`
- All other routers

#### 3. Dual User Endpoints

**Three separate user routers:**
- `users_secure.py` - Login/signup with JWT
- `users_db.py` - Database-backed user CRUD
- `test_users.py` - Simple in-memory test API

**Confusing for developers:**
- Which endpoint should I use?
- Why three separate files?
- What's the difference between secure and db?

---

### Impact of Inconsistency

| Issue | Impact | Severity |
|-------|--------|----------|
| Plural vs singular | Developer confusion, unclear conventions | **Medium** |
| `_api` suffix | Redundant naming (already in `api/v1/`) | **Low** |
| User endpoint split | Security confusion, API fragmentation | **High** |

**Developer Experience:**
- "Should I name my new model `transactions.py` or `transaction.py`?"
- "Do I need `_api` suffix for my router?"
- "Which user endpoint should I integrate with?"

---

## Recommended Standards

### Standard 1: Plural for Collections, Singular for Singletons

**Rule:** Use plural when the domain represents **multiple records**, singular for **singleton/config domains**.

| Pattern | Use Plural | Use Singular |
|---------|-----------|--------------|
| Database tables with multiple rows | ✅ users, projects, properties | ❌ |
| Collections of entities | ✅ entitlements, imports, agents | ❌ |
| Singleton configuration | ❌ | ✅ compliance, finance |
| Utility modules | ❌ | ✅ audit, overlay, base |
| Domain with 1 record per context | ❌ | ✅ market (per location) |

**Examples:**

✅ **Correct:**
```
models/users.py          # Multiple user records
models/projects.py       # Multiple projects
models/properties.py     # Multiple properties
models/finance.py        # Singleton finance config
models/audit.py          # Utility module
```

❌ **Incorrect:**
```
models/user.py           # Implies single user
models/project.py        # Implies single project
models/finances.py       # Finance is not a collection
```

---

### Standard 2: No `_api` Suffix for Routers

**Rule:** Remove `_api` suffix from all router files in `backend/app/api/v1/`.

**Rationale:**
- Files are already in `api/v1/` directory (context is obvious)
- Suffix is redundant and adds noise
- No other routers use this pattern (inconsistent)

**Current State:**
```
backend/app/api/v1/
├── projects_api.py          ❌ Redundant suffix
├── singapore_property_api.py ❌ Redundant suffix
├── finance.py               ✅ Clean name
├── entitlements.py          ✅ Clean name
└── market_intelligence.py    ✅ Clean name
```

**Target State:**
```
backend/app/api/v1/
├── projects.py              ✅ Clean
├── singapore_property.py    ✅ Clean
├── finance.py               ✅ Clean
├── entitlements.py          ✅ Clean
└── market_intelligence.py    ✅ Clean
```

---

### Standard 3: Consolidate User Endpoints

**Rule:** Single `/auth` router for authentication, single `/users` router for user management.

**Current (Fragmented):**
```
api/v1/users_secure.py    # Login, signup (JWT)
api/v1/users_db.py        # User CRUD (database)
api/v1/test_users.py      # Test endpoint (in-memory)
```

**Target (Consolidated):**
```
api/v1/auth.py            # Login, signup, refresh tokens
api/v1/users.py           # User profile, settings, CRUD
```

**Rationale:**
- Clear separation: authentication (`/auth`) vs user management (`/users`)
- Matches industry conventions (GitHub, Stripe, Auth0 all use `/auth`)
- Easier to secure (single entrypoint for auth)
- Remove test endpoints from production code

---

## Migration Strategy

### 6-Phase Gradual Migration

**Goal:** Zero breaking changes, backward compatibility during transition

#### Phase 1: Document Standards (Complete)
- ✅ Create `DOMAIN_NAMING_STANDARDS.md` (this file)
- ✅ Update `CODING_RULES.md` to reference this document
- ✅ Add to AI agent onboarding checklist

**Timeline:** 1 day (complete)

---

#### Phase 2: Lead by Example (1-2 sprints)

**For all new modules, follow the standard:**

✅ **New Models:**
```python
# ✅ Correct
backend/app/models/transactions.py      # Plural
backend/app/models/compliance.py        # Singular (singleton)

# ❌ Wrong (violates standard)
backend/app/models/transaction.py       # Should be plural
backend/app/models/compliances.py       # Should be singular
```

✅ **New Routers:**
```python
# ✅ Correct
backend/app/api/v1/transactions.py      # No _api suffix
backend/app/api/v1/compliance.py        # No _api suffix

# ❌ Wrong (violates standard)
backend/app/api/v1/transactions_api.py  # Redundant suffix
```

**Enforcement:** Code review checklist + pre-commit hook

**Timeline:** Ongoing (start immediately)

---

#### Phase 3: Deprecation Warnings (Sprint after Phase 2)

**Add deprecation notices to old modules:**

```python
# backend/app/api/v1/projects_api.py
"""
DEPRECATED: Use projects.py instead.

This module will be removed in v2.0.0.
All functionality has been moved to api/v1/projects.py
"""

import warnings
warnings.warn(
    "projects_api is deprecated, use projects instead",
    DeprecationWarning,
    stacklevel=2
)

# Import from new location
from .projects import router  # noqa
```

**Update Docs:**
- Add deprecation badges to API documentation
- Update `architecture_honest.md` with migration timeline
- Email notification to integrators (if external API users exist)

**Timeline:** 1 week

---

#### Phase 4: Create Aliases (Concurrent with Phase 3)

**Create new files that import from old ones:**

```python
# backend/app/api/v1/projects.py (new file)
"""Projects API endpoints."""

from .projects_api import router

__all__ = ["router"]
```

```python
# backend/app/models/properties.py (new file)
"""Property models - replaces property.py."""

from .property import *  # noqa

__all__ = [...] # Import all from property.py
```

**Both old and new imports work:**
```python
# Old (deprecated, still works)
from app.api.v1.projects_api import router

# New (recommended)
from app.api.v1.projects import router
```

**Timeline:** 1-2 days

---

#### Phase 5: Update Internal References (1-2 sprints)

**Update all imports in codebase:**

```bash
# Find all imports of deprecated modules
grep -r "from.*projects_api" backend/
grep -r "import.*projects_api" backend/

# Update to new names
sed -i 's/projects_api/projects/g' backend/**/*.py
```

**Test thoroughly:**
```bash
# Run full test suite
pytest backend/tests/ -v

# Check for regressions
make verify
```

**Rollback plan:** Git revert if issues found

**Timeline:** 2-3 weeks (gradual updates)

---

#### Phase 6: Remove Old Modules (Major version bump)

**After 6+ months with deprecation warnings:**

```bash
# Remove deprecated files
rm backend/app/api/v1/projects_api.py
rm backend/app/api/v1/singapore_property_api.py
rm backend/app/api/v1/users_secure.py
rm backend/app/api/v1/users_db.py
rm backend/app/api/v1/test_users.py

# Update __init__.py router registration
# Remove deprecation warnings from docs
```

**Version:** v2.0.0 (breaking change)

**Communication:**
- Changelog with upgrade guide
- Migration script if needed
- 3-month advance notice to integrators

**Timeline:** After 6 months of Phase 5

---

## Decision Tree

### For New Models: Plural or Singular?

```
Does this model represent multiple database records?
├─ YES → Use PLURAL (users.py, projects.py, transactions.py)
└─ NO → Is it a singleton or config domain?
    ├─ YES → Use SINGULAR (compliance.py, finance.py, audit.py)
    └─ NO → Is it a utility module?
        ├─ YES → Use SINGULAR (base.py, types.py, utils.py)
        └─ UNSURE → Default to PLURAL (safer choice)
```

### For New API Routers: Add `_api` Suffix?

```
Am I creating a router in backend/app/api/v1/?
├─ YES → NO SUFFIX (projects.py, not projects_api.py)
└─ NO → Are you sure it's not an API router?
    ├─ CONFIRMED → Use descriptive name (auth_utils.py)
    └─ ACTUALLY IT IS → NO SUFFIX (move to api/v1/)
```

### For Authentication Endpoints: Where Should It Go?

```
Is this endpoint for login/signup/token management?
├─ YES → Put in api/v1/auth.py
└─ NO → Is it for user profile/settings/CRUD?
    ├─ YES → Put in api/v1/users.py
    └─ NO → Is it for role/permission management?
        ├─ YES → Put in api/v1/auth.py (or api/v1/permissions.py)
        └─ UNSURE → Ask in code review
```

---

## Examples

### Example 1: Adding Transaction History Feature

**❌ Old Way (Inconsistent):**
```python
# Model
backend/app/models/transaction.py  # Wrong: should be plural

# Schema
backend/app/schemas/transaction.py

# Router
backend/app/api/v1/transactions_api.py  # Wrong: redundant _api suffix
```

**✅ New Way (Following Standards):**
```python
# Model
backend/app/models/transactions.py  # Correct: plural for collection

# Schema
backend/app/schemas/transaction.py  # Singular is OK for schemas (Pydantic models)

# Router
backend/app/api/v1/transactions.py  # Correct: no _api suffix
```

---

### Example 2: Adding Compliance Module

**❌ Old Way:**
```python
# Wrong: compliance is singleton, should be singular
backend/app/models/compliances.py

# Router
backend/app/api/v1/compliance_api.py  # Wrong: redundant suffix
```

**✅ New Way:**
```python
# Correct: singular for singleton
backend/app/models/compliance.py

# Router
backend/app/api/v1/compliance.py  # Correct: no suffix
```

---

### Example 3: Refactoring User Endpoints

**❌ Current (Fragmented):**
```python
# Three separate routers
api/v1/users_secure.py → /api/v1/secure-users/signup
api/v1/users_db.py     → /api/v1/db-users/123
api/v1/test_users.py   → /api/v1/test-users
```

**✅ Target (Consolidated):**
```python
# Two clear routers
api/v1/auth.py  → /api/v1/auth/signup
                  /api/v1/auth/login
                  /api/v1/auth/refresh

api/v1/users.py → /api/v1/users/me
                  /api/v1/users/123
                  /api/v1/users/123/profile
```

---

## Enforcement

### Pre-commit Hook

```python
# .pre-commit-config.yaml (add this check)
- repo: local
  hooks:
    - id: check-naming-standards
      name: Check domain naming standards
      entry: python scripts/check_naming_standards.py
      language: python
      files: ^backend/app/(models|api/v1)/.*\.py$
```

```python
# scripts/check_naming_standards.py
import sys
from pathlib import Path

VIOLATIONS = []

for file in Path("backend/app/api/v1").glob("*.py"):
    if "_api.py" in file.name and file.name != "__init__.py":
        VIOLATIONS.append(f"❌ {file}: Remove _api suffix")

if VIOLATIONS:
    print("\n".join(VIOLATIONS))
    print("\nSee docs/DOMAIN_NAMING_STANDARDS.md for standards")
    sys.exit(1)
```

### Code Review Checklist

**For all new modules, reviewers must check:**

- [ ] Model name follows plural/singular standard
- [ ] Router name has no `_api` suffix
- [ ] Auth endpoints in `auth.py` (not `users_secure.py`)
- [ ] User management in `users.py` (not `users_db.py`)
- [ ] Matches examples in `DOMAIN_NAMING_STANDARDS.md`

---

## Exceptions

### When to Break the Rules

**Rare cases where exceptions are acceptable:**

1. **Third-party library conventions**
   - Example: `alembic/env.py` (required by Alembic)
   - Example: `__init__.py` (Python convention)

2. **Industry-standard terminology**
   - Example: `models/rkp.py` (RKP is acronym, not plural/singular)
   - Example: `models/types.py` (Python convention for type definitions)

3. **Legacy integrations**
   - If external systems depend on specific naming
   - Document the exception in code comments

**How to document exceptions:**
```python
# backend/app/models/rkp.py
"""RKP (Real Estate Knowledge Platform) models.

NAMING EXCEPTION: RKP is an acronym, not subject to plural/singular rules.
See docs/DOMAIN_NAMING_STANDARDS.md for general standards.
"""
```

---

## FAQs

### Q: Why is `property.py` singular but `users.py` plural?

**A:** Historical inconsistency. `property.py` predates this standard.

**Correct:** Should be `properties.py` (multiple property records)

**Migration:** Rename to `properties.py` in Phase 4 of migration plan

---

### Q: Should Pydantic schemas be plural or singular?

**A:** **Singular** (conventional for Pydantic models)

**Rationale:**
```python
# Pydantic models represent SINGLE instances
class User(BaseModel):      # ✅ Singular
    name: str

class Users(BaseModel):     # ❌ Wrong (confusing)
    name: str
```

**File Naming:**
```python
# Schema files can be singular
backend/app/schemas/user.py     # ✅ OK (contains User, UserCreate, UserUpdate)
backend/app/schemas/users.py    # ❌ Confusing (what's the difference?)
```

---

### Q: What about `market.py` - singular or plural?

**A:** **Singular** (singleton per location/context)

**Rationale:** "Market" represents aggregate metrics for a location, not multiple market records.

**Tables:**
- `yield_benchmarks` (plural)
- `absorption_tracking` (singular, aggregated data)
- `market_cycle` (singular, one per location)

---

### Q: When do I use `_api` suffix?

**A:** **Never** (for routers in `api/v1/`)

**Exception:** If creating an API client library (not a router):
```python
# ✅ OK for client libraries
backend/app/clients/stripe_api.py  # External API client
backend/app/clients/ura_api.py     # URA external API

# ❌ Never for internal routers
backend/app/api/v1/projects_api.py  # Wrong
```

---

## Related Documentation

- [CODING_RULES.md](../CODING_RULES.md) - General coding standards
- [AUTHENTICATION.md](AUTHENTICATION.md) - Auth endpoint consolidation plan
- [architecture_honest.md](architecture_honest.md) - Current file organization

---

**Last Updated:** 2025-10-22
**Next Review:** After Phase 2 completion (Q1 2026)
**Questions:** Open GitHub discussion or ask in #architecture channel
