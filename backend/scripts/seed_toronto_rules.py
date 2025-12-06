#!/usr/bin/env python
"""Seed Toronto Zoning By-law and Ontario Building Code rules into RefRule database.

Usage:
    python -m scripts.seed_toronto_rules

This script populates the RefRule table with Toronto building regulations:
- City of Toronto Zoning By-law 569-2013
- Ontario Building Code (OBC)
- Toronto Green Standard (TGS)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import _resolve_database_url
from app.models.rkp import RefRule, RefSource


# Toronto Zoning By-law 569-2013 Rules
# Reference: https://www.toronto.ca/city-government/planning-development/zoning-by-law-preliminary-zoning-reviews/
TOR_ZONING_RULES = [
    # Residential Detached (RD)
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_fsi",
        "operator": "<=",
        "value": "0.6",
        "unit": "ratio",
        "applicability": {"zone_code": "TOR:RD"},
        "description": "Maximum FSI for RD zone",
        "source_reference": "By-law 569-2013, Chapter 10",
    },
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "10",
        "unit": "m",
        "applicability": {"zone_code": "TOR:RD"},
        "description": "Maximum building height for RD zone",
        "source_reference": "By-law 569-2013, Chapter 10",
    },
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_lot_coverage",
        "operator": "<=",
        "value": "35",
        "unit": "percent",
        "applicability": {"zone_code": "TOR:RD"},
        "description": "Maximum lot coverage for RD zone",
        "source_reference": "By-law 569-2013, Chapter 10",
    },
    # Residential Semi-Detached (RS)
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_fsi",
        "operator": "<=",
        "value": "0.6",
        "unit": "ratio",
        "applicability": {"zone_code": "TOR:RS"},
        "description": "Maximum FSI for RS zone",
        "source_reference": "By-law 569-2013, Chapter 20",
    },
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "10",
        "unit": "m",
        "applicability": {"zone_code": "TOR:RS"},
        "description": "Maximum building height for RS zone",
        "source_reference": "By-law 569-2013, Chapter 20",
    },
    # Residential Townhouse (RT)
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_fsi",
        "operator": "<=",
        "value": "1.0",
        "unit": "ratio",
        "applicability": {"zone_code": "TOR:RT"},
        "description": "Maximum FSI for RT zone",
        "source_reference": "By-law 569-2013, Chapter 30",
    },
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "12",
        "unit": "m",
        "applicability": {"zone_code": "TOR:RT"},
        "description": "Maximum building height for RT zone",
        "source_reference": "By-law 569-2013, Chapter 30",
    },
    # Residential Multiple Dwelling (RM)
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_fsi",
        "operator": "<=",
        "value": "1.5",
        "unit": "ratio",
        "applicability": {"zone_code": "TOR:RM"},
        "description": "Maximum FSI for RM zone",
        "source_reference": "By-law 569-2013, Chapter 40",
    },
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "14",
        "unit": "m",
        "applicability": {"zone_code": "TOR:RM"},
        "description": "Maximum building height for RM zone",
        "source_reference": "By-law 569-2013, Chapter 40",
    },
    # Residential Apartment (RA)
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_fsi",
        "operator": "<=",
        "value": "3.0",
        "unit": "ratio",
        "applicability": {"zone_code": "TOR:RA"},
        "description": "Maximum FSI for RA zone (base)",
        "source_reference": "By-law 569-2013, Chapter 50",
    },
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "24",
        "unit": "m",
        "applicability": {"zone_code": "TOR:RA"},
        "description": "Maximum building height for RA zone (base)",
        "source_reference": "By-law 569-2013, Chapter 50",
    },
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_lot_coverage",
        "operator": "<=",
        "value": "60",
        "unit": "percent",
        "applicability": {"zone_code": "TOR:RA"},
        "description": "Maximum lot coverage for RA zone",
        "source_reference": "By-law 569-2013, Chapter 50",
    },
    # Commercial Residential (CR)
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_fsi",
        "operator": "<=",
        "value": "4.0",
        "unit": "ratio",
        "applicability": {"zone_code": "TOR:CR"},
        "description": "Maximum FSI for CR zone (base)",
        "source_reference": "By-law 569-2013, Chapter 200",
    },
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "36",
        "unit": "m",
        "applicability": {"zone_code": "TOR:CR"},
        "description": "Maximum building height for CR zone (base)",
        "source_reference": "By-law 569-2013, Chapter 200",
    },
    # Employment (E)
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_fsi",
        "operator": "<=",
        "value": "2.0",
        "unit": "ratio",
        "applicability": {"zone_code": "TOR:E"},
        "description": "Maximum FSI for E zone",
        "source_reference": "By-law 569-2013, Chapter 400",
    },
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "18",
        "unit": "m",
        "applicability": {"zone_code": "TOR:E"},
        "description": "Maximum building height for E zone",
        "source_reference": "By-law 569-2013, Chapter 400",
    },
    # Institutional (I)
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_fsi",
        "operator": "<=",
        "value": "2.5",
        "unit": "ratio",
        "applicability": {"zone_code": "TOR:I"},
        "description": "Maximum FSI for I zone",
        "source_reference": "By-law 569-2013, Chapter 500",
    },
    {
        "jurisdiction": "TOR",
        "authority": "CityPlanning",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "24",
        "unit": "m",
        "applicability": {"zone_code": "TOR:I"},
        "description": "Maximum building height for I zone",
        "source_reference": "By-law 569-2013, Chapter 500",
    },
]

# Ontario Building Code and Toronto Green Standard Rules
TOR_OBC_RULES = [
    {
        "jurisdiction": "TOR",
        "authority": "OBC",
        "topic": "building",
        "parameter_key": "building.energy.tier1_required",
        "operator": "==",
        "value": "true",
        "unit": "boolean",
        "applicability": None,
        "description": "Toronto Green Standard Tier 1 mandatory for all new developments",
        "source_reference": "TGS Version 4",
    },
    {
        "jurisdiction": "TOR",
        "authority": "OBC",
        "topic": "building",
        "parameter_key": "building.fire.max_travel_distance_m",
        "operator": "<=",
        "value": "45",
        "unit": "m",
        "applicability": {"building_type": "residential", "sprinklered": True},
        "description": "Maximum travel distance for sprinklered residential",
        "source_reference": "OBC 3.4.2",
    },
    {
        "jurisdiction": "TOR",
        "authority": "OBC",
        "topic": "building",
        "parameter_key": "building.fire.max_travel_distance_m",
        "operator": "<=",
        "value": "30",
        "unit": "m",
        "applicability": {"building_type": "residential", "sprinklered": False},
        "description": "Maximum travel distance for non-sprinklered residential",
        "source_reference": "OBC 3.4.2",
    },
    {
        "jurisdiction": "TOR",
        "authority": "OBC",
        "topic": "building",
        "parameter_key": "building.accessibility.barrier_free_path_width_mm",
        "operator": ">=",
        "value": "1100",
        "unit": "mm",
        "applicability": None,
        "description": "Minimum barrier-free path width (AODA compliant)",
        "source_reference": "OBC 3.8.1",
    },
    {
        "jurisdiction": "TOR",
        "authority": "OBC",
        "topic": "building",
        "parameter_key": "building.accessibility.door_width_mm",
        "operator": ">=",
        "value": "850",
        "unit": "mm",
        "applicability": None,
        "description": "Minimum door width for barrier-free access",
        "source_reference": "OBC 3.8.3",
    },
]

# Toronto regulatory sources
TOR_SOURCES = [
    {
        "jurisdiction": "TOR",
        "name": "City of Toronto Planning",
        "abbreviation": "CityPlanning",
        "url": "https://www.toronto.ca/city-government/planning-development/",
        "description": "City department responsible for planning and development applications",
    },
    {
        "jurisdiction": "TOR",
        "name": "Ontario Building Code",
        "abbreviation": "OBC",
        "url": "https://www.ontario.ca/laws/regulation/120332",
        "description": "Ontario Building Code administered by MMAH",
    },
    {
        "jurisdiction": "TOR",
        "name": "Toronto Building",
        "abbreviation": "TorontoBuilding",
        "url": "https://www.toronto.ca/city-government/planning-development/building-toronto/",
        "description": "City division responsible for building permits and inspections",
    },
]


async def seed_sources(session: AsyncSession) -> dict[str, RefSource]:
    """Seed Toronto regulatory sources."""
    sources: dict[str, RefSource] = {}

    for source_data in TOR_SOURCES:
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
    """Main function to seed Toronto rules."""
    print("Seeding Toronto Zoning By-law 569-2013 and OBC rules...")
    print("-" * 50)

    engine = create_async_engine(_resolve_database_url(), future=True, echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            print("\nSeeding regulatory sources...")
            sources = await seed_sources(session)
            print(f"  Total sources: {len(sources)}")

            print("\nSeeding Zoning By-law 569-2013 rules...")
            zoning_count = await seed_rules(session, sources, TOR_ZONING_RULES)
            print(f"  Created {zoning_count} zoning rules")

            print("\nSeeding OBC and TGS rules...")
            obc_count = await seed_rules(session, sources, TOR_OBC_RULES)
            print(f"  Created {obc_count} OBC rules")

            await session.commit()

            print("\n" + "-" * 50)
            print("Seeding complete!")
            print(f"  Sources: {len(sources)}")
            print(f"  Zoning rules: {zoning_count}")
            print(f"  OBC rules: {obc_count}")
            print(f"  Total rules: {zoning_count + obc_count}")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
