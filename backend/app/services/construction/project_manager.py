"""Construction project management service.

Handles:
- Contractor management
- Quality inspections
- Safety incident logging
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.construction import (
    Contractor,
    ContractorType,
    InspectionStatus,
    QualityInspection,
    SafetyIncident,
)
from app.schemas.construction import (
    ContractorCreate,
    ContractorUpdate,
    QualityInspectionCreate,
    QualityInspectionUpdate,
    SafetyIncidentCreate,
    SafetyIncidentUpdate,
)


class ConstructionProjectManager:
    """Service for managing construction execution details."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Contractors ---

    async def create_contractor(self, payload: ContractorCreate) -> Contractor:
        """Create a new contractor."""
        contractor = Contractor(**payload.model_dump())
        self.session.add(contractor)
        await self.session.commit()
        await self.session.refresh(contractor)
        return contractor

    async def get_contractors(
        self, project_id: UUID, contractor_type: Optional[ContractorType] = None
    ) -> List[Contractor]:
        """List contractors for a project."""
        query = select(Contractor).where(Contractor.project_id == project_id)
        if contractor_type:
            query = query.where(Contractor.contractor_type == contractor_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_contractor(self, contractor_id: UUID) -> Optional[Contractor]:
        """Get contractor by ID."""
        return await self.session.get(Contractor, contractor_id)

    async def update_contractor(
        self, contractor_id: UUID, payload: ContractorUpdate
    ) -> Optional[Contractor]:
        """Update a contractor."""
        contractor = await self.get_contractor(contractor_id)
        if not contractor:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contractor, key, value)

        await self.session.commit()
        await self.session.refresh(contractor)
        return contractor

    # --- Quality Inspections ---

    async def create_inspection(
        self, payload: QualityInspectionCreate
    ) -> QualityInspection:
        """Log a quality inspection."""
        inspection = QualityInspection(**payload.model_dump())
        self.session.add(inspection)
        await self.session.commit()
        await self.session.refresh(inspection)
        return inspection

    async def get_inspections(
        self, project_id: UUID, status: Optional[InspectionStatus] = None
    ) -> List[QualityInspection]:
        """List inspections for a project."""
        query = select(QualityInspection).where(
            QualityInspection.project_id == project_id
        )
        if status:
            query = query.where(QualityInspection.status == status)
        query = query.order_by(desc(QualityInspection.inspection_date))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_inspection(
        self, inspection_id: UUID, payload: QualityInspectionUpdate
    ) -> Optional[QualityInspection]:
        """Update an inspection record."""
        inspection = await self.session.get(QualityInspection, inspection_id)
        if not inspection:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(inspection, key, value)

        await self.session.commit()
        await self.session.refresh(inspection)
        return inspection

    # --- Safety Incidents ---

    async def create_safety_incident(
        self, payload: SafetyIncidentCreate
    ) -> SafetyIncident:
        """Log a safety incident."""
        incident = SafetyIncident(**payload.model_dump())
        self.session.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def get_safety_incidents(
        self, project_id: UUID, unresolved_only: bool = False
    ) -> List[SafetyIncident]:
        """List safety incidents for a project."""
        query = select(SafetyIncident).where(SafetyIncident.project_id == project_id)
        if unresolved_only:
            query = query.where(SafetyIncident.is_resolved.is_(False))
        query = query.order_by(desc(SafetyIncident.incident_date))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_safety_incident(
        self, incident_id: UUID, payload: SafetyIncidentUpdate
    ) -> Optional[SafetyIncident]:
        """Update a safety incident."""
        incident = await self.session.get(SafetyIncident, incident_id)
        if not incident:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(incident, key, value)

        await self.session.commit()
        await self.session.refresh(incident)
        return incident
