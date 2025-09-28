"""API endpoints for reference products."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.database import get_session
from app.models.rkp import RefProduct

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/")
async def list_products(
    brand: str | None = Query(default=None),
    category: str | None = Query(default=None),
    width_mm_min: int | None = Query(default=None),
    width_mm_max: int | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> list[dict[str, Any]]:
    stmt = select(RefProduct)
    if brand:
        stmt = stmt.where(RefProduct.brand == brand)
    if category:
        stmt = stmt.where(RefProduct.category == category)

    result = await session.execute(stmt)
    items: list[dict[str, Any]] = []
    for product in result.scalars().all():
        dimensions = product.dimensions or {}
        width_value = dimensions.get("width_mm")
        width: float | None
        try:
            width = float(width_value) if width_value is not None else None
        except (TypeError, ValueError):
            width = None

        if width_mm_min is not None and (width is None or width < width_mm_min):
            continue
        if width_mm_max is not None and (width is None or width > width_mm_max):
            continue

        items.append(product.as_dict())

    return items


__all__ = ["router"]
