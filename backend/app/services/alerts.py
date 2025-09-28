"""Alert service helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefAlert, RefIngestionRun
from app.utils import metrics
from app.utils.logging import get_logger, log_event

logger = get_logger(__name__)


async def create_alert(
    session: AsyncSession,
    *,
    alert_type: str,
    level: str,
    message: str,
    ingestion_run: RefIngestionRun | None = None,
    context: dict[str, Any] | None = None,
) -> RefAlert:
    """Persist an alert record and update metrics."""

    record = RefAlert(
        alert_type=alert_type,
        level=level,
        message=message,
        context=context or {},
        ingestion_run=ingestion_run,
        ingestion_run_id=ingestion_run.id if ingestion_run is not None else None,
    )
    session.add(record)
    await session.flush()
    metrics.ALERT_COUNTER.labels(level=level).inc()
    log_event(
        logger, "alert_created", alert_type=alert_type, level=level, alert_id=record.id
    )
    return record


async def list_alerts(
    session: AsyncSession, *, alert_type: str | None = None
) -> list[RefAlert]:
    """Return alerts optionally filtered by type."""

    stmt: Select[Any] = select(RefAlert)
    if alert_type:
        stmt = stmt.where(RefAlert.alert_type == alert_type)

    result = await session.execute(stmt.order_by(RefAlert.created_at.desc()))
    alerts = list(result.scalars().all())
    log_event(logger, "alerts_listed", alert_type=alert_type, count=len(alerts))
    return alerts


async def acknowledge_alert(
    session: AsyncSession,
    alert_id: int,
    *,
    acknowledged_by: str,
) -> RefAlert | None:
    """Mark an alert as acknowledged."""

    stmt: Select[Any] = select(RefAlert).where(RefAlert.id == alert_id)
    result = await session.execute(stmt)
    alert = result.scalar_one_or_none()
    if alert is None:
        return None

    alert_db = cast(RefAlert, alert)
    alert_record = cast(Any, alert_db)
    alert_record.acknowledged = True
    alert_record.acknowledged_at = datetime.now(UTC)
    alert_record.acknowledged_by = acknowledged_by
    await session.flush()
    log_event(
        logger, "alert_acknowledged", alert_id=alert_id, acknowledged_by=acknowledged_by
    )
    return alert_db
