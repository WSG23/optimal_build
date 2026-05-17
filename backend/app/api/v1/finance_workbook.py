"""Finance workbook import/export endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import RequestIdentity, require_reviewer
from app.core.audit.ledger import append_event
from app.core.database import get_session
from app.models.finance import FinScenario
from app.schemas._typing import validate_model
from app.schemas.finance import FinanceFeasibilityRequest, FinanceFeasibilityResponse
from app.schemas.finance_workbook import FinanceWorkbookPreviewResponse
from app.services.deals.utils import audit_key_from_value
from app.services.finance.workbook_exchange import (
    XLSX_MEDIA_TYPE,
    build_finance_workbook,
    preview_finance_workbook,
)

from .finance_feasibility import run_finance_feasibility
from .finance_scenarios import _ensure_project_owner, summarise_persisted_scenario

router = APIRouter(prefix="/finance", tags=["finance"])


def _build_workbook_import_description(
    description: str | None,
    *,
    workbook_format: str,
    filename: str,
) -> str:
    parts: list[str] = []
    if description and description.strip():
        parts.append(description.strip())
    parts.extend(
        [
            "[Workbook import context]",
            f"Workbook format: {workbook_format}",
            f"Filename: {filename}",
        ]
    )
    return "\n".join(parts)


@router.get("/export/workbook")
async def export_finance_workbook(
    scenario_id: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> StreamingResponse:
    """Export a finance scenario as an Excel workbook."""

    stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(
            selectinload(FinScenario.results),
            selectinload(FinScenario.fin_project),
            selectinload(FinScenario.capital_stack),
            selectinload(FinScenario.asset_breakdowns),
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    scenario = result.scalar_one_or_none()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")

    await _ensure_project_owner(session, scenario.project_id, identity)
    summary = await summarise_persisted_scenario(scenario, session=session)
    workbook_bytes = build_finance_workbook(
        summary,
        assumptions=scenario.assumptions or {},
    )
    audit_project_id = audit_key_from_value(scenario.project_id)
    if audit_project_id is not None:
        await append_event(
            session,
            project_id=audit_project_id,
            event_type="export_generated",
            context={
                "format": "xlsx",
                "scenario_id": scenario.id,
                "scenario_name": summary.scenario_name,
                "recipient_email": identity.email,
                "export_type": "finance_workbook",
            },
        )
        await session.commit()
    filename = f"finance_scenario_{scenario.id}.xlsx"
    response = StreamingResponse(iter([workbook_bytes]), media_type=XLSX_MEDIA_TYPE)
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@router.post("/import/workbook/preview", response_model=FinanceWorkbookPreviewResponse)
async def preview_import_finance_workbook(
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
    project_name: str | None = Form(default=None),
    _identity: RequestIdentity = Depends(require_reviewer),
) -> FinanceWorkbookPreviewResponse:
    """Preview an uploaded finance workbook before importing it."""

    filename = file.filename or "finance-workbook.xlsx"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty workbook upload.")
    try:
        result: FinanceWorkbookPreviewResponse = preview_finance_workbook(
            content,
            filename=filename,
            project_id=project_id,
            project_name=project_name,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/workbook", response_model=FinanceFeasibilityResponse)
async def import_finance_workbook(
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
    project_name: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> FinanceFeasibilityResponse:
    """Import an uploaded workbook into a persisted finance scenario."""

    filename = file.filename or "finance-workbook.xlsx"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty workbook upload.")

    try:
        preview = preview_finance_workbook(
            content,
            filename=filename,
            project_id=project_id,
            project_name=project_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not preview.is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Workbook could not be validated.",
                "validation_errors": [
                    issue.model_dump(mode="json") for issue in preview.validation_errors
                ],
            },
        )

    payload = validate_model(FinanceFeasibilityRequest, preview.request_payload)
    payload.scenario.description = _build_workbook_import_description(
        payload.scenario.description,
        workbook_format=preview.workbook_format,
        filename=filename,
    )
    response = await run_finance_feasibility(
        payload,
        session=session,
        identity=identity,
    )
    audit_project_id = audit_key_from_value(payload.project_id)
    if audit_project_id is not None:
        await append_event(
            session,
            project_id=audit_project_id,
            event_type="workbook_imported",
            context={
                "format": "xlsx",
                "scenario_id": response.scenario_id,
                "scenario_name": response.scenario_name,
                "asset_count": len(response.asset_breakdowns),
                "workbook_format": preview.workbook_format,
                "recipient_email": identity.email,
            },
        )
        await session.commit()
    return response
