"""Prefect flow for ingesting ergonomics reference data."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from prefect import flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.rkp import RefErgonomics


DEFAULT_ERGONOMICS_METRICS: List[Dict[str, Any]] = [
    {
        "metric_key": "reach.forward.max_distance_mm",
        "population": "wheelchair",
        "percentile": "95th",
        "value": 1200.0,
        "unit": "mm",
        "context": {"posture": "seated"},
        "notes": "Maximum comfortable forward reach for wheelchair users.",
    },
    {
        "metric_key": "stairs.tread.min_depth_mm",
        "population": "adult",
        "percentile": "50th",
        "value": 280.0,
        "unit": "mm",
        "context": {"environment": "residential"},
        "notes": "Recommended minimum tread depth for standard stairs.",
    },
]


async def _upsert_metric(
    session_factory: "async_sessionmaker[AsyncSession]",
    metric: Dict[str, Any],
) -> None:
    async with session_factory() as session:
        await _merge_metric(session, metric)
        await session.commit()


async def _merge_metric(session: AsyncSession, metric: Dict[str, Any]) -> None:
    stmt = (
        select(RefErgonomics)
        .where(RefErgonomics.metric_key == metric["metric_key"])
        .where(RefErgonomics.population == metric["population"])
        .limit(1)
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.percentile = metric.get("percentile")
        existing.value = metric.get("value")
        existing.unit = metric.get("unit")
        existing.context = metric.get("context") or {}
        existing.notes = metric.get("notes")
        existing.source = metric.get("source")
    else:
        session.add(RefErgonomics(**metric))


@flow(name="seed-ergonomics-metrics")
async def seed_ergonomics_metrics(
    session_factory: "async_sessionmaker[AsyncSession]",
    metrics: Optional[Iterable[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Seed the ergonomics reference table with baseline metrics."""

    payload = list(metrics) if metrics is not None else list(DEFAULT_ERGONOMICS_METRICS)
    for metric in payload:
        await _upsert_metric(session_factory, metric)
    return payload


async def fetch_seeded_metrics(
    session_factory: "async_sessionmaker[AsyncSession]",
) -> List[Dict[str, Any]]:
    """Retrieve all ergonomics metrics from the reference table."""

    async with session_factory() as session:
        result = await session.execute(select(RefErgonomics))
        metrics = [
            {
                "metric_key": item.metric_key,
                "population": item.population,
                "percentile": item.percentile,
                "value": float(item.value),
                "unit": item.unit,
                "context": item.context or {},
                "notes": item.notes,
            }
            for item in result.scalars().all()
        ]
    return metrics


__all__ = ["seed_ergonomics_metrics", "fetch_seeded_metrics", "DEFAULT_ERGONOMICS_METRICS"]
