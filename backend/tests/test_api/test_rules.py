"""API tests for rules and buildable screening."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.main import app
from app.models.rkp import RefClause, RefDocument, RefRule, RefSource
from scripts.seed_screening import seed_screening_sample_data


async def _seed_reference_data(async_session_factory) -> None:
    async with async_session_factory() as session:
        await seed_screening_sample_data(session, commit=False)

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
    overlays = set(item["overlays"])
    assert {"heritage", "daylight"} <= overlays
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
    assert set(address_payload["overlays"]) == {"heritage", "daylight"}
    assert address_payload["input_kind"] == "address"
    metrics = address_payload["metrics"]
    assert metrics["gfa_cap_m2"] == 4375
    assert metrics["floors_max"] == 8
    assert metrics["footprint_m2"] == 563
    assert metrics["nsa_est_m2"] == 3588
    zone_source = address_payload["zone_source"]
    assert zone_source["kind"] == "parcel"
    assert zone_source["parcel_ref"] == "MK01-01234"
    assert zone_source["layer_name"] == "MasterPlan"
    rules = address_payload["rules"]
    assert rules, "Expected buildable screening to surface applicable rules"
    first_rule = rules[0]
    assert first_rule["parameter_key"] == "parking.min_car_spaces_per_unit"
    provenance = first_rule["provenance"]
    assert provenance["rule_id"] == first_rule["id"]
    assert provenance["clause_ref"] == "4.2.1"
    assert provenance["document_id"] is not None
    assert provenance["seed_tag"] == "zoning"

    geojson_response = await client.post(
        "/api/v1/screen/buildable",
        json={
            "geometry": {"type": "Feature", "properties": {"zone_code": "R2"}},
            "defaults": {"site_area_m2": 1250.0},
        },
    )
    assert geojson_response.status_code == 200
    geojson_payload = geojson_response.json()
    assert geojson_payload["zone_code"] == "R2"
    assert set(geojson_payload["overlays"]) == {"heritage", "daylight"}
    assert geojson_payload["input_kind"] == "geometry"
    assert geojson_payload["metrics"] == metrics
    assert geojson_payload["zone_source"]["kind"] == "geometry"
    assert geojson_payload["rules"] == rules

    for address, expected_zone, expected_overlays, parcel_ref in (
        ("456 River Road", "C1", {"airport"}, "MK02-00021"),
        ("789 Coastal Way", "B1", {"coastal"}, "MK03-04567"),
    ):
        response = await client.post(
            "/api/v1/screen/buildable",
            json={"address": address},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["zone_code"] == expected_zone
        assert set(payload["overlays"]) == expected_overlays
        assert payload["input_kind"] == "address"
        zone_source = payload["zone_source"]
        assert zone_source["kind"] == "parcel"
        assert zone_source["parcel_ref"] == parcel_ref


@pytest.mark.asyncio
async def test_rule_review_publish_action(client: AsyncClient, async_session_factory) -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(RefRule))
        rule = result.scalars().first()
        assert rule is not None
        rule_id = rule.id

    response = await client.post(
        f"/api/v1/rules/{rule_id}/review",
        json={"action": "publish", "reviewer": "Casey", "notes": "Ready"},
    )
    assert response.status_code == 200
    item = response.json()["item"]
    assert item["is_published"] is True
    assert item["review_notes"] == "Ready"

    # The review notes are exposed via the list endpoint without altering the canonical text.
    list_response = await client.get("/api/v1/rules")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["items"][0]["review_notes"] == "Ready"

    async with async_session_factory() as session:
        rule = await session.get(RefRule, rule_id)
        assert rule is not None
        assert (
            rule.notes
            == "Provide 1.5 parking spaces per unit; maximum ramp slope 1:12"
        )
        assert rule.review_notes == "Ready"


@pytest.mark.asyncio
async def test_buildable_screening_respects_efficiency_override(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/screen/buildable",
        json={"address": "123 Example Ave", "efficiency_ratio": 0.5},
    )
    assert response.status_code == 200
    payload = response.json()
    metrics = payload["metrics"]
    assert metrics["gfa_cap_m2"] == 4375
    assert metrics["nsa_est_m2"] == 2188
