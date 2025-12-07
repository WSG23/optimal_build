"""Construction Delivery API (Phase 2G).

Handles:
- Contractor management
- Quality inspections
- Safety incidents
- Drawdown requests (Construction Loan)
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.construction import ContractorType, InspectionStatus, DrawdownStatus
from app.schemas.construction import (
    ContractorCreate,
    ContractorUpdate,
    ContractorResponse,
    QualityInspectionCreate,
    QualityInspectionUpdate,
    QualityInspectionResponse,
    SafetyIncidentCreate,
    SafetyIncidentUpdate,
    SafetyIncidentResponse,
    DrawdownRequestCreate,
    DrawdownRequestUpdate,
    DrawdownRequestResponse,
)
from app.services.construction.project_manager import ConstructionProjectManager
from app.services.construction.construction_finance import ConstructionFinanceService

router = APIRouter(prefix="/projects", tags=["Construction"])


# Helper to get services
def get_project_manager(
    session: AsyncSession = Depends(get_session),
) -> ConstructionProjectManager:
    return ConstructionProjectManager(session)


def get_finance_service(
    session: AsyncSession = Depends(get_session),
) -> ConstructionFinanceService:
    return ConstructionFinanceService(session)


# --- Contractors ---


@router.post(
    "/{project_id}/contractors",
    response_model=ContractorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_contractor(
    project_id: UUID,
    payload: ContractorCreate,
    service: ConstructionProjectManager = Depends(get_project_manager),
) -> ContractorResponse:
    """Register a new contractor for the project."""
    if payload.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch in payload")
    return await service.create_contractor(payload)


@router.get("/{project_id}/contractors", response_model=List[ContractorResponse])
async def list_contractors(
    project_id: UUID,
    type: Optional[ContractorType] = None,
    service: ConstructionProjectManager = Depends(get_project_manager),
) -> List[ContractorResponse]:
    """List all contractors for the project."""
    return await service.get_contractors(project_id, contractor_type=type)


@router.patch("/contractors/{contractor_id}", response_model=ContractorResponse)
async def update_contractor(
    contractor_id: UUID,
    payload: ContractorUpdate,
    service: ConstructionProjectManager = Depends(get_project_manager),
) -> ContractorResponse:
    """Update contractor details."""
    contractor = await service.update_contractor(contractor_id, payload)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return contractor


# --- Quality Inspections ---


@router.post(
    "/{project_id}/inspections",
    response_model=QualityInspectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_inspection(
    project_id: UUID,
    payload: QualityInspectionCreate,
    service: ConstructionProjectManager = Depends(get_project_manager),
) -> QualityInspectionResponse:
    """Log a new quality inspection."""
    if payload.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch in payload")
    return await service.create_inspection(payload)


@router.get("/{project_id}/inspections", response_model=List[QualityInspectionResponse])
async def list_inspections(
    project_id: UUID,
    status: Optional[InspectionStatus] = None,
    service: ConstructionProjectManager = Depends(get_project_manager),
) -> List[QualityInspectionResponse]:
    """List inspections for the project."""
    return await service.get_inspections(project_id, status=status)


@router.patch("/inspections/{inspection_id}", response_model=QualityInspectionResponse)
async def update_inspection(
    inspection_id: UUID,
    payload: QualityInspectionUpdate,
    service: ConstructionProjectManager = Depends(get_project_manager),
) -> QualityInspectionResponse:
    """Update inspection details."""
    inspection = await service.update_inspection(inspection_id, payload)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


# --- Safety Incidents ---


@router.post(
    "/{project_id}/incidents",
    response_model=SafetyIncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def report_incident(
    project_id: UUID,
    payload: SafetyIncidentCreate,
    service: ConstructionProjectManager = Depends(get_project_manager),
) -> SafetyIncidentResponse:
    """Report a safety incident."""
    if payload.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch in payload")
    return await service.create_safety_incident(payload)


@router.get("/{project_id}/incidents", response_model=List[SafetyIncidentResponse])
async def list_incidents(
    project_id: UUID,
    unresolved: bool = False,
    service: ConstructionProjectManager = Depends(get_project_manager),
) -> List[SafetyIncidentResponse]:
    """List safety incidents."""
    return await service.get_safety_incidents(project_id, unresolved_only=unresolved)


@router.patch("/incidents/{incident_id}", response_model=SafetyIncidentResponse)
async def update_incident(
    incident_id: UUID,
    payload: SafetyIncidentUpdate,
    service: ConstructionProjectManager = Depends(get_project_manager),
) -> SafetyIncidentResponse:
    """Update incident details or resolve it."""
    incident = await service.update_safety_incident(incident_id, payload)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


# --- Drawdown Requests (Construction Finance) ---


@router.post(
    "/{project_id}/drawdowns",
    response_model=DrawdownRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_drawdown(
    project_id: UUID,
    payload: DrawdownRequestCreate,
    service: ConstructionFinanceService = Depends(get_finance_service),
) -> DrawdownRequestResponse:
    """Submit a new drawdown request."""
    if payload.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch in payload")
    return await service.create_drawdown_request(payload)


@router.get("/{project_id}/drawdowns", response_model=List[DrawdownRequestResponse])
async def list_drawdowns(
    project_id: UUID,
    status: Optional[DrawdownStatus] = None,
    service: ConstructionFinanceService = Depends(get_finance_service),
) -> List[DrawdownRequestResponse]:
    """List drawdown requests."""
    return await service.get_drawdown_requests(project_id, status=status)


@router.patch("/drawdowns/{drawdown_id}", response_model=DrawdownRequestResponse)
async def update_drawdown(
    drawdown_id: UUID,
    payload: DrawdownRequestUpdate,
    service: ConstructionFinanceService = Depends(get_finance_service),
) -> DrawdownRequestResponse:
    """Update drawdown details."""
    request = await service.update_drawdown_request(drawdown_id, payload)
    if not request:
        raise HTTPException(status_code=404, detail="Drawdown request not found")
    return request


@router.post("/drawdowns/{drawdown_id}/approve", response_model=DrawdownRequestResponse)
async def approve_drawdown(
    drawdown_id: UUID,
    approved_amount: Optional[float] = None,
    service: ConstructionFinanceService = Depends(get_finance_service),
) -> DrawdownRequestResponse:
    """Approve a drawdown request (Architect Approval)."""
    request = await service.approve_drawdown(drawdown_id, approved_amount)
    if not request:
        raise HTTPException(status_code=404, detail="Drawdown request not found")
    return request
