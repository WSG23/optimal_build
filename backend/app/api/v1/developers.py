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
from app.core.auth.jwt import TokenData, get_optional_user
from app.models.developer_checklists import ChecklistStatus
from app.models.property import Property
from app.services.developer_checklist_service import DeveloperChecklistService
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
    )


def _normalise_scenario_param(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    slug = value.strip().lower()
    if not slug or slug == "all":
        return None
    return slug


__all__ = ["router"]


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
