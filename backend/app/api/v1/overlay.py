"""Overlay evaluation API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.overlay import OverlayDecision, OverlaySuggestion
from app.services.audit import record_project_event
from app.schemas.overlay import OverlayDecisionPayload, OverlaySuggestion as OverlaySuggestionSchema
from jobs.overlay_run import OverlayRunResult, run_overlay_for_project


router = APIRouter(prefix="/overlay")


OVERLAY_RUN_BASELINE_SECONDS = 45 * 60
OVERLAY_RUN_AUTOMATED_SECONDS = 5 * 60
OVERLAY_DECISION_BASELINE_SECONDS = 20 * 60
OVERLAY_DECISION_AUTOMATED_SECONDS = 3 * 60
EXPORT_BASELINE_SECONDS = 30 * 60
EXPORT_AUTOMATED_SECONDS = 5 * 60


@router.post("/{project_id}/run")
async def run_overlay(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, object]:
    """Execute the overlay feasibility engine for a project."""

    result: OverlayRunResult = await run_overlay_for_project(session, project_id=project_id)
    evaluated = max(result.evaluated, 1)
    await record_project_event(
        session,
        project_id=project_id,
        event_type="overlay_run",
        baseline_seconds=evaluated * OVERLAY_RUN_BASELINE_SECONDS,
        automated_seconds=evaluated * OVERLAY_RUN_AUTOMATED_SECONDS,
        metadata={
            "evaluated": result.evaluated,
            "created": result.created,
            "updated": result.updated,
        },
    )
    await session.commit()

    return {
        "status": "completed",
        "project_id": project_id,
        "evaluated": result.evaluated,
        "created": result.created,
        "updated": result.updated,
    }


@router.get("/{project_id}")
async def list_project_overlays(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, object]:
    """Return overlay suggestions for the requested project."""

    stmt = (
        select(OverlaySuggestion)
        .where(OverlaySuggestion.project_id == project_id)
        .options(selectinload(OverlaySuggestion.decision))
        .order_by(OverlaySuggestion.id)
    )
    result = await session.execute(stmt)
    suggestions: List[OverlaySuggestion] = list(result.scalars().unique().all())
    items = [
        OverlaySuggestionSchema.model_validate(suggestion, from_attributes=True)
        for suggestion in suggestions
    ]
    payload_items = [item.model_dump(mode="json") for item in items]
    return {"items": payload_items, "count": len(payload_items)}


def _normalise_decision_value(decision: str) -> str:
    value = decision.strip().lower()
    if value in {"approve", "approved"}:
        return "approved"
    if value in {"reject", "rejected"}:
        return "rejected"
    raise HTTPException(status_code=400, detail="Decision must be approve or reject")


@router.post("/{project_id}/decision")
async def decide_overlay(
    project_id: int,
    payload: OverlayDecisionPayload,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, object]:
    """Persist a decision on a generated overlay suggestion."""

    suggestion = await session.get(OverlaySuggestion, payload.suggestion_id)
    if suggestion is None or suggestion.project_id != project_id:
        raise HTTPException(status_code=404, detail="Overlay suggestion not found")

    decision_value = _normalise_decision_value(payload.decision)
    timestamp = datetime.now(timezone.utc)

    if suggestion.decision is None:
        decision = OverlayDecision(
            project_id=project_id,
            source_geometry_id=suggestion.source_geometry_id,
            suggestion_id=suggestion.id,
            decision=decision_value,
            decided_by=payload.decided_by,
            decided_at=timestamp,
            notes=payload.notes,
        )
        session.add(decision)
        suggestion.decision = decision
    else:
        suggestion.decision.decision = decision_value
        suggestion.decision.decided_by = payload.decided_by
        suggestion.decision.decided_at = timestamp
        suggestion.decision.notes = payload.notes

    suggestion.status = decision_value
    suggestion.decided_at = timestamp
    suggestion.decided_by = payload.decided_by
    suggestion.decision_notes = payload.notes

    await record_project_event(
        session,
        project_id=project_id,
        event_type="overlay_decision",
        baseline_seconds=OVERLAY_DECISION_BASELINE_SECONDS,
        automated_seconds=OVERLAY_DECISION_AUTOMATED_SECONDS,
        accepted_suggestions=1 if decision_value == "approved" else 0,
        metadata={
            "suggestion_id": suggestion.id,
            "decision": decision_value,
        },
    )

    await session.commit()
    await session.refresh(suggestion)
    item = OverlaySuggestionSchema.model_validate(suggestion, from_attributes=True)
    return {"item": item.model_dump(mode="json")}


@router.post("/{project_id}/export")
async def export_overlay(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, object]:
    """Record an export event for analytics and report suggestion counts."""

    approved_count_result = await session.execute(
        select(func.count())
        .select_from(OverlaySuggestion)
        .where(
            OverlaySuggestion.project_id == project_id,
            OverlaySuggestion.status == "approved",
        )
    )
    approved_count = int(approved_count_result.scalar_one() or 0)
    multiplier = max(approved_count, 1)
    log_entry = await record_project_event(
        session,
        project_id=project_id,
        event_type="overlay_export",
        baseline_seconds=multiplier * EXPORT_BASELINE_SECONDS,
        automated_seconds=multiplier * EXPORT_AUTOMATED_SECONDS,
        accepted_suggestions=approved_count,
        metadata={"approved": approved_count},
    )
    await session.commit()
    return {
        "status": "exported",
        "accepted": approved_count,
        "baseline_seconds": log_entry.baseline_seconds,
        "automated_seconds": log_entry.automated_seconds,
        "logged_at": log_entry.created_at.isoformat() if log_entry.created_at else None,
    }


__all__ = ["router"]
