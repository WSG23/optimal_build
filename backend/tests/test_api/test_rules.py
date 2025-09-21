"""API tests for rules and buildable screening."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.main import app
from app.models.rkp import (
    RefClause,
    RefDocument,
    RefGeocodeCache,
    RefParcel,
    RefRule,
    RefSource,
    RefZoningLayer,
)


async def _seed_reference_data(async_session_factory) -> None:
    async with async_session_factory() as session:
        source = RefSource(
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            doc_title="Urban Redevelopment Authority",
            landing_url="https://example.com/ura",
        )
        session.add(source)
        await session.flush()

        document = RefDocument(
            source_id=source.id,
            version_label="2024",
            storage_path="s3://docs/ura-2024.pdf",
            file_hash="abc123",
        )
        session.add(document)
        await session.flush()

        clause = RefClause(
            document_id=document.id,
            clause_ref="4.2.1",
            section_heading="Parking Provision",
            text_span="Provide 1.5 parking spaces per unit and ensure maximum ramp slope is 1:12.",
        )
        session.add(clause)

        rule = RefRule(
            source_id=source.id,
            document_id=document.id,
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            clause_ref="4.2.1",
            parameter_key="parking.min_car_spaces_per_unit",
            operator=">=",
            value="1.5",
            unit="spaces_per_unit",
            applicability={"zone_code": "R2"},
            notes="Provide 1.5 parking spaces per unit; maximum ramp slope 1:12",
        )
        session.add(rule)

        zoning = RefZoningLayer(
            jurisdiction="SG",
            layer_name="MasterPlan",
            zone_code="R2",
            attributes={
                "overlays": ["heritage"],
                "advisory_hints": ["Heritage impact assessment required."],
            },
        )
        session.add(zoning)

        parcel = RefParcel(
            jurisdiction="SG",
            parcel_ref="MK01-01234",
            bounds_json={"zone_code": "R2"},
        )
        session.add(parcel)
        await session.flush()

        geocode = RefGeocodeCache(address="123 Example Ave", parcel_id=parcel.id)
        session.add(geocode)

        await session.commit()


@pytest_asyncio.fixture
async def client(async_session_factory):
    await _seed_reference_data(async_session_factory)

    async def _override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rules_endpoint_includes_overlays_and_hints(client: AsyncClient) -> None:
    response = await client.get("/api/v1/rules")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    item = payload["items"][0]
    assert "heritage" in item["overlays"]
    assert any("parking" in hint.lower() for hint in item["advisory_hints"])
    assert any("slope" in hint.lower() for hint in item["advisory_hints"])


@pytest.mark.asyncio
async def test_buildable_screening_supports_address_and_geojson(
    client: AsyncClient,
) -> None:
    address_response = await client.post(
        "/api/v1/screen/buildable",
        json={"address": "123 Example Ave"},
    )
    assert address_response.status_code == 200
    address_payload = address_response.json()
    assert address_payload["zone_code"] == "R2"
    assert "heritage" in address_payload["overlays"]

    geojson_response = await client.post(
        "/api/v1/screen/buildable",
        json={"geometry": {"type": "Feature", "properties": {"zone_code": "R2"}}},
    )
    assert geojson_response.status_code == 200
    geojson_payload = geojson_response.json()
    assert geojson_payload["zone_code"] == "R2"
    assert geojson_payload["overlays"] == address_payload["overlays"]


@pytest.mark.asyncio
async def test_rule_review_publish_action(client: AsyncClient, async_session_factory) -> None:
    async with async_session_factory() as session:
        rule_id = (await session.execute(select(RefRule.id))).scalar_one()

    response = await client.post(
        f"/api/v1/rules/{rule_id}/review",
        json={"action": "publish", "reviewer": "Casey", "notes": "Ready"},
    )
    assert response.status_code == 200
    item = response.json()["item"]
    assert item["is_published"] is True
