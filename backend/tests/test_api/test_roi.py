"""ROI analytics API tests."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

import pytest_asyncio
from httpx import AsyncClient

from app.core.database import get_session
from app.core.models.geometry import CanonicalGeometry, GeometryNode, serialize_geometry
from app.main import app
from app.models.overlay import OverlaySourceGeometry

PROJECT_ID = 8125


@pytest_asyncio.fixture
async def roi_client(async_session_factory):
    """Seed overlay geometry and provide an instrumented client."""

    geometry = CanonicalGeometry(
        root=GeometryNode(
            node_id="site-002",
            kind="site",
            properties={
                "heritage_zone": False,
                "flood_zone": "coastal",
                "site_area_sqm": 14250,
            },
            children=[
                GeometryNode(
                    node_id="tower-roi",
                    kind="building",
                    properties={"height_m": 58},
                )
            ],
        ),
        metadata={"source": "roi-test"},
    )
    serialized = serialize_geometry(geometry)
    checksum = geometry.fingerprint()

    async with async_session_factory() as session:
        record = OverlaySourceGeometry(
            project_id=PROJECT_ID,
            source_geometry_key="roi-source",
            graph=serialized,
            metadata={"fixture": "roi"},
            checksum=checksum,
        )
        session.add(record)
        await session.commit()

    async def _override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_roi_metrics_after_workflow(roi_client: AsyncClient) -> None:
    """Running overlay, decisions and export produces meaningful ROI metrics."""

    run_response = await roi_client.post(f"/api/v1/overlay/{PROJECT_ID}/run")
    assert run_response.status_code == 200

    list_response = await roi_client.get(f"/api/v1/overlay/{PROJECT_ID}")
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert items

    approve_target = next(item for item in items if item["code"] == "tall_building_review")
    reject_target = next(item for item in items if item["code"] == "flood_mitigation")

    approve_response = await roi_client.post(
        f"/api/v1/overlay/{PROJECT_ID}/decision",
        json={
            "suggestion_id": approve_target["id"],
            "decision": "approve",
            "decided_by": "Planner",
            "notes": "High impact automation.",
        },
    )
    assert approve_response.status_code == 200

    reject_response = await roi_client.post(
        f"/api/v1/overlay/{PROJECT_ID}/decision",
        json={
            "suggestion_id": reject_target["id"],
            "decision": "reject",
            "decided_by": "Planner",
            "notes": "Handled via external review.",
        },
    )
    assert reject_response.status_code == 200

    export_response = await roi_client.post(f"/api/v1/overlay/{PROJECT_ID}/export")
    assert export_response.status_code == 200
    export_payload = export_response.json()
    assert export_payload["baseline_seconds"] > export_payload["automated_seconds"]

    roi_response = await roi_client.get(f"/api/v1/roi/{PROJECT_ID}")
    assert roi_response.status_code == 200
    metrics = roi_response.json()

    assert metrics["iterations"] >= 1
    assert metrics["event_count"] >= 3
    assert metrics["review_hours_saved"] > 0
    assert metrics["savings_percent"] > 0
    assert metrics["automation_score"] > 0
    assert metrics["acceptance_rate"] > 0
    assert metrics["last_event_at"]
