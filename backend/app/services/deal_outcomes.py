"""Service layer for deal outcome CRUD and benchmark aggregation."""

from __future__ import annotations

from datetime import date
from statistics import median
from typing import Any
from uuid import UUID

from app.models.business_performance import AgentDeal, DealStatus
from app.models.deal_outcome import DealOutcome
from app.models.finance import FinResult
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class DealOutcomeService:
    """Create, update, query, and benchmark deal outcomes."""

    async def create_outcome(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        recorded_by: UUID,
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
        """Record a deal outcome. Deal must be CLOSED_WON or CLOSED_LOST."""

        if deal.status not in (
            DealStatus.CLOSED_WON,
            DealStatus.CLOSED_LOST,
            DealStatus.CANCELLED,
        ):
            msg = f"Deal must be closed before recording outcome (current: {deal.status.value})"
            raise ValueError(msg)

        outcome = DealOutcome(
            deal_id=deal.id,
            recorded_by=str(recorded_by),
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
        outcome: DealOutcome,
        **fields: Any,
    ) -> DealOutcome:
        """Incrementally update outcome fields (only set non-None values)."""

        metadata_value = fields.pop("metadata", None)
        if metadata_value is not None:
            outcome.metadata_json = metadata_value

        for key, value in fields.items():
            if value is not None and hasattr(outcome, key):
                setattr(outcome, key, value)

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
        """Aggregate benchmark statistics across matching outcomes."""

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

        result = await session.execute(stmt)
        outcomes = list(result.scalars().all())

        if not outcomes:
            return {
                "sample_size": 0,
                "median_yield_pct": None,
                "median_price_psm": None,
                "median_approval_days": None,
                "median_gfa_amendment_pct": None,
                "resolution_distribution": {},
            }

        # Yield
        yields = [
            float(o.actual_yield_pct)
            for o in outcomes
            if o.actual_yield_pct is not None
        ]

        # Price per sqm
        prices_psm = []
        for o in outcomes:
            if (
                o.actual_purchase_price is not None
                and o.actual_gfa_approved_sqm
                and float(o.actual_gfa_approved_sqm) > 0
            ):
                prices_psm.append(
                    float(o.actual_purchase_price) / float(o.actual_gfa_approved_sqm)
                )

        # Approval duration in days
        approval_days = []
        for o in outcomes:
            if o.approval_submitted_date and o.approval_decided_date:
                delta = o.approval_decided_date - o.approval_submitted_date
                approval_days.append(delta.days)

        # GFA amendment percentage
        gfa_amend_pcts = []
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

        # Resolution distribution
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
        }

    async def compare_projected_vs_actual(
        self,
        *,
        session: AsyncSession,
        scenario_id: int,
    ) -> dict[str, Any] | None:
        """Compare a scenario's projected results with its deal outcome."""

        stmt = select(DealOutcome).where(DealOutcome.scenario_id == scenario_id)
        result = await session.execute(stmt)
        outcome = result.scalar_one_or_none()
        if outcome is None:
            return None

        # Fetch projected results from FinResult
        results_stmt = select(FinResult).where(FinResult.scenario_id == scenario_id)
        results_result = await session.execute(results_stmt)
        fin_results = {
            r.name: float(r.value)
            for r in results_result.scalars().all()
            if r.value is not None
        }

        comparison: dict[str, Any] = {"scenario_id": scenario_id, "deltas": {}}

        if (
            outcome.actual_purchase_price is not None
            and "total_development_cost" in fin_results
        ):
            projected = fin_results["total_development_cost"]
            actual = float(outcome.actual_purchase_price)
            comparison["deltas"]["purchase_price"] = {
                "projected": projected,
                "actual": actual,
                "delta_pct": (
                    round(((actual - projected) / projected) * 100, 2)
                    if projected
                    else None
                ),
            }

        if outcome.actual_yield_pct is not None and "stabilised_yield" in fin_results:
            projected = fin_results["stabilised_yield"]
            actual = float(outcome.actual_yield_pct)
            comparison["deltas"]["yield_pct"] = {
                "projected": projected,
                "actual": actual,
                "delta_pct": (
                    round(((actual - projected) / projected) * 100, 2)
                    if projected
                    else None
                ),
            }

        if outcome.actual_noi is not None and "annual_noi" in fin_results:
            projected = fin_results["annual_noi"]
            actual = float(outcome.actual_noi)
            comparison["deltas"]["noi"] = {
                "projected": projected,
                "actual": actual,
                "delta_pct": (
                    round(((actual - projected) / projected) * 100, 2)
                    if projected
                    else None
                ),
            }

        return comparison
