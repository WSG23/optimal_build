"""Flow utilities for synchronising vendor CSV product catalogues."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from prefect import flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.rkp import RefProduct

from .adapters import ProductRow, validate_csv

__all__ = [
    "sync_products_csv_once",
    "upsert_products",
    "mark_deprecated",
]


def _row_to_payload(vendor: str, row: ProductRow) -> dict[str, object]:
    name = row.name or " ".join(filter(None, (row.brand, row.model, row.sku))) or row.sku
    product_code = row.product_code or row.sku
    dimensions = {
        key: value
        for key, value in {
            "width_mm": row.width_mm,
            "depth_mm": row.depth_mm,
            "height_mm": row.height_mm,
        }.items()
        if value is not None
    }
    specifications = {
        key: value
        for key, value in {
            "weight_kg": row.weight_kg,
            "power_w": row.power_w,
        }.items()
        if value is not None
    }
    return {
        "vendor": vendor,
        "category": row.category,
        "product_code": product_code,
        "name": name,
        "brand": row.brand,
        "model_number": row.model,
        "sku": row.sku,
        "dimensions": dimensions,
        "specifications": specifications,
        "bim_uri": row.bim_uri,
        "spec_uri": row.spec_uri,
        "is_active": True,
    }


async def upsert_products(session: AsyncSession, vendor: str, rows: Sequence[ProductRow]) -> int:
    """Insert or update product rows for the given vendor."""

    count = 0
    for row in rows:
        payload = _row_to_payload(vendor, row)
        stmt = (
            select(RefProduct)
            .where(RefProduct.vendor == vendor)
            .where(RefProduct.sku == row.sku)
            .limit(1)
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            session.add(RefProduct(**payload))
        count += 1
    return count


async def mark_deprecated(session: AsyncSession, vendor: str, seen_skus: set[str]) -> int:
    """Mark vendor products as inactive when missing from the latest feed."""

    stmt = select(RefProduct).where(RefProduct.vendor == vendor)
    result = await session.execute(stmt)
    count = 0
    for product in result.scalars():
        if product.sku not in seen_skus and product.is_active:
            product.is_active = False
            count += 1
        elif product.sku in seen_skus and not product.is_active:
            product.is_active = True
    return count


@flow(name="sync_products_csv_once")
async def sync_products_csv_once(csv_path: str, vendor: str = "ikea") -> dict[str, object]:
    """Synchronise a vendor product CSV with the reference catalogue."""

    path = Path(csv_path)
    report, rows = validate_csv(path)
    if report.failed > 0:
        return {"ok": False, "report": report.model_dump()}

    async with AsyncSessionLocal() as session:
        inserted = await upsert_products(session, vendor, rows)
        await session.commit()
        deprecated = await mark_deprecated(session, vendor, {row.sku for row in rows})
        await session.commit()

    return {
        "ok": True,
        "inserted": inserted,
        "deprecated": deprecated,
        "report": report.model_dump(),
    }
