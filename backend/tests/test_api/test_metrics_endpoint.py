from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_payload(client):
    # Trigger at least one request so counters are non-zero
    await client.get("/docs")

    response = await client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "api_requests_total" in body
