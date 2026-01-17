# Compliance & Data Protection Guide

## Overview

This document outlines compliance requirements and data protection measures for optimal_build, covering GDPR, SOC 2, and general security best practices.

---

## GDPR Compliance

### Data Subject Rights

optimal_build must support the following GDPR rights:

#### 1. Right to Access (Article 15)
Users can request a copy of all their personal data.

**Implementation**:
```python
# API endpoint: GET /api/v1/users/me/data-export
# Returns: JSON file with all user data

async def export_user_data(user_id: int, db: AsyncSession) -> dict:
    """Export all data associated with a user."""
    return {
        "personal_info": await get_user_profile(db, user_id),
        "projects": await get_user_projects(db, user_id),
        "activity_log": await get_user_activity(db, user_id),
        "preferences": await get_user_preferences(db, user_id),
        "export_date": datetime.utcnow().isoformat(),
    }
```

**Response time**: Within 30 days (aim for 72 hours)

#### 2. Right to Rectification (Article 16)
Users can correct inaccurate personal data.

**Implementation**:
- Profile editing via `/api/v1/users/me`
- Audit trail for all changes
- Email verification for email changes

#### 3. Right to Erasure (Article 17)
Users can request deletion of their personal data.

**Implementation**:
```python
# API endpoint: DELETE /api/v1/users/me
# Triggers: Soft delete → 30-day retention → Hard delete

async def delete_user_account(user_id: int, db: AsyncSession) -> None:
    """Process user deletion request."""
    # 1. Soft delete user record
    await soft_delete_user(db, user_id)

    # 2. Anonymize related data
    await anonymize_user_projects(db, user_id)
    await anonymize_user_comments(db, user_id)

    # 3. Schedule hard delete after retention period
    await schedule_hard_delete(user_id, days=30)

    # 4. Send confirmation email
    await send_deletion_confirmation(user_id)
```

**Exceptions** (data retained for legal obligations):
- Financial records: 7 years
- Audit logs: 1 year (anonymized)
- Legal disputes: Duration of dispute

#### 4. Right to Data Portability (Article 20)
Users can export data in machine-readable format.

**Implementation**:
- Export formats: JSON, CSV
- Endpoint: `GET /api/v1/users/me/export?format=json`
- Includes: All user-generated content

#### 5. Right to Restrict Processing (Article 18)
Users can request limitation of data processing.

**Implementation**:
```python
# User preference: processing_restricted = True
# When restricted:
# - No marketing emails
# - No analytics tracking
# - Data not used for AI/ML training
# - Basic functionality only
```

#### 6. Right to Object (Article 21)
Users can object to certain types of processing.

**Implementation**:
- Marketing opt-out: One-click unsubscribe
- Analytics opt-out: Cookie consent banner
- Profiling opt-out: Account settings

### Lawful Basis for Processing

| Data Type | Lawful Basis | Justification |
|-----------|--------------|---------------|
| Account data | Contract | Required for service |
| Project data | Contract | Core functionality |
| Usage analytics | Legitimate interest | Service improvement |
| Marketing emails | Consent | Optional, opt-in |
| Payment data | Legal obligation | Tax/financial records |

### Data Processing Records

**Required documentation** (Article 30):

```yaml
# data-processing-register.yaml
processing_activities:
  - name: User Registration
    purpose: Account creation and authentication
    data_categories: [name, email, password_hash]
    recipients: [internal_systems]
    retention: Account lifetime + 30 days
    security_measures: [encryption, access_control]

  - name: Project Management
    purpose: Core application functionality
    data_categories: [project_data, geometry, calculations]
    recipients: [internal_systems, user_designated_sharing]
    retention: Account lifetime + 30 days
    security_measures: [encryption, access_control, audit_logging]

  - name: Analytics
    purpose: Service improvement
    data_categories: [usage_patterns, feature_usage]
    recipients: [internal_analytics]
    retention: 2 years (anonymized)
    security_measures: [anonymization, aggregation]
```

### Data Protection Impact Assessment (DPIA)

Required for high-risk processing:

1. **Automated decision-making**: AI-powered recommendations
2. **Large-scale processing**: Batch operations on user data
3. **Sensitive data**: Financial calculations, property valuations

