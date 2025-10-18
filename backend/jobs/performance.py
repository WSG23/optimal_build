"""Background jobs for agent performance analytics."""

from __future__ import annotations

from datetime import date
from typing import Iterable
from uuid import UUID

from backend.jobs import job

from app.core.database import AsyncSessionLocal
from app.services.deals.performance import AgentPerformanceService


def _parse_ids(agent_ids: Iterable[str] | None) -> list[UUID] | None:
    if not agent_ids:
        return None
    parsed: list[UUID] = []
    for value in agent_ids:
        try:
            parsed.append(UUID(str(value)))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            continue
    return parsed or None


def _parse_as_of(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    return date.fromisoformat(value)


@job(name="performance.generate_snapshots")
async def generate_snapshots_job(
    agent_ids: Iterable[str] | None = None,
    as_of: str | None = None,
) -> dict[str, int]:
    service = AgentPerformanceService()
    async with AsyncSessionLocal() as session:
        snapshots = await service.generate_daily_snapshots(
            session=session,
            agent_ids=_parse_ids(agent_ids),
            as_of=_parse_as_of(as_of),
        )
        return {"snapshots": len(snapshots)}


@job(name="performance.seed_benchmarks")
async def seed_benchmarks_job() -> dict[str, int]:
    service = AgentPerformanceService()
    async with AsyncSessionLocal() as session:
        count = await service.seed_default_benchmarks(session=session)
        return {"benchmarks": count}


__all__ = ["generate_snapshots_job", "seed_benchmarks_job"]
