from __future__ import annotations

import pytest

from app.api.v1 import agents as agents_api


@pytest.mark.asyncio
async def test_calculate_financial_metrics_endpoint(client):
    payload = {
        "property_value": 5_000_000,
        "gross_rental_income": 600_000,
        "operating_expenses": 200_000,
        "loan_amount": 2_500_000,
        "annual_debt_service": 180_000,
        "initial_cash_investment": 1_200_000,
        "vacancy_rate": 0.05,
        "other_income": 50_000,
    }

    response = await client.post(
        "/api/v1/agents/commercial-property/financial/metrics",
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "SGD"
    assert body["noi"] > 0
    assert body["cap_rate"] is not None
    assert body["dscr"] is not None


@pytest.mark.asyncio
async def test_calculate_financial_metrics_handles_errors(client, monkeypatch):
    def boom(**kwargs):  # noqa: W0613
        raise ValueError("bad input")

    monkeypatch.setattr(agents_api, "calculate_comprehensive_metrics", boom)

    response = await client.post(
        "/api/v1/agents/commercial-property/financial/metrics",
        json={
            "property_value": 1,
            "gross_rental_income": 1,
            "operating_expenses": 1,
            "vacancy_rate": 0,
            "other_income": 0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "bad input"


@pytest.mark.asyncio
async def test_value_property_endpoint(client):
    payload = {
        "noi": 420_000,
        "market_cap_rate": 0.05,
        "comparable_psf": 2_500,
        "property_size_sqf": 100_000,
        "replacement_cost_psf": 3_000,
        "land_value": 1_000_000,
        "depreciation_factor": 0.9,
    }

    response = await client.post(
        "/api/v1/agents/commercial-property/financial/valuation",
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["income_approach_value"] > 0
    assert body["recommended_value"] > 0
    assert body["currency"] == "SGD"
