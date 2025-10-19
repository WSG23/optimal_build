"""Schemas for agent performance snapshots and benchmarks."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.business_performance import (
    AgentPerformanceSnapshot,
    PerformanceBenchmark,
)


class SnapshotRequest(BaseModel):
    """Request payload for generating a snapshot."""

    agent_id: UUID
    as_of: date | None = None


class AgentPerformanceSnapshotResponse(BaseModel):
    """Response model for agent performance snapshots."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    as_of_date: date
    deals_open: int
    deals_closed_won: int
    deals_closed_lost: int
    gross_pipeline_value: float | None = None
    weighted_pipeline_value: float | None = None
    confirmed_commission_amount: float | None = None
    disputed_commission_amount: float | None = None
    avg_cycle_days: float | None = None
    conversion_rate: float | None = None
    roi_metrics: dict[str, Any]
    snapshot_context: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_snapshot(
        cls, snapshot: AgentPerformanceSnapshot
    ) -> "AgentPerformanceSnapshotResponse":
        return cls.model_validate(snapshot)


class BenchmarkResponse(BaseModel):
    """Representation of a performance benchmark entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    metric_key: str
    asset_type: str | None = None
    deal_type: str | None = None
    cohort: str
    value_numeric: float | None = None
    value_text: str | None = None
    source: str | None = None
    effective_date: date | None = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_benchmark(cls, benchmark: PerformanceBenchmark) -> "BenchmarkResponse":
        return cls.model_validate(benchmark)


__all__ = [
    "SnapshotRequest",
    "AgentPerformanceSnapshotResponse",
    "BenchmarkResponse",
]
