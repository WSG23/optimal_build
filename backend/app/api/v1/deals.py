"""API endpoints for the business performance deal pipeline."""

from __future__ import annotations

from typing import Iterable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Role, require_reviewer, require_viewer
from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.business_performance import DealStatus, PipelineStage
from app.schemas.deals import (
    DealCreate,
    DealSchema,
    DealStageChangeRequest,
    DealStageEventSchema,
    DealUpdate,
    DealWithTimelineSchema,
)
from app.services.deals import AgentDealService

router = APIRouter(prefix="/deals", tags=["Business Performance"])

service = AgentDealService()


def _resolve_agent_id(
    *,
    token: TokenData | None,
    agent_id: UUID | None,
    require: bool = True,
) -> UUID:
    """Resolve the acting agent identifier from payload or token."""

    if agent_id is not None:
        return agent_id
    if token and token.user_id:
        try:
            return UUID(token.user_id)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="Invalid user token") from exc
    if require:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent identifier required",
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Agent identifier required",
    )


def _maybe_actor(token: TokenData | None) -> UUID | None:
    if token and token.user_id:
        try:
            return UUID(token.user_id)
        except ValueError:
            return None
    return None


@router.get("", response_model=list[DealSchema])
async def list_deals(
    agent_id: UUID | None = Query(default=None),
    stage: PipelineStage | None = Query(default=None),
    status_filter: DealStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: Role = Depends(require_viewer),
    session: AsyncSession = Depends(get_session),
) -> list[DealSchema]:
    """Return deals for the current agent."""

    agent_ids: Iterable[UUID] | None = [agent_id] if agent_id else None
    deals = await service.list_deals(
        session=session,
        agent_ids=agent_ids,
        stages=[stage] if stage else None,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return [DealSchema.from_orm_deal(deal) for deal in deals]


@router.post("", response_model=DealSchema, status_code=status.HTTP_201_CREATED)
async def create_deal(
    payload: DealCreate,
    _: Role = Depends(require_reviewer),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> DealSchema:
    """Create a new deal for the authenticated agent."""

    agent_id = _resolve_agent_id(token=token, agent_id=payload.agent_id)

    record = await service.create_deal(
        session=session,
        agent_id=agent_id,
        title=payload.title,
        description=payload.description,
        asset_type=payload.asset_type,
        deal_type=payload.deal_type,
        pipeline_stage=payload.pipeline_stage,
        status=payload.status,
        lead_source=payload.lead_source,
        estimated_value_amount=(
            float(payload.estimated_value_amount)
            if payload.estimated_value_amount is not None
            else None
        ),
        estimated_value_currency=payload.estimated_value_currency,
        expected_close_date=payload.expected_close_date,
        confidence=(
            float(payload.confidence) if payload.confidence is not None else None
        ),
        project_id=payload.project_id,
        property_id=payload.property_id,
        metadata=payload.metadata,
        created_by=_maybe_actor(token),
    )
    return DealSchema.from_orm_deal(record)


@router.get("/{deal_id}", response_model=DealSchema)
async def get_deal(
    deal_id: UUID,
    _: Role = Depends(require_viewer),
    session: AsyncSession = Depends(get_session),
) -> DealSchema:
    """Fetch details for a single deal."""

    record = await service.get_deal(session=session, deal_id=deal_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return DealSchema.from_orm_deal(record)


@router.patch("/{deal_id}", response_model=DealSchema)
async def update_deal(
    deal_id: UUID,
    payload: DealUpdate,
    _: Role = Depends(require_reviewer),
    session: AsyncSession = Depends(get_session),
) -> DealSchema:
    """Update mutable fields on an existing deal."""

    record = await service.get_deal(session=session, deal_id=deal_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Deal not found")

    updated = await service.update_deal(
        session=session,
        deal=record,
        title=payload.title,
        description=payload.description,
        asset_type=payload.asset_type,
        deal_type=payload.deal_type,
        lead_source=payload.lead_source,
        estimated_value_amount=(
            float(payload.estimated_value_amount)
            if payload.estimated_value_amount is not None
            else None
        ),
        estimated_value_currency=payload.estimated_value_currency,
        expected_close_date=payload.expected_close_date,
        actual_close_date=payload.actual_close_date,
        confidence=(
            float(payload.confidence) if payload.confidence is not None else None
        ),
        project_id=payload.project_id,
        property_id=payload.property_id,
        metadata=payload.metadata,
        status=payload.status,
    )
    return DealSchema.from_orm_deal(updated)


@router.post("/{deal_id}/stage", response_model=DealWithTimelineSchema)
async def change_stage(
    deal_id: UUID,
    payload: DealStageChangeRequest,
    _: Role = Depends(require_reviewer),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> DealWithTimelineSchema:
    """Transition a deal to a new stage and return the updated timeline."""

    record = await service.get_deal(session=session, deal_id=deal_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Deal not found")

    actor = _maybe_actor(token)
    await service.change_stage(
        session=session,
        deal=record,
        to_stage=payload.to_stage,
        changed_by=actor,
        note=payload.note,
        metadata=payload.metadata,
        occurred_at=payload.occurred_at,
    )
    timeline, audit_logs = await service.timeline_with_audit(
        session=session, deal=record
    )
    return DealWithTimelineSchema.from_orm_deal(
        record, timeline=timeline, audit_logs=audit_logs
    )


@router.get("/{deal_id}/timeline", response_model=list[DealStageEventSchema])
async def get_timeline(
    deal_id: UUID,
    _: Role = Depends(require_viewer),
    session: AsyncSession = Depends(get_session),
) -> list[DealStageEventSchema]:
    """Return the ordered stage history for a deal."""

    record = await service.get_deal(session=session, deal_id=deal_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    timeline, audit_logs = await service.timeline_with_audit(
        session=session, deal=record
    )
    serialised = []
    for index, event in enumerate(timeline):
        next_event = timeline[index + 1] if index + 1 < len(timeline) else None
        duration_seconds: float | None = None
        if (
            event.recorded_at
            and next_event
            and next_event.recorded_at
            and next_event.recorded_at >= event.recorded_at
        ):
            duration_seconds = (next_event.recorded_at - event.recorded_at).total_seconds()
        audit_log = None
        audit_id = None
        if event.metadata:
            audit_id = event.metadata.get("audit_log_id")
        if audit_id:
            audit_log = audit_logs.get(str(audit_id))
        serialised.append(
            DealStageEventSchema.from_orm_event(
                event,
                duration_seconds=duration_seconds,
                audit_log=audit_log,
            )
        )
    return serialised


__all__ = ["router"]
