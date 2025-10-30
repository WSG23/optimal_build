"""Tests for ingestion run helpers."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest

pytest.importorskip("sqlalchemy")

from app.services import ingestion


@pytest.mark.asyncio
async def test_start_ingestion_run_creates_record(session):
    """Test creating a new ingestion run record."""
    run = await ingestion.start_ingestion_run(
        session, flow_name="test-flow", notes="Test notes"
    )
    await session.commit()

    assert run.id is not None
    assert run.flow_name == "test-flow"
    assert run.status == "running"
    assert run.started_at is not None
    assert run.notes == "Test notes"
    assert run.run_key is not None


@pytest.mark.asyncio
async def test_start_ingestion_run_generates_run_key(session):
    """Test that run_key is auto-generated if not provided."""
    run = await ingestion.start_ingestion_run(session, flow_name="test-flow")
    await session.commit()

    assert run.run_key is not None
    # Should be a valid UUID
    UUID(run.run_key)


@pytest.mark.asyncio
async def test_start_ingestion_run_uses_provided_run_key(session):
    """Test that provided run_key is used."""
    custom_key = "custom-run-key-123"

    run = await ingestion.start_ingestion_run(
        session, flow_name="test-flow", run_key=custom_key
    )
    await session.commit()

    assert run.run_key == custom_key


@pytest.mark.asyncio
async def test_start_ingestion_run_without_notes(session):
    """Test creating run without notes."""
    run = await ingestion.start_ingestion_run(session, flow_name="test-flow")
    await session.commit()

    assert run.notes is None


@pytest.mark.asyncio
async def test_complete_ingestion_run_updates_status(session):
    """Test completing an ingestion run updates status."""
    run = await ingestion.start_ingestion_run(session, flow_name="test-flow")
    await session.flush()

    completed_run = await ingestion.complete_ingestion_run(
        session,
        run,
        status="completed",
        records_ingested=100,
        suspected_updates=5,
    )
    await session.commit()

    assert completed_run.status == "completed"
    assert completed_run.records_ingested == 100
    assert completed_run.suspected_updates == 5
    assert completed_run.finished_at is not None


@pytest.mark.asyncio
async def test_complete_ingestion_run_with_extra_metrics(session):
    """Test completing run with extra metrics."""
    run = await ingestion.start_ingestion_run(session, flow_name="test-flow")
    await session.flush()

    extra_metrics = {"processing_time_ms": 1500, "error_count": 2}

    completed_run = await ingestion.complete_ingestion_run(
        session,
        run,
        status="completed",
        records_ingested=50,
        suspected_updates=3,
        extra_metrics=extra_metrics,
    )
    await session.commit()

    assert completed_run.metrics == extra_metrics


@pytest.mark.asyncio
async def test_complete_ingestion_run_without_extra_metrics(session):
    """Test completing run without extra metrics."""
    run = await ingestion.start_ingestion_run(session, flow_name="test-flow")
    await session.flush()

    completed_run = await ingestion.complete_ingestion_run(
        session,
        run,
        status="completed",
        records_ingested=25,
        suspected_updates=1,
    )
    await session.commit()

    assert completed_run.metrics == {}


@pytest.mark.asyncio
async def test_complete_ingestion_run_with_failed_status(session):
    """Test completing run with failed status."""
    run = await ingestion.start_ingestion_run(session, flow_name="test-flow")
    await session.flush()

    completed_run = await ingestion.complete_ingestion_run(
        session,
        run,
        status="failed",
        records_ingested=0,
        suspected_updates=0,
    )
    await session.commit()

    assert completed_run.status == "failed"
    assert completed_run.records_ingested == 0


@pytest.mark.asyncio
async def test_complete_ingestion_run_sets_finished_at(session):
    """Test that finished_at timestamp is set on completion."""
    run = await ingestion.start_ingestion_run(session, flow_name="test-flow")
    await session.flush()

    start_time = run.started_at

    completed_run = await ingestion.complete_ingestion_run(
        session,
        run,
        status="completed",
        records_ingested=10,
        suspected_updates=0,
    )
    await session.commit()

    assert completed_run.finished_at is not None
    assert completed_run.finished_at > start_time


@pytest.mark.asyncio
async def test_start_ingestion_run_different_flow_names(session):
    """Test creating runs with different flow names."""
    flow_names = ["flow-a", "flow-b", "flow-c"]

    for flow_name in flow_names:
        run = await ingestion.start_ingestion_run(session, flow_name=flow_name)
        await session.flush()
        assert run.flow_name == flow_name

    await session.commit()


@pytest.mark.asyncio
async def test_complete_ingestion_run_with_zero_records(session):
    """Test completing run with zero records ingested."""
    run = await ingestion.start_ingestion_run(session, flow_name="test-flow")
    await session.flush()

    completed_run = await ingestion.complete_ingestion_run(
        session,
        run,
        status="completed",
        records_ingested=0,
        suspected_updates=0,
    )
    await session.commit()

    assert completed_run.records_ingested == 0
    assert completed_run.suspected_updates == 0


@pytest.mark.asyncio
async def test_complete_ingestion_run_with_large_numbers(session):
    """Test completing run with large record counts."""
    run = await ingestion.start_ingestion_run(session, flow_name="test-flow")
    await session.flush()

    completed_run = await ingestion.complete_ingestion_run(
        session,
        run,
        status="completed",
        records_ingested=1000000,
        suspected_updates=50000,
    )
    await session.commit()

    assert completed_run.records_ingested == 1000000
    assert completed_run.suspected_updates == 50000
