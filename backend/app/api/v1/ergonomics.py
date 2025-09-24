"""API endpoints for ergonomics reference data."""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.database import get_session
from app.models.rkp import RefErgonomics
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

router = APIRouter(prefix="/ergonomics", tags=["ergonomics"])


@router.get("/")
async def list_ergonomics(
    metric_key: str | None = Query(default=None),
    population: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> List[Dict[str, Any]]:
    stmt = select(RefErgonomics)
    if metric_key:
        stmt = stmt.where(RefErgonomics.metric_key == metric_key)
    if population:
        stmt = stmt.where(RefErgonomics.population == population)

    result = await session.execute(stmt)
    return [record.as_dict() for record in result.scalars().all()]


__all__ = ["router"]
