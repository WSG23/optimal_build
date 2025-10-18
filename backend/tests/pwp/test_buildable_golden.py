"""Golden tests for buildable screening responses."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.models.rkp import RefClause, RefDocument, RefRule, RefSource
from scripts.seed_screening import seed_screening_sample_data

DEFAULT_REQUEST_DEFAULTS = {
    "plot_ratio": 3.5,
    "site_area_m2": 1000.0,
    "site_coverage": 0.45,
    "floor_height_m": 4.0,
    "efficiency_factor": 0.82,
}
DEFAULT_REQUEST_OVERRIDES = {
    "typ_floor_to_floor_m": 4.0,
    "efficiency_ratio": 0.82,
}


async def _seed_reference_data(async_session_factory) -> dict[str, object]:
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
            text_span=(
                "Provide 1.5 parking spaces per unit and ensure maximum ramp "
                "slope is 1:12."
            ),
        )
        session.add(clause)
        await session.flush()

        rule = RefRule(
            source_id=source.id,
            document_id=document.id,
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            clause_ref=clause.clause_ref,
            parameter_key="parking.min_car_spaces_per_unit",
            operator=">=",
            value="1.5",
            unit="spaces_per_unit",
            applicability={"zone_code": "R2"},
            source_provenance={"seed_tag": "zoning", "pages": [7]},
            review_status="approved",
            is_published=True,
        )
        session.add(rule)

        await session.commit()

    return {
        "rule_parameter_key": rule.parameter_key,
        "provenance": {
            "rule_id": rule.id,
            "clause_ref": clause.clause_ref,
            "document_id": document.id,
            "pages": [7],
            "seed_tag": "zoning",
        },
    }


@pytest_asyncio.fixture
async def buildable_client(async_session_factory, monkeypatch, app_client: AsyncClient):
    context = await _seed_reference_data(async_session_factory)

    monkeypatch.setattr(settings, "BUILDABLE_TYP_FLOOR_TO_FLOOR_M", 4.0)
    monkeypatch.setattr(settings, "BUILDABLE_EFFICIENCY_RATIO", 0.82)

    return app_client, context


@pytest.mark.asyncio
async def test_buildable_golden_addresses(buildable_client):
    client, context = buildable_client

    test_cases = [
        (
            "123 Example Ave",
            {
                "zone_code": "R2",
                "overlays": {"heritage", "daylight"},
                "parcel_ref": "MK01-01234",
                "metrics": {
                    "gfa_cap_m2": 4375,
                    "floors_max": 8,
                    "footprint_m2": 563,
                    "nsa_est_m2": 3588,
                },
            },
        ),
        (
            "456 River Road",
            {
                "zone_code": "C1",
                "overlays": {"airport"},
                "parcel_ref": "MK02-00021",
                "metrics": {
                    "gfa_cap_m2": 3430,
                    "floors_max": 8,
                    "footprint_m2": 441,
                    "nsa_est_m2": 2813,
                },
            },
        ),
        (
            "789 Coastal Way",
            {
                "zone_code": "B1",
                "overlays": {"coastal"},
                "parcel_ref": "MK03-04567",
                "metrics": {
                    "gfa_cap_m2": 3920,
                    "floors_max": 8,
                    "footprint_m2": 504,
                    "nsa_est_m2": 3214,
                },
            },
        ),
    ]

    for address, expected in test_cases:
        payload = {
            "address": address,
            "defaults": dict(DEFAULT_REQUEST_DEFAULTS),
            **DEFAULT_REQUEST_OVERRIDES,
        }
        response = await client.post("/api/v1/screen/buildable", json=payload)
        assert response.status_code == 200
        body = response.json()

        assert body["input_kind"] == "address"
        assert body["zone_code"] == expected["zone_code"]
        assert set(body["overlays"]) == expected["overlays"]

        metrics = body["metrics"]
        for key, value in expected["metrics"].items():
            assert metrics[key] == value

        zone_source = body["zone_source"]
        assert zone_source["kind"] == "parcel"
        assert zone_source["parcel_ref"] == expected["parcel_ref"]
        assert zone_source["parcel_source"] == "sample_loader"
        assert zone_source["layer_name"] == "MasterPlan"
        assert zone_source["jurisdiction"] == "SG"

        rules = body["rules"]
        if expected["zone_code"] == "R2":
            assert rules, "Expected R2 buildable screening to include zoning rules"
            target_rule = next(
                (
                    item
                    for item in rules
                    if item["id"] == context["provenance"]["rule_id"]
                ),
                None,
            )
            assert (
                target_rule is not None
            ), "Expected seeded zoning rule to appear in response"
            assert target_rule["authority"] == "URA"
            assert target_rule["parameter_key"] == context["rule_parameter_key"]
            assert target_rule["provenance"] == context["provenance"]
        else:
            assert rules == []
