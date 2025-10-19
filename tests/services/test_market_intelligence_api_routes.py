"""Integration checks for the market intelligence API router."""

from __future__ import annotations

import pytest
from app.models.property import PropertyType
from app.utils import metrics


@pytest.mark.asyncio
async def test_market_report_returns_seeded_payload(app_client, market_demo_data):
    metrics.reset_metrics()

    response = await app_client.get(
        "/api/v1/market-intelligence/report",
        params={
            "property_type": PropertyType.OFFICE.value,
            "location": "D01",
            "period_months": 12,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()["report"]

    assert payload["property_type"] == PropertyType.OFFICE.value
    assert payload["comparables_analysis"]["transaction_count"] >= 1
    assert payload["supply_dynamics"]["pipeline_projects"] >= 0
    assert payload["yield_benchmarks"]["current_metrics"]["cap_rate"][
        "median"
    ] == pytest.approx(0.046, rel=1e-3)

    metrics_text = metrics.render_latest_metrics().decode()
    assert "market_intelligence_cap_rate" in metrics_text
    assert "market_intelligence_rental_psf" in metrics_text
