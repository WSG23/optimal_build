"""Smoke tests for non-regulatory reference API endpoints."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from backend.scripts import seed_nonreg
from app.models.rkp import RefProduct


@pytest.mark.asyncio
async def test_nonreg_reference_endpoints_expose_provenance(
    app_client, async_session_factory
) -> None:
    """Endpoints should return seeded data with provenance metadata."""

    async with async_session_factory() as session:
        await seed_nonreg.seed_nonregulated_reference_data(session, commit=True)
        session.add(
            RefProduct(
                vendor="Acme Fixtures",
                category="bathroom",
                product_code="ACME-SINK-001",
                name="Acme Universal Sink",
                brand="Acme",
                specifications={"provenance": {"catalog": "2024"}},
                spec_uri="https://example.com/specs/acme-sink",
                bim_uri="https://example.com/bim/acme-sink.ifc",
            )
        )
        await session.commit()

    ergonomics_response = await app_client.get("/api/v1/ergonomics")
    assert ergonomics_response.status_code == 200
    ergonomics_payload = ergonomics_response.json()
    assert len(ergonomics_payload) >= 1
    assert any(entry.get("source") for entry in ergonomics_payload)

    products_response = await app_client.get("/api/v1/products", params={"category": "bathroom"})
    assert products_response.status_code == 200
    products_payload = products_response.json()
    assert len(products_payload) == 1
    product = products_payload[0]
    assert product["vendor"] == "Acme Fixtures"
    assert product["specifications"].get("provenance") == {"catalog": "2024"}

    standards_response = await app_client.get("/api/v1/standards")
    assert standards_response.status_code == 200
    standards_payload = standards_response.json()
    assert len(standards_payload) >= 1
    assert any(entry.get("provenance") for entry in standards_payload)

    cost_response = await app_client.get(
        "/api/v1/costs/indices/latest",
        params={"series_name": "construction_all_in", "provider": "Public"},
    )
    assert cost_response.status_code == 200
    cost_payload = cost_response.json()
    assert cost_payload.get("source") == "seed"
    assert cost_payload.get("methodology") == "seed"