**DPIA Template**:
```markdown
## Processing Activity: [Name]

### Description
[What data is processed, how, and why]

### Necessity Assessment
- Is this processing necessary? [Yes/No]
- Could the same result be achieved with less data? [Yes/No]

### Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data breach | Medium | High | Encryption, access control |
| Unauthorized access | Low | High | MFA, audit logging |

### Conclusion
[Approved/Requires additional measures/Rejected]
```

---

## SOC 2 Compliance

### Trust Service Criteria

#### Security (Common Criteria)

**CC6.1 - Logical Access Controls**
```yaml
controls:
  - Authentication:
      - MFA required for all users
      - Password policy: 12+ chars, complexity requirements
      - Session timeout: 30 minutes idle

  - Authorization:
      - Role-based access control (RBAC)
      - Principle of least privilege
      - Regular access reviews (quarterly)

  - Monitoring:
      - All access attempts logged
      - Failed login alerts
      - Privileged action auditing
```

**CC6.6 - System Boundaries**
```yaml
network_controls:
  - VPC isolation
  - Security groups (minimal ports)
  - WAF protection
  - DDoS mitigation
```

**CC6.7 - Data Transmission**
```yaml
encryption:
  - TLS 1.3 for all connections
  - Certificate pinning for mobile apps
  - HSTS enabled (max-age=31536000)
```

#### Availability

**A1.1 - Capacity Planning**
```yaml
monitoring:
  - CPU utilization alerts at 70%
  - Memory alerts at 80%
  - Disk space alerts at 85%
  - Auto-scaling triggers at 60% average CPU
```

**A1.2 - Recovery**
```yaml
backup_strategy:
  - Database: Daily full, hourly incremental
  - Application: Container images in registry
  - Configuration: Git versioned
  - Recovery testing: Monthly
```

#### Confidentiality

**C1.1 - Data Classification**
```yaml
classification_levels:
  - Public:
      examples: [marketing_content, documentation]
      controls: [none_required]

  - Internal:
      examples: [aggregate_analytics, system_metrics]
      controls: [authentication_required]

  - Confidential:
      examples: [user_data, project_data]
      controls: [encryption, access_control, audit_logging]

  - Restricted:
      examples: [credentials, api_keys, financial_data]
      controls: [encryption, strict_access, enhanced_audit]
```

#### Processing Integrity

**PI1.1 - Input Validation**
```python
# All API inputs validated with Pydantic
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    budget: float = Field(..., gt=0, le=1e12)
    property_id: int = Field(..., gt=0)

    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        # Prevent XSS
        return bleach.clean(v)
```

**PI1.4 - Output Integrity**
```python
# All outputs validated before sending
class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: ProjectStatus
    created_at: datetime

    @model_validator(mode='after')
    def validate_output(self) -> 'ProjectResponse':
        # Ensure no sensitive data leaked
        assert not hasattr(self, 'internal_notes')
        return self
```

#### Privacy

**P1.1 - Privacy Notice**
Required elements:
- What data is collected
- How it's used
- Who it's shared with
- User rights
- Contact information

**P3.1 - Consent Management**
```python
class ConsentRecord(BaseModel):
    user_id: int
    consent_type: str  # marketing, analytics, data_sharing
    granted: bool
    granted_at: datetime | None
    ip_address: str
    user_agent: str
```

---

## Security Controls Checklist

### Authentication & Authorization

- [x] Multi-factor authentication available
- [x] Password hashing (bcrypt, cost factor 12)
- [x] Session management with secure cookies
- [x] JWT tokens with short expiration (15 min access, 7 day refresh)
- [x] Role-based access control
- [x] API key authentication for integrations

### Data Protection

- [x] Encryption at rest (AES-256)
- [x] Encryption in transit (TLS 1.3)
- [x] Database field-level encryption for sensitive data
- [x] Secure key management (AWS KMS / HashiCorp Vault)
- [x] Data masking in logs

### Audit & Monitoring

- [x] Comprehensive audit logging
- [x] HMAC-signed audit records (tamper-evident)
- [x] Real-time security alerts
- [x] Log retention (1 year)
- [x] Regular log reviews

### Vulnerability Management

