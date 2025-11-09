"""Tests for alert logging services."""

from __future__ import annotations

from datetime import datetime

import pytest
from backend._compat.datetime import UTC

pytest.importorskip("sqlalchemy")

from app.models.rkp import RefAlert
from app.services import alerts, ingestion
from app.utils import metrics


@pytest.mark.asyncio
async def test_alert_logging(session):
    """Creating an alert persists data and updates metrics."""

    metrics.reset_metrics()
    run = await ingestion.start_ingestion_run(session, flow_name="test-flow")
    alert = await alerts.create_alert(
        session,
        alert_type="material_standard_update",
        level="warning",
        message="Suspected update",
        ingestion_run=run,
        context={"records": 2},
    )
    await session.commit()

    assert alert.id is not None
    assert alert.ingestion_run_id == run.id
    value = metrics.counter_value(metrics.ALERT_COUNTER, {"level": "warning"})
    assert value == 1.0


@pytest.mark.asyncio
async def test_list_alerts_filters_by_type(session):
    """Listing alerts supports optional type filters and retains ordering."""

    metrics.reset_metrics()
    run = await ingestion.start_ingestion_run(session, flow_name="filter-flow")
    first = await alerts.create_alert(
        session,
        alert_type="ingestion",
        level="info",
        message="Initial",
        ingestion_run=run,
    )
    second = await alerts.create_alert(
        session,
        alert_type="material_standard_update",
        level="warning",
        message="Follow-up",
    )
    await session.commit()

    all_alerts = await alerts.list_alerts(session)
    assert {alert.id for alert in all_alerts} == {first.id, second.id}

    filtered = await alerts.list_alerts(session, alert_type="ingestion")
    assert [alert.id for alert in filtered] == [first.id]


@pytest.mark.asyncio
async def test_acknowledge_alert_updates_state(session):
    """Acknowledging an alert persists audit fields."""

    run = await ingestion.start_ingestion_run(session, flow_name="ack-flow")
    alert = await alerts.create_alert(
        session,
        alert_type="ingestion",
        level="error",
        message="Needs review",
        ingestion_run=run,
    )
    await session.commit()

    acknowledged = await alerts.acknowledge_alert(
        session, alert.id, acknowledged_by="operator@test"
    )
    assert acknowledged is not None
    assert acknowledged.acknowledged is True
    assert acknowledged.acknowledged_by == "operator@test"
    assert isinstance(acknowledged.acknowledged_at, datetime)
    assert acknowledged.acknowledged_at.tzinfo is UTC

    await session.commit()
    refreshed = await session.get(RefAlert, alert.id)
    assert refreshed is not None
    assert refreshed.acknowledged is True
    assert refreshed.acknowledged_by == "operator@test"


@pytest.mark.asyncio
async def test_acknowledge_alert_missing_returns_none(session):
    """Acknowledging a non-existent alert yields ``None``."""

    result = await alerts.acknowledge_alert(
        session, alert_id=9999, acknowledged_by="nobody"
    )
    assert result is None
