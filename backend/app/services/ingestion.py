"""Prefect ingestion run helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefIngestionRun
from app.utils import metrics
from app.utils.logging import get_logger, log_event
from backend._compat.datetime import UTC

logger = get_logger(__name__)


async def start_ingestion_run(
    session: AsyncSession,
    *,
    flow_name: str,
    run_key: str | None = None,
    notes: str | None = None,
) -> RefIngestionRun:
    """Create a new ingestion run record."""

    record = RefIngestionRun(
        flow_name=flow_name,
        run_key=run_key or str(uuid4()),
        status="running",
        started_at=datetime.now(UTC),
        notes=notes,
    )
    session.add(record)
    await session.flush()
    metrics.INGESTION_RUN_COUNTER.labels(flow=flow_name).inc()
    log_event(logger, "ingestion_run_started", flow_name=flow_name, run_id=record.id)
    return record


async def complete_ingestion_run(
    session: AsyncSession,
    run: RefIngestionRun,
    *,
    status: str,
    records_ingested: int,
    suspected_updates: int,
    extra_metrics: dict[str, Any] | None = None,
) -> RefIngestionRun:
    """Finalize an ingestion run and update metrics."""

    run_record = cast(Any, run)
    run_record.status = status
    run_record.finished_at = datetime.now(UTC)
    run_record.records_ingested = records_ingested
    run_record.suspected_updates = suspected_updates
    run_record.metrics = extra_metrics or {}
    await session.flush()

    metrics.INGESTED_RECORD_COUNTER.labels(flow=run_record.flow_name).inc(
        records_ingested
    )
    log_event(
        logger,
        "ingestion_run_completed",
        flow_name=run.flow_name,
        run_id=run.id,
        status=status,
        records=records_ingested,
        suspected_updates=suspected_updates,
    )
    return run
