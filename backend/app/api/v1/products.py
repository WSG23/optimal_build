"""API endpoints for reference products."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.rkp import RefProduct


router = APIRouter(prefix="/products")


@router.get("/")
async def list_products(
    session: AsyncSession = Depends(get_session),
) -> Dict[str, List[Dict[str, object]]]:
    result = await session.execute(select(RefProduct))
    items = [
        {
            "id": product.id,
            "vendor": product.vendor,
            "category": product.category,
            "product_code": product.product_code,
            "name": product.name,
            "brand": product.brand,
            "model_number": product.model_number,
            "sku": product.sku,
            "dimensions": product.dimensions or {},
            "bim_uri": product.bim_uri,
            "spec_uri": product.spec_uri,
        }
        for product in result.scalars().all()
    ]
    return {"items": items, "count": len(items)}


__all__ = ["router"]
