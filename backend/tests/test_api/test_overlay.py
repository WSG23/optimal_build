"""Overlay API integration tests."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.core.models.geometry import CanonicalGeometry, GeometryNode, serialize_geometry
from app.main import app
from app.models.overlay import (
    OverlayRunLock,
    OverlaySourceGeometry,
    OverlaySuggestion,
)

PROJECT_ID = 4120


@pytest_asyncio.fixture
async def overlay_client(async_session_factory):
    """Seed canonical geometry and provide a test client."""

    geometry = CanonicalGeometry(
        root=GeometryNode(
            node_id="site-001",
            kind="site",
            properties={
                "heritage_zone": True,
                "flood_zone": "coastal",
                "site_area_sqm": 12500,
            },
            children=[
                GeometryNode(
                    node_id="tower-01",
                    kind="building",
                    properties={"height_m": 52},
                )
            ],
        ),
        metadata={"source": "test"},
    )
    serialized = serialize_geometry(geometry)
    checksum = geometry.fingerprint()

    async with async_session_factory() as session:
        record = OverlaySourceGeometry(
            project_id=PROJECT_ID,
            source_geometry_key="site-001",
            graph=serialized,
            metadata={"ingest": "fixture"},
            checksum=checksum,
        )
        session.add(record)
        await session.commit()
        source_id = record.id

    async def _override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client, source_id
    app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_overlay_run_and_decisions(overlay_client, async_session_factory) -> None:
    client, source_id = overlay_client

    run_response = await client.post(f"/api/v1/overlay/{PROJECT_ID}/run")
    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["status"] == "completed"
    assert run_payload["project_id"] == PROJECT_ID
    assert run_payload["evaluated"] == 1
    assert run_payload["created"] >= 3

    list_response = await client.get(f"/api/v1/overlay/{PROJECT_ID}")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["count"] >= 3
    codes = {item["code"] for item in payload["items"]}
    assert "heritage_conservation" in codes
    assert "flood_mitigation" in codes
    assert "tall_building_review" in codes
    assert all(item["status"] == "pending" for item in payload["items"])

    heritage = next(item for item in payload["items"] if item["code"] == "heritage_conservation")
    approve_response = await client.post(
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

    flood = next(item for item in payload["items"] if item["code"] == "flood_mitigation")
    reject_response = await client.post(
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

    second_run = await client.post(f"/api/v1/overlay/{PROJECT_ID}/run")
    assert second_run.status_code == 200
    rerun_payload = second_run.json()
    assert rerun_payload["created"] == 0
    assert rerun_payload["updated"] >= 3
    assert rerun_payload["evaluated"] == 1

    final_response = await client.get(f"/api/v1/overlay/{PROJECT_ID}")
    final_payload = final_response.json()
    final_status = {item["code"]: item["status"] for item in final_payload["items"]}
    assert final_status["heritage_conservation"] == "approved"
    assert final_status["flood_mitigation"] == "rejected"
    assert final_status["tall_building_review"] == "pending"

    async with async_session_factory() as session:
        source = await session.get(OverlaySourceGeometry, source_id)
        assert source is not None
        suggestions = (
            await session.execute(
                select(OverlaySuggestion).where(OverlaySuggestion.project_id == PROJECT_ID)
            )
        ).scalars().all()
        for suggestion in suggestions:
            assert suggestion.geometry_checksum == source.checksum
        locks = (
            await session.execute(
                select(OverlayRunLock).where(OverlayRunLock.source_geometry_id == source_id)
            )
        ).scalars().all()
        assert locks
        assert all(lock.is_active is False for lock in locks)
