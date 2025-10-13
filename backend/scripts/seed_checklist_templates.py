"""Seed checklist templates for all development scenarios.

Run with: python -m backend.scripts.seed_checklist_templates
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.models.developer_checklists import (
    ChecklistCategory,
    ChecklistPriority,
    DeveloperChecklistTemplate,
)

# Template data for each scenario and category
CHECKLIST_TEMPLATES = [
    # RAW_LAND SCENARIO
    {
        "development_scenario": "raw_land",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "item_title": "Verify land title and ownership",
        "item_description": "Confirm clear title, check for encumbrances, mortgages, or liens",
        "priority": ChecklistPriority.CRITICAL,
        "typical_duration_days": 14,
        "requires_professional": True,
        "professional_type": "Lawyer/Title Company",
        "display_order": 1,
    },
    {
        "development_scenario": "raw_land",
        "category": ChecklistCategory.ZONING_COMPLIANCE,
        "item_title": "Verify URA Master Plan zoning",
        "item_description": "Confirm zoning designation, plot ratio, site coverage, use restrictions",
        "priority": ChecklistPriority.CRITICAL,
        "typical_duration_days": 7,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 2,
    },
    {
        "development_scenario": "raw_land",
        "category": ChecklistCategory.ENVIRONMENTAL_ASSESSMENT,
        "item_title": "Conduct Phase 1 environmental assessment",
        "item_description": "Soil testing, contamination check, groundwater assessment",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 21,
        "requires_professional": True,
        "professional_type": "Environmental Consultant",
        "display_order": 3,
    },
    {
        "development_scenario": "raw_land",
        "category": ChecklistCategory.UTILITY_CAPACITY,
        "item_title": "Check utility connection availability",
        "item_description": "Water, sewage, electricity, gas, telecoms capacity and connection costs",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 14,
        "requires_professional": True,
        "professional_type": "M&E Consultant",
        "display_order": 4,
    },
    {
        "development_scenario": "raw_land",
        "category": ChecklistCategory.ACCESS_RIGHTS,
        "item_title": "Verify access rights and easements",
        "item_description": "Confirm vehicular access, check for right-of-way issues, easements",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 10,
        "requires_professional": True,
        "professional_type": "Lawyer",
        "display_order": 5,
    },
    # EXISTING_BUILDING SCENARIO
    {
        "development_scenario": "existing_building",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "item_title": "Verify property title and strata status",
        "item_description": "Check title, strata subdivision, management corporation status",
        "priority": ChecklistPriority.CRITICAL,
        "typical_duration_days": 14,
        "requires_professional": True,
        "professional_type": "Lawyer",
        "display_order": 1,
    },
    {
        "development_scenario": "existing_building",
        "category": ChecklistCategory.STRUCTURAL_SURVEY,
        "item_title": "Conduct comprehensive structural survey",
        "item_description": "Assess structural integrity, identify defects, estimate repair costs",
        "priority": ChecklistPriority.CRITICAL,
        "typical_duration_days": 21,
        "requires_professional": True,
        "professional_type": "Structural Engineer",
        "display_order": 2,
    },
    {
        "development_scenario": "existing_building",
        "category": ChecklistCategory.STRUCTURAL_SURVEY,
        "item_title": "M&E systems assessment",
        "item_description": "Evaluate electrical, plumbing, HVAC, fire protection, lifts",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 14,
        "requires_professional": True,
        "professional_type": "M&E Consultant",
        "display_order": 3,
    },
    {
        "development_scenario": "existing_building",
        "category": ChecklistCategory.ZONING_COMPLIANCE,
        "item_title": "Verify existing use and GFA compliance",
        "item_description": "Check approved GFA, existing use authorization, any unauthorized works",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 10,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 4,
    },
    {
        "development_scenario": "existing_building",
        "category": ChecklistCategory.ENVIRONMENTAL_ASSESSMENT,
        "item_title": "Asbestos and hazardous materials survey",
        "item_description": "Check for asbestos, lead paint, other hazardous materials",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 14,
        "requires_professional": True,
        "professional_type": "Environmental Consultant",
        "display_order": 5,
    },
    # HERITAGE_PROPERTY SCENARIO
    {
        "development_scenario": "heritage_property",
        "category": ChecklistCategory.HERITAGE_CONSTRAINTS,
        "item_title": "Verify conservation status with URA",
        "item_description": "Check gazetted status, conservation guidelines, allowable modifications",
        "priority": ChecklistPriority.CRITICAL,
        "typical_duration_days": 14,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 1,
    },
    {
        "development_scenario": "heritage_property",
        "category": ChecklistCategory.HERITAGE_CONSTRAINTS,
        "item_title": "Engage heritage consultant for feasibility",
        "item_description": "Assess conservation requirements, facade retention, modern integration",
        "priority": ChecklistPriority.CRITICAL,
        "typical_duration_days": 28,
        "requires_professional": True,
        "professional_type": "Heritage Architect",
        "display_order": 2,
    },
    {
        "development_scenario": "heritage_property",
        "category": ChecklistCategory.STRUCTURAL_SURVEY,
        "item_title": "Specialized heritage structural survey",
        "item_description": "Assess historical building fabric, stability, restoration needs",
        "priority": ChecklistPriority.CRITICAL,
        "typical_duration_days": 21,
        "requires_professional": True,
        "professional_type": "Structural Engineer (Heritage Specialist)",
        "display_order": 3,
    },
    {
        "development_scenario": "heritage_property",
        "category": ChecklistCategory.ZONING_COMPLIANCE,
        "item_title": "Review bonus GFA eligibility",
        "item_description": "Check conservation bonus GFA, additional height/plot ratio allowances",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 10,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 4,
    },
    # UNDERUSED_ASSET SCENARIO
    {
        "development_scenario": "underused_asset",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "item_title": "Verify title and existing tenancies",
        "item_description": "Check title, existing lease agreements, tenant rights",
        "priority": ChecklistPriority.CRITICAL,
        "typical_duration_days": 14,
        "requires_professional": True,
        "professional_type": "Lawyer",
        "display_order": 1,
    },
    {
        "development_scenario": "underused_asset",
        "category": ChecklistCategory.ZONING_COMPLIANCE,
        "item_title": "Assess change of use feasibility",
        "item_description": "Check if proposed use change requires authority approval, restrictions",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 10,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 2,
    },
    {
        "development_scenario": "underused_asset",
        "category": ChecklistCategory.STRUCTURAL_SURVEY,
        "item_title": "Evaluate repositioning requirements",
        "item_description": "Assess building adaptability, renovation costs, AEI improvements",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 21,
        "requires_professional": True,
        "professional_type": "Architect",
        "display_order": 3,
    },
    # MIXED_USE_REDEVELOPMENT SCENARIO
    {
        "development_scenario": "mixed_use_redevelopment",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "item_title": "Verify title and subdivision potential",
        "item_description": "Check title, assess strata subdivision feasibility for mixed-use",
        "priority": ChecklistPriority.CRITICAL,
        "typical_duration_days": 14,
        "requires_professional": True,
        "professional_type": "Lawyer",
        "display_order": 1,
    },
    {
        "development_scenario": "mixed_use_redevelopment",
        "category": ChecklistCategory.ZONING_COMPLIANCE,
        "item_title": "Verify multi-use zoning permissions",
        "item_description": "Confirm zoning allows residential + commercial mix, check use group restrictions",
        "priority": ChecklistPriority.CRITICAL,
        "typical_duration_days": 10,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 2,
    },
    {
        "development_scenario": "mixed_use_redevelopment",
        "category": ChecklistCategory.UTILITY_CAPACITY,
        "item_title": "Assess mixed-use utility requirements",
        "item_description": "Check capacity for residential + commercial loads, separate metering needs",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 21,
        "requires_professional": True,
        "professional_type": "M&E Consultant",
        "display_order": 3,
    },
    {
        "development_scenario": "mixed_use_redevelopment",
        "category": ChecklistCategory.ACCESS_RIGHTS,
        "item_title": "Verify access for mixed-use operations",
        "item_description": "Check loading bays, separate entrances, service access requirements",
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 10,
        "requires_professional": True,
        "professional_type": "Architect",
        "display_order": 4,
    },
]


async def seed_templates():
    """Seed checklist templates into the database."""
    async with AsyncSessionLocal() as session:
        # Check if templates already exist
        result = await session.execute(select(DeveloperChecklistTemplate).limit(1))
        existing = result.scalar_one_or_none()

        if existing:
            print("⚠️  Templates already exist. Skipping seed.")
            print(f"   Found existing template: {existing.item_title}")
            return

        print(f"📋 Seeding {len(CHECKLIST_TEMPLATES)} checklist templates...")

        # Create all templates
        templates = [
            DeveloperChecklistTemplate(
                id=uuid4(),
                **template_data
            )
            for template_data in CHECKLIST_TEMPLATES
        ]

        session.add_all(templates)
        await session.commit()

        print(f"✅ Successfully seeded {len(templates)} checklist templates")
        print(f"   Scenarios covered: raw_land, existing_building, heritage_property, underused_asset, mixed_use_redevelopment")
        print(f"   Categories: Title, Zoning, Environmental, Structural, Heritage, Utilities, Access")


async def main():
    """Main entry point."""
    print("🌱 Starting checklist template seed...")

    async with engine.begin() as conn:
        # Ensure tables exist
        print("   Checking database tables...")

    await seed_templates()

    print("🎉 Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
