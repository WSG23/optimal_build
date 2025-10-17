"""Developer workspace API endpoints."""

from __future__ import annotations

import html
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.developer_checklists import (
    ChecklistStatus,
    DeveloperChecklistTemplate,
)
from app.models.property import Property
from app.services.developer_checklist_service import (
    DEFAULT_TEMPLATE_DEFINITIONS,
    DeveloperChecklistService,
)
from app.services.developer_condition_service import (
    ConditionAssessment,
    ConditionSystem,
    DeveloperConditionService,
)
from app.utils.render import render_html_to_pdf

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


class ConditionSystemResponse(BaseModel):
    """System-level assessment details."""

    name: str
    rating: str
    score: int
    notes: str
    recommended_actions: List[str]


class ConditionInsightResponse(BaseModel):
    """Insight surfaced from condition assessment heuristics."""

    id: str
    severity: str
    title: str
    detail: str
    specialist: Optional[str] = None


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
    insights: List[ConditionInsightResponse] = Field(default_factory=list)


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


class ChecklistProgressResponse(BaseModel):
    """Summary of checklist completion."""

    model_config = {"populate_by_name": True}

    total: int
    completed: int
    in_progress: int = Field(alias="inProgress")
    pending: int
    not_applicable: int = Field(alias="notApplicable")
    completion_percentage: int = Field(alias="completionPercentage")


class ConditionReportResponse(BaseModel):
    """Structured condition assessment export."""

    model_config = {"populate_by_name": True}

    property_id: str = Field(alias="propertyId")
    property_name: Optional[str] = Field(default=None, alias="propertyName")
    address: Optional[str] = None
    generated_at: str = Field(alias="generatedAt")
    scenario_assessments: List[ConditionAssessmentResponse] = Field(
        alias="scenarioAssessments"
    )
    history: List[ConditionAssessmentResponse]
    checklist_summary: Optional[ChecklistProgressResponse] = Field(
        default=None, alias="checklistSummary"
    )


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
):
    """Return checklist templates, optionally filtered by development scenario."""

    await DeveloperChecklistService.ensure_templates_seeded(session)
    templates = await DeveloperChecklistService.list_templates(
        session, development_scenario=development_scenario
    )
    return [_serialize_checklist_template(template) for template in templates]


@router.post(
    "/checklists/templates",
    response_model=ChecklistTemplateResponse,
    status_code=201,
)
async def create_checklist_template(
    request: ChecklistTemplateCreateRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Create a new checklist template definition."""

    try:
        template = await DeveloperChecklistService.create_template(
            session, request.model_dump(exclude_none=True, by_alias=False)
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await session.commit()
    return _serialize_checklist_template(template)


@router.put(
    "/checklists/templates/{template_id}",
    response_model=ChecklistTemplateResponse,
)
async def update_checklist_template(
    template_id: UUID,
    request: ChecklistTemplateUpdateRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
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
    return _serialize_checklist_template(template)


@router.delete(
    "/checklists/templates/{template_id}",
    status_code=204,
)
async def delete_checklist_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
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
):
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


@router.get(
    "/properties/{property_id}/condition-assessment/report",
)
async def export_condition_report(
    property_id: UUID,
    format: str = Query("json", pattern="^(json|pdf)$"),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Return a structured condition report in JSON (default) or PDF format."""

    property_record = await session.get(Property, property_id)
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    scenario_assessments = (
        await DeveloperConditionService.get_latest_assessments_by_scenario(
            session=session,
            property_id=property_id,
        )
    )
    history = await DeveloperConditionService.get_assessment_history(
        session=session,
        property_id=property_id,
        scenario=None,
        limit=10,
    )
    checklist_summary_raw = await DeveloperChecklistService.get_checklist_summary(
        session, property_id
    )

    report = ConditionReportResponse(
        property_id=str(property_id),
        property_name=property_record.name,
        address=property_record.address,
        generated_at=datetime.utcnow().isoformat(),
        scenario_assessments=[
            _serialize_condition_assessment(assessment)
            for assessment in scenario_assessments
        ],
        history=[_serialize_condition_assessment(assessment) for assessment in history],
        checklist_summary=(
            ChecklistProgressResponse(
                total=checklist_summary_raw["total"],
                completed=checklist_summary_raw["completed"],
                in_progress=checklist_summary_raw["in_progress"],
                pending=checklist_summary_raw["pending"],
                not_applicable=checklist_summary_raw["not_applicable"],
                completion_percentage=checklist_summary_raw["completion_percentage"],
            )
            if checklist_summary_raw
            else None
        ),
    )

    if format == "pdf":
        html_body = _render_condition_report_html(report)
        pdf_data = render_html_to_pdf(html_body)
        if pdf_data is None:
            raise HTTPException(
                status_code=503,
                detail="PDF generation not available on this environment.",
            )
        filename = f"condition-report-{property_id}.pdf"
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return JSONResponse(content=report.model_dump(by_alias=True))


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
        insights=[
            ConditionInsightResponse(
                id=insight.id,
                severity=insight.severity,
                title=insight.title,
                detail=insight.detail,
                specialist=insight.specialist,
            )
            for insight in assessment.insights
        ],
    )


