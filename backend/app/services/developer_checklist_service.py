"""Developer due diligence checklist service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.developer_checklists import (
    ChecklistStatus,
    DeveloperChecklistTemplate,
    DeveloperPropertyChecklist,
)


class DeveloperChecklistService:
    """Service for managing developer due diligence checklists."""

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

        for scenario in development_scenarios:
            # Get templates for this scenario
            templates = await DeveloperChecklistService.get_templates_for_scenario(
                session, scenario
            )

            for template in templates:
                # Create property checklist item from template
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

        total = len(items)
        if total == 0:
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "not_applicable": 0,
                "completion_percentage": 0,
            }

        completed = sum(1 for item in items if item.status == ChecklistStatus.COMPLETED)
        in_progress = sum(
            1 for item in items if item.status == ChecklistStatus.IN_PROGRESS
        )
        pending = sum(1 for item in items if item.status == ChecklistStatus.PENDING)
        not_applicable = sum(
            1 for item in items if item.status == ChecklistStatus.NOT_APPLICABLE
        )

        completion_percentage = int((completed / total) * 100) if total > 0 else 0

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "not_applicable": not_applicable,
            "completion_percentage": completion_percentage,
        }
