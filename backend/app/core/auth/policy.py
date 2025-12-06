"""Compatibility wrapper for policy helpers.

The canonical implementations live in ``app.core.auth.service`` to keep all
authentication and authorization logic in a single module.
"""

from app.core.auth.service import (  # noqa: F401
    PolicyContext,
    SignoffSnapshot,
    SignoffStatus,
    WorkspaceRole,
    can_export_permit_ready,
    can_invite_architect,
    requires_signoff,
    watermark_forced,
    watermark_text,
)

__all__ = [
    "WorkspaceRole",
    "PolicyContext",
    "SignoffSnapshot",
    "SignoffStatus",
    "requires_signoff",
    "can_export_permit_ready",
    "can_invite_architect",
    "watermark_forced",
    "watermark_text",
]
