"""Cost API endpoints."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.database import get_session
from app.models.rkp import RefCostIndex

router = APIRouter(prefix="/costs", tags=["costs"])


@router.get("/indices/latest")
async def latest_index(
    series_name: str | None = Query(default=None),
    index_name: str | None = Query(default=None),
    jurisdiction: str = Query("SG"),
    provider: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    lookup_name = index_name or series_name
    if lookup_name is None:
        raise HTTPException(
            status_code=422, detail="series_name or index_name is required"
        )
    stmt = select(RefCostIndex).where(
        RefCostIndex.jurisdiction == jurisdiction,
        RefCostIndex.series_name == lookup_name,
    )
    if provider:
        stmt = stmt.where(RefCostIndex.provider == provider)

    result = await session.execute(stmt)
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Cost index not found")

    def sort_key(item: RefCostIndex) -> tuple[int, str]:
        period = item.period
        if period is None:
            return (1, "")
        return (0, str(period))

    record = max(rows, key=sort_key)
    return cast(dict[str, Any], record.as_dict())
