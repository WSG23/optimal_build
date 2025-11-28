"""Checklist API endpoints for developer workspace."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.developer_checklists import ChecklistStatus, DeveloperChecklistTemplate
from app.services.developer_checklist_service import (
    DEFAULT_TEMPLATE_DEFINITIONS,
    DeveloperChecklistService,
)

router = APIRouter(prefix="/developers", tags=["developers"])


# =============================================================================
# Request/Response Models
# =============================================================================


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


class ChecklistTemplateResponse(BaseModel):
    """Serialized checklist template record."""

    model_config = {"populate_by_name": True}

    id: str
    development_scenario: str = Field(alias="developmentScenario")
    category: str
    item_title: str = Field(alias="itemTitle")
    item_description: Optional[str] = Field(default=None, alias="itemDescription")
    priority: str
    typical_duration_days: Optional[int] = Field(
        default=None, alias="typicalDurationDays"
    )
    requires_professional: bool = Field(alias="requiresProfessional")
    professional_type: Optional[str] = Field(default=None, alias="professionalType")
    display_order: int = Field(alias="displayOrder")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class ChecklistTemplateBaseRequest(BaseModel):
    """Base payload for template authoring."""

    model_config = {"populate_by_name": True}

    development_scenario: str = Field(alias="developmentScenario")
    category: str
    item_title: str = Field(alias="itemTitle")
    item_description: Optional[str] = Field(default=None, alias="itemDescription")
    priority: str
    typical_duration_days: Optional[int] = Field(
        default=None, alias="typicalDurationDays", ge=0
    )
    requires_professional: bool = Field(default=False, alias="requiresProfessional")
    professional_type: Optional[str] = Field(default=None, alias="professionalType")
    display_order: Optional[int] = Field(default=None, alias="displayOrder")


class ChecklistTemplateCreateRequest(ChecklistTemplateBaseRequest):
    """Create payload (inherits base fields)."""


class ChecklistTemplateUpdateRequest(BaseModel):
    """Partial update payload for checklist templates."""

    model_config = {"populate_by_name": True}

    development_scenario: Optional[str] = Field(
        default=None, alias="developmentScenario"
    )
    category: Optional[str] = None
    item_title: Optional[str] = Field(default=None, alias="itemTitle")
    item_description: Optional[str] = Field(default=None, alias="itemDescription")
    priority: Optional[str] = None
    typical_duration_days: Optional[int] = Field(
        default=None, alias="typicalDurationDays", ge=0
    )
    requires_professional: Optional[bool] = Field(
        default=None, alias="requiresProfessional"
    )
    professional_type: Optional[str] = Field(default=None, alias="professionalType")
    display_order: Optional[int] = Field(default=None, alias="displayOrder")


class ChecklistTemplateBulkImportRequest(BaseModel):
    """Bulk authoring payload for template definitions."""

    model_config = {"populate_by_name": True}

    templates: List[ChecklistTemplateBaseRequest] = Field(default_factory=list)
    replace_existing: bool = Field(default=False, alias="replaceExisting")


class ChecklistTemplateBulkImportResponse(BaseModel):
    """Summary of bulk import results."""

    model_config = {"populate_by_name": True}

    created: int
    updated: int
    deleted: int


class UpdateChecklistStatusRequest(BaseModel):
    """Request model for updating checklist status."""

    status: str  # pending, in_progress, completed, not_applicable
    notes: Optional[str] = None


class ChecklistProgressResponse(BaseModel):
    """Summary of checklist completion."""

    model_config = {"populate_by_name": True}

    total: int
    completed: int
    in_progress: int = Field(alias="inProgress")
    pending: int
    not_applicable: int = Field(alias="notApplicable")
    completion_percentage: int = Field(alias="completionPercentage")


# =============================================================================
# Helper Functions
# =============================================================================


def _serialize_checklist_template(
    template: DeveloperChecklistTemplate,
) -> ChecklistTemplateResponse:
    return ChecklistTemplateResponse(
        id=str(template.id),
        developmentScenario=template.development_scenario,
        category=template.category.value,
        itemTitle=template.item_title,
        itemDescription=template.item_description,
        priority=template.priority.value,
        typicalDurationDays=template.typical_duration_days,
        requiresProfessional=template.requires_professional,
        professionalType=template.professional_type,
        displayOrder=template.display_order,
        createdAt=template.created_at.isoformat(),
        updatedAt=template.updated_at.isoformat(),
    )


# =============================================================================
# Route Handlers - Templates
# =============================================================================


@router.get(
    "/checklists/templates",
    response_model=List[ChecklistTemplateResponse],
)
async def list_checklist_templates(
    development_scenario: Optional[str] = Query(
        default=None, alias="developmentScenario"
    ),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> List[Dict[str, Any]]:
    """Return checklist templates, optionally filtered by development scenario."""

    await DeveloperChecklistService.ensure_templates_seeded(session)
    templates = await DeveloperChecklistService.list_templates(
        session, development_scenario=development_scenario
    )
    return [
        _serialize_checklist_template(template).model_dump(by_alias=True)
        for template in templates
    ]


@router.post(
    "/checklists/templates",
    response_model=ChecklistTemplateResponse,
    status_code=201,
)
async def create_checklist_template(
    request: ChecklistTemplateCreateRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> Dict[str, Any]:
    """Create a new checklist template definition."""

    try:
        template = await DeveloperChecklistService.create_template(
            session, request.model_dump(exclude_none=True, by_alias=False)
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await session.commit()
    return _serialize_checklist_template(template).model_dump(by_alias=True)


@router.put(
    "/checklists/templates/{template_id}",
    response_model=ChecklistTemplateResponse,
)
async def update_checklist_template(
    template_id: UUID,
    request: ChecklistTemplateUpdateRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> Dict[str, Any]:
    """Update an existing checklist template definition."""

    try:
        template = await DeveloperChecklistService.update_template(
            session, template_id, request.model_dump(exclude_none=True, by_alias=False)
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await session.commit()
    return _serialize_checklist_template(template).model_dump(by_alias=True)


@router.delete(
    "/checklists/templates/{template_id}",
    status_code=204,
)
async def delete_checklist_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> Response:
    """Delete a checklist template."""

    deleted = await DeveloperChecklistService.delete_template(session, template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")

    await session.commit()
    return Response(status_code=204)


@router.post(
    "/checklists/templates/import",
    response_model=ChecklistTemplateBulkImportResponse,
)
async def bulk_import_checklist_templates(
    request: ChecklistTemplateBulkImportRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> ChecklistTemplateBulkImportResponse:
    """Bulk import checklist templates from a JSON payload."""

    templates_payload = [
        template.model_dump(exclude_none=True, by_alias=False)
        for template in request.templates
    ]

    result = await DeveloperChecklistService.bulk_upsert_templates(
        session, templates_payload, replace_existing=request.replace_existing
    )
    await session.commit()
    return ChecklistTemplateBulkImportResponse(**result)


# =============================================================================
# Route Handlers - Property Checklists
# =============================================================================


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
) -> ChecklistItemsResponse:
    """
    Get due diligence checklist items for a property.

    Optionally filter by development scenario and/or status.
    """
    await DeveloperChecklistService.ensure_templates_seeded(session)

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

    if not items:
        if development_scenario:
            scenarios_to_seed = [development_scenario]
        else:
            scenarios_to_seed = sorted(
                {
                    str(defn["development_scenario"])
                    for defn in DEFAULT_TEMPLATE_DEFINITIONS
                }
            )
        created = await DeveloperChecklistService.auto_populate_checklist(
            session=session,
            property_id=property_id,
            development_scenarios=scenarios_to_seed,
        )
        if created:
            await session.commit()
            items = await DeveloperChecklistService.get_property_checklist(
                session,
                property_id,
                development_scenario=development_scenario,
                status=checklist_status,
            )

    payloads = DeveloperChecklistService.format_property_checklist_items(items)
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
) -> ChecklistSummaryResponse:
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
) -> ChecklistItemResponse:
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
