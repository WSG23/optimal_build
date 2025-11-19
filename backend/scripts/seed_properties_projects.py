"""Seed sample properties and projects for API testing."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Sequence
from uuid import UUID, uuid4

import structlog

from app.core.database import AsyncSessionLocal, engine
from app.models.developer_checklists import DeveloperChecklistTemplate
from app.models.market import YieldBenchmark
from app.models.projects import ProjectPhase, ProjectType
from app.models.property import (
    DevelopmentAnalysis,
    MarketTransaction,
    Property,
    PropertyStatus,
    PropertyType,
    TenureType,
)
from app.services.developer_checklist_service import DeveloperChecklistService
from sqlalchemy import String, cast, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MARKET_DEMO_PROPERTY_ID = UUID("d47174ee-bb6f-4f3f-8baa-141d7c5d9051")


@dataclass
class SeedSummary:
    """Summary of seeded property/project rows."""

    projects: int
    properties: int
    developer_checklists: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "projects": self.projects,
            "properties": self.properties,
            "developer_checklists": self.developer_checklists,
        }


_PROPERTIES: Sequence[dict[str, object]] = (
    {
        "id": UUID("d47174ee-bb6f-4f3f-8baa-141d7c5d9051"),
        "name": "Market Demo Tower",
        "address": "1 Demo Way, Singapore",
        "postal_code": "049999",
        "jurisdiction_code": "SG",
        "location": "SRID=4326;POINT(103.8198 1.2894)",
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
        "jurisdiction_code": "SG",
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
    {
        "id": UUID("88a5b6d4-2d25-4ff1-a549-7bbd2d5e81c2"),
        "name": "Central Harbour Gateway",
        "address": "1 Connaught Place, Central, Hong Kong",
        "postal_code": "HK0001",
        "jurisdiction_code": "HK",
        "property_type": PropertyType.MIXED_USE,
        "status": PropertyStatus.EXISTING,
        "location": "SRID=4326;POINT(114.1589 22.2854)",
        "district": "Central and Western",
        "planning_area": "Central District",
        "land_area_sqm": Decimal("7500"),
        "gross_floor_area_sqm": Decimal("82000"),
        "net_lettable_area_sqm": Decimal("72000"),
        "building_height_m": Decimal("230"),
        "floors_above_ground": 50,
        "units_total": 30,
        "year_built": 2016,
        "tenure_type": TenureType.FREEHOLD,
        "zoning_code": "RA/HK/001",
        "plot_ratio": Decimal("10.0"),
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
    for payload in _PROPERTIES:
        property_id = payload["id"]
        property_type = payload.get("property_type")
        district = payload.get("district")

        await session.execute(
            delete(MarketTransaction).where(
                MarketTransaction.property_id == property_id
            )
        )
        await session.execute(
            delete(DevelopmentAnalysis).where(
                DevelopmentAnalysis.property_id == property_id
            )
        )
        if district and property_type:
            property_type_value = (
                property_type.value
                if hasattr(property_type, "value")
                else str(property_type)
            )
            await session.execute(
                delete(YieldBenchmark).where(
                    YieldBenchmark.district == district,
                    cast(YieldBenchmark.property_type, String) == property_type_value,
                )
            )

    await session.execute(
        delete(Property).where(Property.data_source == "seed_properties")
    )

    # NOTE: Skip purging projects until schema updated with required columns
    # await session.execute(
    #     delete(Project).where(Project.project_code.in_(["FIN-DEMO-191", "MWR-2025"]))
    # )
    await session.commit()


async def _seed_market_demo_enrichments(session: AsyncSession) -> None:
    """Populate development analyses, transactions, and benchmarks for demo tower."""

    property_record = await session.get(Property, MARKET_DEMO_PROPERTY_ID)
    if property_record is None:
        return

    # Development analysis (only seed once)
    existing_analysis = await session.execute(
        select(DevelopmentAnalysis).where(
            DevelopmentAnalysis.property_id == MARKET_DEMO_PROPERTY_ID
        )
    )
    if existing_analysis.scalars().first() is None:
        session.add(
            DevelopmentAnalysis(
                property_id=MARKET_DEMO_PROPERTY_ID,
                analysis_type="existing_building",
                analysis_date=datetime(2025, 9, 15, 9, 0, 0),
                gfa_potential_sqm=Decimal("58000"),
                optimal_use_mix={"office": 0.62, "retail": 0.25, "amenities": 0.13},
                market_value_estimate=Decimal("365000000"),
                projected_cap_rate=Decimal("0.043"),
                site_constraints=[
                    "Setback requirements along Demo Way frontage",
                    "Loading/unloading bay access limited to 2 entrances",
                ],
                regulatory_constraints={"plot_ratio_cap": 12.0},
                development_opportunities=[
                    "Convert podium levels to lifestyle retail cluster",
                    "Introduce wellness floors to lift blended rents",
                ],
                value_add_potential={"noi_uplift_pct": 0.12},
                development_scenarios=[
                    {
                        "name": "Premium Grade A repositioning",
                        "gfa": 52000,
                        "estimated_cost": 42000000,
                        "target_rent_psf": 14.2,
                    },
                    {
                        "name": "Flex office + hospitality hybrid",
                        "gfa": 50500,
                        "estimated_cost": 38000000,
                        "target_rent_psf": 13.6,
                    },
                ],
                recommended_scenario="Premium Grade A repositioning",
                assumptions={
                    "fit_out_cost_psf": 95,
                    "downtime_months": 6,
                    "stabilized_occupancy_pct": 94,
                },
                methodology="market_comparables",
                confidence_level=Decimal("0.82"),
            )
        )

    # Comparable transactions (seed if none)
    existing_transactions = await session.execute(
        select(MarketTransaction).where(
            MarketTransaction.property_id == MARKET_DEMO_PROPERTY_ID
        )
    )
    if existing_transactions.scalars().first() is None:
        transaction_payloads = [
            {
                "transaction_date": date(2025, 6, 20),
                "sale_price": Decimal("78500000"),
                "psf_price": Decimal("2780"),
                "buyer_type": "institutional",
                "market_segment": "CBD",
            },
            {
                "transaction_date": date(2025, 4, 18),
                "sale_price": Decimal("76400000"),
                "psf_price": Decimal("2710"),
                "buyer_type": "reit",
                "market_segment": "CBD",
            },
            {
                "transaction_date": date(2025, 1, 27),
                "sale_price": Decimal("74250000"),
                "psf_price": Decimal("2650"),
                "buyer_type": "family_office",
                "market_segment": "CBD",
            },
        ]

        for payload in transaction_payloads:
            session.add(
                MarketTransaction(
                    property_id=MARKET_DEMO_PROPERTY_ID,
                    transaction_date=payload["transaction_date"],
                    transaction_type="sale",
                    sale_price=payload["sale_price"],
                    psf_price=payload["psf_price"],
                    buyer_type=payload["buyer_type"],
                    market_segment=payload["market_segment"],
                    data_source="seed_properties",
                )
            )

    property_type_value = PropertyType.OFFICE.value
    existing_benchmarks = await session.execute(
        select(YieldBenchmark).where(
            YieldBenchmark.district == (property_record.district or "D01"),
            cast(YieldBenchmark.property_type, String) == property_type_value,
        )
    )
    if existing_benchmarks.scalars().first() is None:
        benchmark_dates = [date(2025, month, 1) for month in range(1, 7)]
        for idx, benchmark_date in enumerate(benchmark_dates):
            session.add(
                YieldBenchmark(
                    benchmark_date=benchmark_date,
                    period_type="monthly",
                    country="Singapore",
                    district=property_record.district or "D01",
                    location_tier="prime",
                    property_type=PropertyType.OFFICE,
                    property_grade="A",
                    cap_rate_mean=Decimal("0.044") + Decimal(idx) * Decimal("0.0003"),
                    cap_rate_median=Decimal("0.043") + Decimal(idx) * Decimal("0.0002"),
                    cap_rate_p25=Decimal("0.041"),
                    cap_rate_p75=Decimal("0.046"),
                    rental_yield_mean=Decimal("0.039"),
                    rental_yield_median=Decimal("0.0385"),
                    rental_psf_mean=Decimal("11.80") + Decimal(idx) * Decimal("0.10"),
                    rental_psf_median=Decimal("11.60") + Decimal(idx) * Decimal("0.10"),
                    occupancy_rate_mean=Decimal("0.935"),
                    vacancy_rate_mean=Decimal("0.065"),
                    sale_psf_mean=Decimal("2950") + Decimal(idx) * Decimal("15"),
                    sale_psf_median=Decimal("2900") + Decimal(idx) * Decimal("15"),
                    transaction_count=48 + idx * 2,
                    total_transaction_value=Decimal("320000000")
                    + Decimal(idx) * Decimal("4500000"),
                    sample_size=62 + idx,
                    data_quality_score=Decimal("0.82"),
                    data_sources=["seed_properties"],
                )
            )


async def _seed_developer_checklists(
    session: AsyncSession, property_ids: Sequence[UUID]
) -> int:
    """Ensure developer checklist templates and property items exist."""
    if not property_ids:
        return 0

    result = await session.execute(
        select(DeveloperChecklistTemplate.development_scenario).distinct()
    )
    scenario_keys = sorted(row[0] for row in result.all() if row[0])
    if not scenario_keys:
        logger.warning(
            "seed_properties_projects.developer_checklists.undefined_scenarios"
        )
        return 0

    total_created = 0
    for property_id in property_ids:
        property_record = await session.get(Property, property_id)
        if property_record is None:
            continue

        created_items = await DeveloperChecklistService.auto_populate_checklist(
            session=session,
            property_id=property_id,
            development_scenarios=list(scenario_keys),
        )
        if created_items:
            logger.info(
                "seed_properties_projects.developer_checklists.created",
                property_id=str(property_id),
                items=len(created_items),
                scenarios=len(scenario_keys),
            )
        total_created += len(created_items)

    return total_created


async def seed_properties_and_projects(
    session: AsyncSession,
    *,
    reset_existing: bool = True,
) -> SeedSummary:
    if reset_existing:
        await _purge_existing(session)

    # NOTE: Skip seeding projects - table schema doesn't have required columns yet
    # Once migration is created to add project_name, project_code, etc., uncomment this
    project_count = 0
    # for payload in _PROJECTS:
    #     if "id" in payload:
    #         existing_by_id = await session.get(Project, payload["id"])
    #         if existing_by_id:
    #             continue
    #     existing = await session.execute(
    #         select(Project).where(Project.project_code == payload["project_code"])
    #     )
    #     if existing.scalar_one_or_none():
    #         continue
    #     record = Project(
    #         project_name=payload["project_name"],
    #         project_code=payload["project_code"],
    #         description=payload.get("description"),
    #         owner_email=payload.get("owner_email"),
    #         project_type=payload["project_type"],
    #         current_phase=payload.get("current_phase"),
    #         estimated_cost_sgd=payload.get("estimated_cost_sgd"),
    #     )
    #     if "id" in payload:
    #         record.id = payload["id"]
    #     session.add(record)
    #     project_count += 1

    # Seed properties
    property_count = 0
    property_ids = [payload["id"] for payload in _PROPERTIES]
    for payload in _PROPERTIES:
        existing = await session.get(Property, payload["id"])
        if existing:
            continue
        property_payload = dict(payload)
        record = Property(**property_payload)
        session.add(record)
        property_count += 1

    await session.commit()

    # Add demo analytics/benchmarks for the primary property
    await _seed_market_demo_enrichments(session)
    await session.commit()

    checklist_items_created = await _seed_developer_checklists(session, property_ids)
    await session.commit()

    if checklist_items_created:
        logger.info(
            "seed_properties_projects.developer_checklists.summary",
            properties=len(property_ids),
            items_created=checklist_items_created,
        )

    return SeedSummary(
        projects=project_count,
        properties=property_count,
        developer_checklists=checklist_items_created,
    )


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
