"""Tests for finance API metrics instrumentation."""

from __future__ import annotations

from decimal import Decimal

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from httpx import AsyncClient

from app.models.rkp import RefCostIndex
from app.utils import metrics


@pytest.mark.asyncio
async def test_finance_metrics_surface_in_health(
    app_client: AsyncClient, session
) -> None:
    session.add_all(
        [
            RefCostIndex(
                jurisdiction="SG",
                series_name="construction_cost",
                category="cost",
                subcategory="escalation",
                period="2023-Q4",
                value=Decimal("100"),
                unit="index",
                source="seed",
                provider="official",
            ),
            RefCostIndex(
                jurisdiction="SG",
                series_name="construction_cost",
                category="cost",
                subcategory="escalation",
                period="2024-Q1",
                value=Decimal("110"),
                unit="index",
                source="seed",
                provider="official",
            ),
        ]
    )
    await session.commit()

    payload = {
        "project_id": 4242,
        "project_name": "Harbour Residences",
        "scenario": {
            "name": "Base Case",
            "description": "Primary underwriting scenario",
            "currency": "SGD",
            "is_primary": True,
            "cost_escalation": {
                "amount": "1000000",
                "base_period": "2023-Q4",
                "series_name": "construction_cost",
                "jurisdiction": "SG",
                "provider": "official",
            },
            "cash_flow": {
                "discount_rate": "0.05",
                "cash_flows": ["-1000000", "350000", "400000", "450000"],
            },
        },
    }

    response = await app_client.post("/api/v1/finance/feasibility", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert metrics.counter_value(metrics.FINANCE_FEASIBILITY_TOTAL, {}) == 1.0
    metrics_output = metrics.render_latest_metrics().decode()
    assert "finance_feasibility_duration_ms" in metrics_output

    scenario_id = body["scenario_id"]

    export_response = await app_client.get(
        "/api/v1/finance/export",
        params={"scenario_id": scenario_id},
    )
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/csv")
    assert metrics.counter_value(metrics.FINANCE_EXPORT_TOTAL, {}) == 1.0

    metrics_output = metrics.render_latest_metrics().decode()
    assert "finance_export_duration_ms" in metrics_output

    health_response = await app_client.get("/health/metrics")
    assert health_response.status_code == 200
    metrics_text = health_response.read().decode()
    assert "finance_feasibility_total" in metrics_text
    assert "finance_export_total" in metrics_text
