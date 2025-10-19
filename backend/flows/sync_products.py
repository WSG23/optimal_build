"""Prefect flow for syncing vendor product CSV files."""

from __future__ import annotations

import datetime as dt
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from prefect import flow, task

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.flows.adapters.products_csv_validator import ProductRow, validate_csv

from app.core.database import AsyncSessionLocal
from app.models.rkp import RefProduct


def _table_column_names() -> set[str]:
    """Return the set of column names available on :class:`RefProduct`."""

    mapped = getattr(RefProduct, "__mapped_columns__", None)
    if mapped:
        return set(mapped.keys())
    table = getattr(RefProduct, "__table__", None)
    if (
        table is None
    ):  # pragma: no cover - defensive; RefProduct is declarative in practice
        return set()
    if hasattr(table, "columns"):
        return {column.name for column in table.columns}
    if hasattr(table, "c"):
        return set(table.c.keys())
    return set()


def _normalise_optional_url(value: str | None) -> str | None:
    """Convert optional URL values to plain strings."""

    if value is None:
        return None
    return str(value)


def _build_product_values(
    row: ProductRow, vendor: str, now: dt.datetime
) -> dict[str, object]:
    """Construct a mapping of column values for a ``RefProduct`` upsert."""

    columns = _table_column_names()
    values: dict[str, object] = {}

    def maybe_set(column: str, value: object) -> None:
        if column in columns:
            values[column] = value

    maybe_set("vendor", vendor)
    maybe_set("brand", row.brand)
    if "model" in columns:
        maybe_set("model", row.model)
    else:
        maybe_set("model_number", row.model)
    maybe_set("sku", row.sku)
    if "product_code" in columns and "sku" not in columns:
        maybe_set("product_code", row.sku)
    maybe_set("category", row.category)

    dimensions = {
        "width_mm": int(row.width_mm),
        "depth_mm": int(row.depth_mm),
        "height_mm": int(row.height_mm),
    }
    if "dimensions" in columns:
        maybe_set("dimensions", dimensions)
    else:
        for key, value in dimensions.items():
            maybe_set(key, value)

    if "weight_kg" in columns:
        maybe_set(
            "weight_kg", float(row.weight_kg) if row.weight_kg is not None else None
        )
    if "power_w" in columns:
        maybe_set("power_w", float(row.power_w) if row.power_w is not None else None)
    maybe_set("bim_uri", _normalise_optional_url(row.bim_uri))
    maybe_set("spec_uri", _normalise_optional_url(row.spec_uri))
    maybe_set("data_source", "csv")
    if "last_synced_at" in columns:
        maybe_set("last_synced_at", now)
    if "deprecated_at" in columns:
        maybe_set("deprecated_at", None)
    if "is_active" in columns:
        maybe_set("is_active", True)

    return values


def _sku_filters(vendor: str) -> tuple[list, dict[str, object]]:
    """Return filters and additional insert defaults for vendor-aware lookups."""

    columns = _table_column_names()
    filters = []
    defaults: dict[str, object] = {}

    if "vendor" in columns:
        filters.append(RefProduct.vendor == vendor)
        defaults["vendor"] = vendor
    if "data_source" in columns:
        filters.append(RefProduct.data_source == "csv")
        defaults["data_source"] = "csv"

    return filters, defaults


def _resolve_sku(row: RefProduct) -> str | None:
    """Extract the SKU identifier from a ``RefProduct`` instance."""

    if hasattr(row, "sku") and row.sku is not None:
        return str(row.sku)
    if hasattr(row, "product_code") and row.product_code is not None:
        return str(row.product_code)
    return None


@task
async def upsert_products(
    session: AsyncSession, vendor: str, rows: Sequence[ProductRow]
) -> int:
    """Insert or update rows in the ``ref_products`` table."""

    now = dt.datetime.now(dt.UTC)
    count = 0

    sku_column_name = "sku" if "sku" in _table_column_names() else "product_code"
    sku_column = getattr(RefProduct, sku_column_name)

    filters, defaults = _sku_filters(vendor)

    for row in rows:
        stmt = select(RefProduct).where(sku_column == row.sku, *filters)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        values = _build_product_values(row, vendor, now)
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            payload = {**defaults, **values}
            instance = RefProduct(**payload)
            session.add(instance)
        count += 1
    return count


@task
async def mark_deprecated(
    session: AsyncSession, vendor: str, seen_skus: Iterable[str]
) -> int:
    """Mark products as deprecated when they disappear from the feed."""

    seen = {str(sku) for sku in seen_skus}
    filters, _ = _sku_filters(vendor)
    stmt = select(RefProduct).where(*filters)
    result = await session.execute(stmt)
    rows = result.scalars().all()

    now = dt.datetime.now(dt.UTC)
    count = 0
    has_deprecated_at = "deprecated_at" in _table_column_names()
    has_is_active = "is_active" in _table_column_names()

    for row in rows:
        sku = _resolve_sku(row)
        if sku in seen:
            continue
        if has_deprecated_at and getattr(row, "deprecated_at", None) is not None:
            continue
        if has_is_active and getattr(row, "is_active", True) is False:
            continue

        if has_deprecated_at:
            row.deprecated_at = now
        if has_is_active:
            row.is_active = False
        session.add(row)
        count += 1
    return count


@flow(name="sync_products_csv_once")
async def sync_products_csv_once(
    csv_path: str,
    vendor: str = "ikea",
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> dict[str, object]:
    """Validate a CSV file and upsert its contents into ``ref_products``."""

    path = Path(csv_path)
    report, rows = validate_csv(path)
    if report.failed > 0:
        return {"ok": False, "report": report.model_dump()}

    factory = session_factory or AsyncSessionLocal
    rows_list = list(rows)
    async with factory() as session:
        upsert_callable = getattr(upsert_products, "fn", upsert_products)
        mark_callable = getattr(mark_deprecated, "fn", mark_deprecated)
        inserted = await upsert_callable(session, vendor, rows_list)
        await session.commit()
        deprecated = await mark_callable(
            session, vendor, {row.sku for row in rows_list}
        )
        await session.commit()
    return {
        "ok": True,
        "inserted": inserted,
        "deprecated": deprecated,
        "report": report.model_dump(),
    }


__all__ = ["sync_products_csv_once", "upsert_products", "mark_deprecated"]
