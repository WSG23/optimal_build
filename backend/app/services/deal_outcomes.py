"""Service layer for deal outcome CRUD and benchmark aggregation."""

from __future__ import annotations

from datetime import date
from statistics import median
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.ledger import append_event
from app.models.business_performance import AgentDeal, DealStatus
from app.models.deal_outcome import DealOutcome
from app.models.finance import FinAssetBreakdown, FinProject, FinScenario
from app.services.deals.utils import audit_project_key

# Cap for in-memory benchmark aggregation. Above this we mark the response
# truncated and let callers narrow filters; SQL-side aggregation can come
# later if real volumes demand it.
BENCHMARK_SAMPLE_LIMIT = 10_000

# Resolutions accepted when recording an outcome. CANCELLED is included
# deliberately — users may want to capture context on why a deal was killed
# before it reached won/lost.
_OUTCOME_ELIGIBLE_STATUSES = frozenset(
    {DealStatus.CLOSED_WON, DealStatus.CLOSED_LOST, DealStatus.CANCELLED}
)


def _delta_pct(projected: float, actual: float) -> float | None:
    """Return percent change from projected to actual, or None when undefined."""

    if projected == 0:
        return None
    return round(((actual - projected) / projected) * 100, 2)


class DealOutcomeService:
    """Create, update, query, and benchmark deal outcomes."""

    async def create_outcome(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        recorded_by: UUID | None,
        resolution: str,
        resolution_note: str | None = None,
        scenario_id: int | None = None,
        actual_purchase_price: float | None = None,
        actual_price_currency: str = "SGD",
        actual_gfa_approved_sqm: float | None = None,
        actual_construction_cost: float | None = None,
        actual_noi: float | None = None,
        actual_yield_pct: float | None = None,
        actual_completion_date: date | None = None,
        approval_submitted_date: date | None = None,
        approval_decided_date: date | None = None,
        approval_authority: str | None = None,
        approval_outcome: str | None = None,
        approval_conditions: str | None = None,
        gfa_amendment_sqm: float | None = None,
        jurisdiction_code: str | None = None,
        asset_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DealOutcome:
        """Record a deal outcome. Deal must be in a terminal status.

        Eligible deal statuses are CLOSED_WON, CLOSED_LOST, and CANCELLED.
        Raises ValueError if the deal is still open. Raises IntegrityError
        if an outcome already exists for the deal (unique constraint on
        deal_id) — callers should translate that to a 409 response.
        """

        if deal.status not in _OUTCOME_ELIGIBLE_STATUSES:
            msg = f"Deal must be closed before recording outcome (current: {deal.status.value})"
            raise ValueError(msg)

        outcome = DealOutcome(
            deal_id=deal.id,
            recorded_by=str(recorded_by) if recorded_by is not None else None,
            resolution=resolution,
            resolution_note=resolution_note,
            scenario_id=scenario_id,
            actual_purchase_price=actual_purchase_price,
            actual_price_currency=actual_price_currency,
            actual_gfa_approved_sqm=actual_gfa_approved_sqm,
            actual_construction_cost=actual_construction_cost,
            actual_noi=actual_noi,
            actual_yield_pct=actual_yield_pct,
            actual_completion_date=actual_completion_date,
            approval_submitted_date=approval_submitted_date,
            approval_decided_date=approval_decided_date,
            approval_authority=approval_authority,
            approval_outcome=approval_outcome,
            approval_conditions=approval_conditions,
            gfa_amendment_sqm=gfa_amendment_sqm,
            jurisdiction_code=jurisdiction_code,
            asset_type=asset_type,
            metadata_json=metadata or {},
        )
        session.add(outcome)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            raise

        await self._audit(
            session=session,
            deal=deal,
            outcome=outcome,
            event_type="deal_outcome.created",
            actor_id=recorded_by,
        )
        await session.commit()
        await session.refresh(outcome)
        return outcome

    async def get_outcome_for_deal(
        self,
        *,
        session: AsyncSession,
        deal_id: UUID,
    ) -> DealOutcome | None:
        """Fetch the outcome attached to a deal."""

        stmt = select(DealOutcome).where(DealOutcome.deal_id == str(deal_id))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_outcome(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        outcome: DealOutcome,
        fields: dict[str, Any],
        actor_id: UUID | None = None,
    ) -> DealOutcome:
        """Update outcome fields.

        ``fields`` should contain only keys the caller explicitly set in the
        request (e.g. via ``model_dump(exclude_unset=True)``). Passing
        ``None`` for a nullable field clears it.
        """

        touched: list[str] = []
        if "metadata" in fields:
            metadata_value = fields.pop("metadata")
            if metadata_value is not None:
                outcome.metadata_json = metadata_value
                touched.append("metadata")

        for key, value in fields.items():
            if hasattr(outcome, key):
                setattr(outcome, key, value)
                touched.append(key)

        await self._audit(
            session=session,
            deal=deal,
            outcome=outcome,
            event_type="deal_outcome.updated",
            actor_id=actor_id,
            extra={"updated_fields": sorted(touched)},
        )
        await session.commit()
        await session.refresh(outcome)
        return outcome

    async def get_benchmarks(
        self,
        *,
        session: AsyncSession,
        jurisdiction_code: str | None = None,
        asset_type: str | None = None,
        resolution: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict[str, Any]:
        """Aggregate benchmark statistics across matching outcomes.

        Caps the sample at BENCHMARK_SAMPLE_LIMIT rows and flags
        ``truncated`` when the cap is reached. Callers should narrow filters
        if the sample is truncated.
        """

        stmt = select(DealOutcome)
        if jurisdiction_code:
            stmt = stmt.where(DealOutcome.jurisdiction_code == jurisdiction_code)
        if asset_type:
            stmt = stmt.where(DealOutcome.asset_type == asset_type)
        if resolution:
            stmt = stmt.where(DealOutcome.resolution == resolution)
        if date_from:
            stmt = stmt.where(DealOutcome.created_at >= date_from)
        if date_to:
            stmt = stmt.where(DealOutcome.created_at <= date_to)

        stmt = stmt.limit(BENCHMARK_SAMPLE_LIMIT + 1)
        result = await session.execute(stmt)
        rows = list(result.scalars().all())
        truncated = len(rows) > BENCHMARK_SAMPLE_LIMIT
        outcomes = rows[:BENCHMARK_SAMPLE_LIMIT]

        if not outcomes:
            return {
                "sample_size": 0,
                "median_yield_pct": None,
                "median_price_psm": None,
                "median_approval_days": None,
                "median_gfa_amendment_pct": None,
                "resolution_distribution": {},
                "truncated": truncated,
            }

        yields = [
            float(o.actual_yield_pct)
            for o in outcomes
            if o.actual_yield_pct is not None
        ]

        prices_psm: list[float] = []
        for o in outcomes:
            if (
                o.actual_purchase_price is not None
                and o.actual_gfa_approved_sqm
                and float(o.actual_gfa_approved_sqm) > 0
            ):
                prices_psm.append(
                    float(o.actual_purchase_price) / float(o.actual_gfa_approved_sqm)
                )

        approval_days: list[int] = []
        for o in outcomes:
            if o.approval_submitted_date and o.approval_decided_date:
                delta = o.approval_decided_date - o.approval_submitted_date
                approval_days.append(delta.days)

        gfa_amend_pcts: list[float] = []
        for o in outcomes:
            if (
                o.gfa_amendment_sqm is not None
                and o.actual_gfa_approved_sqm
                and float(o.actual_gfa_approved_sqm) > 0
            ):
                pct = (
                    float(o.gfa_amendment_sqm) / float(o.actual_gfa_approved_sqm)
                ) * 100
                gfa_amend_pcts.append(pct)

        resolution_dist: dict[str, int] = {}
        for o in outcomes:
            resolution_dist[o.resolution] = resolution_dist.get(o.resolution, 0) + 1

        return {
            "sample_size": len(outcomes),
            "median_yield_pct": round(median(yields), 3) if yields else None,
            "median_price_psm": round(median(prices_psm), 2) if prices_psm else None,
            "median_approval_days": (
                int(median(approval_days)) if approval_days else None
            ),
            "median_gfa_amendment_pct": (
                round(median(gfa_amend_pcts), 2) if gfa_amend_pcts else None
            ),
            "resolution_distribution": resolution_dist,
            "truncated": truncated,
        }

    async def compare_projected_vs_actual(
        self,
        *,
        session: AsyncSession,
        scenario_id: int,
    ) -> dict[str, Any] | None:
        """Compare a scenario's projected results with its deal outcome.

        Pulls projections from FinProject (cost) and FinAssetBreakdown
        (yield/NOI aggregated across assets). Returns None when no
        outcome is linked to the scenario.
        """

        # Scenarios can be referenced by multiple outcomes over time; take the
        # most recent so the comparison reflects the latest realised data.
        outcome_stmt = (
            select(DealOutcome)
            .where(DealOutcome.scenario_id == scenario_id)
            .order_by(DealOutcome.created_at.desc())
            .limit(1)
        )
        outcome_result = await session.execute(outcome_stmt)
        outcome = outcome_result.scalar_one_or_none()
        if outcome is None:
            return None

        # Scenario → FinProject for project-level totals
        scenario_stmt = select(FinScenario).where(FinScenario.id == scenario_id)
        scenario_result = await session.execute(scenario_stmt)
        scenario = scenario_result.scalar_one_or_none()

        fin_project: FinProject | None = None
        if scenario is not None:
            fin_project_stmt = select(FinProject).where(
                FinProject.id == scenario.fin_project_id
            )
            fin_project_result = await session.execute(fin_project_stmt)
            fin_project = fin_project_result.scalar_one_or_none()

        # Aggregate per-asset breakdowns to project-level NOI / weighted yield
        sum_noi_stmt = select(
            func.sum(FinAssetBreakdown.annual_noi_sgd),
            func.sum(
                FinAssetBreakdown.stabilised_yield_pct
                * FinAssetBreakdown.allocation_pct
            ),
            func.sum(FinAssetBreakdown.allocation_pct),
        ).where(FinAssetBreakdown.scenario_id == scenario_id)
        agg_result = await session.execute(sum_noi_stmt)
        projected_noi_raw, weighted_yield_raw, total_alloc_raw = agg_result.one()
        projected_noi = (
            float(projected_noi_raw) if projected_noi_raw is not None else None
        )
        projected_yield: float | None = None
        if (
            weighted_yield_raw is not None
            and total_alloc_raw is not None
            and float(total_alloc_raw) > 0
        ):
            projected_yield = float(weighted_yield_raw) / float(total_alloc_raw)

        deltas: dict[str, dict[str, Any]] = {}

        if (
            outcome.actual_purchase_price is not None
            and fin_project is not None
            and fin_project.total_development_cost is not None
        ):
            projected = float(fin_project.total_development_cost)
            actual = float(outcome.actual_purchase_price)
            deltas["purchase_price"] = {
                "projected": projected,
                "actual": actual,
                "delta_pct": _delta_pct(projected, actual),
            }

        if outcome.actual_yield_pct is not None and projected_yield is not None:
            actual = float(outcome.actual_yield_pct)
            deltas["yield_pct"] = {
                "projected": projected_yield,
                "actual": actual,
                "delta_pct": _delta_pct(projected_yield, actual),
            }

        if outcome.actual_noi is not None and projected_noi is not None:
            actual = float(outcome.actual_noi)
            deltas["noi"] = {
                "projected": projected_noi,
                "actual": actual,
                "delta_pct": _delta_pct(projected_noi, actual),
            }

        return {
            "scenario_id": scenario_id,
            "deal_id": outcome.deal_id,
            "deltas": deltas,
        }

    async def _audit(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        outcome: DealOutcome,
        event_type: str,
        actor_id: UUID | None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Append an audit ledger entry for an outcome lifecycle event."""

        project_key = audit_project_key(deal)
        if project_key is None:
            return

        context: dict[str, Any] = {
            "outcome_id": str(outcome.id),
            "deal_id": str(deal.id),
            "resolution": outcome.resolution,
            "scenario_id": outcome.scenario_id,
            "actor_id": str(actor_id) if actor_id else None,
        }
        if extra:
            context.update(extra)

        await append_event(
            session,
            project_id=project_key,
            event_type=event_type,
            context=context,
        )
