"""Overlay evaluation API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit.ledger import append_event
from app.core.database import get_session
from app.core.metrics import DECISION_REVIEW_BASELINE_SECONDS
from app.models.overlay import (
    OverlayDecision,
    OverlaySuggestion,
)
from app.schemas.overlay import OverlayDecisionPayload, OverlaySuggestion as OverlaySuggestionSchema
from jobs import job_queue
from jobs.overlay_run import run_overlay_job


router = APIRouter(prefix="/overlay")


@router.post("/{project_id}/run")
async def run_overlay(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, object]:
    """Execute the overlay feasibility engine for a project."""

    dispatch = await job_queue.enqueue(run_overlay_job, project_id=project_id)
    if dispatch.result and isinstance(dispatch.result, dict):
        payload = dict(dispatch.result)
        if "project_id" in payload:
            try:
                payload["project_id"] = int(payload["project_id"])
            except (TypeError, ValueError):
                pass
        return payload
    payload: Dict[str, object] = {
        "status": dispatch.status,
        "project_id": project_id,
    }
    if dispatch.task_id:
        payload["job_id"] = dispatch.task_id
    return payload


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

    created_at = suggestion.created_at
    if created_at:
        actual_seconds = max((timestamp - created_at).total_seconds(), 0.0)
    else:
        actual_seconds = None
    await append_event(
        session,
        project_id=project_id,
        event_type="overlay_decision",
        baseline_seconds=DECISION_REVIEW_BASELINE_SECONDS,
        actual_seconds=actual_seconds,
        context={
            "suggestion_id": suggestion.id,
            "decision": decision_value,
            "accepted": decision_value == "approved",
            "decided_by": payload.decided_by,
        },
    )

    await session.commit()
    await session.refresh(suggestion)
    item = OverlaySuggestionSchema.model_validate(suggestion, from_attributes=True)
    return {"item": item.model_dump(mode="json")}


__all__ = ["router"]
