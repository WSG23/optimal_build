"""Cost API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas import CostIndex
from app.services import costs as costs_service
from app.utils import metrics
from app.utils.logging import get_logger, log_event

router = APIRouter(prefix="/costs", tags=["costs"])
logger = get_logger(__name__)


@router.get("/indices/latest", response_model=CostIndex)
async def get_latest_index(
    series_name: str = Query(..., description="Cost index series name"),
    jurisdiction: str = Query("SG"),
    provider: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> CostIndex:
    """Return the latest cost index entry for the requested series."""

    metrics.REQUEST_COUNTER.labels(endpoint="cost_index_latest").inc()
    record = await costs_service.get_latest_cost_index(
        session,
        series_name=series_name,
        jurisdiction=jurisdiction,
        provider=provider,
    )
    if record is None:
        log_event(logger, "cost_index_not_found", series=series_name, jurisdiction=jurisdiction, provider=provider)
        raise HTTPException(status_code=404, detail="Cost index not found")

    log_event(
        logger,
        "cost_index_returned",
        series=series_name,
        jurisdiction=jurisdiction,
        provider=provider,
        period=record.period,
    )
    return CostIndex.model_validate(record, from_attributes=True)
