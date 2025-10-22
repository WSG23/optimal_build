# Authentication & Authorization Architecture

**Last Updated:** 2025-10-22

This document describes the actual authentication and authorization implementation in the optimal_build platform.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Flow](#authentication-flow)
3. [JWT Token System](#jwt-token-system)
4. [Authorization Models](#authorization-models)
5. [File Organization](#file-organization)
6. [Security Configuration](#security-configuration)
7. [Common Patterns](#common-patterns)
8. [Known Issues & Improvements](#known-issues--improvements)

---

## Overview

The platform uses **JWT (JSON Web Tokens)** for authentication and a **dual authorization model**:
1. **Header-based roles** (viewer, reviewer, admin) for entitlements/regulatory endpoints
2. **Workspace roles** (agency, developer, architect) for export/signoff policies

### Authentication
- **Library**: python-jose (JWT implementation)
- **Password Hashing**: bcrypt via passlib
- **Token Types**: Access tokens (30 min) + Refresh tokens (7 days)
- **Bearer Scheme**: HTTP Authorization header

### Authorization
- **Simple RBAC**: Header-based roles (X-Role header)
- **Workspace Policies**: Role-based export/signoff rules

---

## Authentication Flow

### 1. User Registration

**Endpoint:** `POST /api/v1/secure-users/signup`

**Flow:**
```
User submits credentials
    ↓
Validate email/username/full_name (Pydantic validation)
    ↓
Check email uniqueness
    ↓
Check username uniqueness
    ↓
Hash password with bcrypt
    ↓
Store user in database (currently in-memory)
    ↓
Return UserResponse (without password)
```

**Implementation:** `backend/app/api/v1/users_secure.py:signup()`

**Validation Rules:**
- Email: Valid email format (via pydantic EmailStr)
- Username: Required, must be unique
- Full name: Cannot be empty/whitespace
- Password: Minimum length enforced

---

### 2. User Login

**Endpoint:** `POST /api/v1/secure-users/login`

**Flow:**
```
User submits email + password
    ↓
Look up user by email
    ↓
Verify password against hashed_password (bcrypt)
    ↓
Generate JWT tokens (access + refresh)
    ↓
Return tokens + user data
```

**Implementation:** `backend/app/api/v1/users_secure.py:login()`

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "user_1",
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "company_name": "Acme Corp",
    "created_at": "2025-10-22T00:00:00",
    "is_active": true
  },
  "tokens": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

---

### 3. Authenticated Requests

**Flow:**
```
Client includes token in header: Authorization: Bearer <access_token>
    ↓
FastAPI HTTPBearer extracts credentials
    ↓
get_current_user() dependency called
    ↓
verify_token() decodes JWT
    ↓
Validate token type == "access"
    ↓
Extract TokenData (email, username, user_id)
    ↓
Return TokenData to route handler
```

**Implementation:** `backend/app/core/jwt_auth.py:get_current_user()`

**Usage in Endpoints:**
```python
from app.core.jwt_auth import TokenData, get_current_user

@router.get("/protected")
async def protected_route(user: TokenData = Depends(get_current_user)):
    # user.email, user.username, user.user_id available
    return {"message": f"Hello {user.username}"}
```

---

## JWT Token System

### Token Structure

**Access Token Payload:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "user_id": "user_1",
  "exp": 1634567890,
  "type": "access"
}
```

**Refresh Token Payload:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "user_id": "user_1",
  "exp": 1635172690,
  "type": "refresh"
}
```

### Token Expiration

| Token Type | Lifespan | Use Case |
|------------|----------|----------|
| Access Token | 30 minutes | API requests |
| Refresh Token | 7 days | Renewing access tokens |

**Constants:** `backend/app/core/jwt_auth.py:19-20`
- `ACCESS_TOKEN_EXPIRE_MINUTES = 30`
- `REFRESH_TOKEN_EXPIRE_DAYS = 7`

### Token Generation

**File:** `backend/app/core/jwt_auth.py`

```python
# Create both tokens
tokens = create_tokens({
    "email": user["email"],
    "username": user["username"],
    "id": user["id"]
})

# Returns TokenResponse with access_token + refresh_token
```

### Token Verification

```python
# Verify access token
token_data = verify_token(token, token_type="access")
# Returns TokenData(email, username, user_id)

# Verify refresh token
token_data = verify_token(token, token_type="refresh")
```

**Security Checks:**
1. Decode JWT with SECRET_KEY
2. Validate token type matches expected ("access" or "refresh")
3. Extract required fields (email, username, user_id)
4. Raise 401 if any check fails

---

## Authorization Models

### Model 1: Header-Based Roles (Simple RBAC)

**File:** `backend/app/api/deps.py`

**Roles:**
- `viewer` - Read-only access
- `reviewer` - Read + write access
- `admin` - Full access

**Header:** `X-Role: reviewer`

**Usage:**
```python
from app.api.deps import require_viewer, require_reviewer

@router.get("/data")
async def get_data(role: Role = Depends(require_viewer)):
    # Any authenticated user can access (viewer, reviewer, admin)
    pass

@router.post("/data")
async def create_data(role: Role = Depends(require_reviewer)):
    # Only reviewer or admin can access
    # (viewer rejected with 403 unless ALLOW_VIEWER_MUTATIONS=true)
    pass
```

**Default Role:** Configured via `settings.DEFAULT_ROLE` (defaults to "viewer")

**Permission Matrix:**
| Role | Read | Write | Admin |
|------|------|-------|-------|
| viewer | ✅ | ❌* | ❌ |
| reviewer | ✅ | ✅ | ❌ |
| admin | ✅ | ✅ | ✅ |

*Viewer can write if `ALLOW_VIEWER_MUTATIONS=true` (development mode)

---

### Model 2: Workspace Roles (Business Logic)

**File:** `backend/app/core/auth/policy.py`

**Roles:**
- `agency` - Real estate agency (marketing only)
- `developer` - Property developer (needs architect signoff)
- `architect` - Licensed architect (can approve exports)

**Used For:**
- Export permissions (permit-ready vs marketing-only)
- Watermark enforcement
- Signoff requirements

**Policy Functions:**

#### 1. Export Permissions
```python
can_export_permit_ready(context: PolicyContext) -> bool:
    - agency: Always False (marketing only)
    - developer: True if architect approved signoff
    - architect: True if signoff approved
```

#### 2. Watermark Enforcement
```python
watermark_forced(context: PolicyContext) -> bool:
    - agency: Always True
    - No signoff: Always True
    - With signoff: False (clean exports allowed)
```

#### 3. Signoff Requirements
```python
requires_signoff(context: PolicyContext) -> bool:
    - developer: True
    - agency: True
    - architect: False
```

#### 4. Architect Invitation
```python
can_invite_architect(context: PolicyContext) -> bool:
    - developer: True
    - Others: False
```

**Watermark Text:**
```
"Marketing Feasibility Only – Not for Permit or Construction."
```

---

## File Organization

### Current Structure (Fragmented)

**⚠️ Known Issue:** Authentication logic is split across 4 modules

```
backend/app/
├── api/v1/
│   ├── users_secure.py         # Login, signup endpoints
│   └── users_db.py             # Database-backed user CRUD
├── api/
│   └── deps.py                 # Header-based role enforcement
└── core/
    ├── jwt_auth.py             # JWT token generation/validation
    └── auth/
        └── policy.py           # Workspace role policies
```

### Responsibilities by File

| File | Responsibility | Lines |
|------|----------------|-------|
| `users_secure.py` | Registration, login endpoints | ~150 |
| `users_db.py` | User database CRUD operations | ~200 |
| `jwt_auth.py` | JWT creation, verification, dependencies | ~118 |
| `auth/policy.py` | Workspace role business logic | ~94 |
| `api/deps.py` | Header-based role checking | ~52 |

### Recommended Structure

**Goal:** Consolidate authentication into single auth module

```
backend/app/
├── api/v1/
│   ├── auth.py                 # All auth endpoints (login, signup, refresh)
│   └── users.py                # User management (profile, settings)
└── core/auth/
    ├── jwt.py                  # JWT utilities (moved from core/jwt_auth.py)
    ├── policy.py               # Workspace policies (existing)
    └── rbac.py                 # Header-based roles (moved from api/deps.py)
```

**Benefits:**
- Single entry point for authentication (`api/v1/auth.py`)
- All auth utilities in `core/auth/`
- Clear separation: authn (auth.py) vs authz (policy.py, rbac.py)

---

## Security Configuration

### Environment Variables

**Required:**
```bash
SECRET_KEY=<random-256-bit-key>  # JWT signing key
```

**Optional:**
```bash
DEFAULT_ROLE=viewer              # Default role if X-Role header missing
ALLOW_VIEWER_MUTATIONS=false     # Allow viewers to write (dev only)
```

### Secret Key Generation

**Development:**
```python
# Current fallback (DO NOT USE IN PRODUCTION)
SECRET_KEY = "fallback-secret-key-for-development-only-do-not-use-in-production"
```

**Production:**
```bash
# Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in environment
export SECRET_KEY="<generated-key>"
```

### Password Hashing

**Library:** passlib with bcrypt

**File:** `backend/app/utils/security.py`

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Algorithm:** bcrypt (industry standard, slow by design to resist brute force)

---

## Common Patterns

### Pattern 1: Protected Endpoint (JWT Auth)

```python
from app.core.jwt_auth import TokenData, get_current_user

@router.get("/profile")
async def get_profile(user: TokenData = Depends(get_current_user)):
    return {
        "email": user.email,
        "username": user.username,
        "user_id": user.user_id
    }
```

### Pattern 2: Optional Auth

```python
from app.core.jwt_auth import TokenData, get_optional_user

@router.get("/public-or-private")
async def hybrid_endpoint(user: TokenData | None = Depends(get_optional_user)):
    if user:
        return {"message": f"Welcome {user.username}", "authenticated": True}
    else:
        return {"message": "Public view", "authenticated": False}
```

### Pattern 3: Role-Based Access

```python
from app.api.deps import require_reviewer, Role

@router.post("/admin-action")
async def admin_action(role: Role = Depends(require_reviewer)):
    # Only reviewer/admin can execute
    return {"message": "Action executed", "role": role}
```

### Pattern 4: Workspace Policy Check

```python
from app.core.auth.policy import PolicyContext, WorkspaceRole, can_export_permit_ready

context = PolicyContext(role=WorkspaceRole.DEVELOPER, signoff=signoff_snapshot)

if can_export_permit_ready(context):
    # Export without watermark
    generate_clean_export()
else:
    # Force watermark
    generate_marketing_export()
```

---

## Known Issues & Improvements

### Current Issues

1. **Fragmented Code** (High Priority)
   - Auth logic split across 4 files makes auditing difficult
   - No single entry point for authentication
   - **Fix:** Consolidate to `api/v1/auth.py` + `core/auth/` module

2. **In-Memory User Storage**
   - Users stored in dict, lost on restart
   - **Fix:** Migrate to database (models/users.py already exists)

3. **No Refresh Token Endpoint**
   - Refresh tokens generated but no `/refresh` endpoint
   - **Fix:** Add `POST /api/v1/auth/refresh` endpoint

4. **No Token Revocation**
   - No blacklist for invalidating tokens before expiry
   - **Fix:** Add Redis-backed token blacklist

5. **Dual Authorization Models**
   - Header roles (`X-Role`) vs workspace roles causes confusion
   - **Consider:** Unify into single RBAC with workspace context

### Security Improvements

**Short-term:**
1. ✅ Rotate SECRET_KEY in production
2. ✅ Implement refresh token endpoint
3. ✅ Add token blacklist for logout
4. ✅ Migrate users to database

**Medium-term:**
1. Add rate limiting for auth endpoints (✅ rate limit middleware exists, enable it)
2. Add account lockout after N failed login attempts
3. Add email verification for new signups
4. Add password reset flow

**Long-term:**
1. Implement SSO (SAML/OAuth)
2. Add multi-factor authentication (MFA)
3. Add session management (track active sessions)
4. Add audit logging for auth events

---

## Testing Authentication

### Manual Testing

**1. Register User:**
```bash
curl -X POST http://localhost:9400/api/v1/secure-users/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "secure123"
  }'
```

**2. Login:**
```bash
curl -X POST http://localhost:9400/api/v1/secure-users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "secure123"
  }'
```

**3. Access Protected Endpoint:**
```bash
# Extract access_token from login response
TOKEN="<access_token>"

curl http://localhost:9400/api/v1/protected \
  -H "Authorization: Bearer $TOKEN"
```

### Automated Testing

**File:** `backend/tests/test_api/test_users_secure.py`

```bash
# Run auth tests
pytest backend/tests/test_api/test_users_secure.py -v
```

---

## Migration Plan

### Phase 1: Consolidate Files (2-3 days)
1. Create `backend/app/api/v1/auth.py`
2. Move signup/login from `users_secure.py` to `auth.py`
3. Add refresh token endpoint
4. Deprecate `users_secure.py` with warnings

### Phase 2: Move JWT Utilities (1 day)
1. Create `backend/app/core/auth/jwt.py`
2. Move JWT functions from `core/jwt_auth.py` to `core/auth/jwt.py`
3. Update all imports
4. Deprecate `core/jwt_auth.py`

### Phase 3: Database Integration (2-3 days)
1. Remove in-memory `users_db` dict
2. Use `app/models/users.py` (already exists)
3. Update endpoints to use database queries
4. Add database migrations if needed

### Phase 4: Enhanced Security (1 week)
1. Add refresh token endpoint
2. Add token blacklist (Redis)
3. Add rate limiting to auth endpoints
4. Add audit logging

---

## Related Documentation

- [CODING_RULES.md](../CODING_RULES.md) - Coding standards (async/await, testing)
- [architecture_honest.md](architecture_honest.md) - Current system architecture
- [DOMAIN_NAMING_STANDARDS.md](DOMAIN_NAMING_STANDARDS.md) - Naming conventions

---

**Last Updated:** 2025-10-22
**Maintainer:** Platform Team
**Review Cycle:** Quarterly (or after major auth changes)
