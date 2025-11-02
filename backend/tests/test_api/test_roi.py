"""ROI metrics API integration tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(
    reason="ROI overlay endpoints depend on scenario generation backends not wired for the test suite"
)

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

import pytest_asyncio
from app.core.geometry import GeometrySerializer
from app.core.models.geometry import GeometryGraph, Level, Relationship, Space
from app.models.overlay import OverlaySourceGeometry
from httpx import AsyncClient

PROJECT_ID = 5821


@pytest_asyncio.fixture
async def roi_client(app_client: AsyncClient, async_session_factory):
    """Seed overlay source geometry and provide a configured API client."""

    geometry = GeometryGraph(
        levels=[
            Level(
                id="SITE",
                name="Site",
                elevation=0.0,
                metadata={
                    "heritage_zone": True,
                    "flood_zone": "river",
                    "site_area_sqm": 8400,
                },
            )
        ],
        spaces=[
            Space(
                id="tower-01",
                name="Tower",
                level_id="SITE",
                metadata={"height_m": 60},
            )
        ],
        relationships=[
            Relationship(rel_type="contains", source_id="SITE", target_id="tower-01"),
        ],
    )
    serialized = GeometrySerializer.to_export(geometry)
    checksum = geometry.fingerprint()

    async with async_session_factory() as session:
        record = OverlaySourceGeometry(
            project_id=PROJECT_ID,
            source_geometry_key="roi-site",
            graph=serialized,
            metadata={"ingest": "roi-fixture"},
            checksum=checksum,
        )
        session.add(record)
        await session.commit()

    return app_client


@pytest.mark.asyncio
async def test_roi_metrics_after_workflow(roi_client: AsyncClient) -> None:
    """ROI endpoint should surface non-zero metrics after workflow execution."""

    client = roi_client

    run_response = await client.post(f"/api/v1/overlay/{PROJECT_ID}/run")
    assert run_response.status_code == 200

    list_response = await client.get(f"/api/v1/overlay/{PROJECT_ID}")
    assert list_response.status_code == 200
    suggestions = list_response.json()["items"]
    assert suggestions, "Overlay run should generate suggestions"

    first = suggestions[0]
    approve_payload = {
        "suggestion_id": first["id"],
        "decision": "approve",
        "decided_by": "Planner",
        "notes": "Meets conservation objectives.",
    }
    approve_response = await client.post(
        f"/api/v1/overlay/{PROJECT_ID}/decision",
        json=approve_payload,
    )
    assert approve_response.status_code == 200

    if len(suggestions) > 1:
        second = suggestions[1]
        reject_payload = {
            "suggestion_id": second["id"],
            "decision": "reject",
            "decided_by": "Planner",
            "notes": "Handled via separate mitigation programme.",
        }
        reject_response = await client.post(
            f"/api/v1/overlay/{PROJECT_ID}/decision",
            json=reject_payload,
        )
        assert reject_response.status_code == 200

    export_response = await client.post(
        f"/api/v1/export/{PROJECT_ID}",
        json={"format": "dxf", "include_source": True},
    )
    assert export_response.status_code == 200
    _ = export_response.content

    rerun_response = await client.post(f"/api/v1/overlay/{PROJECT_ID}/run")
    assert rerun_response.status_code == 200

    roi_response = await client.get(f"/api/v1/roi/{PROJECT_ID}")
    assert roi_response.status_code == 200
    metrics = roi_response.json()

    assert metrics["iterations"] >= 1
    assert metrics["automation_score"] > 0
    assert metrics["review_hours_saved"] > 0
    assert metrics["acceptance_rate"] > 0
    assert metrics["savings_percent"] > 0
    assert metrics["payback_weeks"] >= 1
    assert metrics["accepted_suggestions"] >= 1
