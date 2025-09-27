"""Permit-ready export gating helpers."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.auth import PolicyContext, WorkspaceRole, can_export_permit_ready


@dataclass(frozen=True)
class ExportRequest:
    project_id: int
    overlay_version: str
    permit_ready: bool


@dataclass(frozen=True)
class ExportDecision:
    allowed: bool
    reason: str | None = None


def evaluate_export(request: ExportRequest, context: PolicyContext) -> ExportDecision:
    if not request.permit_ready:
        return ExportDecision(allowed=True)
    if can_export_permit_ready(context):
        return ExportDecision(allowed=True)
    role = context.role
    if role == WorkspaceRole.AGENCY:
        return ExportDecision(allowed=False, reason="Agency exports cannot be permit-ready")
    if role == WorkspaceRole.DEVELOPER:
        return ExportDecision(
            allowed=False,
            reason="Developer exports require architect sign-off before permit-ready",
        )
    return ExportDecision(
        allowed=False,
        reason="Permit-ready exports require an approved sign-off",
    )


__all__ = ["ExportRequest", "ExportDecision", "evaluate_export"]
