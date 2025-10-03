"""Workspace policy helper utilities."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal


class WorkspaceRole(str, Enum):
    AGENCY = "agency"
    DEVELOPER = "developer"
    ARCHITECT = "architect"


SignoffStatus = Literal["pending", "approved", "rejected"]


@dataclass(frozen=True)
class SignoffSnapshot:
    project_id: int
    overlay_version: str
    status: SignoffStatus
    architect_user_id: int | None
    signed_at: datetime | None

    def is_approved(self) -> bool:
        return self.status == "approved"


@dataclass(frozen=True)
class PolicyContext:
    role: WorkspaceRole
    signoff: SignoffSnapshot | None = None

    @property
    def has_approved_signoff(self) -> bool:
        if not self.signoff:
            return False
        return self.signoff.is_approved()


_WATERMARK_TEXT = "Marketing Feasibility Only – Not for Permit or Construction."


def requires_signoff(context: PolicyContext) -> bool:
    if context.role == WorkspaceRole.DEVELOPER:
        return True
    if context.role == WorkspaceRole.AGENCY:
        return True
    return False


def can_export_permit_ready(context: PolicyContext) -> bool:
    if context.role == WorkspaceRole.AGENCY:
        return False
    if context.role == WorkspaceRole.DEVELOPER:
        return context.has_approved_signoff
    if context.role == WorkspaceRole.ARCHITECT:
        return context.has_approved_signoff
    return False


def can_invite_architect(context: PolicyContext) -> bool:
    return context.role == WorkspaceRole.DEVELOPER


def watermark_forced(context: PolicyContext) -> bool:
    if context.role == WorkspaceRole.AGENCY:
        return True
    if not context.has_approved_signoff:
        return True
    return False


def watermark_text(context: PolicyContext) -> str:
    if watermark_forced(context):
        return _WATERMARK_TEXT
    return ""


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
