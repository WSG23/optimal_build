"""Helpers for recording project audit events."""

from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import ProjectAuditLog


async def record_project_event(
    session: AsyncSession,
    *,
    project_id: int,
    event_type: str,
    baseline_seconds: int = 0,
    automated_seconds: int = 0,
    accepted_suggestions: int = 0,
    metadata: Mapping[str, Any] | None = None,
) -> ProjectAuditLog:
    """Persist an audit log entry summarising automation impact."""

    payload = ProjectAuditLog(
        project_id=project_id,
        event_type=event_type,
        baseline_seconds=max(int(baseline_seconds), 0),
        automated_seconds=max(int(automated_seconds), 0),
        accepted_suggestions=max(int(accepted_suggestions), 0),
        metadata=dict(metadata or {}),
    )
    session.add(payload)
    await session.flush()
    return payload


__all__ = ["record_project_event"]