- [x] Automated dependency scanning (Dependabot)
- [x] SAST in CI/CD pipeline
- [x] Container image scanning
- [x] Regular penetration testing (annual)
- [x] Bug bounty program (recommended)

### Incident Response

- [x] Incident response plan documented
- [x] On-call rotation established
- [x] Communication templates prepared
- [x] Regular incident drills

---

## Data Retention Policy

| Data Type | Retention Period | Deletion Method |
|-----------|------------------|-----------------|
| Active user data | Account lifetime | On request |
| Deleted user data | 30 days | Hard delete |
| Audit logs | 1 year | Automated purge |
| Financial records | 7 years | Manual review |
| Session logs | 90 days | Automated purge |
| Analytics (raw) | 90 days | Aggregation then purge |
| Analytics (aggregated) | 2 years | Automated purge |
| Backups | 30 days | Automated rotation |

### Retention Implementation

```python
# Scheduled job: daily at 03:00 UTC
async def enforce_data_retention():
    """Enforce data retention policies."""

    # Delete expired user data
    await db.execute(
        delete(User)
        .where(User.deleted_at < datetime.utcnow() - timedelta(days=30))
    )

    # Purge old audit logs
    await db.execute(
        delete(AuditLog)
        .where(AuditLog.created_at < datetime.utcnow() - timedelta(days=365))
    )

    # Purge old sessions
    await db.execute(
        delete(Session)
        .where(Session.created_at < datetime.utcnow() - timedelta(days=90))
    )

    await db.commit()
```

---

## Compliance Reporting

### Required Reports

| Report | Frequency | Audience | Content |
|--------|-----------|----------|---------|
| Security metrics | Monthly | Engineering | Vulnerabilities, incidents, patch status |
| Access review | Quarterly | Security team | User access audit |
| Compliance status | Quarterly | Leadership | Control effectiveness |
| Penetration test | Annual | Security team | External assessment |
| SOC 2 audit | Annual | Customers | Type II report |

### Metrics to Track

```yaml
security_metrics:
  - Mean time to patch critical vulnerabilities
  - Number of security incidents
  - Percentage of systems with current patches
  - MFA adoption rate
  - Failed login attempt trends
  - Data access request response time
  - Backup success rate
  - Recovery test success rate
```

---

## Vendor Management

### Third-Party Risk Assessment

Before integrating any third-party service:

1. **Security questionnaire**: SOC 2, ISO 27001 status
2. **Data processing agreement**: GDPR-compliant DPA
3. **Penetration test results**: Recent assessment
4. **Insurance**: Cyber liability coverage
5. **Incident notification**: SLA for breach notification

### Current Vendors

| Vendor | Service | Data Shared | DPA Status |
|--------|---------|-------------|------------|
| AWS | Infrastructure | All data | ✅ Signed |
| Sentry | Error tracking | Error context | ✅ Signed |
| Stripe | Payments | Payment data | ✅ Signed |
| SendGrid | Email | Email addresses | ✅ Signed |

---

## Training Requirements

### Security Awareness Training

| Role | Training | Frequency |
|------|----------|-----------|
| All employees | Security basics | Annual |
| Developers | Secure coding | Annual |
| DevOps | Infrastructure security | Annual |
| Support | Data handling | Annual |
| Management | Compliance overview | Annual |

### Training Topics

1. **General Security**
   - Password hygiene
   - Phishing awareness
   - Social engineering
   - Physical security

2. **Developer-Specific**
   - OWASP Top 10
   - Secure coding practices
   - Dependency management
   - Secret handling

3. **Compliance-Specific**
   - GDPR requirements
   - Data subject rights
   - Incident reporting
   - Data classification

---

## Contact Information

### Data Protection

- **Data Protection Officer**: [Name/Email]
- **Privacy inquiries**: privacy@optimalbuild.com
- **Data requests**: data-requests@optimalbuild.com

### Security

- **Security team**: security@optimalbuild.com
- **Vulnerability reports**: security@optimalbuild.com (PGP key available)
- **Incident reports**: incidents@optimalbuild.com

---

**Document Version**: 1.0
**Last Updated**: 2025-01-17
**Next Review**: 2025-04-17
**Owner**: Security & Compliance Team
