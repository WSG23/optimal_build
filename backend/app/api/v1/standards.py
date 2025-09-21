"""Standards API endpoints."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas import MaterialStandard
from app.services import standards as standards_service
from app.utils import metrics
from app.utils.logging import get_logger, log_event

router = APIRouter(prefix="/standards", tags=["standards"])
logger = get_logger(__name__)


@router.get("", response_model=List[MaterialStandard])
async def list_material_standards(
    standard_code: Optional[str] = Query(default=None),
    standard_body: Optional[str] = Query(default=None),
    material_type: Optional[str] = Query(default=None),
    section: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> List[MaterialStandard]:
    """Return material standards matching the provided filters."""

    metrics.REQUEST_COUNTER.labels(endpoint="standards_lookup").inc()
    records = await standards_service.lookup_material_standards(
        session,
        standard_code=standard_code,
        standard_body=standard_body,
        material_type=material_type,
        section=section,
    )
    log_event(
        logger,
        "standards_lookup_response",
        standard_code=standard_code,
        standard_body=standard_body,
        material_type=material_type,
        count=len(records),
    )
    return [MaterialStandard.model_validate(record, from_attributes=True) for record in records]
