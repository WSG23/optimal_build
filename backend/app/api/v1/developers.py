"""Developer workspace API endpoints."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.developer_checklists import ChecklistStatus
from app.services.developer_checklist_service import DeveloperChecklistService
from app.services.developer_condition_service import (
    ConditionAssessment,
    DeveloperConditionService,
)

router = APIRouter(prefix="/developers", tags=["developers"])


# Request/Response Models
class ChecklistItemResponse(BaseModel):
    """Response model for a single checklist item."""

    id: str
    property_id: str
    development_scenario: str
    category: str
    item_title: str
    item_description: Optional[str]
    priority: str
    status: str
    assigned_to: Optional[str]
    due_date: Optional[str]
    completed_date: Optional[str]
    completed_by: Optional[str]
    notes: Optional[str]
    metadata: dict
    created_at: str
    updated_at: str
    requires_professional: Optional[bool] = None
    professional_type: Optional[str] = None
    typical_duration_days: Optional[int] = None
    display_order: Optional[int] = None


class ChecklistItemsResponse(BaseModel):
    """Envelope for checklist item collections."""

    items: List[ChecklistItemResponse]
    total: int


class ChecklistSummaryResponse(BaseModel):
    """Response model for checklist summary."""

    property_id: str
    total: int
    completed: int
    in_progress: int
    pending: int
    not_applicable: int
    completion_percentage: int
    by_category_status: dict[str, dict[str, int]]


class UpdateChecklistStatusRequest(BaseModel):
    """Request model for updating checklist status."""

    status: str  # pending, in_progress, completed, not_applicable
    notes: Optional[str] = None


class ConditionSystemResponse(BaseModel):
    """System-level assessment details."""

    name: str
    rating: str
    score: int
    notes: str
    recommended_actions: List[str]


class ConditionAssessmentResponse(BaseModel):
    """Developer-friendly property condition assessment."""

    property_id: str
    overall_score: int
    overall_rating: str
    risk_level: str
    summary: str
    scenario_context: Optional[str] = None
    systems: List[ConditionSystemResponse]
    recommended_actions: List[str]


@router.get(
    "/properties/{property_id}/checklists",
    response_model=ChecklistItemsResponse,
)
async def get_property_checklists(
    property_id: UUID,
    development_scenario: Optional[str] = None,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """
    Get due diligence checklist items for a property.

    Optionally filter by development scenario and/or status.
    """
    # Parse status if provided
    checklist_status = None
    if status:
        try:
            checklist_status = ChecklistStatus(status)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of: pending, in_progress, completed, not_applicable",
            ) from exc

    items = await DeveloperChecklistService.get_property_checklist(
        session,
        property_id,
        development_scenario=development_scenario,
        status=checklist_status,
    )

    payloads = [item.to_dict() for item in items]
    response_items = [ChecklistItemResponse(**payload) for payload in payloads]
    return ChecklistItemsResponse(items=response_items, total=len(response_items))


@router.get(
    "/properties/{property_id}/checklists/summary",
    response_model=ChecklistSummaryResponse,
)
async def get_checklist_summary(
    property_id: UUID,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Get a summary of checklist completion status for a property."""
    summary = await DeveloperChecklistService.get_checklist_summary(
        session, property_id
    )
    return ChecklistSummaryResponse(**summary)


@router.patch(
    "/checklists/{checklist_id}",
    response_model=ChecklistItemResponse,
)
async def update_checklist_item(
    checklist_id: UUID,
    request: UpdateChecklistStatusRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Update a checklist item's status and notes."""
    try:
        checklist_status = ChecklistStatus(request.status)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}. Must be one of: pending, in_progress, completed, not_applicable",
        ) from exc

    # Get user_id if authenticated
    completed_by = UUID(token.user_id) if token and token.user_id else None

    updated_item = await DeveloperChecklistService.update_checklist_status(
        session,
        checklist_id,
        checklist_status,
        completed_by=completed_by,
        notes=request.notes,
    )

    if not updated_item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    await session.commit()

    return ChecklistItemResponse(**updated_item.to_dict())


@router.get(
    "/properties/{property_id}/condition-assessment",
    response_model=ConditionAssessmentResponse,
)
async def get_condition_assessment(
    property_id: UUID,
    scenario: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """
    Generate a developer property condition assessment.

    Optionally pass `scenario` (e.g. existing_building, heritage_property) to
    contextualise the recommendation set.
    """

    try:
        assessment: ConditionAssessment = (
            await DeveloperConditionService.generate_assessment(
                session=session,
                property_id=property_id,
                scenario=scenario,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    response_payload = ConditionAssessmentResponse(
        property_id=str(assessment.property_id),
        overall_score=assessment.overall_score,
        overall_rating=assessment.overall_rating,
        risk_level=assessment.risk_level,
        summary=assessment.summary,
        scenario_context=assessment.scenario_context,
        systems=[
            ConditionSystemResponse(
                name=system.name,
                rating=system.rating,
                score=system.score,
                notes=system.notes,
                recommended_actions=system.recommended_actions,
            )
            for system in assessment.systems
        ],
        recommended_actions=assessment.recommended_actions,
    )
    return response_payload


__all__ = ["router"]
