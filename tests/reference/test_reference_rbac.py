"""RBAC regression tests for reference data endpoints."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

from httpx import AsyncClient


VIEWER_HEADERS = {"X-Role": "viewer"}


@pytest.mark.asyncio
async def test_ergonomics_requires_valid_role(app_client: AsyncClient) -> None:
    ok_response = await app_client.get(
        "/api/v1/ergonomics/",
        headers=VIEWER_HEADERS,
    )
    assert ok_response.status_code == 200

    forbidden_response = await app_client.get(
        "/api/v1/ergonomics/",
        headers={"X-Role": "guest"},
    )
    assert forbidden_response.status_code == 403


@pytest.mark.asyncio
async def test_cost_indices_require_valid_role(app_client: AsyncClient) -> None:
    params = {"series_name": "construction_all_in", "jurisdiction": "SG"}

    ok_response = await app_client.get(
        "/api/v1/costs/indices/latest",
        params=params,
        headers=VIEWER_HEADERS,
    )
    assert ok_response.status_code == 200

    forbidden_response = await app_client.get(
        "/api/v1/costs/indices/latest",
        params=params,
        headers={"X-Role": "guest"},
    )
    assert forbidden_response.status_code == 403
