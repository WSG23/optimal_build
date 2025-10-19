"""Developer due diligence checklist service."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.developer_checklists import (
    ChecklistCategory,
    ChecklistPriority,
    ChecklistStatus,
    DeveloperChecklistTemplate,
    DeveloperPropertyChecklist,
)

# NOTE: These definitions intentionally mirror the template data used by the
# seeding script in ``backend/scripts/seed_checklist_templates.py`` so the
# automatic seeding logic and manual script stay consistent. Keeping the data
# here allows service-level tests to exercise idempotent seeding without having
# to reach for the CLI script during unit tests.
DEFAULT_TEMPLATE_DEFINITIONS: Tuple[Dict[str, object], ...] = (
    {
        "development_scenario": "raw_land",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "item_title": "Verify land title and ownership",
        "item_description": (
            "Confirm clear title, check for encumbrances, mortgages, or liens"
        ),
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
        "item_description": (
            "Confirm zoning designation, plot ratio, site coverage, use restrictions"
        ),
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
        "item_description": (
            "Soil testing, contamination check, groundwater assessment"
        ),
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
        "item_description": (
            "Water, sewage, electricity, gas, telecoms capacity and connection costs"
        ),
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
        "item_description": (
            "Confirm vehicular access, check for right-of-way issues, easements"
        ),
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 10,
        "requires_professional": True,
        "professional_type": "Lawyer",
        "display_order": 5,
    },
    {
        "development_scenario": "existing_building",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "item_title": "Verify property title and strata status",
        "item_description": (
            "Check title, strata subdivision, management corporation status"
        ),
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
        "item_description": (
            "Assess structural integrity, identify defects, estimate repair costs"
        ),
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
        "item_description": (
            "Evaluate electrical, plumbing, HVAC, fire protection, lifts"
        ),
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
        "item_description": (
            "Check approved GFA, existing use authorization, any unauthorized works"
        ),
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
        "item_description": (
            "Check for asbestos, lead paint, other hazardous materials"
        ),
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 14,
        "requires_professional": True,
        "professional_type": "Environmental Consultant",
        "display_order": 5,
    },
    {
        "development_scenario": "heritage_property",
        "category": ChecklistCategory.HERITAGE_CONSTRAINTS,
        "item_title": "Verify conservation status with URA",
        "item_description": (
            "Check gazetted status, conservation guidelines, allowable modifications"
        ),
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
        "item_description": (
            "Assess conservation requirements, facade retention, modern integration"
        ),
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
        "item_description": (
            "Assess historical building fabric, stability, restoration needs"
        ),
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
        "item_description": (
            "Check conservation bonus GFA, additional height/plot ratio allowances"
        ),
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 10,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 4,
    },
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
        "item_description": (
            "Check if proposed use change requires authority approval, restrictions"
        ),
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
        "item_description": (
            "Assess building adaptability, renovation costs, AEI improvements"
        ),
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 21,
        "requires_professional": True,
        "professional_type": "Architect",
        "display_order": 3,
    },
    {
        "development_scenario": "mixed_use_redevelopment",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "item_title": "Verify title and subdivision potential",
        "item_description": (
            "Check title, assess strata subdivision feasibility for mixed-use"
        ),
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
        "item_description": (
            "Confirm zoning allows residential + commercial mix, check use group restrictions"
        ),
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
        "item_description": (
            "Check capacity for residential + commercial loads, separate metering needs"
        ),
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
        "item_description": (
            "Check loading bays, separate entrances, service access requirements"
        ),
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": 10,
        "requires_professional": True,
        "professional_type": "Architect",
        "display_order": 4,
    },
)


def _existing_template_keys(
    templates: Sequence[DeveloperChecklistTemplate],
) -> set[Tuple[str, str]]:
    """Build a lookup of (scenario, title) pairs for fast duplicate detection."""

    return {
        (template.development_scenario, template.item_title)
        for template in templates
    }


class DeveloperChecklistService:
    """Service for managing developer due diligence checklists."""

    @staticmethod
    async def ensure_templates_seeded(session: AsyncSession) -> bool:
        """Ensure default checklist templates exist.

        Returns ``True`` if new templates were inserted, otherwise ``False``.
        The implementation is intentionally idempotent so repeated invocations
        never create duplicate template rows.
        """

        # Load existing templates once to avoid repeated queries when checking
        # for duplicates.
        existing_result = await session.execute(select(DeveloperChecklistTemplate))
        existing_templates = list(existing_result.scalars().all())
        existing_keys = _existing_template_keys(existing_templates)

        templates_to_create: List[DeveloperChecklistTemplate] = []
        for definition in DEFAULT_TEMPLATE_DEFINITIONS:
            key = (
                definition["development_scenario"],
                definition["item_title"],
            )
            if key in existing_keys:
                continue

            templates_to_create.append(DeveloperChecklistTemplate(**definition))

        if not templates_to_create:
            return False

        session.add_all(templates_to_create)
        await session.flush()
        return True

    @staticmethod
    async def get_templates_for_scenario(
        session: AsyncSession,
        development_scenario: str,
    ) -> List[DeveloperChecklistTemplate]:
        """Get all checklist templates for a development scenario."""
        result = await session.execute(
            select(DeveloperChecklistTemplate)
            .where(
                DeveloperChecklistTemplate.development_scenario == development_scenario
            )
            .order_by(DeveloperChecklistTemplate.display_order)
        )
        return list(result.scalars().all())

    @staticmethod
    async def auto_populate_checklist(
        session: AsyncSession,
        property_id: UUID,
        development_scenarios: List[str],
        assigned_to: Optional[UUID] = None,
    ) -> List[DeveloperPropertyChecklist]:
        """
        Auto-populate checklist items for a property based on development scenarios.

        Creates property-specific checklist items from templates for each selected scenario.
        """
        created_items: List[DeveloperPropertyChecklist] = []

        # Identify existing checklist rows so we don't duplicate entries when
        # the method is invoked multiple times for the same property.
        existing_items = await session.execute(
            select(
                DeveloperPropertyChecklist.template_id,
                DeveloperPropertyChecklist.item_title,
                DeveloperPropertyChecklist.development_scenario,
            ).where(DeveloperPropertyChecklist.property_id == property_id)
        )
        existing_lookup = {
            (
                row.template_id or row.item_title,
                row.item_title,
                row.development_scenario,
            )
            for row in existing_items.all()
        }

        for scenario in development_scenarios:
            # Get templates for this scenario
            templates = await DeveloperChecklistService.get_templates_for_scenario(
                session, scenario
            )

            for template in templates:
                # Create property checklist item from template
                template_identifier = template.id or template.item_title
                duplicate_key = (template_identifier, template.item_title, scenario)
                if duplicate_key in existing_lookup:
                    continue

                due_date = None
                if template.typical_duration_days:
                    due_date = (
                        datetime.utcnow()
                        + timedelta(days=template.typical_duration_days)
                    ).date()

                checklist_item = DeveloperPropertyChecklist(
                    property_id=property_id,
                    template_id=template.id,
                    development_scenario=template.development_scenario,
                    category=template.category,
                    item_title=template.item_title,
                    item_description=template.item_description,
                    priority=template.priority,
                    status=ChecklistStatus.PENDING,
                    assigned_to=assigned_to,
                    due_date=due_date,
                    metadata={
                        "requires_professional": template.requires_professional,
                        "professional_type": template.professional_type,
                        "typical_duration_days": template.typical_duration_days,
                    },
                )
                session.add(checklist_item)
                created_items.append(checklist_item)

                existing_lookup.add(duplicate_key)

        await session.flush()
        return created_items

    @staticmethod
    async def get_property_checklist(
        session: AsyncSession,
        property_id: UUID,
        development_scenario: Optional[str] = None,
        status: Optional[ChecklistStatus] = None,
    ) -> List[DeveloperPropertyChecklist]:
        """Get checklist items for a property, optionally filtered by scenario and status."""
        query = select(DeveloperPropertyChecklist).where(
            DeveloperPropertyChecklist.property_id == property_id
        )

        if development_scenario:
            query = query.where(
                DeveloperPropertyChecklist.development_scenario == development_scenario
            )

        if status:
            query = query.where(DeveloperPropertyChecklist.status == status)

        query = query.order_by(
            DeveloperPropertyChecklist.development_scenario,
            DeveloperPropertyChecklist.category,
            DeveloperPropertyChecklist.created_at,
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_checklist_status(
        session: AsyncSession,
        checklist_id: UUID,
        status: ChecklistStatus,
        completed_by: Optional[UUID] = None,
        notes: Optional[str] = None,
    ) -> Optional[DeveloperPropertyChecklist]:
        """Update the status of a checklist item."""
        result = await session.execute(
            select(DeveloperPropertyChecklist).where(
                DeveloperPropertyChecklist.id == checklist_id
            )
        )
        checklist_item = result.scalar_one_or_none()

        if not checklist_item:
            return None

        checklist_item.status = status

        if status == ChecklistStatus.COMPLETED:
            checklist_item.completed_date = datetime.utcnow().date()
            if completed_by:
                checklist_item.completed_by = completed_by

        if notes:
            checklist_item.notes = notes

        await session.flush()
        return checklist_item

    @staticmethod
    async def get_checklist_summary(
        session: AsyncSession,
        property_id: UUID,
    ) -> dict:
        """Get a summary of checklist completion status for a property."""
        items = await DeveloperChecklistService.get_property_checklist(
            session, property_id
        )

        totals = {
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "not_applicable": 0,
        }
        category_breakdown: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "not_applicable": 0,
            }
        )

        for item in items:
            status_key = item.status.value
            if status_key in totals:
                totals[status_key] += 1

            category_key = item.category.value
            category_breakdown[category_key]["total"] += 1
            if status_key in category_breakdown[category_key]:
                category_breakdown[category_key][status_key] += 1

        total_items = len(items)
        completion_percentage = (
            int((totals["completed"] / total_items) * 100)
            if total_items
            else 0
        )

        return {
            "property_id": str(property_id),
            "total": total_items,
            "completed": totals["completed"],
            "in_progress": totals["in_progress"],
            "pending": totals["pending"],
            "not_applicable": totals["not_applicable"],
            "completion_percentage": completion_percentage,
            "by_category_status": dict(category_breakdown),
        }
