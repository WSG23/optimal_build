"""Comprehensive audit logging service for compliance tracking.

This module provides a complete audit trail for:
- Data modifications (CRUD operations)
- User authentication events
- Authorization decisions
- API access patterns
- Sensitive data access
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.types import FlexibleJSONB

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Types of auditable actions."""

    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token.refresh"
    PASSWORD_CHANGE = "auth.password.change"
    PASSWORD_RESET = "auth.password.reset"
    MFA_ENABLED = "auth.mfa.enabled"
    MFA_DISABLED = "auth.mfa.disabled"

    # Authorization
    ACCESS_GRANTED = "authz.access.granted"
    ACCESS_DENIED = "authz.access.denied"
    PERMISSION_CHANGE = "authz.permission.change"
    ROLE_ASSIGNED = "authz.role.assigned"
    ROLE_REMOVED = "authz.role.removed"

    # Data Operations
    CREATE = "data.create"
    READ = "data.read"
    UPDATE = "data.update"
    DELETE = "data.delete"
    EXPORT = "data.export"
    IMPORT = "data.import"

    # Sensitive Data
    PII_ACCESS = "sensitive.pii.access"
    FINANCIAL_ACCESS = "sensitive.financial.access"
    DOCUMENT_ACCESS = "sensitive.document.access"

    # Administrative
    USER_CREATED = "admin.user.created"
    USER_DELETED = "admin.user.deleted"
    USER_SUSPENDED = "admin.user.suspended"
    CONFIG_CHANGE = "admin.config.change"
    BACKUP_CREATED = "admin.backup.created"
    BACKUP_RESTORED = "admin.backup.restored"

    # API
    API_REQUEST = "api.request"
    API_ERROR = "api.error"
    RATE_LIMIT_HIT = "api.ratelimit.hit"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditService:
    """Service for comprehensive audit logging."""

    def __init__(
        self,
        db: AsyncSession,
        signing_key: str | None = None,
    ) -> None:
        self.db = db
        self.signing_key: str = signing_key or os.getenv("AUDIT_SIGNING_KEY", "")
        if not self.signing_key:
            logger.warning("AUDIT_SIGNING_KEY not set, using SECRET_KEY")
            self.signing_key = os.getenv("SECRET_KEY") or "default-key"

    async def log(
        self,
        action: AuditAction,
        user_id: int | None = None,
        user_email: str | None = None,
        resource_type: str | None = None,
        resource_id: str | int | None = None,
        details: dict[str, Any] | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: str | None = None,
        user_agent: str | None = None,
        correlation_id: str | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
    ) -> int:
        """Create an audit log entry.

        Args:
            action: The type of action being audited.
            user_id: ID of the user performing the action.
            user_email: Email of the user (for easier querying).
            resource_type: Type of resource affected (e.g., 'project', 'user').
            resource_id: ID of the affected resource.
            details: Additional details about the action.
            severity: Severity level of the event.
            ip_address: Client IP address.
            user_agent: Client user agent string.
            correlation_id: Request correlation ID for tracing.
            old_values: Previous values (for updates).
            new_values: New values (for creates/updates).

        Returns:
            The ID of the created audit log entry.
        """
        timestamp = datetime.now(timezone.utc)

        # Build the audit record
        record = {
            "action": action.value,
            "user_id": user_id,
            "user_email": user_email,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "severity": severity.value,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "correlation_id": correlation_id,
            "timestamp": timestamp.isoformat(),
            "details": details or {},
        }

        # Add change tracking for data operations
        if old_values is not None:
            record["old_values"] = self._sanitize_sensitive_data(old_values)
        if new_values is not None:
            record["new_values"] = self._sanitize_sensitive_data(new_values)

        # Calculate hash for integrity
        content_hash = self._calculate_hash(record)
        signature = self._sign_record(content_hash)

        # Get previous hash for chain integrity
        prev_hash = await self._get_last_hash()

        # Insert using raw SQL for the extended audit table
        query = text("""
            INSERT INTO compliance_audit_logs (
                action, user_id, user_email, resource_type, resource_id,
                severity, ip_address, user_agent, correlation_id,
                old_values, new_values, details,
                content_hash, prev_hash, signature, created_at
            ) VALUES (
                :action, :user_id, :user_email, :resource_type, :resource_id,
                :severity, :ip_address, :user_agent, :correlation_id,
                :old_values, :new_values, :details,
                :content_hash, :prev_hash, :signature, :created_at
            ) RETURNING id
        """)

        result = await self.db.execute(
            query,
            {
                "action": action.value,
                "user_id": user_id,
                "user_email": user_email,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "severity": severity.value,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "correlation_id": correlation_id,
                "old_values": json.dumps(record.get("old_values")),
                "new_values": json.dumps(record.get("new_values")),
                "details": json.dumps(details or {}),
                "content_hash": content_hash,
                "prev_hash": prev_hash,
                "signature": signature,
                "created_at": timestamp,
            },
        )

        row = result.fetchone()
        audit_id = row[0] if row else 0

        await self.db.commit()

        logger.debug(
            f"Audit log created: {action.value} for user {user_id}, "
            f"resource {resource_type}/{resource_id}"
        )

        return audit_id

    def _calculate_hash(self, record: dict[str, Any]) -> str:
        """Calculate SHA-256 hash of the audit record."""
        content = json.dumps(record, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()

    def _sign_record(self, content_hash: str) -> str:
        """Sign the content hash with HMAC-SHA256."""
        return hmac.new(
            self.signing_key.encode(),
            content_hash.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def _get_last_hash(self) -> str | None:
        """Get the hash of the last audit entry for chain integrity."""
        query = text("""
            SELECT content_hash FROM compliance_audit_logs
            ORDER BY id DESC LIMIT 1
        """)
        result = await self.db.execute(query)
        row = result.fetchone()
        return row[0] if row else None

    def _sanitize_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove or mask sensitive fields from audit data."""
        sensitive_fields = {
            "password",
            "secret",
            "token",
            "api_key",
            "credit_card",
            "ssn",
            "social_security",
        }

        sanitized: dict[str, Any] = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_fields):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_sensitive_data(value)
            else:
                sanitized[key] = value

        return sanitized

    async def verify_integrity(self, start_id: int | None = None) -> bool:
        """Verify the integrity of the audit log chain.

        Args:
            start_id: Start verification from this ID (or from beginning).

        Returns:
            True if chain is valid, False if tampered.
        """
        query = text("""
            SELECT id, content_hash, prev_hash, signature
            FROM compliance_audit_logs
            WHERE id >= COALESCE(:start_id, 1)
            ORDER BY id ASC
        """)

        result = await self.db.execute(query, {"start_id": start_id})
        rows = result.fetchall()

        prev_hash = None
        for row in rows:
            audit_id, content_hash, stored_prev_hash, signature = row

            # Verify chain linkage
            if prev_hash is not None and stored_prev_hash != prev_hash:
                logger.error(f"Chain break detected at audit ID {audit_id}")
                return False

            # Verify signature
            expected_signature = self._sign_record(content_hash)
            if signature != expected_signature:
                logger.error(f"Invalid signature detected at audit ID {audit_id}")
                return False

            prev_hash = content_hash

        return True


# Migration SQL for the compliance audit table
COMPLIANCE_AUDIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS compliance_audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    user_id INTEGER,
    user_email VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    ip_address VARCHAR(45),
    user_agent TEXT,
    correlation_id VARCHAR(64),
    old_values JSONB,
    new_values JSONB,
    details JSONB DEFAULT '{}',
    content_hash VARCHAR(64) NOT NULL,
    prev_hash VARCHAR(64),
    signature VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_compliance_audit_user_id ON compliance_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_compliance_audit_action ON compliance_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_compliance_audit_resource ON compliance_audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_compliance_audit_created ON compliance_audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_compliance_audit_severity ON compliance_audit_logs(severity);
CREATE INDEX IF NOT EXISTS idx_compliance_audit_correlation ON compliance_audit_logs(correlation_id);

-- Index for chain verification
CREATE INDEX IF NOT EXISTS idx_compliance_audit_hash ON compliance_audit_logs(content_hash);

-- Comment on table
COMMENT ON TABLE compliance_audit_logs IS 'Immutable audit log for compliance tracking with chain integrity verification';
"""


async def log_data_change(
    db: AsyncSession,
    action: AuditAction,
    user_id: int | None,
    user_email: str | None,
    resource_type: str,
    resource_id: str | int,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    ip_address: str | None = None,
    correlation_id: str | None = None,
) -> int:
    """Convenience function for logging data changes.

    Args:
        db: Database session.
        action: The audit action.
        user_id: User performing the action.
        user_email: User's email.
        resource_type: Type of resource.
        resource_id: ID of resource.
        old_values: Previous values.
        new_values: New values.
        ip_address: Client IP.
        correlation_id: Request correlation ID.

    Returns:
        Audit log ID.
    """
    service = AuditService(db)
    return await service.log(
        action=action,
        user_id=user_id,
        user_email=user_email,
        resource_type=resource_type,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        correlation_id=correlation_id,
    )


async def log_auth_event(
    db: AsyncSession,
    action: AuditAction,
    user_id: int | None,
    user_email: str | None,
    success: bool = True,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict[str, Any] | None = None,
) -> int:
    """Convenience function for logging authentication events.

    Args:
        db: Database session.
        action: The audit action.
        user_id: User ID (if known).
        user_email: User's email.
        success: Whether the auth action succeeded.
        ip_address: Client IP.
        user_agent: Client user agent.
        details: Additional details.

    Returns:
        Audit log ID.
    """
    service = AuditService(db)
    severity = AuditSeverity.INFO if success else AuditSeverity.WARNING

    return await service.log(
        action=action,
        user_id=user_id,
        user_email=user_email,
        severity=severity,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"success": success, **(details or {})},
    )
