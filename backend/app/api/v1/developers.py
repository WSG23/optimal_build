"""Developer workspace API endpoints."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.developer_checklists import ChecklistStatus
from app.services.developer_checklist_service import DeveloperChecklistService
from app.services.developer_condition_service import (
    ConditionAssessment,
    ConditionSystem,
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
    scenario: Optional[str] = None
    overall_score: int
    overall_rating: str
    risk_level: str
    summary: str
    scenario_context: Optional[str] = None
    systems: List[ConditionSystemResponse]
    recommended_actions: List[str]
    recorded_at: Optional[str] = None


class ConditionSystemRequest(BaseModel):
    """Payload for persisting inspection system data."""

    model_config = {"populate_by_name": True}

    name: str
    rating: str
    score: int
    notes: str
    recommended_actions: List[str] = Field(
        default_factory=list, alias="recommendedActions"
    )


class ConditionAssessmentUpsertRequest(BaseModel):
    """Payload for saving developer inspection assessments."""

    model_config = {"populate_by_name": True}

    scenario: Optional[str] = None
    overall_rating: str = Field(alias="overallRating")
    overall_score: int = Field(alias="overallScore")
    risk_level: str = Field(alias="riskLevel")
    summary: str
    scenario_context: Optional[str] = Field(default=None, alias="scenarioContext")
    systems: List[ConditionSystemRequest]
    recommended_actions: List[str] = Field(
        default_factory=list, alias="recommendedActions"
    )


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

    scenario_key = _normalise_scenario_param(scenario)
    try:
        assessment: ConditionAssessment = (
            await DeveloperConditionService.generate_assessment(
                session=session,
                property_id=property_id,
                scenario=scenario_key,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _serialize_condition_assessment(assessment)


@router.put(
    "/properties/{property_id}/condition-assessment",
    response_model=ConditionAssessmentResponse,
)
async def upsert_condition_assessment(
    property_id: UUID,
    request: ConditionAssessmentUpsertRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Persist a developer inspection assessment for a property."""

    scenario_key = _normalise_scenario_param(request.scenario)
    recorded_by = UUID(token.user_id) if token and token.user_id else None
    systems = [
        ConditionSystem(
            name=item.name,
            rating=item.rating,
            score=item.score,
            notes=item.notes,
            recommended_actions=item.recommended_actions,
        )
        for item in request.systems
    ]

    assessment = await DeveloperConditionService.record_assessment(
        session=session,
        property_id=property_id,
        scenario=scenario_key,
        overall_rating=request.overall_rating,
        overall_score=request.overall_score,
        risk_level=request.risk_level,
        summary=request.summary,
        scenario_context=request.scenario_context,
        systems=systems,
        recommended_actions=request.recommended_actions,
        recorded_by=recorded_by,
    )
    await session.commit()
    return _serialize_condition_assessment(assessment)


@router.get(
    "/properties/{property_id}/condition-assessment/history",
    response_model=List[ConditionAssessmentResponse],
)
async def get_condition_assessment_history(
    property_id: UUID,
    scenario: Optional[str] = None,
    limit: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Return stored inspection assessments ordered by most recent first."""

    scenario_key = _normalise_scenario_param(scenario)
    history = await DeveloperConditionService.get_assessment_history(
        session=session,
        property_id=property_id,
        scenario=scenario_key,
        limit=limit,
    )
    return [_serialize_condition_assessment(item) for item in history]


@router.get(
    "/properties/{property_id}/condition-assessment/scenarios",
    response_model=List[ConditionAssessmentResponse],
)
async def get_condition_assessment_scenarios(
    property_id: UUID,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Return the latest stored inspection assessment for each scenario."""

    assessments = await DeveloperConditionService.get_latest_assessments_by_scenario(
        session=session,
        property_id=property_id,
    )
    return [_serialize_condition_assessment(assessment) for assessment in assessments]


def _serialize_condition_system(system: ConditionSystem) -> ConditionSystemResponse:
    return ConditionSystemResponse(
        name=system.name,
        rating=system.rating,
        score=system.score,
        notes=system.notes,
        recommended_actions=system.recommended_actions,
    )


def _serialize_condition_assessment(
    assessment: ConditionAssessment,
) -> ConditionAssessmentResponse:
    recorded_at = assessment.recorded_at.isoformat() if assessment.recorded_at else None
    return ConditionAssessmentResponse(
        property_id=str(assessment.property_id),
        scenario=assessment.scenario,
        overall_score=assessment.overall_score,
        overall_rating=assessment.overall_rating,
        risk_level=assessment.risk_level,
        summary=assessment.summary,
        scenario_context=assessment.scenario_context,
        systems=[_serialize_condition_system(system) for system in assessment.systems],
        recommended_actions=assessment.recommended_actions,
        recorded_at=recorded_at,
    )


def _normalise_scenario_param(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    slug = value.strip().lower()
    if not slug or slug == "all":
        return None
    return slug


__all__ = ["router"]
