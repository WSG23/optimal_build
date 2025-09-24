"""API tests for rules and buildable screening."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

import pytest_asyncio
from app.core.database import get_session
from app.main import app
from app.models.rkp import RefClause, RefDocument, RefRule, RefSource
from app.utils import metrics
from httpx import AsyncClient
from scripts.seed_screening import seed_screening_sample_data
from sqlalchemy import select


async def _seed_reference_data(async_session_factory) -> None:
    async with async_session_factory() as session:
        await seed_screening_sample_data(session, commit=False)

        source = (
            await session.execute(
                select(RefSource)
                .where(RefSource.jurisdiction == "SG")
                .where(RefSource.authority == "URA")
                .where(RefSource.topic == "zoning")
            )
        ).scalar_one()

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
        await session.flush()

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
            review_status="approved",
            is_published=True,
            source_provenance={
                "document_id": document.id,
                "clause_id": clause.id,
                "pages": [5],
            },
        )
        session.add(rule)

        pending_rule = RefRule(
            source_id=source.id,
            document_id=document.id,
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            clause_ref="4.2.2",
            parameter_key="parking.max_ramp_slope_ratio",
            operator="<=",
            value="1:10",
            unit="slope_ratio",
            applicability={"zone_code": "R2"},
            review_status="needs_review",
            source_provenance={
                "document_id": document.id,
                "clause_id": clause.id,
                "pages": [6],
            },
        )
        session.add(pending_rule)

        approved_without_provenance = RefRule(
            source_id=source.id,
            document_id=document.id,
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            clause_ref="4.2.3",
            parameter_key="parking.bicycle_spaces_per_unit",
            operator=">=",
            value="1",
            unit="spaces_per_unit",
            applicability={"zone_code": "R2"},
            review_status="approved",
            notes="Provide at least one bicycle space per unit.",
            source_provenance=None,
        )
        session.add(approved_without_provenance)

        await session.commit()


@pytest_asyncio.fixture
async def rules_app_client(async_session_factory):
    metrics.reset_metrics()
    await _seed_reference_data(async_session_factory)

    async def _override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"X-Role": "admin"},
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rules_endpoint_includes_overlays_and_hints(
    rules_app_client: AsyncClient,
) -> None:
    response = await rules_app_client.get("/api/v1/rules")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    item = next(
        rule
        for rule in payload["items"]
        if rule["parameter_key"] == "parking.min_car_spaces_per_unit"
    )
    overlays = set(item["overlays"])
    assert {"heritage", "daylight"} <= overlays
    assert any("parking" in hint.lower() for hint in item["advisory_hints"])
    assert any("slope" in hint.lower() for hint in item["advisory_hints"])
    assert item["clause_ref"] == "4.2.1"
    assert item["document_id"] is not None
    assert item["source_id"] is not None
    provenance = item["source_provenance"]
    assert provenance["document_id"] == item["document_id"]
    assert provenance["clause_id"] is not None
    assert provenance["pages"] == [5]


@pytest.mark.asyncio
async def test_rules_endpoint_filters_by_query_params(
    rules_app_client: AsyncClient,
) -> None:
    response = await rules_app_client.get(
        "/api/v1/rules",
        params={
            "jurisdiction": "SG",
            "authority": "URA",
            "topic": "zoning",
            "parameter_key": "parking.min_car_spaces_per_unit",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert all(
        item["parameter_key"] == "parking.min_car_spaces_per_unit"
        for item in payload["items"]
    )
    assert all(item["authority"] == "URA" for item in payload["items"])
    assert all(item["topic"] == "zoning" for item in payload["items"])
    assert all(item["jurisdiction"] == "SG" for item in payload["items"])
    assert all(item["review_status"] == "approved" for item in payload["items"])
    assert any(item["source_provenance"]["pages"] == [5] for item in payload["items"])

    # Non-approved rules are excluded even if filters would otherwise match.
    pending_response = await rules_app_client.get(
        "/api/v1/rules",
        params={"parameter_key": "parking.max_ramp_slope_ratio"},
    )
    assert pending_response.status_code == 200
    assert pending_response.json()["count"] == 0

    # Filters that do not match should return an empty result set.
    empty_response = await rules_app_client.get(
        "/api/v1/rules",
        params={"authority": "PUB"},
    )
    assert empty_response.status_code == 200
    assert empty_response.json()["count"] == 0


@pytest.mark.asyncio
async def test_rules_endpoint_supports_review_status_filter(
    rules_app_client: AsyncClient,
) -> None:
    default_response = await rules_app_client.get("/api/v1/rules")
    assert default_response.status_code == 200
    default_payload = default_response.json()
    assert default_payload["count"] >= 1
    assert {item["review_status"] for item in default_payload["items"]} == {"approved"}

    response = await rules_app_client.get(
        "/api/v1/rules",
        params={"review_status": "needs_review"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    statuses = {item["review_status"] for item in payload["items"]}
    assert statuses == {"needs_review"}
    assert any(
        item["parameter_key"] == "parking.max_ramp_slope_ratio"
        for item in payload["items"]
    )

    multi_status_response = await rules_app_client.get(
        "/api/v1/rules",
        params={"review_status": "approved,needs_review"},
    )
    assert multi_status_response.status_code == 200
    multi_payload = multi_status_response.json()
    multi_statuses = {item["review_status"] for item in multi_payload["items"]}
    assert multi_statuses >= {"needs_review", "approved"}


@pytest.mark.asyncio
async def test_rules_endpoint_populates_provenance_for_approved_rules(
    rules_app_client: AsyncClient,
) -> None:
    response = await rules_app_client.get("/api/v1/rules")
    assert response.status_code == 200
    payload = response.json()
    target = next(
        item
        for item in payload["items"]
        if item["parameter_key"] == "parking.bicycle_spaces_per_unit"
    )
    provenance = target["source_provenance"]
    assert provenance["document_id"] == target["document_id"]
    assert "clause_id" in provenance
    assert provenance["pages"] == []


@pytest.mark.asyncio
async def test_buildable_screening_supports_address_and_geojson(
    rules_app_client: AsyncClient,
) -> None:
    address_response = await rules_app_client.post(
        "/api/v1/screen/buildable",
        json={"address": "123 Example Ave"},
    )
    assert address_response.status_code == 200
    address_payload = address_response.json()
    assert metrics.counter_value(metrics.PWP_BUILDABLE_TOTAL, {}) == 1.0
    assert address_payload["zone_code"] == "R2"
    assert set(address_payload["overlays"]) == {"heritage", "daylight"}
    assert address_payload["input_kind"] == "address"
    metrics_payload = address_payload["metrics"]
    assert metrics_payload["gfa_cap_m2"] == 4375
    assert metrics_payload["floors_max"] == 8
    assert metrics_payload["footprint_m2"] == 563
    assert metrics_payload["nsa_est_m2"] == 3588
    zone_source = address_payload["zone_source"]
    assert zone_source["kind"] == "parcel"
    assert zone_source["parcel_ref"] == "MK01-01234"
    assert zone_source["layer_name"] == "MasterPlan"
    rules = address_payload["rules"]
    assert rules, "Expected buildable screening to surface applicable rules"
    first_rule = rules[0]
    assert first_rule["authority"] == "URA"
    assert first_rule["parameter_key"] == "parking.min_car_spaces_per_unit"
    provenance = first_rule["provenance"]
    assert provenance["rule_id"] == first_rule["id"]
    assert provenance["clause_ref"] == "4.2.1"
    assert provenance["document_id"] is not None
    assert provenance["pages"] == [5]
    assert provenance["seed_tag"] == "zoning"

    metrics_output = metrics.render_latest_metrics().decode()
    assert "pwp_buildable_duration_ms" in metrics_output

    geojson_response = await rules_app_client.post(
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
    assert geojson_payload["metrics"] == metrics_payload
    assert geojson_payload["zone_source"]["kind"] == "geometry"
    assert geojson_payload["rules"] == rules

    for address, expected_zone, expected_overlays, parcel_ref in (
        ("456 River Road", "C1", {"airport"}, "MK02-00021"),
        ("789 Coastal Way", "B1", {"coastal"}, "MK03-04567"),
    ):
        response = await rules_app_client.post(
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
async def test_rule_review_publish_action(
    rules_app_client: AsyncClient, async_session_factory
) -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(RefRule))
        rule = result.scalars().first()
        assert rule is not None
        rule_id = rule.id

    response = await rules_app_client.post(
        f"/api/v1/rules/{rule_id}/review",
        json={"action": "publish", "reviewer": "Casey", "notes": "Ready"},
    )
    assert response.status_code == 200
    item = response.json()["item"]
    assert item["is_published"] is True
    assert item["review_notes"] == "Ready"

    # The review notes are exposed via the list endpoint without altering the canonical text.
    list_response = await rules_app_client.get("/api/v1/rules")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["items"][0]["review_notes"] == "Ready"

    async with async_session_factory() as session:
        rule = await session.get(RefRule, rule_id)
        assert rule is not None
        assert (
            rule.notes == "Provide 1.5 parking spaces per unit; maximum ramp slope 1:12"
        )
        assert rule.review_notes == "Ready"


@pytest.mark.asyncio
async def test_buildable_screening_respects_efficiency_override(
    rules_app_client: AsyncClient,
) -> None:
    response = await rules_app_client.post(
        "/api/v1/screen/buildable",
        json={"address": "123 Example Ave", "efficiency_ratio": 0.5},
    )
    assert response.status_code == 200
    payload = response.json()
    metrics_payload = payload["metrics"]
    assert metrics_payload["gfa_cap_m2"] == 4375
    assert metrics_payload["nsa_est_m2"] == 2188
