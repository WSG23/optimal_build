"""Project ROI metrics API."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.database import get_session
from app.core.metrics import RoiSnapshot, compute_project_roi
from pydantic import BaseModel

router = APIRouter(prefix="/roi", tags=["roi"])


class RoiMetricsResponse(BaseModel):
    """Response payload returned for ROI metric lookups."""

    project_id: int
    iterations: int
    total_suggestions: int
    decided_suggestions: int
    accepted_suggestions: int
    acceptance_rate: float
    review_hours_saved: float
    automation_score: float
    savings_percent: int
    payback_weeks: int
    baseline_hours: float
    actual_hours: float

    @classmethod
    def from_snapshot(cls, snapshot: RoiSnapshot) -> RoiMetricsResponse:
        return cls(**snapshot.as_dict())


@router.get("/{project_id}")
async def get_project_roi(
    project_id: int,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    """Return the ROI snapshot for the requested project."""

    snapshot = await compute_project_roi(session, project_id=project_id)
    payload = RoiMetricsResponse.from_snapshot(snapshot)
    return payload.model_dump(mode="json")


__all__ = ["router"]
