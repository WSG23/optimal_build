"""API endpoints for ergonomics reference data."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.database import get_session
from app.models.rkp import RefErgonomics

router = APIRouter(prefix="/ergonomics", tags=["ergonomics"])


@router.get("")
async def list_ergonomics(
    metric_key: str | None = Query(default=None),
    population: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    viewer: str = Depends(require_viewer),
) -> list[dict[str, Any]]:
    stmt = select(RefErgonomics)
    if metric_key:
        stmt = stmt.where(RefErgonomics.metric_key == metric_key)
    if population:
        stmt = stmt.where(RefErgonomics.population == population)

    result = await session.execute(stmt)
    return [record.as_dict() for record in result.scalars().all()]


@router.get("/", include_in_schema=False)
async def list_ergonomics_with_slash(
    metric_key: str | None = Query(default=None),
    population: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    viewer: str = Depends(require_viewer),
) -> list[dict[str, Any]]:
    return await list_ergonomics(
        metric_key=metric_key,
        population=population,
        session=session,
        viewer=viewer,
    )


__all__ = ["router"]
