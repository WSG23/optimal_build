"""Tests for Prefect ingestion flows."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select

from backend.app.flows.ingestion import material_standard_ingestion_flow
from backend.app.models.rkp import RefAlert, RefMaterialStandard
from backend.app.utils import metrics


@pytest.mark.asyncio
async def test_material_standard_ingestion_flow(session_factory, session):
    """The ingestion flow records runs, standards, and alerts."""

    records = [
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "yield_strength",
            "value": "460",
            "unit": "MPa",
            "suspected_update": True,
        }
    ]

    await material_standard_ingestion_flow(records, session_factory=session_factory)

    standards = (await session.execute(select(RefMaterialStandard))).scalars().all()
    assert len(standards) == 1

    alerts = (await session.execute(select(RefAlert))).scalars().all()
    assert len(alerts) == 1

    run_counter = metrics.counter_value(metrics.INGESTION_RUN_COUNTER, {"flow": "material-standard-ingestion"})
    assert run_counter == 1.0
    ingested_counter = metrics.counter_value(metrics.INGESTED_RECORD_COUNTER, {"flow": "material-standard-ingestion"})
    assert ingested_counter == 1.0
