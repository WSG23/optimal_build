from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_market_intelligence_health_endpoint(client):
    response = await client.get("/api/v1/market-intelligence/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ready", "degraded"}
    assert "dependencies" in payload
    assert "numpy" in payload["dependencies"]


@pytest.mark.asyncio
async def test_agents_health_endpoint(client):
    response = await client.get("/api/v1/agents/commercial-property/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ready", "degraded"}
    assert "dependencies" in payload
    assert "optional_features" in payload
