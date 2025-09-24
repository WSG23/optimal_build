"""Tests for alert logging services."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from backend.app.services import alerts, ingestion
from backend.app.utils import metrics


@pytest.mark.asyncio
async def test_alert_logging(session):
    """Creating an alert persists data and updates metrics."""

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
