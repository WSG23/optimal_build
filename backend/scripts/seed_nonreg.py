"""Seed reference tables for non-regulatory datasets."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import structlog

from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseModel
from app.models.rkp import RefCostIndex, RefErgonomics, RefMaterialStandard
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

SEED_ROOT = Path(__file__).parent / "seeds"
ERGONOMICS_SEED = SEED_ROOT / "ergonomics_seed.json"
STANDARDS_SEED = SEED_ROOT / "standards_seed.json"
COST_INDEX_SEED = SEED_ROOT / "cost_index_seed.json"


logger = structlog.get_logger(__name__)


@dataclass
class NonRegSeedSummary:
    """Counts of seeded non-regulatory reference records."""

    ergonomics: int = 0
    standards: int = 0
    cost_indices: int = 0

    def as_dict(self) -> dict[str, int]:
        """Represent the seeded counts as a dictionary."""

        return {
            "ergonomics": self.ergonomics,
            "standards": self.standards,
            "cost_indices": self.cost_indices,
        }


def _load_seed_file(path: Path) -> list[dict[str, Any]]:
    """Load a JSON seed file into Python dictionaries."""

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, list):
        return [dict(item) for item in payload]

    raise ValueError(f"Seed file {path} must contain a JSON array.")


def _parse_date(value: Any) -> date | None:
    """Convert an ISO formatted string into a :class:`date`."""

    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise TypeError(f"Unsupported date value: {value!r}")


def _to_decimal(value: Any, places: int | None = None) -> Decimal:
    """Convert numeric input into a :class:`Decimal` with optional rounding."""

    if isinstance(value, Decimal):
        result = value
    else:
        try:
            result = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid decimal value: {value!r}") from exc

    if places is not None:
        quantiser = Decimal("1") if places == 0 else Decimal(f"1.{'0' * places}")
        result = result.quantize(quantiser, rounding=ROUND_HALF_UP)
    return result


def _prepare_ergonomics(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise ergonomics payloads for insertion/upsert."""

    prepared: list[dict[str, Any]] = []
    for record in records:
        metric = dict(record)
        if "metric_key" not in metric or "population" not in metric:
            raise KeyError(
                "Ergonomics seed entries require 'metric_key' and 'population'."
            )
        if "value" in metric:
            metric["value"] = _to_decimal(metric["value"], places=2)
        metric.setdefault("context", {})
        prepared.append(metric)
    return prepared


