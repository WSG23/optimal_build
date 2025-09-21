"""API endpoints for ergonomics reference data."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.rkp import RefErgonomics


router = APIRouter(prefix="/ergonomics")


@router.get("/")
async def list_ergonomics(
    session: AsyncSession = Depends(get_session),
) -> Dict[str, List[Dict[str, object]]]:
    result = await session.execute(select(RefErgonomics))
    items = [
        {
            "id": metric.id,
            "metric_key": metric.metric_key,
            "population": metric.population,
            "percentile": metric.percentile,
            "value": float(metric.value),
            "unit": metric.unit,
            "context": metric.context or {},
            "notes": metric.notes,
        }
        for metric in result.scalars().all()
    ]
    return {"items": items, "count": len(items)}


__all__ = ["router"]
