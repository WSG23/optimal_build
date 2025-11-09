"""Services for cost index and catalog data."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.models.rkp import RefCostCatalog, RefCostIndex
from app.utils.logging import get_logger, log_event
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


COST_INDEX_UPDATE_FIELDS: Iterable[str] = (
    "value",
    "unit",
    "source",
    "category",
    "subcategory",
    "provider",
    "methodology",
)


async def upsert_cost_index(
    session: AsyncSession, payload: dict[str, Any]
) -> RefCostIndex:
    """Insert or update a cost index value."""

    stmt: Select[Any] = (
        select(RefCostIndex)
        .where(
            RefCostIndex.jurisdiction == payload.get("jurisdiction", "SG"),
            RefCostIndex.series_name == payload["series_name"],
            RefCostIndex.period == payload["period"],
        )
        .limit(1)
    )

    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if record is None:
        record = RefCostIndex(**payload)
        session.add(record)
        action = "created"
    else:
        for field in COST_INDEX_UPDATE_FIELDS:
            if field in payload:
                setattr(record, field, payload[field])
        action = "updated"

    await session.flush()
    log_event(
        logger,
        "cost_index_upserted",
        action=action,
        series=record.series_name,
        period=record.period,
    )
    return record


async def get_latest_cost_index(
    session: AsyncSession,
    *,
    series_name: str,
    jurisdiction: str = "SG",
    provider: str | None = None,
) -> RefCostIndex | None:
    """Retrieve the latest cost index entry for the given series."""

    stmt: Select[Any] = select(RefCostIndex).where(
        RefCostIndex.series_name == series_name,
        RefCostIndex.jurisdiction == jurisdiction,
    )
    if provider:
        stmt = stmt.where(RefCostIndex.provider == provider)

    stmt = stmt.order_by(RefCostIndex.period.desc())
    result = await session.execute(stmt.limit(1))
    record = result.scalar_one_or_none()
    log_event(
        logger,
        "cost_index_lookup",
        series=series_name,
        jurisdiction=jurisdiction,
        provider=provider,
        found=record is not None,
    )
    return record


async def add_cost_catalog_item(
    session: AsyncSession, payload: dict[str, Any]
) -> RefCostCatalog:
    """Insert a new entry in the cost catalog."""

    record = RefCostCatalog(**payload)
    session.add(record)
    await session.flush()
    log_event(
        logger,
        "cost_catalog_item_added",
        catalog=record.catalog_name,
        item_code=record.item_code,
    )
    return record


async def list_cost_catalog(
    session: AsyncSession,
    *,
    catalog_name: str | None = None,
    category: str | None = None,
) -> list[RefCostCatalog]:
    """List catalog entries with optional filters."""

    stmt: Select[Any] = select(RefCostCatalog)
    if catalog_name:
        stmt = stmt.where(RefCostCatalog.catalog_name == catalog_name)
    if category:
        stmt = stmt.where(RefCostCatalog.category == category)

    result = await session.execute(stmt.order_by(RefCostCatalog.item_code))
    entries = list(result.scalars().all())
    log_event(
        logger,
        "cost_catalog_listed",
        catalog=catalog_name,
        category=category,
        count=len(entries),
    )
    return entries
