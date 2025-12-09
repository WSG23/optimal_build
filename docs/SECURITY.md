# Security Guide for Optimal Build

This document outlines security measures implemented in the codebase and provides guidance for secure production deployment.

## Table of Contents

1. [Development vs Production Mode](#development-vs-production-mode)
2. [Authentication & Authorization](#authentication--authorization)
3. [Secrets Management](#secrets-management)
4. [API Security](#api-security)
5. [File Upload Security](#file-upload-security)
6. [Password Security](#password-security)
7. [Production Deployment Checklist](#production-deployment-checklist)
8. [Security Headers](#security-headers)
9. [Rate Limiting](#rate-limiting)
10. [Reporting Vulnerabilities](#reporting-vulnerabilities)

---

## Development vs Production Mode

The application operates in two modes controlled by `ENVIRONMENT`:

### Development Mode (`ENVIRONMENT=development`)

- Header-based identity (`X-Role`, `X-User-Id`, `X-User-Email`) is accepted for easy testing
- Rate limits are relaxed
- Detailed error messages are shown
- CORS allows localhost origins

### Production Mode (`ENVIRONMENT=production`)

- JWT token authentication is enforced
- Strict rate limits apply
- Error messages are sanitized
- CORS is restricted to configured origins
- HSTS and strict security headers are enabled

**Important:** Never use development mode in production environments.

---

## Authentication & Authorization

### Current Implementation

The application uses a dual authentication system:

1. **JWT Tokens** (Recommended for production)
   - Access tokens expire in 30 minutes
   - Refresh tokens expire in 7 days
   - Tokens are signed with `SECRET_KEY` using HS256

2. **Header-Based Identity** (Development only)
   - Uses `X-Role`, `X-User-Id`, `X-User-Email` headers
   - **WARNING:** This is easily spoofable and should never be trusted in production

### Role Hierarchy

```
admin > reviewer > developer > viewer
```

- `viewer`: Read-only access
- `developer`: Can create/modify own resources
- `reviewer`: Can approve/reject submissions
- `admin`: Full system access

### Securing for Production

For production deployment, you should:

1. Disable header-based authentication by setting `ALLOW_VIEWER_MUTATIONS=false`
2. Enforce JWT tokens on all protected endpoints
3. Consider implementing OAuth2/OIDC for enterprise deployments

---

## Secrets Management

### Required Secrets

| Secret | Purpose | Generation |
|--------|---------|------------|
| `SECRET_KEY` | JWT signing, encryption | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `POSTGRES_PASSWORD` | Database access | Strong random password |
| `S3_ACCESS_KEY` | Object storage access | From your S3/MinIO provider |
| `S3_SECRET_KEY` | Object storage access | From your S3/MinIO provider |
| `FIRST_SUPERUSER_PASSWORD` | Initial admin account | Strong password (16+ chars) |

### Best Practices

1. **Never commit secrets to version control**
   - `.env` is already in `.gitignore`
   - Use `.env.example` as a template

2. **Use different secrets per environment**
   - Development, staging, and production should have unique secrets

3. **Rotate secrets regularly**
   - Rotate `SECRET_KEY` quarterly (will invalidate all sessions)
   - Rotate database passwords after any suspected breach

4. **Use a secrets manager in production**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets

---

## API Security

### CORS Configuration

Allowed headers are explicitly whitelisted in `backend/app/main.py`:

```python
_ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "Origin",
    "X-Requested-With",
    "X-Role",  # Development only
    "X-User-Id",  # Development only
    "X-User-Email",  # Development only
    "X-Correlation-ID",
]
```

**For production:** Remove `X-Role`, `X-User-Id`, `X-User-Email` from allowed headers if not using header-based auth.

### Request Size Limits

- Global request size limit: 10 MB (configured in middleware)
- File upload limit: 50 MB per file (configurable per endpoint)

### Input Validation

All API inputs are validated using Pydantic schemas with:
- Type validation
- Range constraints
- String length limits
- Format validation (email, UUID, etc.)

---

## File Upload Security

### Path Traversal Protection

The `sanitize_object_name()` function in `backend/app/services/minio_service.py` prevents:

- Directory traversal (`../`, `..\\`)
- Null byte injection
- Control character injection
- Overly long paths (max 1024 bytes)

### File Size Limits

- Default per-file limit: 50 MB
- Configurable via `max_size_bytes` parameter
- Global request limit: 10 MB (middleware)

### File Type Validation

Supported import formats are validated by extension:
- `.dxf` - CAD drawings
- `.ifc` - BIM models
- `.json` - Data files

**Recommendation:** Add magic byte validation for production deployments.

---

## Password Security

### Hashing Algorithm

Passwords are hashed using **bcrypt** (upgraded from SHA256):

```python
pwd_context = CryptContext(
    schemes=["bcrypt", "sha256_crypt"],
    default="bcrypt",
    deprecated=["sha256_crypt"],
)
```

- New passwords use bcrypt
- Existing SHA256 hashes are accepted but marked deprecated
- Passwords are automatically rehashed on next login

### Account Lockout

The `AccountLockoutService` provides brute-force protection:
- Accounts are locked after multiple failed attempts
- Lockout duration increases with repeated failures
- Successful login clears the lockout counter

---

## Production Deployment Checklist

### Before Deploying

- [ ] Set `ENVIRONMENT=production`
- [ ] Generate unique `SECRET_KEY` (32+ random characters)
- [ ] Set strong `FIRST_SUPERUSER_PASSWORD` (16+ characters)
- [ ] Configure unique database password
- [ ] Configure unique S3/MinIO credentials
- [ ] Set `BACKEND_ALLOWED_ORIGINS` to production domains only
- [ ] Set `ALLOW_VIEWER_MUTATIONS=false`
- [ ] Enable HTTPS (TLS termination at load balancer)
- [ ] Configure Redis authentication if exposed

### Infrastructure

- [ ] Database is not publicly accessible
- [ ] Redis is not publicly accessible
- [ ] S3/MinIO buckets have proper access policies
- [ ] Firewall rules restrict access to necessary ports only
- [ ] Log aggregation is configured
- [ ] Monitoring and alerting is set up

### Post-Deployment

- [ ] Change default superuser password
- [ ] Test authentication flows
- [ ] Verify rate limiting works
- [ ] Check security headers with [securityheaders.com](https://securityheaders.com)
- [ ] Run a vulnerability scan

---

## Security Headers

The `SecurityHeadersMiddleware` adds these headers to all responses:

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | Force HTTPS |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer |
| `Content-Security-Policy` | Restrictive CSP | Prevent XSS |
| `Permissions-Policy` | Disable sensitive APIs | Limit browser features |

---

## Rate Limiting

Rate limiting is implemented using SlowAPI with Redis backend:

- Default limit: `10/minute` (configurable via `API_RATE_LIMIT`)
- Test mode limit: `1000/minute`
- Storage: Redis (falls back to memory if unavailable)

### Endpoints with Custom Limits

Some endpoints may have custom rate limits for:
- Login attempts (stricter)
- File uploads (stricter)
- Public APIs (more relaxed)

---

## Reporting Vulnerabilities

If you discover a security vulnerability:

1. **Do not** open a public issue
2. Email security concerns to the maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a timeline for resolution.

---

## Security Updates Log

| Date | Change | Files Modified |
|------|--------|----------------|
| 2025-12-08 | Removed fallback JWT secret | `backend/app/core/auth/service.py` |
| 2025-12-08 | Restricted CORS allowed headers | `backend/app/main.py` |
| 2025-12-08 | Upgraded to bcrypt password hashing | `backend/app/utils/security.py` |
| 2025-12-08 | Added path traversal protection | `backend/app/services/minio_service.py` |
| 2025-12-08 | Added file size validation | `backend/app/services/minio_service.py` |
| 2025-12-08 | Enhanced .env.example with security guidance | `.env.example` |
