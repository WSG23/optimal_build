#!/usr/bin/env python
"""Seed New Zealand District Plan and Building Code rules into the RefRule database.

Usage:
    python -m scripts.seed_new_zealand_rules

This script populates the RefRule table with New Zealand building regulations:
- Auckland Unitary Plan / District Plan zoning rules
- Building Code (MBIE) requirements
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import _resolve_database_url
from app.models.rkp import RefRule, RefSource


# New Zealand Auckland Unitary Plan Zoning Rules
# Reference: https://unitaryplan.aucklandcouncil.govt.nz/
NZ_DISTRICT_PLAN_RULES = [
    # Residential - Mixed Housing Suburban
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "8",
        "unit": "m",
        "applicability": {"zone_code": "NZ:residential_mixed_housing_suburban"},
        "description": "Maximum building height for Mixed Housing Suburban zone",
        "source_reference": "Auckland Unitary Plan H4.6.4",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_site_coverage",
        "operator": "<=",
        "value": "40",
        "unit": "percent",
        "applicability": {"zone_code": "NZ:residential_mixed_housing_suburban"},
        "description": "Maximum building coverage for Mixed Housing Suburban zone",
        "source_reference": "Auckland Unitary Plan H4.6.6",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_impervious_surface",
        "operator": "<=",
        "value": "60",
        "unit": "percent",
        "applicability": {"zone_code": "NZ:residential_mixed_housing_suburban"},
        "description": "Maximum impervious surface for Mixed Housing Suburban zone",
        "source_reference": "Auckland Unitary Plan H4.6.6",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.min_setback_front_m",
        "operator": ">=",
        "value": "3",
        "unit": "m",
        "applicability": {"zone_code": "NZ:residential_mixed_housing_suburban"},
        "description": "Minimum front yard setback",
        "source_reference": "Auckland Unitary Plan H4.6.8",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.min_setback_side_m",
        "operator": ">=",
        "value": "1",
        "unit": "m",
        "applicability": {"zone_code": "NZ:residential_mixed_housing_suburban"},
        "description": "Minimum side yard setback",
        "source_reference": "Auckland Unitary Plan H4.6.9",
    },
    # Residential - Mixed Housing Urban
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "11",
        "unit": "m",
        "applicability": {"zone_code": "NZ:residential_mixed_housing_urban"},
        "description": "Maximum building height for Mixed Housing Urban zone",
        "source_reference": "Auckland Unitary Plan H5.6.4",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_site_coverage",
        "operator": "<=",
        "value": "45",
        "unit": "percent",
        "applicability": {"zone_code": "NZ:residential_mixed_housing_urban"},
        "description": "Maximum building coverage for Mixed Housing Urban zone",
        "source_reference": "Auckland Unitary Plan H5.6.6",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.min_setback_front_m",
        "operator": ">=",
        "value": "2.5",
        "unit": "m",
        "applicability": {"zone_code": "NZ:residential_mixed_housing_urban"},
        "description": "Minimum front yard setback",
        "source_reference": "Auckland Unitary Plan H5.6.8",
    },
    # Residential - Terrace Housing and Apartment
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "16",
        "unit": "m",
        "applicability": {"zone_code": "NZ:residential_terrace_housing_apartment"},
        "description": "Maximum building height for Terrace Housing and Apartment zone",
        "source_reference": "Auckland Unitary Plan H6.6.4",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_site_coverage",
        "operator": "<=",
        "value": "50",
        "unit": "percent",
        "applicability": {"zone_code": "NZ:residential_terrace_housing_apartment"},
        "description": "Maximum building coverage for THAB zone",
        "source_reference": "Auckland Unitary Plan H6.6.6",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.min_setback_front_m",
        "operator": ">=",
        "value": "2",
        "unit": "m",
        "applicability": {"zone_code": "NZ:residential_terrace_housing_apartment"},
        "description": "Minimum front yard setback",
        "source_reference": "Auckland Unitary Plan H6.6.8",
    },
    # Residential - Single House
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "8",
        "unit": "m",
        "applicability": {"zone_code": "NZ:residential_single_house"},
        "description": "Maximum building height for Single House zone",
        "source_reference": "Auckland Unitary Plan H3.6.4",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_site_coverage",
        "operator": "<=",
        "value": "35",
        "unit": "percent",
        "applicability": {"zone_code": "NZ:residential_single_house"},
        "description": "Maximum building coverage for Single House zone",
        "source_reference": "Auckland Unitary Plan H3.6.6",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.min_lot_size_sqm",
        "operator": ">=",
        "value": "600",
        "unit": "sqm",
        "applicability": {"zone_code": "NZ:residential_single_house"},
        "description": "Minimum lot size for Single House zone",
        "source_reference": "Auckland Unitary Plan H3.6.3",
    },
    # Business - Town Centre
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "18",
        "unit": "m",
        "applicability": {"zone_code": "NZ:business_town_centre"},
        "description": "Maximum building height for Town Centre zone",
        "source_reference": "Auckland Unitary Plan H11.6.1",
    },
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_site_coverage",
        "operator": "<=",
        "value": "100",
        "unit": "percent",
        "applicability": {"zone_code": "NZ:business_town_centre"},
        "description": "No building coverage limit for Town Centre zone",
        "source_reference": "Auckland Unitary Plan H11",
    },
    # Business - Metropolitan Centre
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "72.5",
        "unit": "m",
        "applicability": {"zone_code": "NZ:business_metropolitan_centre"},
        "description": "Maximum building height for Metropolitan Centre zone",
        "source_reference": "Auckland Unitary Plan H9.6.1",
    },
    # Business - City Centre
    {
        "jurisdiction": "NZ",
        "authority": "Council",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "180",
        "unit": "m",
        "applicability": {"zone_code": "NZ:business_city_centre"},
        "description": "Maximum building height for City Centre zone (varies by location)",
        "source_reference": "Auckland Unitary Plan H8.6.1",
    },
]

# New Zealand Building Code Rules (MBIE)
NZ_BUILDING_CODE_RULES = [
    # Energy Efficiency (H1)
    {
        "jurisdiction": "NZ",
        "authority": "MBIE",
        "topic": "building",
        "parameter_key": "building.h1.insulation_r_value",
        "operator": ">=",
        "value": "2.9",
        "unit": "R-value",
        "applicability": {"building_type": "residential", "climate_zone": "1"},
        "description": "Minimum roof insulation R-value for Climate Zone 1",
        "source_reference": "Building Code Clause H1",
    },
    {
        "jurisdiction": "NZ",
        "authority": "MBIE",
        "topic": "building",
        "parameter_key": "building.h1.insulation_r_value",
        "operator": ">=",
        "value": "3.3",
        "unit": "R-value",
        "applicability": {"building_type": "residential", "climate_zone": "3"},
        "description": "Minimum roof insulation R-value for Climate Zone 3",
        "source_reference": "Building Code Clause H1",
    },
    # Fire Safety (C/AS1)
    {
        "jurisdiction": "NZ",
        "authority": "MBIE",
        "topic": "building",
        "parameter_key": "building.fire.max_travel_distance_m",
        "operator": "<=",
        "value": "40",
        "unit": "m",
        "applicability": {"building_type": "residential"},
        "description": "Maximum travel distance to exit for residential buildings",
        "source_reference": "C/AS1 Acceptable Solution",
    },
    {
        "jurisdiction": "NZ",
        "authority": "MBIE",
        "topic": "building",
        "parameter_key": "building.fire.max_travel_distance_m",
        "operator": "<=",
        "value": "25",
        "unit": "m",
        "applicability": {"building_type": "sleeping_risk"},
        "description": "Maximum travel distance for sleeping risk buildings",
        "source_reference": "C/AS1 Acceptable Solution",
    },
    # Access (D1)
    {
        "jurisdiction": "NZ",
        "authority": "MBIE",
        "topic": "building",
        "parameter_key": "building.d1.min_corridor_width_m",
        "operator": ">=",
        "value": "1.2",
        "unit": "m",
        "applicability": {"building_type": "commercial"},
        "description": "Minimum corridor width for accessible routes",
        "source_reference": "Building Code Clause D1",
    },
    # Moisture (E2)
    {
        "jurisdiction": "NZ",
        "authority": "MBIE",
        "topic": "building",
        "parameter_key": "building.e2.weathertightness",
        "operator": "==",
        "value": "true",
        "unit": "boolean",
        "applicability": None,
        "description": "Building must prevent moisture penetration",
        "source_reference": "Building Code Clause E2",
    },
]

# New Zealand regulatory sources
NZ_SOURCES = [
    {
        "jurisdiction": "NZ",
        "name": "Auckland Council",
        "abbreviation": "AC",
        "url": "https://www.aucklandcouncil.govt.nz/",
        "description": "Auckland Council - Resource and Building Consents",
    },
    {
        "jurisdiction": "NZ",
        "name": "Ministry of Business, Innovation and Employment",
        "abbreviation": "MBIE",
        "url": "https://www.building.govt.nz/",
        "description": "National building code and regulations",
    },
    {
        "jurisdiction": "NZ",
        "name": "Heritage New Zealand Pouhere Taonga",
        "abbreviation": "HNZPT",
        "url": "https://www.heritage.org.nz/",
        "description": "Heritage protection and listing",
    },
]


async def seed_sources(session: AsyncSession) -> dict[str, RefSource]:
    """Seed New Zealand regulatory sources."""
    sources: dict[str, RefSource] = {}

    for source_data in NZ_SOURCES:
        stmt = select(RefSource).where(
            RefSource.jurisdiction == source_data["jurisdiction"],
            RefSource.abbreviation == source_data["abbreviation"],
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            sources[source_data["abbreviation"]] = existing
            print(f"  Source exists: {source_data['abbreviation']}")
        else:
            source = RefSource(
                jurisdiction=source_data["jurisdiction"],
                name=source_data["name"],
                abbreviation=source_data["abbreviation"],
                url=source_data["url"],
                description=source_data["description"],
            )
            session.add(source)
            sources[source_data["abbreviation"]] = source
            print(f"  Created source: {source_data['abbreviation']}")

    await session.flush()
    return sources


async def seed_rules(
    session: AsyncSession, sources: dict[str, RefSource], rules_list: list[dict]
) -> int:
    """Seed rules into RefRule table."""
    count = 0

    for rule_data in rules_list:
        stmt = select(RefRule).where(
            RefRule.jurisdiction == rule_data["jurisdiction"],
            RefRule.authority == rule_data["authority"],
            RefRule.parameter_key == rule_data["parameter_key"],
        )
        result = await session.execute(stmt)
        existing_rules = result.scalars().all()

        applicability = rule_data.get("applicability", {})
        exists = False
        for existing in existing_rules:
            if existing.applicability == applicability:
                exists = True
                break

        if exists:
            print(f"  Rule exists: {rule_data['parameter_key']} ({applicability})")
            continue

        source = sources.get(rule_data["authority"])

        rule = RefRule(
            jurisdiction=rule_data["jurisdiction"],
            authority=rule_data["authority"],
            topic=rule_data["topic"],
            parameter_key=rule_data["parameter_key"],
            operator=rule_data["operator"],
            value=rule_data["value"],
            unit=rule_data.get("unit"),
            applicability=applicability,
            description=rule_data.get("description"),
            source_reference=rule_data.get("source_reference"),
            source_id=source.id if source else None,
            review_status="approved",
            is_published=True,
        )
        session.add(rule)
        count += 1
        print(f"  Created rule: {rule_data['parameter_key']} ({applicability})")

    await session.flush()
    return count


async def main() -> None:
    """Main function to seed New Zealand rules."""
    print("Seeding New Zealand District Plan and Building Code rules...")
    print("-" * 50)

    engine = create_async_engine(_resolve_database_url(), future=True, echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            print("\nSeeding regulatory sources...")
            sources = await seed_sources(session)
            print(f"  Total sources: {len(sources)}")

            print("\nSeeding District Plan zoning rules...")
            dp_count = await seed_rules(session, sources, NZ_DISTRICT_PLAN_RULES)
            print(f"  Created {dp_count} District Plan rules")

            print("\nSeeding Building Code rules...")
            bc_count = await seed_rules(session, sources, NZ_BUILDING_CODE_RULES)
            print(f"  Created {bc_count} Building Code rules")

            await session.commit()

            print("\n" + "-" * 50)
            print("Seeding complete!")
            print(f"  Sources: {len(sources)}")
            print(f"  District Plan rules: {dp_count}")
            print(f"  Building Code rules: {bc_count}")
            print(f"  Total rules: {dp_count + bc_count}")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
