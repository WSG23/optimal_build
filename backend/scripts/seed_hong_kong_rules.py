#!/usr/bin/env python
"""Seed Hong Kong TPB and Buildings Department rules into the RefRule database.

Usage:
    python -m scripts.seed_hong_kong_rules

This script populates the RefRule table with Hong Kong building regulations:
- Town Planning Board (TPB) zoning rules from Outline Zoning Plans (OZP)
- Buildings Department (BD) building regulations
- Fire Services Department (FSD) requirements
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


# Hong Kong TPB Zoning Rules (based on typical OZP restrictions)
# Reference: https://www.pland.gov.hk/pland_en/info_serv/tp_plan/
HK_TPB_ZONING_RULES = [
    # Residential (Group A) - High density residential
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_plot_ratio",
        "operator": "<=",
        "value": "10.0",
        "unit": "ratio",
        "applicability": {"zone_code": "HK:R(A)"},
        "description": "Maximum plot ratio for Residential (Group A) zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "120",
        "unit": "m",
        "applicability": {"zone_code": "HK:R(A)"},
        "description": "Maximum building height for Residential (Group A) zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_site_coverage",
        "operator": "<=",
        "value": "65%",
        "unit": "percent",
        "applicability": {"zone_code": "HK:R(A)"},
        "description": "Maximum site coverage for Residential (Group A) zone",
        "source_reference": "Building (Planning) Regulations",
    },
    # Residential (Group B) - Medium density
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_plot_ratio",
        "operator": "<=",
        "value": "5.0",
        "unit": "ratio",
        "applicability": {"zone_code": "HK:R(B)"},
        "description": "Maximum plot ratio for Residential (Group B) zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "60",
        "unit": "m",
        "applicability": {"zone_code": "HK:R(B)"},
        "description": "Maximum building height for Residential (Group B) zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_site_coverage",
        "operator": "<=",
        "value": "50%",
        "unit": "percent",
        "applicability": {"zone_code": "HK:R(B)"},
        "description": "Maximum site coverage for Residential (Group B) zone",
        "source_reference": "Building (Planning) Regulations",
    },
    # Residential (Group C) - Low density
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_plot_ratio",
        "operator": "<=",
        "value": "2.1",
        "unit": "ratio",
        "applicability": {"zone_code": "HK:R(C)"},
        "description": "Maximum plot ratio for Residential (Group C) zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "25",
        "unit": "m",
        "applicability": {"zone_code": "HK:R(C)"},
        "description": "Maximum building height for Residential (Group C) zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_storeys",
        "operator": "<=",
        "value": "8",
        "unit": "storeys",
        "applicability": {"zone_code": "HK:R(C)"},
        "description": "Maximum number of storeys for Residential (Group C) zone",
        "source_reference": "OZP Schedule Notes",
    },
    # Commercial zone
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_plot_ratio",
        "operator": "<=",
        "value": "15.0",
        "unit": "ratio",
        "applicability": {"zone_code": "HK:C"},
        "description": "Maximum plot ratio for Commercial zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "200",
        "unit": "m",
        "applicability": {"zone_code": "HK:C"},
        "description": "Maximum building height for Commercial zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_site_coverage",
        "operator": "<=",
        "value": "100%",
        "unit": "percent",
        "applicability": {"zone_code": "HK:C"},
        "description": "Maximum site coverage for Commercial zone (no restriction)",
        "source_reference": "Building (Planning) Regulations",
    },
    # Commercial/Residential zone
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_plot_ratio",
        "operator": "<=",
        "value": "12.0",
        "unit": "ratio",
        "applicability": {"zone_code": "HK:C/R"},
        "description": "Maximum plot ratio for Commercial/Residential zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "150",
        "unit": "m",
        "applicability": {"zone_code": "HK:C/R"},
        "description": "Maximum building height for Commercial/Residential zone",
        "source_reference": "OZP Schedule Notes",
    },
    # Industrial zone
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_plot_ratio",
        "operator": "<=",
        "value": "9.5",
        "unit": "ratio",
        "applicability": {"zone_code": "HK:I"},
        "description": "Maximum plot ratio for Industrial zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_building_height_m",
        "operator": "<=",
        "value": "100",
        "unit": "m",
        "applicability": {"zone_code": "HK:I"},
        "description": "Maximum building height for Industrial zone",
        "source_reference": "OZP Schedule Notes",
    },
    # Comprehensive Development Area (CDA)
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.requires_master_layout_plan",
        "operator": "==",
        "value": "true",
        "unit": "boolean",
        "applicability": {"zone_code": "HK:CDA"},
        "description": "CDA requires Master Layout Plan submission to TPB",
        "source_reference": "Town Planning Ordinance",
    },
    # Green Belt
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_plot_ratio",
        "operator": "<=",
        "value": "0.4",
        "unit": "ratio",
        "applicability": {"zone_code": "HK:GB"},
        "description": "Maximum plot ratio for Green Belt zone",
        "source_reference": "OZP Schedule Notes",
    },
    {
        "jurisdiction": "HK",
        "authority": "TPB",
        "topic": "zoning",
        "parameter_key": "zoning.max_storeys",
        "operator": "<=",
        "value": "3",
        "unit": "storeys",
        "applicability": {"zone_code": "HK:GB"},
        "description": "Maximum number of storeys for Green Belt zone",
        "source_reference": "OZP Schedule Notes",
    },
]

# Hong Kong Buildings Department Rules
HK_BD_BUILDING_RULES = [
    # Site coverage by zone (Building (Planning) Regulations)
    {
        "jurisdiction": "HK",
        "authority": "BD",
        "topic": "building",
        "parameter_key": "building.site_coverage.max_percent",
        "operator": "<=",
        "value": "65%",
        "unit": "percent",
        "applicability": {"zone_code": "HK:R(A)"},
        "description": "Maximum site coverage for domestic buildings in R(A) zone",
        "source_reference": "Building (Planning) Regulations First Schedule",
    },
    {
        "jurisdiction": "HK",
        "authority": "BD",
        "topic": "building",
        "parameter_key": "building.site_coverage.max_percent",
        "operator": "<=",
        "value": "50%",
        "unit": "percent",
        "applicability": {"zone_code": "HK:R(B)"},
        "description": "Maximum site coverage for domestic buildings in R(B) zone",
        "source_reference": "Building (Planning) Regulations First Schedule",
    },
    {
        "jurisdiction": "HK",
        "authority": "BD",
        "topic": "building",
        "parameter_key": "building.site_coverage.max_percent",
        "operator": "<=",
        "value": "40%",
        "unit": "percent",
        "applicability": {"zone_code": "HK:R(C)"},
        "description": "Maximum site coverage for domestic buildings in R(C) zone",
        "source_reference": "Building (Planning) Regulations First Schedule",
    },
    {
        "jurisdiction": "HK",
        "authority": "BD",
        "topic": "building",
        "parameter_key": "building.site_coverage.max_percent",
        "operator": "<=",
        "value": "100%",
        "unit": "percent",
        "applicability": {"zone_code": "HK:C"},
        "description": "Maximum site coverage for commercial buildings (no restriction)",
        "source_reference": "Building (Planning) Regulations First Schedule",
    },
    # Open space requirements
    {
        "jurisdiction": "HK",
        "authority": "BD",
        "topic": "building",
        "parameter_key": "building.open_space.min_percent",
        "operator": ">=",
        "value": "20%",
        "unit": "percent",
        "applicability": {"zone_code": "HK:R(A)"},
        "description": "Minimum open space for domestic buildings",
        "source_reference": "Building (Planning) Regulations",
    },
    {
        "jurisdiction": "HK",
        "authority": "BD",
        "topic": "building",
        "parameter_key": "building.open_space.min_percent",
        "operator": ">=",
        "value": "30%",
        "unit": "percent",
        "applicability": {"zone_code": "HK:R(B)"},
        "description": "Minimum open space for R(B) developments",
        "source_reference": "Building (Planning) Regulations",
    },
    # Minimum unit sizes (REDA guidelines)
    {
        "jurisdiction": "HK",
        "authority": "BD",
        "topic": "building",
        "parameter_key": "building.min_unit_size_sqft",
        "operator": ">=",
        "value": "260",
        "unit": "sqft",
        "applicability": {"zone_code": "HK:R(A)"},
        "description": "Minimum saleable area per residential unit",
        "source_reference": "REDA Guidelines",
    },
    # Means of escape
    {
        "jurisdiction": "HK",
        "authority": "BD",
        "topic": "building",
        "parameter_key": "building.moe.max_travel_distance_m",
        "operator": "<=",
        "value": "45",
        "unit": "m",
        "applicability": {"building_type": "residential"},
        "description": "Maximum travel distance to means of escape",
        "source_reference": "Code of Practice for Means of Escape",
    },
    {
        "jurisdiction": "HK",
        "authority": "BD",
        "topic": "building",
        "parameter_key": "building.moe.max_travel_distance_m",
        "operator": "<=",
        "value": "30",
        "unit": "m",
        "applicability": {"building_type": "commercial"},
        "description": "Maximum travel distance to means of escape (commercial)",
        "source_reference": "Code of Practice for Means of Escape",
    },
]

# Hong Kong regulatory sources
HK_SOURCES = [
    {
        "jurisdiction": "HK",
        "name": "Town Planning Board",
        "abbreviation": "TPB",
        "url": "https://www.pland.gov.hk/",
        "description": "Statutory body responsible for town planning in Hong Kong",
    },
    {
        "jurisdiction": "HK",
        "name": "Buildings Department",
        "abbreviation": "BD",
        "url": "https://www.bd.gov.hk/",
        "description": "Government department responsible for building control",
    },
    {
        "jurisdiction": "HK",
        "name": "Lands Department",
        "abbreviation": "LandsD",
        "url": "https://www.landsd.gov.hk/",
        "description": "Government department responsible for land administration",
    },
    {
        "jurisdiction": "HK",
        "name": "Fire Services Department",
        "abbreviation": "FSD",
        "url": "https://www.hkfsd.gov.hk/",
        "description": "Government department responsible for fire safety",
    },
]


async def seed_sources(session: AsyncSession) -> dict[str, RefSource]:
    """Seed Hong Kong regulatory sources."""
    sources: dict[str, RefSource] = {}

    for source_data in HK_SOURCES:
        # Check if source already exists
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
        # Check if rule already exists (by jurisdiction, authority, parameter_key, and applicability)
        stmt = select(RefRule).where(
            RefRule.jurisdiction == rule_data["jurisdiction"],
            RefRule.authority == rule_data["authority"],
            RefRule.parameter_key == rule_data["parameter_key"],
        )
        result = await session.execute(stmt)
        existing_rules = result.scalars().all()

        # Check for matching applicability
        applicability = rule_data.get("applicability", {})
        exists = False
        for existing in existing_rules:
            if existing.applicability == applicability:
                exists = True
                break

        if exists:
            print(f"  Rule exists: {rule_data['parameter_key']} ({applicability})")
            continue

        # Get source if available
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
    """Main function to seed Hong Kong rules."""
    print("Seeding Hong Kong TPB and BD rules...")
    print("-" * 50)

    # Create database engine and session
    engine = create_async_engine(_resolve_database_url(), future=True, echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            # Seed sources
            print("\nSeeding regulatory sources...")
            sources = await seed_sources(session)
            print(f"  Total sources: {len(sources)}")

            # Seed TPB zoning rules
            print("\nSeeding TPB zoning rules...")
            tpb_count = await seed_rules(session, sources, HK_TPB_ZONING_RULES)
            print(f"  Created {tpb_count} TPB rules")

            # Seed BD building rules
            print("\nSeeding BD building rules...")
            bd_count = await seed_rules(session, sources, HK_BD_BUILDING_RULES)
            print(f"  Created {bd_count} BD rules")

            # Commit all changes
            await session.commit()

            print("\n" + "-" * 50)
            print("Seeding complete!")
            print(f"  Sources: {len(sources)}")
            print(f"  TPB rules: {tpb_count}")
            print(f"  BD rules: {bd_count}")
            print(f"  Total rules: {tpb_count + bd_count}")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
