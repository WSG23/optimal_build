"""API endpoints for deal outcome capture and benchmarking."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import Role, require_reviewer, require_viewer
from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.deal_outcome import OutcomeResolution
from app.schemas._typing import dump_model
from app.schemas.deal_outcome import (
    DealOutcomeBenchmarkResponse,
    DealOutcomeComparisonResponse,
    DealOutcomeCreate,
    DealOutcomeResponse,
    DealOutcomeUpdate,
)
from app.utils.lazy import LazyProxy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/deals", tags=["Business Performance"])


def _create_deal_service() -> object:
    from app.services.deals import AgentDealService

    return AgentDealService()


def _create_outcome_service() -> object:
    from app.services.deal_outcomes import DealOutcomeService

    return DealOutcomeService()


deal_service = LazyProxy(_create_deal_service)
outcome_service = LazyProxy(_create_outcome_service)


def _actor_or_none(token: TokenData | None) -> UUID | None:
    """Extract user ID from token; return None when not authenticated."""

    if token and token.user_id:
        try:
            return UUID(token.user_id)
        except ValueError:
            return None
    return None


@router.post(
    "/{deal_id}/outcome",
    response_model=DealOutcomeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_outcome(
    deal_id: UUID,
    payload: DealOutcomeCreate,
    _: Role = Depends(require_reviewer),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> DealOutcomeResponse:
    """Record the outcome of a closed deal."""

    actor = _actor_or_none(token)

    deal = await deal_service.get_deal(session=session, deal_id=deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")

    try:
        outcome = await outcome_service.create_outcome(
            session=session,
            deal=deal,
            recorded_by=actor,
            resolution=payload.resolution.value,
            resolution_note=payload.resolution_note,
            scenario_id=payload.scenario_id,
            actual_purchase_price=(
                float(payload.actual_purchase_price)
                if payload.actual_purchase_price is not None
                else None
            ),
            actual_price_currency=payload.actual_price_currency,
            actual_gfa_approved_sqm=(
                float(payload.actual_gfa_approved_sqm)
                if payload.actual_gfa_approved_sqm is not None
                else None
            ),
            actual_construction_cost=(
                float(payload.actual_construction_cost)
                if payload.actual_construction_cost is not None
                else None
            ),
            actual_noi=(
                float(payload.actual_noi) if payload.actual_noi is not None else None
            ),
            actual_yield_pct=(
                float(payload.actual_yield_pct)
                if payload.actual_yield_pct is not None
                else None
            ),
            actual_completion_date=payload.actual_completion_date,
            approval_submitted_date=payload.approval_submitted_date,
            approval_decided_date=payload.approval_decided_date,
            approval_authority=payload.approval_authority,
            approval_outcome=(
                payload.approval_outcome.value
                if payload.approval_outcome is not None
                else None
            ),
            approval_conditions=payload.approval_conditions,
            gfa_amendment_sqm=(
                float(payload.gfa_amendment_sqm)
                if payload.gfa_amendment_sqm is not None
                else None
            ),
            jurisdiction_code=payload.jurisdiction_code,
            asset_type=payload.asset_type,
            metadata=payload.metadata,
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Outcome already recorded for this deal",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return DealOutcomeResponse.from_orm_outcome(outcome)


@router.get("/{deal_id}/outcome", response_model=DealOutcomeResponse)
async def get_outcome(
    deal_id: UUID,
    _: Role = Depends(require_viewer),
    session: AsyncSession = Depends(get_session),
) -> DealOutcomeResponse:
    """Fetch the outcome for a deal."""

    outcome = await outcome_service.get_outcome_for_deal(
        session=session, deal_id=deal_id
    )
    if outcome is None:
        raise HTTPException(status_code=404, detail="No outcome recorded for this deal")

    projected = None
    if outcome.scenario_id is not None:
        projected = await outcome_service.compare_projected_vs_actual(
            session=session, scenario_id=outcome.scenario_id
        )

    return DealOutcomeResponse.from_orm_outcome(outcome, projected_vs_actual=projected)


@router.patch("/{deal_id}/outcome", response_model=DealOutcomeResponse)
async def update_outcome(
    deal_id: UUID,
    payload: DealOutcomeUpdate,
    _: Role = Depends(require_reviewer),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> DealOutcomeResponse:
    """Update outcome fields. Pass null to clear a field."""

    outcome = await outcome_service.get_outcome_for_deal(
        session=session, deal_id=deal_id
    )
    if outcome is None:
        raise HTTPException(status_code=404, detail="No outcome recorded for this deal")

    deal = await deal_service.get_deal(session=session, deal_id=deal_id)
    if deal is None:
        # Outcome exists but deal is gone — shouldn't happen with CASCADE FK,
        # but guard anyway.
        raise HTTPException(status_code=404, detail="Deal not found")

    update_fields = dump_model(payload, exclude_unset=True)

    if "resolution" in update_fields and update_fields["resolution"] is not None:
        update_fields["resolution"] = update_fields["resolution"].value
    if (
        "approval_outcome" in update_fields
        and update_fields["approval_outcome"] is not None
    ):
        update_fields["approval_outcome"] = update_fields["approval_outcome"].value

    decimal_fields = [
        "actual_purchase_price",
        "actual_gfa_approved_sqm",
        "actual_construction_cost",
        "actual_noi",
        "actual_yield_pct",
        "gfa_amendment_sqm",
    ]
    for field in decimal_fields:
        if field in update_fields and update_fields[field] is not None:
            update_fields[field] = float(update_fields[field])

    updated = await outcome_service.update_outcome(
        session=session,
        deal=deal,
        outcome=outcome,
        fields=update_fields,
        actor_id=_actor_or_none(token),
    )
    return DealOutcomeResponse.from_orm_outcome(updated)


@router.get("/outcomes/benchmarks", response_model=DealOutcomeBenchmarkResponse)
async def get_benchmarks(
    jurisdiction_code: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    resolution: OutcomeResolution | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: Role = Depends(require_viewer),
    session: AsyncSession = Depends(get_session),
) -> DealOutcomeBenchmarkResponse:
    """Return aggregated benchmark statistics across deal outcomes."""

    data = await outcome_service.get_benchmarks(
        session=session,
        jurisdiction_code=jurisdiction_code,
        asset_type=asset_type,
        resolution=resolution.value if resolution else None,
        date_from=date_from,
        date_to=date_to,
    )
    return DealOutcomeBenchmarkResponse(**data)


@router.get(
    "/outcomes/compare/{scenario_id}",
    response_model=DealOutcomeComparisonResponse,
)
async def compare_projected_vs_actual(
    scenario_id: int,
    _: Role = Depends(require_viewer),
    session: AsyncSession = Depends(get_session),
) -> DealOutcomeComparisonResponse:
    """Compare projected scenario results with realised outcome."""

    comparison = await outcome_service.compare_projected_vs_actual(
        session=session, scenario_id=scenario_id
    )
    if comparison is None:
        raise HTTPException(
            status_code=404,
            detail="No outcome linked to this scenario",
        )
    return DealOutcomeComparisonResponse(**comparison)


__all__ = ["router"]
