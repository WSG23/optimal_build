"""Helpers for resolving Advanced Intelligence request scope."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.projects import Project


@dataclass(frozen=True, slots=True)
class AnalyticsScope:
    """Resolved analytics scope for snapshot-backed routes."""

    scope_id: str
    project_id: str | None = None


async def resolve_analytics_scope(
    session: AsyncSession,
    *,
    project_id: str | None,
    workspace_id: str | None,
) -> AnalyticsScope:
    """Resolve a durable analytics scope key from route query params."""

    normalized_project_id = (project_id or "").strip()
    if normalized_project_id:
        project = await session.get(Project, normalized_project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{normalized_project_id}' was not found",
            )
        return AnalyticsScope(
            scope_id=f"project:{normalized_project_id}",
            project_id=normalized_project_id,
        )

    normalized_workspace_id = (workspace_id or "").strip()
    if normalized_workspace_id:
        return AnalyticsScope(scope_id=normalized_workspace_id)

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="projectId or workspaceId is required",
    )


__all__ = ["AnalyticsScope", "resolve_analytics_scope"]
