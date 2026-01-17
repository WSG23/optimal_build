"""Tests for Prefect ingestion flows."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from app.flows.ingestion import material_standard_ingestion_flow
from app.models.rkp import RefAlert, RefIngestionRun, RefMaterialStandard
from app.utils import metrics
from sqlalchemy import select


# ============================================================================
# BASIC INGESTION FLOW TESTS
# ============================================================================


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

    run_counter = metrics.counter_value(
        metrics.INGESTION_RUN_COUNTER, {"flow": "material-standard-ingestion"}
    )
    assert run_counter == 1.0
    ingested_counter = metrics.counter_value(
        metrics.INGESTED_RECORD_COUNTER, {"flow": "material-standard-ingestion"}
    )
    assert ingested_counter == 1.0


@pytest.mark.asyncio
async def test_ingestion_flow_empty_records(session_factory, session):
    """The ingestion flow handles empty record list gracefully."""

    records = []

    result = await material_standard_ingestion_flow(
        records, session_factory=session_factory
    )

    assert result == {"records_ingested": 0, "suspected_updates": 0}

    # No standards should be created
    standards = (await session.execute(select(RefMaterialStandard))).scalars().all()
    assert len(standards) == 0

    # No alerts should be created for zero suspected updates
    alerts = (await session.execute(select(RefAlert))).scalars().all()
    assert len(alerts) == 0

    # Ingestion run should still be recorded
    runs = (await session.execute(select(RefIngestionRun))).scalars().all()
    assert len(runs) == 1
    assert runs[0].status == "success"


@pytest.mark.asyncio
async def test_ingestion_flow_multiple_records(session_factory, session):
    """The ingestion flow processes multiple records correctly."""

    records = [
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "yield_strength",
            "value": "460",
            "unit": "MPa",
        },
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "tensile_strength",
            "value": "550",
            "unit": "MPa",
        },
        {
            "standard_code": "SS 2",
            "material_type": "concrete",
            "standard_body": "BCA",
            "property_key": "compressive_strength",
            "value": "40",
            "unit": "MPa",
        },
    ]

    result = await material_standard_ingestion_flow(
        records, session_factory=session_factory
    )

    assert result == {"records_ingested": 3, "suspected_updates": 0}

    standards = (await session.execute(select(RefMaterialStandard))).scalars().all()
    assert len(standards) == 3


@pytest.mark.asyncio
async def test_ingestion_flow_counts_suspected_updates(session_factory, session):
    """The ingestion flow correctly counts suspected updates."""

    records = [
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "yield_strength",
            "value": "460",
            "unit": "MPa",
        },
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "tensile_strength",
            "value": "550",
            "unit": "MPa",
            "suspected_update": True,
        },
        {
            "standard_code": "SS 2",
            "material_type": "concrete",
            "standard_body": "BCA",
            "property_key": "compressive_strength",
            "value": "40",
            "unit": "MPa",
            "suspected_update": True,
        },
    ]

    result = await material_standard_ingestion_flow(
        records, session_factory=session_factory
    )

    assert result == {"records_ingested": 3, "suspected_updates": 2}


@pytest.mark.asyncio
async def test_ingestion_flow_creates_alert_for_suspected_updates(
    session_factory, session
):
    """The ingestion flow creates an alert when suspected updates are found."""

    records = [
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "yield_strength",
            "value": "460",
            "unit": "MPa",
            "suspected_update": True,
        },
        {
            "standard_code": "SS 2",
            "material_type": "concrete",
            "standard_body": "BCA",
            "property_key": "compressive_strength",
            "value": "40",
            "unit": "MPa",
            "suspected_update": True,
        },
    ]

    await material_standard_ingestion_flow(records, session_factory=session_factory)

    alerts = (await session.execute(select(RefAlert))).scalars().all()
    assert len(alerts) == 1

    alert = alerts[0]
    assert alert.alert_type == "material_standard_update"
    assert alert.level == "warning"
    assert "2 material standards flagged for review" in alert.message
    assert alert.context == {"suspected_updates": 2}


@pytest.mark.asyncio
async def test_ingestion_flow_no_alert_without_suspected_updates(
    session_factory, session
):
    """The ingestion flow does not create an alert if no suspected updates."""

    records = [
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "yield_strength",
            "value": "460",
            "unit": "MPa",
        },
    ]

    await material_standard_ingestion_flow(records, session_factory=session_factory)

    alerts = (await session.execute(select(RefAlert))).scalars().all()
    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_ingestion_flow_removes_suspected_update_flag_from_payload(
    session_factory, session
):
    """The suspected_update flag is removed before upserting."""

    records = [
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "yield_strength",
            "value": "460",
            "unit": "MPa",
            "suspected_update": True,
        },
    ]

    await material_standard_ingestion_flow(records, session_factory=session_factory)

    # The standard should be created without the suspected_update field
    standards = (await session.execute(select(RefMaterialStandard))).scalars().all()
    assert len(standards) == 1

    # Verify the record was created successfully (no error from unknown field)
    standard = standards[0]
    assert standard.standard_code == "SS 1"
    assert standard.value == "460"


@pytest.mark.asyncio
async def test_ingestion_run_tracks_success_status(session_factory, session):
    """The ingestion run is recorded with success status."""

    records = [
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "yield_strength",
            "value": "460",
            "unit": "MPa",
        },
    ]

    await material_standard_ingestion_flow(records, session_factory=session_factory)

    runs = (await session.execute(select(RefIngestionRun))).scalars().all()
    assert len(runs) == 1

    run = runs[0]
    assert run.flow_name == "material-standard-ingestion"
    assert run.status == "success"
    assert run.records_ingested == 1
    assert run.suspected_updates == 0
    assert run.started_at is not None
    assert run.finished_at is not None


@pytest.mark.asyncio
async def test_ingestion_run_tracks_metrics(session_factory, session):
    """The ingestion run records extra metrics."""

    records = [
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "yield_strength",
            "value": "460",
            "unit": "MPa",
            "suspected_update": True,
        },
        {
            "standard_code": "SS 2",
            "material_type": "concrete",
            "standard_body": "BCA",
            "property_key": "compressive_strength",
            "value": "40",
            "unit": "MPa",
        },
    ]

    await material_standard_ingestion_flow(records, session_factory=session_factory)

    runs = (await session.execute(select(RefIngestionRun))).scalars().all()
    run = runs[0]
    assert run.metrics == {"records_ingested": 2}


@pytest.mark.asyncio
async def test_ingestion_flow_upserts_existing_standard(session_factory, session):
    """The ingestion flow updates existing standards instead of creating duplicates."""

    # First ingestion
    records_v1 = [
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "yield_strength",
            "value": "460",
            "unit": "MPa",
        },
    ]

    await material_standard_ingestion_flow(records_v1, session_factory=session_factory)

    # Second ingestion with updated value
    records_v2 = [
        {
            "standard_code": "SS 1",
            "material_type": "steel",
            "standard_body": "BCA",
            "property_key": "yield_strength",
            "value": "500",
            "unit": "MPa",
        },
    ]

    await material_standard_ingestion_flow(records_v2, session_factory=session_factory)

    # Should still have only one standard (upserted)
    standards = (await session.execute(select(RefMaterialStandard))).scalars().all()
    assert len(standards) == 1
    assert standards[0].value == "500"  # Updated value
