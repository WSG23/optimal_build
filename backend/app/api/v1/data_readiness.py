"""Data readiness endpoints for production Capture source datasets."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.database import get_session
from app.services.capture_data_readiness import get_capture_data_readiness

router = APIRouter(prefix="/data-readiness", tags=["data-readiness"])


@router.get("/capture")
async def capture_data_readiness(
    jurisdiction: str = Query(default="SG", min_length=2, max_length=10),
    session: AsyncSession = Depends(get_session),
    _: object = Depends(require_viewer),
) -> dict[str, Any]:
    """Return whether Capture can use official source data for a jurisdiction."""

    readiness = await get_capture_data_readiness(session, jurisdiction=jurisdiction)
    return cast(dict[str, Any], readiness)
