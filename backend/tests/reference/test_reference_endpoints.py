"""Integration tests for seeded reference data endpoints."""

import json
from collections.abc import Iterable
from typing import Any

import pytest
from backend.scripts import seed_nonreg


async def _seed_reference_data(async_session_factory) -> None:
    async with async_session_factory() as session:
        await seed_nonreg.seed_nonregulated_reference_data(session, commit=True)


async def test_ergonomics_endpoint_returns_seeded_metrics(
    async_session_factory, client
) -> None:
    await _seed_reference_data(async_session_factory)

    response = await client.get("/api/v1/ergonomics")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, list)

    expected = json.loads(seed_nonreg.ERGONOMICS_SEED.read_text(encoding="utf-8"))
    expected_pairs = {(item["metric_key"], item["population"]) for item in expected}
    observed_pairs = {(item["metric_key"], item["population"]) for item in payload}
    assert observed_pairs == expected_pairs


async def test_products_endpoint_handles_seeded_database(
    async_session_factory, client
) -> None:
    await _seed_reference_data(async_session_factory)

    response = await client.get("/api/v1/products")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, list)


async def test_standards_endpoint_includes_metadata(
    async_session_factory, client
) -> None:
    await _seed_reference_data(async_session_factory)

    response = await client.get("/api/v1/standards")
    assert response.status_code == 200

    records: Iterable[dict[str, Any]] = response.json()
    expected = json.loads(seed_nonreg.STANDARDS_SEED.read_text(encoding="utf-8"))
    assert len(records) == len(expected)

    for record in records:
        assert record.get("provenance") is not None
        assert record.get("license_ref")
        assert record.get("edition")


async def test_cost_indices_latest_endpoint_returns_seeded_index(
    async_session_factory, client
) -> None:
    await _seed_reference_data(async_session_factory)

    params = {"series_name": "construction_all_in", "jurisdiction": "SG"}
    response = await client.get("/api/v1/costs/indices/latest", params=params)
    assert response.status_code == 200

    record = response.json()
    expected = json.loads(seed_nonreg.COST_INDEX_SEED.read_text(encoding="utf-8"))[0]
    assert record["series_name"] == expected["series_name"]
    assert record["jurisdiction"] == expected.get("jurisdiction", "SG")
    assert record["value"] == pytest.approx(expected["value"], rel=1e-6)
    assert record["unit"] == expected["unit"]
