"""Analytics helpers for agent performance snapshots and benchmarks."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Iterable, Mapping, Optional, Sequence
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.metrics import RoiSnapshot, compute_project_roi
from app.data.performance_benchmarks_seed import SEED_BENCHMARKS
from app.models.business_performance import (
    AgentCommissionRecord,
    AgentDeal,
    AgentPerformanceSnapshot,
    PerformanceBenchmark,
)
from backend._compat.datetime import UTC

logger = logging.getLogger(__name__)


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

        snapshot.roi_metrics = await self._aggregate_roi_metrics(
            session=session,
            deals=deals,
        )
        snapshot.snapshot_context = snapshot.snapshot_context or {}
        snapshot.snapshot_context.update(
            _derive_snapshot_context(
                gross_pipeline=gross_pipeline,
                weighted_pipeline=weighted_pipeline,
                deals_open=deals_open,
                deals_closed_won=deals_closed_won,
            )
        )

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

    async def upsert_benchmark(
        self,
        *,
        session: AsyncSession,
        metric_key: str,
        asset_type: str | None = None,
        deal_type: str | None = None,
        cohort: str = "industry_avg",
        effective_date: date | None = None,
        value_numeric: float | None = None,
        value_text: str | None = None,
        source: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> PerformanceBenchmark:
        stmt = select(PerformanceBenchmark).where(
            PerformanceBenchmark.metric_key == metric_key,
            PerformanceBenchmark.cohort == cohort,
        )
        if asset_type is None:
            stmt = stmt.where(PerformanceBenchmark.asset_type.is_(None))
        else:
            stmt = stmt.where(PerformanceBenchmark.asset_type == asset_type)
        if deal_type is None:
            stmt = stmt.where(PerformanceBenchmark.deal_type.is_(None))
        else:
            stmt = stmt.where(PerformanceBenchmark.deal_type == deal_type)
        if effective_date is None:
            stmt = stmt.where(PerformanceBenchmark.effective_date.is_(None))
        else:
            stmt = stmt.where(PerformanceBenchmark.effective_date == effective_date)

        result = await session.execute(stmt.limit(1))
        benchmark = result.scalar_one_or_none()
        if benchmark is None:
            benchmark = PerformanceBenchmark(
                metric_key=metric_key,
                asset_type=asset_type,
                deal_type=deal_type,
                cohort=cohort,
                effective_date=effective_date,
            )
            session.add(benchmark)

        benchmark.value_numeric = value_numeric
        benchmark.value_text = value_text
        benchmark.source = source
        if metadata is not None:
            benchmark.metadata = dict(metadata)
        await session.flush()
        return benchmark

    async def seed_default_benchmarks(
        self,
        *,
        session: AsyncSession,
        seeds: Sequence[Mapping[str, object]] | None = None,
    ) -> int:
        payload = seeds or SEED_BENCHMARKS
        total = 0
        for item in payload:
            metric_key = str(item.get("metric_key"))
            asset_type = item.get("asset_type")
            deal_type = item.get("deal_type")
            cohort = str(item.get("cohort", "industry_avg"))
            effective = _coerce_date(item.get("effective_date"))
            value_numeric = _coerce_float(item.get("value_numeric"))
            value_text = item.get("value_text")
            source = item.get("source")
            metadata = item.get("metadata")
            await self.upsert_benchmark(
                session=session,
                metric_key=metric_key,
                asset_type=str(asset_type) if asset_type is not None else None,
                deal_type=str(deal_type) if deal_type is not None else None,
                cohort=cohort,
                effective_date=effective,
                value_numeric=value_numeric,
                value_text=str(value_text) if value_text is not None else None,
                source=str(source) if source is not None else None,
                metadata=metadata if isinstance(metadata, Mapping) else None,
            )
            total += 1
        await session.commit()
        return total

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
        if not targeted:
            return []
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
        from sqlalchemy import String, cast

        stmt = select(cast(AgentDeal.agent_id, String)).distinct()
        result = await session.execute(stmt)
        ids = []
        for value in result.scalars():
            try:
                ids.append(UUID(str(value)))
            except (TypeError, ValueError):
                continue
        return ids

    async def _aggregate_roi_metrics(
        self,
        *,
        session: AsyncSession,
        deals: Iterable[AgentDeal],
    ) -> dict[str, object]:
        project_snapshots: dict[int, RoiSnapshot] = {}
        offline_snapshots: dict[int, dict[str, object]] = {}

        for deal in deals:
            metadata = getattr(deal, "metadata", {}) or {}
            if not isinstance(metadata, dict):
                continue

            # Capture explicit ROI payloads recorded on the deal metadata.
            raw_roi = metadata.get("roi_metrics")
            if isinstance(raw_roi, Mapping):
                normalised = _normalise_roi_snapshot(raw_roi)
                if normalised is not None:
                    offline_snapshots[normalised["project_id"]] = normalised

            for key in ("roi_project_id", "overlay_project_id", "overlay_project"):
                project_id = _safe_int(metadata.get(key))
                if project_id is None:
                    continue
                if project_id in project_snapshots:
                    continue
                try:
                    snapshot = await compute_project_roi(
                        session,
                        project_id=project_id,
                    )
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.warning(
                        "Unable to compute ROI metrics for project %s: %s",
                        project_id,
                        exc,
                    )
                    continue
                project_snapshots[project_id] = snapshot

        combined: dict[int, dict[str, object]] = {}

        for project_id, snapshot in project_snapshots.items():
            combined[project_id] = snapshot.as_dict()

        for project_id, payload in offline_snapshots.items():
            existing = combined.get(project_id)
            if existing is None:
                combined[project_id] = payload
                continue
            current_score = _safe_float(payload.get("automation_score")) or 0.0
            existing_score = _safe_float(existing.get("automation_score")) or 0.0
            if current_score >= existing_score:
                combined[project_id] = payload

        if not combined:
            return {}

        ordered_projects = [
            combined[project_id] for project_id in sorted(combined.keys())
        ]
        summary = _summarise_roi_snapshots(ordered_projects)
        return {
            "projects": ordered_projects,
            "summary": summary,
        }


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


def _safe_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "":
            return None
        try:
            return int(stripped)
        except ValueError:
            return None
    return None


def _safe_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "":
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _normalise_roi_snapshot(payload: Mapping[str, object]) -> dict[str, object] | None:
    project_id = _safe_int(payload.get("project_id"))
    if project_id is None:
        return None
    return {
        "project_id": project_id,
        "iterations": _safe_int(payload.get("iterations")) or 0,
        "total_suggestions": _safe_int(payload.get("total_suggestions")) or 0,
        "decided_suggestions": _safe_int(payload.get("decided_suggestions")) or 0,
        "accepted_suggestions": _safe_int(payload.get("accepted_suggestions")) or 0,
        "acceptance_rate": _safe_float(payload.get("acceptance_rate")) or 0.0,
        "review_hours_saved": _safe_float(payload.get("review_hours_saved")) or 0.0,
        "automation_score": _safe_float(payload.get("automation_score")) or 0.0,
        "savings_percent": _safe_int(payload.get("savings_percent")) or 0,
        "payback_weeks": _safe_int(payload.get("payback_weeks")) or 0,
        "baseline_hours": _safe_float(payload.get("baseline_hours")) or 0.0,
        "actual_hours": _safe_float(payload.get("actual_hours")) or 0.0,
    }


def _summarise_roi_snapshots(
    snapshots: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    if not snapshots:
        return {}

    project_count = len(snapshots)
    review_hours_saved = sum(
        _safe_float(item.get("review_hours_saved")) or 0.0 for item in snapshots
    )
    baseline_hours = sum(
        _safe_float(item.get("baseline_hours")) or 0.0 for item in snapshots
    )
    actual_hours = sum(
        _safe_float(item.get("actual_hours")) or 0.0 for item in snapshots
    )
    iterations = sum(_safe_int(item.get("iterations")) or 0 for item in snapshots)
    automation_scores = [
        _safe_float(item.get("automation_score")) or 0.0 for item in snapshots
    ]
    acceptance_rates = [
        _safe_float(item.get("acceptance_rate")) or 0.0 for item in snapshots
    ]
    paybacks = [_safe_int(item.get("payback_weeks")) or 0 for item in snapshots]
    savings_percent = [
        _safe_int(item.get("savings_percent")) or 0 for item in snapshots
    ]

    average_automation = (
        sum(automation_scores) / len(automation_scores) if automation_scores else 0.0
    )
    average_acceptance = (
        sum(acceptance_rates) / len(acceptance_rates) if acceptance_rates else 0.0
    )
    average_savings_percent = (
        sum(savings_percent) / len(savings_percent) if savings_percent else 0.0
    )
    best_payback = min((value for value in paybacks if value > 0), default=None)

    return {
        "project_count": project_count,
        "total_review_hours_saved": round(review_hours_saved, 2),
        "total_baseline_hours": round(baseline_hours, 2),
        "total_actual_hours": round(actual_hours, 2),
        "total_iterations": iterations,
        "average_automation_score": round(average_automation, 4),
        "average_acceptance_rate": round(average_acceptance, 4),
        "savings_percent_average": round(average_savings_percent, 2),
        "best_payback_weeks": best_payback,
    }


def _derive_snapshot_context(
    *,
    gross_pipeline: float,
    weighted_pipeline: float,
    deals_open: int,
    deals_closed_won: int,
) -> dict[str, object]:
    weighted_ratio = None
    if gross_pipeline > 0:
        weighted_ratio = (weighted_pipeline or 0.0) / gross_pipeline
    average_pipeline_open = (
        gross_pipeline / deals_open if deals_open and gross_pipeline else None
    )
    win_ratio = (
        deals_closed_won / (deals_open + deals_closed_won)
        if (deals_open + deals_closed_won) > 0
        else None
    )
    return {
        "weighted_to_gross_ratio": (
            round(weighted_ratio, 4) if weighted_ratio is not None else None
        ),
        "average_pipeline_per_open_deal": (
            round(average_pipeline_open, 2)
            if average_pipeline_open is not None
            else None
        ),
        "win_ratio": round(win_ratio, 4) if win_ratio is not None else None,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _coerce_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value:
        return date.fromisoformat(value)
    raise TypeError(f"Unsupported effective_date value: {value!r}")


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as e:  # pragma: no cover - defensive
        raise TypeError(f"Expected numeric value, got {value!r}") from e


__all__ = ["AgentPerformanceService"]
