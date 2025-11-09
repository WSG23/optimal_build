"""Integration tests for preview job execution to prevent regression.

These tests specifically verify that preview jobs complete successfully
without hanging, addressing the issue where inline job execution would
hang due to transaction rollback after job INSERT but before execution.
"""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest

from app.models.preview import PreviewJob, PreviewJobStatus
from app.services.preview_jobs import PreviewJobService
from httpx import AsyncClient
from sqlalchemy import select


@pytest.mark.asyncio
async def test_capture_property_completes_without_hanging(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    """Test that capture property completes within reasonable time.

    This test prevents regression of the bug where preview job execution
    would hang indefinitely due to transaction rollback issues in inline
    backend mode.

    Regression prevention for: Backend hanging during capture (2025-01-09)
    """
    # Use asyncio.wait_for to enforce timeout - should complete in < 30 seconds
    try:
        response = await asyncio.wait_for(
            app_client.post(
                "/api/v1/developers/properties/log-gps",
                json={
                    "latitude": 1.2801,
                    "longitude": 103.8198,
                    "development_scenarios": ["raw_land"],
                },
            ),
            timeout=30.0,  # Fail if request takes > 30 seconds
        )
    except asyncio.TimeoutError:
        pytest.fail(
            "Capture property request timed out after 30 seconds. "
            "This indicates the backend is hanging during preview job execution. "
            "Check preview_jobs.py queue_preview() method for transaction issues."
        )

    assert response.status_code == 200, response.text
    payload = response.json()

    # Verify preview job was created
    assert "preview_jobs" in payload
    assert len(payload["preview_jobs"]) > 0
    preview_job = payload["preview_jobs"][0]

    # Verify job reached a terminal state (not stuck in QUEUED)
    assert preview_job["status"] in {"ready", "processing", "failed"}

    # If status is READY, verify all URLs are populated
    if preview_job["status"] == "ready":
        assert preview_job[
            "preview_url"
        ], "preview_url should be populated for READY jobs"
        assert preview_job[
            "metadata_url"
        ], "metadata_url should be populated for READY jobs"
        assert preview_job[
            "thumbnail_url"
        ], "thumbnail_url should be populated for READY jobs"

    # Verify job exists in database and is not stuck
    job_id = UUID(preview_job["id"])
    async with async_session_factory() as session:
        db_job = await session.get(PreviewJob, job_id)
        assert db_job is not None
        assert db_job.metadata is not None

        # Verify job is not stuck in QUEUED status
        # (The main bug we're preventing - jobs getting stuck without executing)
        assert (
            db_job.status != PreviewJobStatus.QUEUED
        ), f"Job should not be stuck in QUEUED status. Current status: {db_job.status}"


@pytest.mark.asyncio
async def test_refresh_preview_completes_without_hanging(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    """Test that refresh preview completes within reasonable time.

    This test prevents regression of the bug where refresh preview would
    hang indefinitely in inline backend mode.

    Regression prevention for: Backend hanging during refresh (2025-01-09)
    """
    # First create a preview job
    response = await asyncio.wait_for(
        app_client.post(
            "/api/v1/developers/properties/log-gps",
            json={
                "latitude": 1.2801,
                "longitude": 103.8198,
                "development_scenarios": ["raw_land"],
            },
        ),
        timeout=30.0,
    )
    assert response.status_code == 200
    payload = response.json()
    preview_job_id = payload["preview_jobs"][0]["id"]

    # Now test refresh with timeout
    try:
        refresh_response = await asyncio.wait_for(
            app_client.post(
                f"/api/v1/developers/preview-jobs/{preview_job_id}/refresh"
            ),
            timeout=30.0,  # Fail if request takes > 30 seconds
        )
    except asyncio.TimeoutError:
        pytest.fail(
            "Refresh preview request timed out after 30 seconds. "
            "This indicates the backend is hanging during preview job refresh. "
            "Check preview_jobs.py refresh_job() method for transaction issues."
        )

    assert refresh_response.status_code == 200, refresh_response.text
    refreshed_payload = refresh_response.json()

    # Verify refreshed job reached a terminal state
    assert refreshed_payload["status"] in {"ready", "processing", "failed"}

    # Verify job has fresh timestamp
    async with async_session_factory() as session:
        db_job = await session.get(PreviewJob, UUID(preview_job_id))
        assert db_job is not None
        assert db_job.requested_at is not None

        # Verify job is not stuck in QUEUED status
        assert (
            db_job.status != PreviewJobStatus.QUEUED
        ), f"Job stuck in QUEUED after refresh. Status: {db_job.status}"


@pytest.mark.asyncio
async def test_preview_job_service_queue_inline_execution(
    async_session_factory,
) -> None:
    """Test PreviewJobService.queue_preview with inline backend.

    This test directly verifies the service layer logic to ensure
    inline backend commits session before executing generate_preview_job.

    Regression prevention for: Transaction rollback in queue_preview (2025-01-09)
    """
    property_id = uuid4()
    massing_layers = [
        {
            "height_m": 45.0,
            "gfa_sqm": 5000.0,
            "color": "#3B82F6",
            "label": "Office",
        }
    ]

    async with async_session_factory() as session:
        service = PreviewJobService(session)

        # Execute with timeout to catch hangs
        try:
            job = await asyncio.wait_for(
                service.queue_preview(
                    property_id=property_id,
                    scenario="raw_land",
                    massing_layers=massing_layers,
                ),
                timeout=15.0,  # Service layer should complete faster than API
            )
        except asyncio.TimeoutError:
            pytest.fail(
                "PreviewJobService.queue_preview timed out after 15 seconds. "
                "This indicates hanging during inline job execution. "
                "Verify session.commit() happens before generate_preview_job() call."
            )

        assert job is not None
        assert job.id is not None
        assert job.property_id == property_id
        assert job.scenario == "raw_land"

        # Verify job metadata exists
        assert job.metadata is not None

        # Verify job reached a terminal state (not stuck in QUEUED)
        assert job.status in {
            PreviewJobStatus.READY,
            PreviewJobStatus.PROCESSING,
            PreviewJobStatus.FAILED,
        }, f"Job stuck in unexpected status: {job.status}"

        # For inline backend (JOB_QUEUE_BACKEND=inline), job should complete synchronously
        backend_name = job.metadata.get("job_backend")
        if backend_name == "inline":
            await session.refresh(job)
            assert (
                job.status == PreviewJobStatus.READY
            ), "Inline backend should execute synchronously and reach READY status"
            assert job.preview_url is not None
            assert job.metadata_url is not None
            assert job.thumbnail_url is not None


@pytest.mark.asyncio
async def test_multiple_concurrent_captures(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    """Test that multiple concurrent capture requests all complete successfully.

    This test verifies that the fix for inline execution doesn't introduce
    race conditions or deadlocks when multiple requests are processed concurrently.
    """

    async def capture_property(lat: float, lng: float) -> dict:
        response = await app_client.post(
            "/api/v1/developers/properties/log-gps",
            json={
                "latitude": lat,
                "longitude": lng,
                "development_scenarios": ["raw_land"],
            },
        )
        assert response.status_code == 200
        return response.json()

    # Create 3 concurrent capture requests with timeout
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                capture_property(1.2801, 103.8198),
                capture_property(1.2802, 103.8199),
                capture_property(1.2803, 103.8200),
            ),
            timeout=60.0,  # All 3 should complete within 60 seconds total
        )
    except asyncio.TimeoutError:
        pytest.fail(
            "Concurrent capture requests timed out after 60 seconds. "
            "This may indicate deadlock or resource contention issues."
        )

    # Verify all 3 completed successfully
    assert len(results) == 3
    for result in results:
        assert "preview_jobs" in result
        assert len(result["preview_jobs"]) > 0
        preview_job = result["preview_jobs"][0]
        assert preview_job["status"] in {"ready", "processing", "failed"}

    # Verify all jobs are in database and not stuck
    async with async_session_factory() as session:
        all_jobs = (await session.execute(select(PreviewJob))).scalars().all()

        # Should have at least 3 jobs from this test
        assert len(all_jobs) >= 3

        # None should be stuck in QUEUED status
        queued_jobs = [j for j in all_jobs if j.status == PreviewJobStatus.QUEUED]
        assert len(queued_jobs) == 0, (
            f"Found {len(queued_jobs)} jobs stuck in QUEUED status. "
            "This indicates jobs are not being processed."
        )


@pytest.mark.asyncio
async def test_preview_job_includes_checksum(
    async_session_factory,
) -> None:
    """Test that preview jobs include payload checksum for cache validation.

    This test verifies that the payload_checksum field is populated correctly
    and can be used to detect when massing layers have changed.
    """
    property_id = uuid4()
    massing_layers = [
        {
            "height_m": 45.0,
            "gfa_sqm": 5000.0,
            "color": "#3B82F6",
            "label": "Office",
        }
    ]

    async with async_session_factory() as session:
        service = PreviewJobService(session)

        # Create first job
        job1 = await service.queue_preview(
            property_id=property_id,
            scenario="raw_land",
            massing_layers=massing_layers,
        )
        await session.commit()

        # Create second job with same layers - should have same checksum
        job2 = await service.queue_preview(
            property_id=property_id,
            scenario="raw_land",
            massing_layers=massing_layers,
        )
        await session.commit()

        assert (
            job1.payload_checksum == job2.payload_checksum
        ), "Jobs with identical massing layers should have identical checksums"

        # Create third job with different layers - should have different checksum
        different_layers = [
            {
                "height_m": 60.0,  # Different height
                "gfa_sqm": 5000.0,
                "color": "#3B82F6",
                "label": "Office",
            }
        ]
        job3 = await service.queue_preview(
            property_id=property_id,
            scenario="raw_land",
            massing_layers=different_layers,
        )
        await session.commit()

        assert (
            job1.payload_checksum != job3.payload_checksum
        ), "Jobs with different massing layers should have different checksums"
