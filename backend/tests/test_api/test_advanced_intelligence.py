from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_graph_intelligence_returns_stub(client):
    response = await client.get(
        "/api/v1/analytics/intelligence/graph",
        params={"workspaceId": "ws-123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "graph"
    assert payload["status"] == "ok"
    assert payload["graph"]["nodes"]
    assert payload["generatedAt"].endswith("Z")


@pytest.mark.asyncio
async def test_predictive_intelligence_returns_segments(client):
    response = await client.get(
        "/api/v1/analytics/intelligence/predictive",
        params={"workspaceId": "ws-789"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "predictive"
    assert payload["horizonMonths"] == 6
    assert len(payload["segments"]) >= 1
    assert payload["segments"][0]["baseline"] > 0


@pytest.mark.asyncio
async def test_cross_correlation_intelligence_returns_relationships(client):
    response = await client.get(
        "/api/v1/analytics/intelligence/cross-correlation",
        params={"workspaceId": "ws-456"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "correlation"
    assert payload["relationships"]
    first = payload["relationships"][0]
    assert "driver" in first and "outcome" in first
