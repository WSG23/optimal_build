"""Audit API integration tests."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

import pytest_asyncio
from app.core.geometry import GeometrySerializer
from app.core.models.geometry import GeometryGraph, Level, Relationship, Space
from app.models.overlay import OverlaySourceGeometry
from httpx import AsyncClient

PROJECT_ID = 5812


@pytest_asyncio.fixture
async def seeded_project(async_session_factory):
    """Seed source geometry required for overlay and export flows."""

    geometry = GeometryGraph(
        levels=[
            Level(
                id="level-01",
                name="Ground Floor",
                elevation=0.0,
                metadata={"site_area_sqm": 1024, "heritage_zone": False},
            )
        ],
        spaces=[
            Space(
                id="tower-a",
                name="Tower A",
                level_id="level-01",
                metadata={"height_m": 45},
            )
        ],
        relationships=[
            Relationship(
                rel_type="contains", source_id="level-01", target_id="tower-a"
            ),
        ],
    )
    serialized = GeometrySerializer.to_export(geometry)
    checksum = geometry.fingerprint()

    async with async_session_factory() as session:
        record = OverlaySourceGeometry(
            project_id=PROJECT_ID,
            source_geometry_key="site",
            graph=serialized,
            metadata={"seed": "audit-test"},
            checksum=checksum,
        )
        session.add(record)
        await session.commit()
    return PROJECT_ID


@pytest.mark.asyncio
async def test_audit_chain_and_diffs(
    app_client: AsyncClient,
    seeded_project: int,
) -> None:
    """Overlay, export and audit endpoints produce a verifiable ledger."""

    project_id = seeded_project

    run_response = await app_client.post(f"/api/v1/overlay/{project_id}/run")
    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["project_id"] == project_id

    list_response = await app_client.get(f"/api/v1/overlay/{project_id}")
    assert list_response.status_code == 200
    suggestions = list_response.json()["items"]
    assert suggestions

    decision_payload = {
        "suggestion_id": suggestions[0]["id"],
        "decision": "approve",
        "decided_by": "Auditor",
        "notes": "Initial approval for audit chain test.",
    }
    decision_response = await app_client.post(
        f"/api/v1/overlay/{project_id}/decision",
        json=decision_payload,
    )
    assert decision_response.status_code == 200

    export_response = await app_client.post(
        f"/api/v1/export/{project_id}",
        json={
            "format": "pdf",
            "include_source": True,
            "include_approved_overlays": True,
        },
    )
    assert export_response.status_code == 200
    await export_response.aread()

    audit_response = await app_client.get(f"/api/v1/audit/{project_id}")
    assert audit_response.status_code == 200
    audit_payload = audit_response.json()
    assert audit_payload["project_id"] == project_id
    assert audit_payload["valid"] is True
    assert audit_payload["count"] >= 3

    versions = [item["version"] for item in audit_payload["items"]]
    assert versions == sorted(versions)

    for index, entry in enumerate(audit_payload["items"]):
        assert entry["hash"]
        assert entry["signature"]
        if index == 0:
            assert entry["prev_hash"] in (None, "")
        else:
            assert entry["prev_hash"] == audit_payload["items"][index - 1]["hash"]

    diff_response = await app_client.get(
        f"/api/v1/audit/{project_id}/diff/{versions[0]}/{versions[-1]}"
    )
    assert diff_response.status_code == 200
    diff_payload = diff_response.json()
    assert diff_payload["project_id"] == project_id
    assert diff_payload["valid"] is True
    assert diff_payload["version_a"]["version"] == versions[0]
    assert diff_payload["version_b"]["version"] == versions[-1]

    context_diff = diff_payload["diff"]["context"]
    assert set(context_diff) == {"added", "removed", "changed"}
    assert context_diff["added"] or context_diff["removed"] or context_diff["changed"]

    missing_response = await app_client.get(f"/api/v1/audit/{project_id}/diff/999/1000")
    assert missing_response.status_code == 404
