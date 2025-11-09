"""Seed Singapore URA and BCA rules into RefRule database.

This populates the jurisdiction-agnostic RefRule system with Singapore-specific
building regulations from URA (Urban Redevelopment Authority) and BCA (Building
and Construction Authority).

Usage:
    python -m scripts.seed_singapore_rules
"""

import asyncio

from app.core.database import AsyncSessionLocal
from app.models.rkp import RefRule, RefSource
from sqlalchemy import select


async def seed_singapore_rules():
    """Populate Singapore URA and BCA rules into RefRule table.

    This function is idempotent - it only adds rules that don't already exist.
    It checks for specific zoning rules rather than just any SG rules, allowing
    parking rules and other rule types to coexist.
    """

    async with AsyncSessionLocal() as session:
        # Check if Singapore zoning rules already exist (core requirement)
        result = await session.execute(
            select(RefRule)
            .where(RefRule.jurisdiction == "SG")
            .where(RefRule.parameter_key == "zoning.max_building_height_m")
            .where(RefRule.applicability.contains({"zone_code": "SG:residential"}))
            .limit(1)
        )
        existing_zoning = result.scalar_one_or_none()

        if existing_zoning:
            print("Singapore zoning rules already exist in database. Skipping seed.")
            return

        print("Seeding Singapore URA and BCA rules...")

        # Create RefSource for URA Master Plan 2019
        ura_source = RefSource(
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            doc_title="Master Plan 2019 - Written Statement",
            landing_url="https://www.ura.gov.sg/Corporate/Planning/Master-Plan",
            fetch_kind="html",
            is_active=True,
        )
        session.add(ura_source)
        await session.flush()

        # Create RefSource for BCA Code on Accessibility
        bca_source = RefSource(
            jurisdiction="SG",
            authority="BCA",
            topic="building",
            doc_title="Code on Accessibility in the Built Environment 2019",
            landing_url="https://www1.bca.gov.sg/",
            fetch_kind="pdf",
            is_active=True,
        )
        session.add(bca_source)
        await session.flush()

        # Singapore URA Zoning Rules
        singapore_rules = [
            # Residential Zoning
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.max_far",
                "operator": "<=",
                "value": "2.8",
                "unit": "ratio",
                "applicability": {"zone_code": "SG:residential"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.max_building_height_m",
                "operator": "<=",
                "value": "36",
                "unit": "m",
                "applicability": {"zone_code": "SG:residential"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.setback.front_min_m",
                "operator": ">=",
                "value": "7.5",
                "unit": "m",
                "applicability": {"zone_code": "SG:residential"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            # Commercial Zoning
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.max_far",
                "operator": "<=",
                "value": "10.0",
                "unit": "ratio",
                "applicability": {"zone_code": "SG:commercial"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.max_building_height_m",
                "operator": "<=",
                "value": "280",
                "unit": "m",
                "applicability": {"zone_code": "SG:commercial"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.setback.front_min_m",
                "operator": ">=",
                "value": "5.0",
                "unit": "m",
                "applicability": {"zone_code": "SG:commercial"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            # Industrial Zoning
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.max_far",
                "operator": "<=",
                "value": "2.5",
                "unit": "ratio",
                "applicability": {"zone_code": "SG:industrial"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.max_building_height_m",
                "operator": "<=",
                "value": "50",
                "unit": "m",
                "applicability": {"zone_code": "SG:industrial"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.setback.front_min_m",
                "operator": ">=",
                "value": "10.0",
                "unit": "m",
                "applicability": {"zone_code": "SG:industrial"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            # Mixed Use Zoning
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.max_far",
                "operator": "<=",
                "value": "3.0",
                "unit": "ratio",
                "applicability": {"zone_code": "SG:mixed_use"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.max_building_height_m",
                "operator": "<=",
                "value": "80",
                "unit": "m",
                "applicability": {"zone_code": "SG:mixed_use"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            # Business Park Zoning
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.max_far",
                "operator": "<=",
                "value": "2.5",
                "unit": "ratio",
                "applicability": {"zone_code": "SG:business_park"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "zoning",
                "parameter_key": "zoning.max_building_height_m",
                "operator": "<=",
                "value": "50",
                "unit": "m",
                "applicability": {"zone_code": "SG:business_park"},
                "source_id": ura_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            # BCA Site Coverage Rules
            {
                "jurisdiction": "SG",
                "authority": "BCA",
                "topic": "building",
                "parameter_key": "zoning.site_coverage.max_percent",
                "operator": "<=",
                "value": "40",
                "unit": "%",
                "applicability": {"zone_code": "SG:residential"},
                "source_id": bca_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "BCA",
                "topic": "building",
                "parameter_key": "zoning.site_coverage.max_percent",
                "operator": "<=",
                "value": "50",
                "unit": "%",
                "applicability": {"zone_code": "SG:commercial"},
                "source_id": bca_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "BCA",
                "topic": "building",
                "parameter_key": "zoning.site_coverage.max_percent",
                "operator": "<=",
                "value": "60",
                "unit": "%",
                "applicability": {"zone_code": "SG:industrial"},
                "source_id": bca_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "BCA",
                "topic": "building",
                "parameter_key": "zoning.site_coverage.max_percent",
                "operator": "<=",
                "value": "45",
                "unit": "%",
                "applicability": {"zone_code": "SG:mixed_use"},
                "source_id": bca_source.id,
                "review_status": "approved",
                "is_published": True,
            },
            {
                "jurisdiction": "SG",
                "authority": "BCA",
                "topic": "building",
                "parameter_key": "zoning.site_coverage.max_percent",
                "operator": "<=",
                "value": "45",
                "unit": "%",
                "applicability": {"zone_code": "SG:business_park"},
                "source_id": bca_source.id,
                "review_status": "approved",
                "is_published": True,
            },
        ]

        # Insert all rules
        for rule_data in singapore_rules:
            rule = RefRule(**rule_data)
            session.add(rule)

        await session.commit()

        print(
            f"✅ Successfully seeded {len(singapore_rules)} Singapore rules into RefRule database"
        )
        print(
            "These rules are now available for jurisdiction-agnostic buildable calculations"
        )


if __name__ == "__main__":
    asyncio.run(seed_singapore_rules())
