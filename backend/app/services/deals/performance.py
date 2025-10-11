"""Analytics helpers for agent performance snapshots and benchmarks."""

from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Optional
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend._compat.datetime import UTC
from app.models.business_performance import (
    AgentCommissionRecord,
    AgentDeal,
    AgentPerformanceSnapshot,
    PerformanceBenchmark,
    PipelineStage,
)


class AgentPerformanceService:
    """Compute and persist agent performance analytics snapshots."""

    async def compute_snapshot(
        self,
        *,
        session: AsyncSession,
        agent_id: UUID,
        as_of: date | None = None,
    ) -> AgentPerformanceSnapshot:
        as_of = as_of or datetime.now(UTC).date()
        deals = await self._load_deals(session=session, agent_id=agent_id)

        deals_open = 0
        deals_closed_won = 0
        deals_closed_lost = 0
        gross_pipeline = 0.0
        weighted_pipeline = 0.0
        cycle_days: list[float] = []

        for deal in deals:
            status = (deal.status or "").lower()
            if status == "closed_won":
                deals_closed_won += 1
                duration = _deal_cycle_days(deal)
                if duration is not None:
                    cycle_days.append(duration)
            elif status == "closed_lost":
                deals_closed_lost += 1
            else:
                deals_open += 1

            estimation = float(deal.estimated_value_amount or 0.0)
            gross_pipeline += estimation
            weighted_pipeline += estimation * float(deal.confidence or 0.0)

        confirmed_total, disputed_total = await self._commission_totals(
            session=session, deals=deals
        )

        snapshot = await self._get_or_create_snapshot(
            session=session, agent_id=agent_id, as_of=as_of
        )

        snapshot.deals_open = deals_open
        snapshot.deals_closed_won = deals_closed_won
        snapshot.deals_closed_lost = deals_closed_lost
        snapshot.gross_pipeline_value = gross_pipeline or None
        snapshot.weighted_pipeline_value = weighted_pipeline or None
        snapshot.confirmed_commission_amount = confirmed_total or None
        snapshot.disputed_commission_amount = disputed_total or None
        snapshot.avg_cycle_days = (
            sum(cycle_days) / len(cycle_days) if cycle_days else None
        )
        snapshot.conversion_rate = (
            deals_closed_won / (deals_open + deals_closed_won)
            if (deals_open + deals_closed_won) > 0
            else None
        )

        snapshot.roi_metrics = snapshot.roi_metrics or {}
        snapshot.snapshot_context = snapshot.snapshot_context or {}

        await session.commit()
        await session.refresh(snapshot)
        return snapshot

    async def list_snapshots(
        self,
        *,
        session: AsyncSession,
        agent_id: UUID,
        limit: int = 30,
    ) -> list[AgentPerformanceSnapshot]:
        stmt = (
            select(AgentPerformanceSnapshot)
            .where(AgentPerformanceSnapshot.agent_id == str(agent_id))
            .order_by(AgentPerformanceSnapshot.as_of_date.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_benchmarks(
        self,
        *,
        session: AsyncSession,
        metric_key: str,
        asset_type: str | None = None,
        deal_type: str | None = None,
        cohort: str | None = None,
    ) -> list[PerformanceBenchmark]:
        stmt: Select[PerformanceBenchmark] = select(PerformanceBenchmark).where(
            PerformanceBenchmark.metric_key == metric_key
        )
        if asset_type:
            stmt = stmt.where(PerformanceBenchmark.asset_type == asset_type)
        if deal_type:
            stmt = stmt.where(PerformanceBenchmark.deal_type == deal_type)
        if cohort:
            stmt = stmt.where(PerformanceBenchmark.cohort == cohort)
        stmt = stmt.order_by(PerformanceBenchmark.effective_date.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def generate_daily_snapshots(
        self,
        *,
        session: AsyncSession,
        as_of: date | None = None,
        agent_ids: Optional[Iterable[UUID]] = None,
    ) -> list[AgentPerformanceSnapshot]:
        as_of = as_of or datetime.now(UTC).date()
        processed: list[AgentPerformanceSnapshot] = []

        targeted = list(agent_ids) if agent_ids else await self._all_agent_ids(session)
        for agent_id in targeted:
            snapshot = await self.compute_snapshot(
                session=session,
                agent_id=agent_id,
                as_of=as_of,
            )
            processed.append(snapshot)
        return processed

    async def _load_deals(
        self,
        *,
        session: AsyncSession,
        agent_id: UUID,
    ) -> list[AgentDeal]:
        stmt = (
            select(AgentDeal)
            .where(AgentDeal.agent_id == str(agent_id))
            .options(selectinload(AgentDeal.stage_events))
        )
        result = await session.execute(stmt)
        return list(result.scalars().unique())

    async def _commission_totals(
        self,
        *,
        session: AsyncSession,
        deals: Iterable[AgentDeal],
    ) -> tuple[float, float]:
        deal_ids = [deal.id for deal in deals]
        if not deal_ids:
            return 0.0, 0.0

        stmt = (
            select(
                AgentCommissionRecord.status,
                func.sum(AgentCommissionRecord.commission_amount),
            )
            .where(AgentCommissionRecord.deal_id.in_(deal_ids))
            .group_by(AgentCommissionRecord.status)
        )
        result = await session.execute(stmt)
        confirmed_total = 0.0
        disputed_total = 0.0
        for status, total in result:
            status_value = (status or "").lower()
            amount = float(total or 0.0)
            if status_value == "disputed":
                disputed_total += amount
            elif status_value in {"confirmed", "paid", "invoiced"}:
                confirmed_total += amount
        return confirmed_total, disputed_total

    async def _get_or_create_snapshot(
        self,
        *,
        session: AsyncSession,
        agent_id: UUID,
        as_of: date,
    ) -> AgentPerformanceSnapshot:
        stmt = select(AgentPerformanceSnapshot).where(
            AgentPerformanceSnapshot.agent_id == str(agent_id),
            AgentPerformanceSnapshot.as_of_date == as_of,
        )
        result = await session.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if snapshot:
            return snapshot

        snapshot = AgentPerformanceSnapshot(
            agent_id=str(agent_id),
            as_of_date=as_of,
        )
        session.add(snapshot)
        await session.flush()
        return snapshot

    async def _all_agent_ids(self, session: AsyncSession) -> list[UUID]:
        stmt = select(AgentDeal.agent_id).distinct()
        result = await session.execute(stmt)
        ids = []
        for value in result.scalars():
            try:
                ids.append(UUID(str(value)))
            except (TypeError, ValueError):  # pragma: no cover - defensive check
                continue
        return ids


def _deal_cycle_days(deal: AgentDeal) -> Optional[float]:
    try:
        created = min(
            (event.recorded_at for event in deal.stage_events),
            default=deal.created_at,
        )
        closed = deal.actual_close_date or deal.updated_at
        if not created or not closed:
            return None
        delta = closed - created
        return delta.days + delta.seconds / 86400.0
    except Exception:  # pragma: no cover - defensive
        return None


__all__ = ["AgentPerformanceService"]