def _prepare_standards(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise material standard payloads."""

    prepared: list[dict[str, Any]] = []
    for record in records:
        entry = dict(record)
        entry.setdefault("jurisdiction", "SG")
        entry.setdefault("material_type", "general")
        entry.setdefault("applicability", {})
        entry.setdefault("provenance", {})
        if "effective_date" in entry:
            entry["effective_date"] = _parse_date(entry.get("effective_date"))
        prepared.append(entry)
    return prepared


def _prepare_cost_indices(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise cost index payloads."""

    prepared: list[dict[str, Any]] = []
    for record in records:
        entry = dict(record)
        entry.setdefault("jurisdiction", "SG")
        entry.setdefault("provider", "internal")
        if "series_name" not in entry:
            index_name = entry.get("index_name")
            if not index_name:
                raise KeyError(
                    "Cost index seed entries require 'series_name' or 'index_name'."
                )
            entry["series_name"] = index_name
        entry.pop("index_name", None)
        entry.setdefault("category", "composite")
        if "value" in entry:
            entry["value"] = _to_decimal(entry["value"], places=4)
        prepared.append(entry)
    return prepared


async def _upsert_ergonomics(
    session: AsyncSession, metrics: Iterable[dict[str, Any]]
) -> int:
    processed = 0
    for metric in metrics:
        stmt: Select[RefErgonomics] = (
            select(RefErgonomics)
            .where(RefErgonomics.metric_key == metric["metric_key"])
            .where(RefErgonomics.population == metric["population"])
            .limit(1)
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.percentile = metric.get("percentile")
            existing.value = metric.get("value")
            existing.unit = metric.get("unit")
            existing.context = metric.get("context") or {}
            existing.notes = metric.get("notes")
            existing.source = metric.get("source")
        else:
            session.add(RefErgonomics(**metric))
        processed += 1
    return processed


async def _upsert_standards(
    session: AsyncSession, standards: Iterable[dict[str, Any]]
) -> int:
    processed = 0
    for payload in standards:
        stmt: Select[RefMaterialStandard] = select(RefMaterialStandard).where(
            RefMaterialStandard.standard_code == payload["standard_code"],
            RefMaterialStandard.material_type == payload["material_type"],
            RefMaterialStandard.property_key == payload["property_key"],
        )
        if payload.get("section"):
            stmt = stmt.where(RefMaterialStandard.section == payload["section"])
        if payload.get("edition"):
            stmt = stmt.where(RefMaterialStandard.edition == payload["edition"])
        stmt = stmt.limit(1)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.value = payload.get("value")
            existing.unit = payload.get("unit")
            existing.context = payload.get("context")
            existing.section = payload.get("section")
            existing.applicability = payload.get("applicability")
            existing.edition = payload.get("edition")
            existing.effective_date = payload.get("effective_date")
            existing.license_ref = payload.get("license_ref")
            existing.provenance = payload.get("provenance")
            existing.source_document = payload.get("source_document")
            existing.standard_body = payload.get("standard_body")
            existing.jurisdiction = payload.get("jurisdiction", existing.jurisdiction)
        else:
            session.add(RefMaterialStandard(**payload))
        processed += 1
    return processed


async def _upsert_cost_indices(
    session: AsyncSession, indices: Iterable[dict[str, Any]]
) -> int:
    processed = 0
    for payload in indices:
        stmt: Select[RefCostIndex] = select(RefCostIndex).where(
            RefCostIndex.jurisdiction == payload["jurisdiction"],
            RefCostIndex.series_name == payload["series_name"],
            RefCostIndex.period == payload["period"],
            RefCostIndex.provider == payload.get("provider", "internal"),
        )
        stmt = stmt.limit(1)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.category = payload.get("category")
            existing.subcategory = payload.get("subcategory")
            existing.value = payload.get("value")
            existing.unit = payload.get("unit")
            existing.source = payload.get("source")
            existing.methodology = payload.get("methodology")
        else:
            session.add(RefCostIndex(**payload))
        processed += 1
    return processed


async def seed_nonregulated_reference_data(
    session: AsyncSession,
    *,
    commit: bool = True,
) -> NonRegSeedSummary:
    """Seed ergonomics, standards, and cost index reference tables."""

    ergonomics_payload = _prepare_ergonomics(_load_seed_file(ERGONOMICS_SEED))
    standards_payload = _prepare_standards(_load_seed_file(STANDARDS_SEED))
    cost_index_payload = _prepare_cost_indices(_load_seed_file(COST_INDEX_SEED))

    summary = NonRegSeedSummary()
    if ergonomics_payload:
        summary.ergonomics = await _upsert_ergonomics(session, ergonomics_payload)
    if standards_payload:
        summary.standards = await _upsert_standards(session, standards_payload)
    if cost_index_payload:
        summary.cost_indices = await _upsert_cost_indices(session, cost_index_payload)

    if commit:
        await session.commit()

    return summary


async def ensure_schema() -> None:
    """Ensure tables exist before seeding data."""

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


async def _cli_main() -> NonRegSeedSummary:
    await ensure_schema()
    async with AsyncSessionLocal() as session:
        summary = await seed_nonregulated_reference_data(session, commit=True)
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed non-regulatory reference tables."
    )
    return parser


def main(argv: Sequence[str] | None = None) -> NonRegSeedSummary:
    """Entry point for command-line execution."""

    parser = _build_parser()
    parser.parse_args(argv)
    summary = asyncio.run(_cli_main())
    logger.info(
        "seed_nonreg.summary",
        ergonomics=summary.ergonomics,
        standards=summary.standards,
        cost_indices=summary.cost_indices,
    )
    return summary


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()


__all__ = [
    "NonRegSeedSummary",
    "seed_nonregulated_reference_data",
    "ensure_schema",
    "main",
]
