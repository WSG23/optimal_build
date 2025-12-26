# Security Features Documentation

This document describes the security features implemented in the optimal_build platform.

## Multi-Tenancy (Organizations)

The platform supports workspace/organization isolation for enterprise deployments.

### Models

- **Organization**: Top-level tenant container with subscription plans (FREE, STARTER, PROFESSIONAL, ENTERPRISE)
- **OrganizationMember**: User membership with roles (OWNER, ADMIN, MEMBER, VIEWER)
- **OrganizationInvitation**: Token-based invitation workflow with expiry

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/organizations` | POST | Create organization |
| `/api/v1/organizations` | GET | List user's organizations |
| `/api/v1/organizations/{id}` | GET | Get organization details |
| `/api/v1/organizations/{id}` | PATCH | Update organization |
| `/api/v1/organizations/{id}` | DELETE | Soft-delete organization |
| `/api/v1/organizations/{id}/members` | GET | List members |
| `/api/v1/organizations/{id}/members` | POST | Add member |
| `/api/v1/organizations/{id}/members/{id}` | PATCH | Update member role |
| `/api/v1/organizations/{id}/members/{id}` | DELETE | Remove member |
| `/api/v1/organizations/{id}/invitations` | GET | List invitations |
| `/api/v1/organizations/{id}/invitations` | POST | Create invitation |
| `/api/v1/organizations/invitations/accept` | POST | Accept invitation |
| `/api/v1/organizations/switch` | POST | Switch active organization |

### Files

- `backend/app/models/organization.py` - SQLAlchemy models
- `backend/app/schemas/organization.py` - Pydantic schemas
- `backend/app/api/v1/organizations.py` - API endpoints
- `backend/tests/test_api/test_organizations.py` - Tests (28 tests)

---

## Session Management

Secure session management with token blacklisting for logout support.

### Features

- Token blacklisting for logout/revocation
- Multi-device session tracking
- Session expiry management
- Redis-backed storage (with in-memory fallback)

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login and get tokens |
| `/api/v1/auth/logout` | POST | Logout (blacklist token) |
| `/api/v1/auth/logout/all` | POST | Logout all devices |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/sessions` | GET | List active sessions |
| `/api/v1/auth/sessions/{id}` | DELETE | Revoke specific session |
| `/api/v1/auth/password/reset` | POST | Request password reset |
| `/api/v1/auth/password/change` | POST | Change password |

### Files

- `backend/app/core/session.py` - Session management module
- `backend/app/api/v1/auth.py` - Authentication endpoints
- `backend/tests/test_core/test_session.py` - Tests (22 tests)

---

## Rate Limiting

Global rate limiting with SlowAPI and optional Redis backend.

### Configuration

- Default: 10 requests/minute (production)
- Test mode: 1000 requests/minute
- Storage: Redis (preferred) or in-memory

### Configuration Variables

- `API_RATE_LIMIT`: Rate limit string (e.g., "10/minute")
- `RATE_LIMIT_STORAGE_URI`: Redis URL or "memory://"
- `RATE_LIMIT_REDIS_URL`: Alternative Redis configuration

### Files

- `backend/app/main.py` - SlowAPI integration (lines 17-56, 162-206)
- `backend/app/core/config.py` - Rate limit configuration

---

## GDPR Compliance

Full GDPR compliance with consent management, data export, and right to be forgotten.

### Consent Types

- `marketing_email` - Email marketing
- `marketing_sms` - SMS marketing
- `analytics` - Usage analytics
- `third_party_sharing` - Data sharing
- `personalization` - Content personalization
- `cookies_essential` - Essential cookies
- `cookies_analytics` - Analytics cookies
- `cookies_marketing` - Marketing cookies

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/gdpr/consent` | GET | Get consent preferences |
| `/api/v1/gdpr/consent` | PUT | Update consent preferences |
| `/api/v1/gdpr/consent/withdraw-all` | POST | Withdraw all marketing consent |
| `/api/v1/gdpr/export` | POST | Request data export |
| `/api/v1/gdpr/export/{id}` | GET | Check export status |
| `/api/v1/gdpr/export/{id}/download` | GET | Download export |
| `/api/v1/gdpr/delete-account` | POST | Request account deletion |
| `/api/v1/gdpr/delete-account/{id}` | DELETE | Cancel deletion request |
| `/api/v1/gdpr/access-request` | POST | Submit DSAR |
| `/api/v1/gdpr/privacy-dashboard` | GET | Privacy overview |

### GDPR Articles Supported

- **Article 15**: Right of access (data export, DSAR)
- **Article 16**: Right to rectification (consent management)
- **Article 17**: Right to erasure (account deletion)
- **Article 18**: Right to restriction (consent withdrawal)
- **Article 20**: Right to data portability (export to JSON/CSV)
- **Article 21**: Right to object (marketing consent)

### Files

- `backend/app/api/v1/gdpr.py` - GDPR endpoints
- `backend/tests/test_api/test_gdpr.py` - Tests (20 tests)

---

## Security Headers

All responses include security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Content-Security-Policy: default-src 'self'`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### Files

- `backend/app/middleware/security.py` - Security headers middleware

---

## Exception Handling

Standardized error responses with correlation ID tracking.

### Error Response Format

```json
{
  "error_code": "NOT_FOUND",
  "message": "Resource not found",
  "status_code": 404,
  "timestamp": "2025-12-26T00:00:00Z",
  "correlation_id": "uuid-here"
}
```

### Exception Types

- `AppError` - Base error class
- `NotFoundError` - 404 errors
- `ValidationError` - 422 errors
- `AuthenticationError` - 401 errors
- `AuthorizationError` - 403 errors
- `RateLimitError` - 429 errors (with Retry-After header)
- `ServiceUnavailableError` - 503 errors

### Files

- `backend/app/core/exceptions.py` - Exception classes
- `backend/app/middleware/exception_handler.py` - Handler middleware
- `backend/tests/test_middleware/test_exception_handler.py` - Tests

---

## Database Migrations

Multi-tenancy tables added:

```
Migration: 20251226_000002_add_multitenancy_tables.py

Tables:
- organizations (id, name, slug, plan, settings, is_active, uen_number)
- organization_members (organization_id, user_id, role, is_active)
- organization_invitations (organization_id, email, token, status)

Columns added:
- projects.organization_id (FK to organizations)
- users.primary_organization_id (FK to organizations)
```

---

## Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| Organizations | 28 | Passing |
| Sessions | 22 | Passing |
| GDPR | 20 | Passing |
| Pagination | 32 | Passing |
| Query Inspector | 30 | Passing |
| **Total** | **132** | **Passing** |
