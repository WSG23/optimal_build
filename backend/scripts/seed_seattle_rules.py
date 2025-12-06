#!/usr/bin/env python
"""Seed Seattle Municipal Code and Washington State Building Code rules into RefRule database.

Usage:
    python -m scripts.seed_seattle_rules

This script populates the RefRule table with Seattle building regulations:
- Seattle Municipal Code (SMC) Title 23 - Land Use Code
- Washington State Building Code (WSBC)
- Mandatory Housing Affordability (MHA) requirements
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import _resolve_database_url
from app.models.rkp import RefRule, RefSource


# Seattle Municipal Code Title 23 Zoning Rules
# Reference: https://www.seattle.gov/sdci/codes/codes-we-enforce-(a-z)/zoning-code
SEA_SMC_ZONING_RULES = [
    # Single Family SF 5000
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_far",
        "operator": "<=",
        "value": "0.5",
        "unit": "ratio",
        "applicability": {"zone_code": "SEA:SF 5000"},
        "description": "Maximum FAR for SF 5000 zone",
        "source_reference": "SMC 23.44.010",
    },
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_ft",
        "operator": "<=",
        "value": "30",
        "unit": "ft",
        "applicability": {"zone_code": "SEA:SF 5000"},
        "description": "Maximum building height for SF 5000 zone",
        "source_reference": "SMC 23.44.012",
    },
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_lot_coverage",
        "operator": "<=",
        "value": "35",
        "unit": "percent",
        "applicability": {"zone_code": "SEA:SF 5000"},
        "description": "Maximum lot coverage for SF 5000 zone",
        "source_reference": "SMC 23.44.010",
    },
    # Lowrise 1 (LR1)
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_far",
        "operator": "<=",
        "value": "1.0",
        "unit": "ratio",
        "applicability": {"zone_code": "SEA:LR1"},
        "description": "Maximum FAR for LR1 zone",
        "source_reference": "SMC 23.45.510",
    },
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_ft",
        "operator": "<=",
        "value": "30",
        "unit": "ft",
        "applicability": {"zone_code": "SEA:LR1"},
        "description": "Maximum building height for LR1 zone",
        "source_reference": "SMC 23.45.514",
    },
    # Lowrise 2 (LR2)
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_far",
        "operator": "<=",
        "value": "1.3",
        "unit": "ratio",
        "applicability": {"zone_code": "SEA:LR2"},
        "description": "Maximum FAR for LR2 zone",
        "source_reference": "SMC 23.45.510",
    },
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_ft",
        "operator": "<=",
        "value": "40",
        "unit": "ft",
        "applicability": {"zone_code": "SEA:LR2"},
        "description": "Maximum building height for LR2 zone",
        "source_reference": "SMC 23.45.514",
    },
    # Lowrise 3 (LR3)
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_far",
        "operator": "<=",
        "value": "1.6",
        "unit": "ratio",
        "applicability": {"zone_code": "SEA:LR3"},
        "description": "Maximum FAR for LR3 zone",
        "source_reference": "SMC 23.45.510",
    },
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_ft",
        "operator": "<=",
        "value": "50",
        "unit": "ft",
        "applicability": {"zone_code": "SEA:LR3"},
        "description": "Maximum building height for LR3 zone",
        "source_reference": "SMC 23.45.514",
    },
    # Midrise (MR)
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_far",
        "operator": "<=",
        "value": "4.5",
        "unit": "ratio",
        "applicability": {"zone_code": "SEA:MR"},
        "description": "Maximum FAR for MR zone",
        "source_reference": "SMC 23.45.510",
    },
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_ft",
        "operator": "<=",
        "value": "75",
        "unit": "ft",
        "applicability": {"zone_code": "SEA:MR"},
        "description": "Maximum building height for MR zone",
        "source_reference": "SMC 23.45.514",
    },
    # Highrise (HR)
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_far",
        "operator": "<=",
        "value": "6.0",
        "unit": "ratio",
        "applicability": {"zone_code": "SEA:HR"},
        "description": "Maximum FAR for HR zone (base, before incentives)",
        "source_reference": "SMC 23.45.510",
    },
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_ft",
        "operator": "<=",
        "value": "160",
        "unit": "ft",
        "applicability": {"zone_code": "SEA:HR"},
        "description": "Maximum building height for HR zone",
        "source_reference": "SMC 23.45.514",
    },
    # Seattle Mixed - South Lake Union (SM-SLU)
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_far",
        "operator": "<=",
        "value": "7.0",
        "unit": "ratio",
        "applicability": {"zone_code": "SEA:SM-SLU"},
        "description": "Maximum FAR for SM-SLU zone",
        "source_reference": "SMC 23.48.245",
    },
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_ft",
        "operator": "<=",
        "value": "240",
        "unit": "ft",
        "applicability": {"zone_code": "SEA:SM-SLU"},
        "description": "Maximum building height for SM-SLU zone",
        "source_reference": "SMC 23.48.245",
    },
    # Downtown Office Core 2 (DOC2)
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_far",
        "operator": "<=",
        "value": "14.0",
        "unit": "ratio",
        "applicability": {"zone_code": "SEA:DOC2"},
        "description": "Maximum FAR for DOC2 zone",
        "source_reference": "SMC 23.49.011",
    },
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_ft",
        "operator": "<=",
        "value": "500",
        "unit": "ft",
        "applicability": {"zone_code": "SEA:DOC2"},
        "description": "Maximum building height for DOC2 zone",
        "source_reference": "SMC 23.49.008",
    },
    # Neighborhood Commercial 3 (NC3)
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_far",
        "operator": "<=",
        "value": "4.75",
        "unit": "ratio",
        "applicability": {"zone_code": "SEA:NC3"},
        "description": "Maximum FAR for NC3 zone",
        "source_reference": "SMC 23.47A.013",
    },
    {
        "jurisdiction": "SEA",
        "authority": "SDCI",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_ft",
        "operator": "<=",
        "value": "85",
        "unit": "ft",
        "applicability": {"zone_code": "SEA:NC3"},
        "description": "Maximum building height for NC3 zone",
        "source_reference": "SMC 23.47A.012",
    },
]

# Washington State Building Code Rules
SEA_WSBC_BUILDING_RULES = [
    {
        "jurisdiction": "SEA",
        "authority": "WSBC",
        "topic": "building",
        "parameter_key": "building.seismic_design_category",
        "operator": "==",
        "value": "D",
        "unit": "category",
        "applicability": None,
        "description": "Seattle is in Seismic Design Category D",
        "source_reference": "WSBC Chapter 16",
    },
    {
        "jurisdiction": "SEA",
        "authority": "WSBC",
        "topic": "building",
        "parameter_key": "building.fire.max_travel_distance_ft",
        "operator": "<=",
        "value": "250",
        "unit": "ft",
        "applicability": {"building_type": "residential", "sprinklered": True},
        "description": "Maximum travel distance for sprinklered residential",
        "source_reference": "WSBC Chapter 10",
    },
    {
        "jurisdiction": "SEA",
        "authority": "WSBC",
        "topic": "building",
        "parameter_key": "building.fire.max_travel_distance_ft",
        "operator": "<=",
        "value": "200",
        "unit": "ft",
        "applicability": {"building_type": "residential", "sprinklered": False},
        "description": "Maximum travel distance for non-sprinklered residential",
        "source_reference": "WSBC Chapter 10",
    },
    {
        "jurisdiction": "SEA",
        "authority": "WSBC",
        "topic": "building",
        "parameter_key": "building.ada.accessible_route_width_in",
        "operator": ">=",
        "value": "44",
        "unit": "inches",
        "applicability": None,
        "description": "Minimum accessible route width",
        "source_reference": "WSBC Chapter 11",
    },
]

# Seattle regulatory sources
SEA_SOURCES = [
    {
        "jurisdiction": "SEA",
        "name": "Seattle Department of Construction and Inspections",
        "abbreviation": "SDCI",
        "url": "https://www.seattle.gov/sdci",
        "description": "City department responsible for permits and inspections",
    },
    {
        "jurisdiction": "SEA",
        "name": "Washington State Building Code",
        "abbreviation": "WSBC",
        "url": "https://www.lni.wa.gov/licensing-permits/building-codes/",
        "description": "State building code based on IBC with Washington amendments",
    },
    {
        "jurisdiction": "SEA",
        "name": "King County Department of Local Services",
        "abbreviation": "KCDLS",
        "url": "https://kingcounty.gov/depts/local-services.aspx",
        "description": "County department for unincorporated areas",
    },
]


async def seed_sources(session: AsyncSession) -> dict[str, RefSource]:
    """Seed Seattle regulatory sources."""
    sources: dict[str, RefSource] = {}

    for source_data in SEA_SOURCES:
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
    """Main function to seed Seattle rules."""
    print("Seeding Seattle SMC and WSBC rules...")
    print("-" * 50)

    engine = create_async_engine(_resolve_database_url(), future=True, echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            print("\nSeeding regulatory sources...")
            sources = await seed_sources(session)
            print(f"  Total sources: {len(sources)}")

            print("\nSeeding SMC zoning rules...")
            smc_count = await seed_rules(session, sources, SEA_SMC_ZONING_RULES)
            print(f"  Created {smc_count} SMC rules")

            print("\nSeeding WSBC building rules...")
            wsbc_count = await seed_rules(session, sources, SEA_WSBC_BUILDING_RULES)
            print(f"  Created {wsbc_count} WSBC rules")

            await session.commit()

            print("\n" + "-" * 50)
            print("Seeding complete!")
            print(f"  Sources: {len(sources)}")
            print(f"  SMC rules: {smc_count}")
            print(f"  WSBC rules: {wsbc_count}")
            print(f"  Total rules: {smc_count + wsbc_count}")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
