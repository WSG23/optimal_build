from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_graph_intelligence_returns_empty_state(client):
    response = await client.get(
        "/api/v1/analytics/intelligence/graph",
        params={"workspaceId": "ws-123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "graph"
    assert payload["status"] == "empty"
    assert "available" in payload["summary"]


@pytest.mark.asyncio
async def test_predictive_intelligence_returns_empty_state_without_query(client):
    response = await client.get(
        "/api/v1/analytics/intelligence/predictive",
        params={"workspaceId": "ws-789"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "predictive"
    assert payload["status"] == "empty"
    assert "available" in payload["summary"]


@pytest.mark.asyncio
async def test_cross_correlation_intelligence_returns_empty_state(client):
    response = await client.get(
        "/api/v1/analytics/intelligence/cross-correlation",
        params={"workspaceId": "ws-456"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "correlation"
    assert payload["status"] == "empty"
    assert "available" in payload["summary"]
