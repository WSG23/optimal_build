"""Standards API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_viewer
from app.core.database import get_session
from app.models.rkp import RefMaterialStandard
from app.utils import metrics
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["standards"])


@router.get("/standards")
async def list_standards(
    property_key: str | None = Query(default=None),
    standard_body: str | None = Query(default=None),
    standard_code: str | None = Query(default=None),
    section: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> list[dict[str, Any]]:
    metrics.REQUEST_COUNTER.labels(endpoint="standards_lookup").inc()
    stmt = select(RefMaterialStandard)
    if property_key:
        stmt = stmt.where(RefMaterialStandard.property_key == property_key)
    if standard_body:
        stmt = stmt.where(RefMaterialStandard.standard_body == standard_body)
    if standard_code:
        stmt = stmt.where(RefMaterialStandard.standard_code == standard_code)
    if section:
        stmt = stmt.where(RefMaterialStandard.section == section)

    result = await session.execute(stmt)
    return [record.as_dict() for record in result.scalars().all()]
