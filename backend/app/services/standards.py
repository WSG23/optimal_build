"""Services for working with reference material standards."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefMaterialStandard
from app.utils.logging import get_logger, log_event

logger = get_logger(__name__)


STANDARD_UPDATE_FIELDS: Iterable[str] = (
    "value",
    "unit",
    "context",
    "section",
    "applicability",
    "edition",
    "effective_date",
    "license_ref",
    "provenance",
    "source_document",
    "standard_body",
)


async def upsert_material_standard(
    session: AsyncSession, payload: dict[str, Any]
) -> RefMaterialStandard:
    """Insert or update a material standard entry."""

    filters = [
        RefMaterialStandard.standard_code == payload["standard_code"],
        RefMaterialStandard.material_type == payload["material_type"],
        RefMaterialStandard.property_key == payload["property_key"],
    ]

    if "section" in payload and payload["section"]:
        filters.append(RefMaterialStandard.section == payload["section"])
    if "edition" in payload and payload["edition"]:
        filters.append(RefMaterialStandard.edition == payload["edition"])

    stmt: Select[Any] = select(RefMaterialStandard).where(*filters).limit(1)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if record is None:
        record = RefMaterialStandard(**payload)
        session.add(record)
        action = "created"
    else:
        for field in STANDARD_UPDATE_FIELDS:
            if field in payload:
                setattr(record, field, payload[field])
        action = "updated"

    await session.flush()
    log_event(
        logger,
        "material_standard_upserted",
        action=action,
        standard_code=record.standard_code,
    )
    return record


async def lookup_material_standards(
    session: AsyncSession,
    *,
    standard_code: str | None = None,
    standard_body: str | None = None,
    material_type: str | None = None,
    section: str | None = None,
) -> list[RefMaterialStandard]:
    """Retrieve standards matching the provided filters."""

    stmt: Select[Any] = select(RefMaterialStandard)
    if standard_code:
        stmt = stmt.where(RefMaterialStandard.standard_code == standard_code)
    if standard_body:
        stmt = stmt.where(RefMaterialStandard.standard_body == standard_body)
    if material_type:
        stmt = stmt.where(RefMaterialStandard.material_type == material_type)
    if section:
        stmt = stmt.where(RefMaterialStandard.section == section)

    stmt = stmt.order_by(
        RefMaterialStandard.standard_code, RefMaterialStandard.property_key
    )
    results = await session.execute(stmt)
    records = list(results.scalars().all())
    log_event(
        logger,
        "material_standard_lookup",
        standard_code=standard_code,
        standard_body=standard_body,
        material_type=material_type,
        count=len(records),
    )
    return records
