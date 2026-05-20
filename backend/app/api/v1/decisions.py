"""Decision-alternative logging endpoints (PR2).

Two routes:

* ``POST /decisions/choice-sets`` — record every option that was just shown
  to the user. Called when the UI renders >1 alternative.
* ``POST /decisions/choice-sets/{choice_set_id}/resolve`` — record which
  option the user picked (or that they dismissed the set entirely).

Splitting present/resolve into two writes lets the dataset capture the time
between presentation and decision, which is itself a feature.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestIdentity, get_db, get_identity
from app.models.decisions import DecisionAlternative

router = APIRouter(prefix="/decisions", tags=["telemetry"])


class AlternativeIn(BaseModel):
    alternative_rank: int = Field(ge=0)
    alternative_label: str | None = Field(default=None, max_length=255)
    alternative_payload: dict[str, Any] | None = None
    score: Decimal | None = None


class ChoiceSetIn(BaseModel):
    choice_set_id: str = Field(min_length=1, max_length=64)
    decision_type: str = Field(min_length=1, max_length=60)
    context_entity_type: str | None = Field(default=None, max_length=80)
    context_entity_id: str | None = Field(default=None, max_length=64)
    presented_at: datetime
    anonymous_id: str | None = Field(default=None, max_length=64)
    session_id: str | None = Field(default=None, max_length=64)
    alternatives: list[AlternativeIn]


class ChoiceSetResult(BaseModel):
    choice_set_id: str
    alternatives_recorded: int


class ResolveChoiceSetIn(BaseModel):
    chosen_rank: int | None = Field(default=None, ge=0)
    chosen_at: datetime
    time_to_decide_ms: int | None = Field(default=None, ge=0)
    dismissed_reason: str | None = Field(default=None, max_length=120)
    rationale: str | None = Field(default=None, max_length=500)


class ResolveResult(BaseModel):
    choice_set_id: str
    rows_updated: int


@router.post(
    "/choice-sets",
    response_model=ChoiceSetResult,
    status_code=status.HTTP_201_CREATED,
)
async def record_choice_set(
    body: ChoiceSetIn,
    db: AsyncSession = Depends(get_db),
    identity: RequestIdentity = Depends(get_identity),
) -> ChoiceSetResult:
    """Persist every alternative shown inside a single rendered choice set."""

    if not body.alternatives:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one alternative is required",
        )

    rows = [
        DecisionAlternative(
            user_id=identity.user_id,
            anonymous_id=body.anonymous_id,
            session_id=body.session_id,
            decision_type=body.decision_type,
            choice_set_id=body.choice_set_id,
            context_entity_type=body.context_entity_type,
            context_entity_id=body.context_entity_id,
            alternative_rank=alt.alternative_rank,
            alternative_label=alt.alternative_label,
            alternative_payload=alt.alternative_payload,
            score=alt.score,
            presented_at=body.presented_at,
        )
        for alt in body.alternatives
    ]
    db.add_all(rows)
    await db.commit()
    return ChoiceSetResult(
        choice_set_id=body.choice_set_id,
        alternatives_recorded=len(rows),
    )


@router.post(
    "/choice-sets/{choice_set_id}/resolve",
    response_model=ResolveResult,
)
async def resolve_choice_set(
    choice_set_id: str,
    body: ResolveChoiceSetIn,
    db: AsyncSession = Depends(get_db),
    _: RequestIdentity = Depends(get_identity),
) -> ResolveResult:
    """Mark which alternative (if any) the user picked."""

    existing = await db.execute(
        select(DecisionAlternative.id).where(
            DecisionAlternative.choice_set_id == choice_set_id
        )
    )
    if existing.first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Choice set not found",
        )

    # Stamp the dismissal reason / rationale on every row in the set; mark
    # only the chosen rank as chosen=True. If chosen_rank is None the user
    # walked away — every row stays chosen=False but gets the dismissal note.
    base_update = (
        update(DecisionAlternative)
        .where(DecisionAlternative.choice_set_id == choice_set_id)
        .values(
            chosen_at=body.chosen_at,
            time_to_decide_ms=body.time_to_decide_ms,
            dismissed_reason=body.dismissed_reason,
            rationale=body.rationale,
        )
    )
    result = await db.execute(base_update)
    rows_updated = int(result.rowcount or 0)

    if body.chosen_rank is not None:
        await db.execute(
            update(DecisionAlternative)
            .where(
                DecisionAlternative.choice_set_id == choice_set_id,
                DecisionAlternative.alternative_rank == body.chosen_rank,
            )
            .values(chosen=True)
        )

    await db.commit()
    return ResolveResult(choice_set_id=choice_set_id, rows_updated=rows_updated)


__all__ = ["router"]
