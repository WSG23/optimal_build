"""Tests for cost API endpoints."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from app.models.rkp import RefCostIndex
from app.utils import metrics


@pytest.mark.asyncio
async def test_latest_cost_index(app_client, session):
    """Latest cost index endpoint returns the most recent period."""

    session.add_all(
        [
            RefCostIndex(
                jurisdiction="SG",
                series_name="concrete",
                category="material",
                subcategory="ready_mix",
                period="2023-Q4",
                value=1.10,
                unit="scalar",
                source="test",
                provider="official",
            ),
            RefCostIndex(
                jurisdiction="SG",
                series_name="concrete",
                category="material",
                subcategory="ready_mix",
                period="2023-Q3",
                value=1.05,
                unit="scalar",
                source="test",
                provider="official",
            ),
        ]
    )
    await session.commit()

    response = await app_client.get(
        "/api/v1/costs/indices/latest",
        params={"series_name": "concrete", "provider": "official"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["period"] == "2023-Q4"
    assert float(payload["value"]) == pytest.approx(1.10)

    count = metrics.counter_value(
        metrics.REQUEST_COUNTER, {"endpoint": "cost_index_latest"}
    )
    assert count == 1.0


@pytest.mark.asyncio
async def test_latest_cost_index_not_found(app_client):
    """A 404 is returned when the series is absent."""

    response = await app_client.get(
        "/api/v1/costs/indices/latest",
        params={"series_name": "missing"},
    )
    assert response.status_code == 404
