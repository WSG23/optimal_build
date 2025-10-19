from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from backend.jobs import job_queue
from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.overlay import OverlayRunLock, OverlaySourceGeometry, OverlaySuggestion
from httpx import AsyncClient

PROJECT_ID = 4120
SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"


@pytest.mark.asyncio
async def test_overlay_run_and_decisions(
    app_client: AsyncClient,
    async_session_factory,
    monkeypatch,
) -> None:
    sample_path = SAMPLES_DIR / "sample_floorplan.json"

    with sample_path.open("rb") as handle:
        upload_response = await app_client.post(
            "/api/v1/import",
            files={"file": (sample_path.name, handle, "application/json")},
            data={"project_id": str(PROJECT_ID), "zone_code": "SG:residential"},
        )

    assert upload_response.status_code == 201
    import_payload = upload_response.json()

    parse_response = await app_client.post(
        f"/api/v1/parse/{import_payload['import_id']}"
    )
    assert parse_response.status_code == 200
    parse_payload = parse_response.json()
    assert parse_payload["status"] == "completed"
    assert parse_payload["result"]

    async with async_session_factory() as session:
        sources = (
            (
                await session.execute(
                    select(OverlaySourceGeometry).where(
                        OverlaySourceGeometry.project_id == PROJECT_ID
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(sources) == 1
        source = sources[0]
        assert source.source_geometry_key.endswith(import_payload["import_id"])
        assert source.metadata["import_id"] == import_payload["import_id"]
        assert source.metadata["floors"] == parse_payload["result"]["floors"]
        assert source.metadata["units"] == parse_payload["result"]["units"]
        assert (
            source.metadata["parser"] == parse_payload["result"]["metadata"]["source"]
        )
        assert source.checksum

        events = (
            (
                await session.execute(
                    select(AuditLog)
                    .where(AuditLog.project_id == PROJECT_ID)
                    .order_by(AuditLog.version)
                )
            )
            .scalars()
            .all()
        )
        assert events
        event_types = [event.event_type for event in events]
        assert "geometry_ingested" in event_types
        geometry_event = next(
            event for event in events if event.event_type == "geometry_ingested"
        )
        assert geometry_event.context["overlay_source_id"] == source.id
        source_id = source.id

    metadata_section = parse_payload["result"].get("metadata", {})
    assert metadata_section.get("overlay_source_id") == source_id
    assert metadata_section.get("overlay_checksum") == source.checksum

    calls = []
    original_enqueue = job_queue.enqueue

    async def tracking_enqueue(*args, **kwargs):
        calls.append(args)
        return await original_enqueue(*args, **kwargs)

    monkeypatch.setattr(job_queue, "enqueue", tracking_enqueue)

    run_response = await app_client.post(f"/api/v1/overlay/{PROJECT_ID}/run")
    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["status"] == "completed"
    assert run_payload["project_id"] == PROJECT_ID
    assert run_payload["evaluated"] == 1
    assert run_payload["created"] >= 5

    list_response = await app_client.get(f"/api/v1/overlay/{PROJECT_ID}")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["count"] >= 5
    codes = {item["code"] for item in payload["items"]}
    assert "heritage_conservation" in codes
    assert "flood_mitigation" in codes
    assert "tall_building_review" in codes
    assert "coastal_evacuation_plan" in codes
    assert "rule_violation_zoning_max_building_height_m" in codes
    assert "rule_data_missing_front_setback_m" in codes
    assert (
        "rule_violation_zoning_site_coverage_max_percent" in codes
        or "rule_data_missing_site_coverage_percent" in codes
    )
    unit_codes = [code for code in codes if code.startswith("unit_space_")]
    assert unit_codes, "Expected unit overlays to be generated for parsed spaces"
    summary = next(
        (item for item in payload["items"] if item["code"] == "unit_area_summary"),
        None,
    )
    assert summary is not None
    assert summary["engine_payload"]["unit_count"] >= len(unit_codes)
    assert all(item["status"] == "pending" for item in payload["items"])
    assert all(isinstance(item["target_ids"], list) for item in payload["items"])
    assert all(isinstance(item["props"], dict) for item in payload["items"])
    assert all(isinstance(item["rule_refs"], list) for item in payload["items"])

    heritage = next(
        item for item in payload["items"] if item["code"] == "heritage_conservation"
    )
    assert heritage["type"] == "review"
    assert heritage["target_ids"]
    assert "heritage.zone.compliance" in heritage["rule_refs"]
    approve_response = await app_client.post(
        f"/api/v1/overlay/{PROJECT_ID}/decision",
        json={
            "suggestion_id": heritage["id"],
            "decision": "approve",
            "decided_by": "Planner",
            "notes": "Align with national heritage strategy.",
        },
    )
    assert approve_response.status_code == 200
    approved_item = approve_response.json()["item"]
    assert approved_item["status"] == "approved"
    assert approved_item["decision"]["decision"] == "approved"

    flood = next(
        item for item in payload["items"] if item["code"] == "flood_mitigation"
    )
    reject_response = await app_client.post(
        f"/api/v1/overlay/{PROJECT_ID}/decision",
        json={
            "suggestion_id": flood["id"],
            "decision": "reject",
            "decided_by": "Planner",
            "notes": "Mitigation handled by infrastructure team.",
        },
    )
    assert reject_response.status_code == 200
    rejected_item = reject_response.json()["item"]
    assert rejected_item["status"] == "rejected"
    assert rejected_item["decision"]["decision"] == "rejected"

    second_run = await app_client.post(f"/api/v1/overlay/{PROJECT_ID}/run")
    assert second_run.status_code == 200
    rerun_payload = second_run.json()
    assert rerun_payload["created"] == 0
    assert rerun_payload["updated"] >= 5
    assert rerun_payload["evaluated"] == 1

    final_response = await app_client.get(f"/api/v1/overlay/{PROJECT_ID}")
    final_payload = final_response.json()
    final_status = {item["code"]: item["status"] for item in final_payload["items"]}
    assert final_status["heritage_conservation"] == "approved"
    assert final_status["flood_mitigation"] == "rejected"
    assert final_status["tall_building_review"] == "pending"
    assert final_status["coastal_evacuation_plan"] == "pending"

    assert calls
    job_callable, *_ = calls[0]
    assert getattr(job_callable, "job_name", "").endswith("run_for_project")

    export_response = await app_client.post(
        f"/api/v1/export/{PROJECT_ID}",
        json={
            "format": "pdf",
            "include_source": True,
            "include_approved_overlays": True,
            "include_pending_overlays": True,
            "include_rejected_overlays": True,
        },
    )
    assert export_response.status_code == 200
    export_payload = await export_response.aread()
    assert export_payload

    async with async_session_factory() as session:
        source = await session.get(OverlaySourceGeometry, source_id)
        assert source is not None
        suggestions = (
            (
                await session.execute(
                    select(OverlaySuggestion).where(
                        OverlaySuggestion.project_id == PROJECT_ID
                    )
                )
            )
            .scalars()
            .all()
        )
        for suggestion in suggestions:
            assert suggestion.geometry_checksum == source.checksum
        locks = (
            (
                await session.execute(
                    select(OverlayRunLock).where(
                        OverlayRunLock.source_geometry_id == source_id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert locks
        assert all(lock.is_active is False for lock in locks)
