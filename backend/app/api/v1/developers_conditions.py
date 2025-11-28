"""Condition assessment API endpoints for developer workspace."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any, Iterable, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.developers_checklists import ChecklistProgressResponse
from app.api.v1.developers_common import (
    _normalise_scenario_param,
    _format_scenario_label,
)
from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.developer_checklists import ChecklistStatus
from app.models.property import Property
from app.services.developer_checklist_service import DeveloperChecklistService
from app.services.developer_condition_service import (
    ConditionAssessment,
    ConditionInsight,
    ConditionSystem,
    DeveloperConditionService,
)
from app.utils.render import render_html_to_pdf

router = APIRouter(prefix="/developers", tags=["developers"])


# =============================================================================
# Request/Response Models
# =============================================================================


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

    model_config = {"populate_by_name": True}

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
    inspector_name: Optional[str] = Field(default=None, alias="inspectorName")
    recorded_by: Optional[str] = Field(default=None, alias="recordedBy")
    attachments: List[dict[str, Any]] = Field(default_factory=list)
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
    inspector_name: Optional[str] = Field(default=None, alias="inspectorName")
    recorded_at: Optional[str] = Field(default=None, alias="recordedAt")
    attachments: List[dict[str, Any]] = Field(default_factory=list)


class ScenarioComparisonEntryResponse(BaseModel):
    """Aggregated comparison entry for scenario scorecards."""

    model_config = {"populate_by_name": True}

    scenario: Optional[str] = None
    label: str
    recorded_at: Optional[str] = Field(default=None, alias="recordedAt")
    overall_score: Optional[int] = Field(default=None, alias="overallScore")
    overall_rating: Optional[str] = Field(default=None, alias="overallRating")
    risk_level: Optional[str] = Field(default=None, alias="riskLevel")
    checklist_completed: Optional[int] = Field(default=None, alias="checklistCompleted")
    checklist_total: Optional[int] = Field(default=None, alias="checklistTotal")
    checklist_percent: Optional[int] = Field(default=None, alias="checklistPercent")
    primary_insight: Optional[ConditionInsightResponse] = Field(
        default=None, alias="primaryInsight"
    )
    insight_count: int = Field(default=0, alias="insightCount")
    recommended_action: Optional[str] = Field(default=None, alias="recommendedAction")
    inspector_name: Optional[str] = Field(default=None, alias="inspectorName")
    source: str


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
    scenario_comparison: List[ScenarioComparisonEntryResponse] = Field(
        default_factory=list, alias="scenarioComparison"
    )


# =============================================================================
# Helper Functions
# =============================================================================


_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2, "positive": 3}


def _serialize_condition_system(system: ConditionSystem) -> ConditionSystemResponse:
    return ConditionSystemResponse(
        name=system.name,
        rating=system.rating,
        score=system.score,
        notes=system.notes,
        recommended_actions=system.recommended_actions,
    )


def _serialize_condition_insight(insight: ConditionInsight) -> ConditionInsightResponse:
    return ConditionInsightResponse(
        id=insight.id,
        severity=insight.severity,
        title=insight.title,
        detail=insight.detail,
        specialist=insight.specialist,
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
        inspectorName=assessment.inspector_name,
        recordedBy=str(assessment.recorded_by) if assessment.recorded_by else None,
        attachments=list(assessment.attachments or []),
        insights=[
            _serialize_condition_insight(insight) for insight in assessment.insights
        ],
    )


def _summarise_checklist_progress(
    checklist_items: Iterable[Any],
) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}

    for item in checklist_items:
        scenario_key = _normalise_scenario_param(item.development_scenario)
        key = scenario_key or "all"
        bucket = summary.setdefault(
            key,
            {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "not_applicable": 0,
                "percent": 0,
            },
        )
        bucket["total"] += 1
        status = item.status
        if status == ChecklistStatus.COMPLETED:
            bucket["completed"] += 1
        elif status == ChecklistStatus.IN_PROGRESS:
            bucket["in_progress"] += 1
        elif status == ChecklistStatus.PENDING:
            bucket["pending"] += 1
        elif status == ChecklistStatus.NOT_APPLICABLE:
            bucket["not_applicable"] += 1
        else:
            bucket["pending"] += 1

    for bucket in summary.values():
        denominator = bucket["total"] - bucket["not_applicable"]
        if denominator > 0:
            bucket["percent"] = int((bucket["completed"] / denominator) * 100)
        else:
            bucket["percent"] = 0

    return summary


def _select_primary_insight(
    insights: List[ConditionInsight],
) -> Optional[ConditionInsight]:
    if not insights:
        return None
    ranked = sorted(
        insights,
        key=lambda item: (_SEVERITY_ORDER.get(item.severity, 99), insights.index(item)),
    )
    return ranked[0]


def _build_scenario_comparison_entries(
    *,
    scenario_assessments: List[ConditionAssessment],
    checklist_items: Iterable[Any],
) -> List[ScenarioComparisonEntryResponse]:
    progress_by_scenario = _summarise_checklist_progress(checklist_items)

    entries: List[ScenarioComparisonEntryResponse] = []
    for assessment in scenario_assessments:
        scenario_key = assessment.scenario
        label = _format_scenario_label(scenario_key)
        progress_key = scenario_key or "all"
        checklist_progress = progress_by_scenario.get(progress_key)

        primary_insight = _select_primary_insight(assessment.insights)
        entry = ScenarioComparisonEntryResponse(
            scenario=scenario_key,
            label=label,
            recordedAt=(
                assessment.recorded_at.isoformat() if assessment.recorded_at else None
            ),
            overallScore=assessment.overall_score,
            overallRating=assessment.overall_rating,
            riskLevel=assessment.risk_level,
            checklistCompleted=(
                checklist_progress["completed"] if checklist_progress else None
            ),
            checklistTotal=(
                checklist_progress["total"] if checklist_progress else None
            ),
            checklistPercent=(
                checklist_progress["percent"] if checklist_progress else None
            ),
            primaryInsight=(
                _serialize_condition_insight(primary_insight)
                if primary_insight
                else None
            ),
            insightCount=len(assessment.insights),
            recommendedAction=(
                assessment.recommended_actions[0]
                if assessment.recommended_actions
                else None
            ),
            inspectorName=assessment.inspector_name,
            source="manual" if assessment.recorded_at else "heuristic",
        )
        entries.append(entry)

    return entries


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

    comparison_html = ""
    if report.scenario_comparison:
        comparison_rows = []
        for entry in report.scenario_comparison:
            progress = (
                f"{entry.checklist_completed}/{entry.checklist_total}"
                if entry.checklist_completed is not None
                and entry.checklist_total is not None
                else "N/A"
            )
            if entry.checklist_percent is not None and progress != "N/A":
                progress = f"{progress} ({entry.checklist_percent}%)"

            if entry.primary_insight:
                insight_text = (
                    f"<strong>{_escape(entry.primary_insight.title)}</strong><br/>"
                    f"{_escape(entry.primary_insight.detail)}"
                )
            else:
                insight_text = "N/A"

            comparison_rows.append(
                f"""
                <tr>
                  <td>{_escape(entry.label)}</td>
                  <td>{_escape(entry.overall_rating or '–')}</td>
                  <td>{entry.overall_score if entry.overall_score is not None else '–'}</td>
                  <td>{_escape(entry.risk_level or '–')}</td>
                  <td>{progress}</td>
                  <td>{insight_text}</td>
                  <td>{_escape(entry.recommended_action or 'None')}</td>
                  <td>{_escape(entry.inspector_name or 'N/A')}</td>
                  <td>{_escape('Manual inspection' if entry.source == 'manual' else 'Automated baseline')}</td>
                </tr>
                """
            )

        comparison_html = f"""
        <section>
          <h3>Scenario Comparison</h3>
          <table style=\"width:100%; border-collapse: collapse;\">
            <thead>
              <tr>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Scenario</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Rating</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Score</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Risk</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Checklist</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Primary insight</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Next action</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Inspector</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Source</th>
              </tr>
            </thead>
            <tbody>
              {''.join(comparison_rows)}
            </tbody>
          </table>
        </section>
        """

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

        {comparison_html}

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


# =============================================================================
# Route Handlers
# =============================================================================


@router.get(
    "/properties/{property_id}/condition-assessment",
    response_model=ConditionAssessmentResponse,
)
async def get_condition_assessment(
    property_id: UUID,
    scenario: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> ConditionAssessmentResponse:
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
) -> ConditionAssessmentResponse:
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

    recorded_at_override: Optional[datetime] = None
    if request.recorded_at:
        iso_value = request.recorded_at.strip()
        if iso_value.endswith("Z"):
            iso_value = iso_value[:-1] + "+00:00"
        try:
            recorded_at_override = datetime.fromisoformat(iso_value)
        except ValueError as exc:  # pragma: no cover - validated client input
            raise HTTPException(
                status_code=400,
                detail="Invalid recordedAt timestamp. Use ISO 8601 format.",
            ) from exc

    attachments_payload = []
    for attachment in request.attachments:
        if isinstance(attachment, dict):
            attachments_payload.append(dict(attachment))

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
        inspector_name=request.inspector_name,
        recorded_at=recorded_at_override,
        attachments=attachments_payload,
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
) -> List[ConditionAssessmentResponse]:
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
) -> List[ConditionAssessmentResponse]:
    """Return the latest stored inspection assessment for each scenario."""

    assessments = await DeveloperConditionService.get_latest_assessments_by_scenario(
        session=session,
        property_id=property_id,
    )
    return [_serialize_condition_assessment(assessment) for assessment in assessments]


@router.get(
    "/properties/{property_id}/condition-assessment/report",
    response_model=None,
)
async def export_condition_report(
    property_id: UUID,
    report_format: str = Query("json", alias="format", pattern="^(json|pdf)$"),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> Response:
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
    try:
        checklist_items = await DeveloperChecklistService.get_property_checklist(
            session,
            property_id,
        )
    except Exception:  # pragma: no cover - fallback if table bootstrap fails
        checklist_items = []

    scenario_comparison = _build_scenario_comparison_entries(
        scenario_assessments=scenario_assessments,
        checklist_items=checklist_items,
    )

    report = ConditionReportResponse(
        propertyId=str(property_id),
        propertyName=property_record.name,
        address=property_record.address,
        generatedAt=datetime.utcnow().isoformat(),
        scenarioAssessments=[
            _serialize_condition_assessment(assessment)
            for assessment in scenario_assessments
        ],
        history=[_serialize_condition_assessment(assessment) for assessment in history],
        checklistSummary=(
            ChecklistProgressResponse(
                total=checklist_summary_raw["total"],
                completed=checklist_summary_raw["completed"],
                inProgress=checklist_summary_raw["in_progress"],
                pending=checklist_summary_raw["pending"],
                notApplicable=checklist_summary_raw["not_applicable"],
                completionPercentage=checklist_summary_raw["completion_percentage"],
            )
            if checklist_summary_raw
            else None
        ),
        scenarioComparison=scenario_comparison,
    )

    if report_format == "pdf":
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
