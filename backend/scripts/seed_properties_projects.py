"""Seed sample properties and projects for API testing."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Sequence
from uuid import UUID, uuid4

import structlog
from app.core.database import AsyncSessionLocal, engine
from app.models.projects import Project, ProjectPhase, ProjectType
from app.models.property import Property, PropertyStatus, PropertyType, TenureType
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


@dataclass
class SeedSummary:
    """Summary of seeded property/project rows."""

    projects: int
    properties: int

    def as_dict(self) -> dict[str, int]:
        return {"projects": self.projects, "properties": self.properties}


_PROPERTIES: Sequence[dict[str, object]] = (
    {
        "id": UUID("d47174ee-bb6f-4f3f-8baa-141d7c5d9051"),
        "name": "Market Demo Tower",
        "address": "1 Demo Way, Singapore",
        "postal_code": "049999",
        "property_type": PropertyType.OFFICE,
        "status": PropertyStatus.EXISTING,
        "district": "D01",
        "planning_area": "Downtown Core",
        "land_area_sqm": Decimal("4500"),
        "gross_floor_area_sqm": Decimal("52000"),
        "net_lettable_area_sqm": Decimal("48000"),
        "building_height_m": Decimal("210"),
        "floors_above_ground": 45,
        "units_total": 25,
        "year_built": 2018,
        "tenure_type": TenureType.LEASEHOLD_99,
        "lease_start_date": date(2015, 7, 1),
        "lease_expiry_date": date(2114, 6, 30),
        "zoning_code": "C1",
        "plot_ratio": Decimal("11.5"),
        "data_source": "seed_properties",
    },
    {
        "id": uuid4(),
        "name": "Harbourfront Business Hub",
        "address": "23 Harbour Road, Singapore",
        "postal_code": "099100",
        "property_type": PropertyType.MIXED_USE,
        "status": PropertyStatus.EXISTING,
        "location": "POINT(103.8225 1.2650)",
        "district": "D04",
        "planning_area": "HarbourFront",
        "land_area_sqm": Decimal("12000"),
        "gross_floor_area_sqm": Decimal("86000"),
        "net_lettable_area_sqm": Decimal("79000"),
        "building_height_m": Decimal("180"),
        "floors_above_ground": 38,
        "units_total": 42,
        "year_built": 2012,
        "tenure_type": TenureType.LEASEHOLD_99,
        "lease_start_date": date(2010, 4, 1),
        "lease_expiry_date": date(2109, 3, 31),
        "zoning_code": "B1",
        "plot_ratio": Decimal("2.5"),
        "data_source": "seed_properties",
    },
)


_PROJECTS: Sequence[dict[str, object]] = (
    {
        "id": uuid4(),
        "project_name": "Marina Waterfront Redevelopment",
        "project_code": "MWR-2025",
        "description": "Mixed-use redevelopment with residential and office towers.",
        "owner_email": "planner@example.com",
        "project_type": ProjectType.REDEVELOPMENT,
        "current_phase": ProjectPhase.DESIGN,
        "estimated_cost_sgd": Decimal("850000000"),
    },
)


async def _purge_existing(session: AsyncSession) -> None:
    await session.execute(
        delete(Property).where(Property.data_source == "seed_properties")
    )
    await session.execute(
        delete(Project).where(Project.project_code.in_(["FIN-DEMO-191", "MWR-2025"]))
    )
    await session.commit()


async def seed_properties_and_projects(
    session: AsyncSession,
    *,
    reset_existing: bool = True,
) -> SeedSummary:
    if reset_existing:
        await _purge_existing(session)

    # Seed projects first to ensure foreign-key references are valid
    project_count = 0
    for payload in _PROJECTS:
        if "id" in payload:
            existing_by_id = await session.get(Project, payload["id"])
            if existing_by_id:
                continue
        existing = await session.execute(
            select(Project).where(Project.project_code == payload["project_code"])
        )
        if existing.scalar_one_or_none():
            continue
        record = Project(
            project_name=payload["project_name"],
            project_code=payload["project_code"],
            description=payload.get("description"),
            owner_email=payload.get("owner_email"),
            project_type=payload["project_type"],
            current_phase=payload.get("current_phase"),
            estimated_cost_sgd=payload.get("estimated_cost_sgd"),
        )
        if "id" in payload:
            record.id = payload["id"]
        session.add(record)
        project_count += 1

    # Seed properties
    property_count = 0
    for payload in _PROPERTIES:
        existing = await session.get(Property, payload["id"])
        if existing:
            continue
        property_payload = dict(payload)
        record = Property(**property_payload)
        session.add(record)
        property_count += 1

    await session.commit()
    return SeedSummary(projects=project_count, properties=property_count)


async def _run_async(reset_existing: bool) -> SeedSummary:
    async with engine.begin() as conn:
        await conn.run_sync(Property.metadata.create_all)

    async with AsyncSessionLocal() as session:
        summary = await seed_properties_and_projects(
            session, reset_existing=reset_existing
        )
        return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed sample properties and projects.")
    parser.add_argument(
        "--reset", action="store_true", help="Purge existing demo data before seeding"
    )
    return parser


def main(argv: list[str] | None = None) -> SeedSummary:
    parser = build_parser()
    args = parser.parse_args(argv)
    summary = asyncio.run(_run_async(reset_existing=args.reset))
    logger.info("seed_properties_projects.summary", **summary.as_dict())
    return summary


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
