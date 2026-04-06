from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.advanced_intelligence import (
    WorkspaceCorrelationSnapshot,
    WorkspaceGraphSnapshot,
    WorkspacePredictiveSnapshot,
)
from app.services.intelligence import intelligence_service
from app.services.analytics import WorkspaceAnalyticsSnapshotService


@pytest.mark.asyncio
async def test_graph_intelligence_persists_empty_snapshot(client, db_session):
    response = await client.get(
        "/api/v1/analytics/intelligence/graph",
        params={"workspaceId": "ws-123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "graph"
    assert payload["status"] == "empty"
    assert "ws-123" in payload["summary"]

    snapshot = await db_session.scalar(
        select(WorkspaceGraphSnapshot).where(
            WorkspaceGraphSnapshot.workspace_id == "ws-123"
        )
    )
    assert snapshot is not None
    assert snapshot.status == "empty"
    assert snapshot.sample_size == 0
    assert snapshot.payload_json["kind"] == "graph"


@pytest.mark.asyncio
async def test_graph_intelligence_returns_persisted_snapshot(client, db_session):
    service = WorkspaceAnalyticsSnapshotService(db_session)
    await service.save_graph_snapshot(
        "ws-graph-ok",
        payload={
            "kind": "graph",
            "status": "ok",
            "summary": "Persisted relationship graph",
            "generatedAt": "2026-04-06T00:00:00Z",
            "graph": {
                "nodes": [
                    {
                        "id": "user-1",
                        "label": "Analyst",
                        "category": "team",
                        "score": 0.8,
                    }
                ],
                "edges": [
                    {
                        "id": "edge-1",
                        "source": "user-1",
                        "target": "workflow-1",
                        "weight": 0.4,
                    }
                ],
            },
        },
        sample_size=5,
    )

    response = await client.get(
        "/api/v1/analytics/intelligence/graph",
        params={"workspaceId": "ws-graph-ok"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["graph"]["nodes"][0]["label"] == "Analyst"


@pytest.mark.asyncio
async def test_predictive_intelligence_persists_empty_snapshot_without_query(
    client, db_session
):
    response = await client.get(
        "/api/v1/analytics/intelligence/predictive",
        params={"workspaceId": "ws-789"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "predictive"
    assert payload["status"] == "empty"
    assert "ws-789" in payload["summary"]

    snapshot = await db_session.scalar(
        select(WorkspacePredictiveSnapshot).where(
            WorkspacePredictiveSnapshot.workspace_id == "ws-789"
        )
    )
    assert snapshot is not None
    assert snapshot.status == "empty"
    assert snapshot.sample_size == 0


@pytest.mark.asyncio
async def test_predictive_intelligence_returns_persisted_snapshot(client, db_session):
    service = WorkspaceAnalyticsSnapshotService(db_session)
    await service.save_predictive_snapshot(
        "ws-predictive-ok",
        payload={
            "kind": "predictive",
            "status": "ok",
            "summary": "Persisted predictive snapshot",
            "generatedAt": "2026-04-06T00:00:00Z",
            "horizonMonths": 6,
            "segments": [
                {
                    "segmentId": "seg-1",
                    "segmentName": "High fit",
                    "baseline": 10,
                    "projection": 14,
                    "probability": 0.7,
                }
            ],
        },
        sample_size=8,
    )

    response = await client.get(
        "/api/v1/analytics/intelligence/predictive",
        params={"workspaceId": "ws-predictive-ok"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["segments"][0]["segmentName"] == "High fit"


@pytest.mark.asyncio
async def test_predictive_intelligence_query_path_still_returns_agent_payload(
    client, monkeypatch
):
    monkeypatch.setattr(
        intelligence_service,
        "query_agent",
        lambda query: f"Agent answer for {query}",
    )

    response = await client.get(
        "/api/v1/analytics/intelligence/predictive",
        params={"workspaceId": "ws-agent", "query": "status"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "predictive_agent"
    assert payload["status"] == "ok"
    assert payload["summary"] == "Agent answer for status"


@pytest.mark.asyncio
async def test_cross_correlation_intelligence_persists_empty_snapshot(
    client, db_session
):
    response = await client.get(
        "/api/v1/analytics/intelligence/cross-correlation",
        params={"workspaceId": "ws-456"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "correlation"
    assert payload["status"] == "empty"
    assert "ws-456" in payload["summary"]

    snapshot = await db_session.scalar(
        select(WorkspaceCorrelationSnapshot).where(
            WorkspaceCorrelationSnapshot.workspace_id == "ws-456"
        )
    )
    assert snapshot is not None
    assert snapshot.status == "empty"
    assert snapshot.sample_size == 0


@pytest.mark.asyncio
async def test_cross_correlation_intelligence_returns_persisted_snapshot(
    client, db_session
):
    service = WorkspaceAnalyticsSnapshotService(db_session)
    await service.save_correlation_snapshot(
        "ws-correlation-ok",
        payload={
            "kind": "correlation",
            "status": "ok",
            "summary": "Persisted cross-correlation snapshot",
            "updatedAt": "2026-04-06T00:00:00Z",
            "relationships": [
                {
                    "pairId": "finance_speed",
                    "driver": "Finance readiness",
                    "outcome": "Approval speed",
                    "coefficient": 0.62,
                    "pValue": 0.03,
                }
            ],
        },
        sample_size=12,
    )

    response = await client.get(
        "/api/v1/analytics/intelligence/cross-correlation",
        params={"workspaceId": "ws-correlation-ok"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["relationships"][0]["pairId"] == "finance_speed"
