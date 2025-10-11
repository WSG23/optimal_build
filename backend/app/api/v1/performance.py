"""Agent performance analytics endpoints."""

from __future__ import annotations

from datetime import date
from typing import Iterable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.database import get_session
from app.models.business_performance import AgentPerformanceSnapshot, PerformanceBenchmark
from app.schemas.performance import (
    AgentPerformanceSnapshotResponse,
    BenchmarkResponse,
    SnapshotRequest,
)
from app.services.deals import AgentPerformanceService

router = APIRouter(prefix="/performance", tags=["Business Performance"])

service = AgentPerformanceService()


@router.post("/snapshots", response_model=AgentPerformanceSnapshotResponse)
async def create_snapshot(
    payload: SnapshotRequest,
    _: str = Depends(require_viewer),
    session: AsyncSession = Depends(get_session),
) -> AgentPerformanceSnapshotResponse:
    snapshot = await service.compute_snapshot(
        session=session,
        agent_id=payload.agent_id,
        as_of=payload.as_of,
    )
    return AgentPerformanceSnapshotResponse.from_orm_snapshot(snapshot)


@router.get(
    "/snapshots",
    response_model=list[AgentPerformanceSnapshotResponse],
)
async def list_snapshots(
    agent_id: UUID = Query(...),
    limit: int = Query(default=30, ge=1, le=90),
    _: str = Depends(require_viewer),
    session: AsyncSession = Depends(get_session),
) -> list[AgentPerformanceSnapshotResponse]:
    snapshots = await service.list_snapshots(
        session=session, agent_id=agent_id, limit=limit
    )
    return [AgentPerformanceSnapshotResponse.from_orm_snapshot(s) for s in snapshots]


@router.post(
    "/snapshots/generate",
    response_model=list[AgentPerformanceSnapshotResponse],
)
async def generate_daily_snapshots(
    agent_ids: Iterable[UUID] | None = Query(default=None),
    as_of: date | None = Query(default=None),
    _: str = Depends(require_viewer),
    session: AsyncSession = Depends(get_session),
) -> list[AgentPerformanceSnapshotResponse]:
    snapshots = await service.generate_daily_snapshots(
        session=session,
        as_of=as_of,
        agent_ids=agent_ids,
    )
    return [AgentPerformanceSnapshotResponse.from_orm_snapshot(s) for s in snapshots]


@router.get(
    "/benchmarks",
    response_model=list[BenchmarkResponse],
)
async def list_benchmarks(
    metric_key: str = Query(...),
    asset_type: str | None = Query(default=None),
    deal_type: str | None = Query(default=None),
    cohort: str | None = Query(default=None),
    _: str = Depends(require_viewer),
    session: AsyncSession = Depends(get_session),
) -> list[BenchmarkResponse]:
    if not metric_key:
        raise HTTPException(status_code=400, detail="metric_key is required")

    benchmarks = await service.list_benchmarks(
        session=session,
        metric_key=metric_key,
        asset_type=asset_type,
        deal_type=deal_type,
        cohort=cohort,
    )
    return [BenchmarkResponse.from_orm_benchmark(b) for b in benchmarks]


__all__ = ["router"]