def _normalise_scenario_param(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    slug = value.strip().lower()
    if not slug or slug == "all":
        return None
    return slug


__all__ = ["router"]


def _serialize_checklist_template(
    template: DeveloperChecklistTemplate,
) -> ChecklistTemplateResponse:
    return ChecklistTemplateResponse(
        id=str(template.id),
        development_scenario=template.development_scenario,
        category=template.category.value,
        item_title=template.item_title,
        item_description=template.item_description,
        priority=template.priority.value,
        typical_duration_days=template.typical_duration_days,
        requires_professional=template.requires_professional,
        professional_type=template.professional_type,
        display_order=template.display_order,
        created_at=template.created_at.isoformat(),
        updated_at=template.updated_at.isoformat(),
    )


def _render_condition_report_html(report: ConditionReportResponse) -> str:
    """Render a simple HTML report suitable for PDF conversion."""

    def _escape(value: Optional[str]) -> str:
        return html.escape(value or "")

    scenario_rows = []
    for scenario_assessment in report.scenario_assessments:
        systems_html = "".join(
            f"<li><strong>{_escape(system.name)}</strong>: "
            f"rating {_escape(system.rating)}, score {system.score}/100 "
            f"- {_escape(system.notes)}</li>"
            for system in scenario_assessment.systems
        )
        recommended_html = "".join(
            f"<li>{_escape(action)}</li>"
            for action in scenario_assessment.recommended_actions
        )
        scenario_rows.append(
            f"""
            <section>
              <h3>{_escape(scenario_assessment.scenario or "All scenarios")}</h3>
              <p><strong>Rating:</strong> {scenario_assessment.overall_rating} &nbsp;
                 <strong>Score:</strong> {scenario_assessment.overall_score}/100 &nbsp;
                 <strong>Risk:</strong> {_escape(scenario_assessment.risk_level)}</p>
              <p>{_escape(scenario_assessment.summary)}</p>
              {"<p><em>" + _escape(scenario_assessment.scenario_context) + "</em></p>" if scenario_assessment.scenario_context else ""}
              <h4>Systems</h4>
              <ul>{systems_html}</ul>
              {"<h4>Recommended actions</h4><ul>" + recommended_html + "</ul>" if recommended_html else ""}
            </section>
            """
        )

    history_rows = []
    for history_entry in report.history:
        history_rows.append(
            f"""
            <li>
              <strong>{_escape(history_entry.recorded_at or '')}</strong>:
              scenario {_escape(history_entry.scenario or 'n/a')},
              rating {history_entry.overall_rating},
              score {history_entry.overall_score}/100,
              risk {_escape(history_entry.risk_level)}
            </li>
            """
        )

    checklist_html = ""
    if report.checklist_summary:
        summary = report.checklist_summary
        checklist_html = f"""
        <section>
          <h3>Checklist Summary</h3>
          <p>
            Total {summary.total} · Completed {summary.completed} ·
            In progress {summary.in_progress} · Pending {summary.pending} ·
            Not applicable {summary.not_applicable} ·
            Completion {summary.completion_percentage}%
          </p>
        </section>
        """

    html_report = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Condition Report</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 2rem; color: #1d1d1f; }}
          h1, h2, h3 {{ margin-bottom: 0.5rem; }}
          section {{ margin-bottom: 2rem; }}
          ul {{ padding-left: 1.2rem; }}
        </style>
      </head>
      <body>
        <h1>Condition Summary</h1>
        <p><strong>Property:</strong> {_escape(report.property_name)}<br/>
           <strong>Address:</strong> {_escape(report.address)}<br/>
           <strong>Generated:</strong> {_escape(report.generated_at)}</p>

        <h2>Scenario Assessments</h2>
        {''.join(scenario_rows)}

        {checklist_html}

        <section>
          <h3>Recent History</h3>
          <ul>
            {''.join(history_rows)}
          </ul>
        </section>
      </body>
    </html>
    """
    return html_report
