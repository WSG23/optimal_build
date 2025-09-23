"""Prefect flow that syncs vendor product catalogues."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from prefect import flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.rkp import RefProduct
from app.services.products import VendorProduct, VendorProductAdapter


async def _upsert_product(
    session: AsyncSession,
    payload: Dict[str, Any],
) -> None:
    stmt = (
        select(RefProduct)
        .where(RefProduct.vendor == payload["vendor"])
        .where(RefProduct.product_code == payload["product_code"])
        .limit(1)
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.category = payload["category"]
        existing.name = payload["name"]
        existing.brand = payload.get("brand")
        existing.model_number = payload.get("model_number")
        existing.sku = payload.get("sku")
        existing.dimensions = payload.get("dimensions") or {}
        existing.specifications = payload.get("specifications") or {}
        existing.bim_uri = payload.get("bim_uri")
        existing.spec_uri = payload.get("spec_uri")
    else:
        session.add(RefProduct(**payload))


@flow(name="sync-vendor-products")
async def sync_vendor_products(
    session_factory: "async_sessionmaker[AsyncSession]",
    vendor_payload: Dict[str, Any],
    *,
    adapter: Optional[VendorProductAdapter] = None,
) -> List[Dict[str, Any]]:
    """Ingest a vendor payload into the ``ref_products`` table."""

    vendor_name = str(vendor_payload.get("vendor") or "unknown")
    if adapter is None:
        adapter = VendorProductAdapter(vendor_name)
    products: Iterable[VendorProduct] = adapter.transform(vendor_payload)

    as_dicts: List[Dict[str, Any]] = []
    async with session_factory() as session:
        for product in products:
            data = product.as_orm_kwargs()
            as_dicts.append(data)
            await _upsert_product(session, data)
        await session.commit()
    return as_dicts


__all__ = ["sync_vendor_products"]
