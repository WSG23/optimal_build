"""Golden test covering buildable screening sample data."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

from typing import Any, Dict

from httpx import AsyncClient

from app.core.config import settings
from app.core.database import get_session
from app.main import app
from app.models.rkp import RefDocument, RefRule, RefSource
from app.schemas.buildable import BuildableDefaults, BuildableRequest
from scripts.seed_screening import seed_screening_sample_data


_EXPECTED_RESPONSES: Dict[str, Dict[str, Any]] = {
    "123 Example Ave": {
        "zone_code": "R2",
        "overlays": ["heritage"],
        "metrics": {
            "gfa_cap_m2": 4375,
            "floors_max": 8,
            "footprint_m2": 563,
            "nsa_est_m2": 3588,
        },
        "parcel_ref": "MK01-01234",
    },
    "456 River Road": {
        "zone_code": "C1",
        "overlays": ["transport"],
        "metrics": {
            "gfa_cap_m2": 3430,
            "floors_max": 8,
            "footprint_m2": 441,
            "nsa_est_m2": 2813,
        },
        "parcel_ref": "MK02-00021",
    },
    "789 Innovation Drive": {
        "zone_code": "MX1",
        "overlays": ["innovation", "mixed_use"],
        "metrics": {
            "gfa_cap_m2": 6750,
            "floors_max": 10,
            "footprint_m2": 600,
            "nsa_est_m2": 5535,
        },
        "parcel_ref": "MK03-04567",
    },
}


async def _seed_reference_data(async_session_factory) -> Dict[str, Any]:
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

        rule = RefRule(
            source_id=source.id,
            document_id=document.id,
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            clause_ref="MP-4.2.1",
            parameter_key="planning.plot_ratio.max",
            operator="<=",
            value="4.5",
            unit="ratio",
            applicability={"zone_codes": ["R2", "C1", "MX1"]},
            source_provenance={"seed_tag": "screening-sample"},
        )
        session.add(rule)

        await session.commit()

    return {
        "document_id": document.id,
        "seed_tag": "screening-sample",
        "clause_ref": rule.clause_ref,
    }


@pytest.mark.asyncio
async def test_buildable_golden_sample(async_session_factory, monkeypatch) -> None:
    provenance_expectation = await _seed_reference_data(async_session_factory)

    monkeypatch.setattr(settings, "BUILDABLE_TYP_FLOOR_TO_FLOOR_M", 4.0, raising=False)
    monkeypatch.setattr(settings, "BUILDABLE_EFFICIENCY_RATIO", 0.82, raising=False)
    monkeypatch.setattr(
        BuildableDefaults.model_fields["floor_height_m"], "default", 4.0, raising=False
    )
    monkeypatch.setattr(
        BuildableDefaults.model_fields["efficiency_factor"], "default", 0.82, raising=False
    )
    monkeypatch.setattr(
        BuildableRequest.model_fields["typ_floor_to_floor_m"], "default", 4.0, raising=False
    )
    monkeypatch.setattr(
        BuildableRequest.model_fields["efficiency_ratio"], "default", 0.82, raising=False
    )

    async def _override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    try:
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            for address, expectation in _EXPECTED_RESPONSES.items():
                response = await client.post(
                    "/api/v1/screen/buildable",
                    json={"address": address},
                )
                assert response.status_code == 200, response.text
                payload = response.json()

                assert payload["input_kind"] == "address"
                assert payload["zone_code"] == expectation["zone_code"]
                assert payload["overlays"] == expectation["overlays"]

                metrics = payload["metrics"]
                assert metrics == expectation["metrics"]

                zone_source = payload["zone_source"]
                assert zone_source["kind"] == "parcel"
                assert zone_source["parcel_ref"] == expectation["parcel_ref"]

                rules = payload["rules"]
                assert rules, "Expected buildable screening to surface applicable rules"
                first_rule = rules[0]
                provenance = first_rule["provenance"]
                assert provenance["rule_id"] == first_rule["id"]
                assert provenance["document_id"] == provenance_expectation["document_id"]
                assert provenance["seed_tag"] == provenance_expectation["seed_tag"]
                assert provenance["clause_ref"] == provenance_expectation["clause_ref"]
    finally:
        app.dependency_overrides.pop(get_session, None)
