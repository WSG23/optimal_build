"""ROI analytics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.metrics import compute_project_roi


router = APIRouter(prefix="/roi", tags=["roi"])


@router.get("/{project_id}")
async def get_project_roi(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    """Return ROI metrics for the requested project."""

    snapshot = await compute_project_roi(session, project_id)
    return dict(snapshot.to_payload())


__all__ = ["router"]
