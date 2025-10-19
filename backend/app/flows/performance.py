"""Prefect flows for agent performance analytics."""

from __future__ import annotations

from datetime import date
from typing import Iterable
from uuid import UUID

from prefect import flow

from app.core.database import AsyncSessionLocal
from app.services.deals.performance import AgentPerformanceService


def _parse_agent_ids(agent_ids: Iterable[str] | None) -> list[UUID] | None:
    if not agent_ids:
        return None
    parsed: list[UUID] = []
    for value in agent_ids:
        try:
            parsed.append(UUID(str(value)))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            continue
    return parsed or None


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return date.fromisoformat(value)


@flow(name="agent-performance-snapshots")
async def agent_performance_snapshots_flow(
    agent_ids: Iterable[str] | None = None,
    as_of: str | None = None,
) -> dict[str, int]:
    """Generate daily performance snapshots for the supplied agents."""

    service = AgentPerformanceService()
    parsed_ids = _parse_agent_ids(agent_ids)
    parsed_date = _parse_date(as_of)

    async with AsyncSessionLocal() as session:
        snapshots = await service.generate_daily_snapshots(
            session=session,
            as_of=parsed_date,
            agent_ids=parsed_ids,
        )
        return {"snapshots": len(snapshots)}


@flow(name="seed-performance-benchmarks")
async def seed_performance_benchmarks_flow() -> dict[str, int]:
    """Seed default performance benchmarks if they are missing."""

    service = AgentPerformanceService()
    async with AsyncSessionLocal() as session:
        count = await service.seed_default_benchmarks(session=session)
        return {"benchmarks": count}


__all__ = [
    "agent_performance_snapshots_flow",
    "seed_performance_benchmarks_flow",
]
