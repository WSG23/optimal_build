from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from backend._compat.datetime import utcnow

from app.api.v1 import developers_gps as developers_api
from app.models.finance import FinCapitalStack, FinProject, FinScenario
from app.models.preview import PreviewJob
from app.models.projects import Project
from app.models.property import Property, PropertyStatus, PropertyType
from app.models.rkp import RefBuildingFootprint, RefParcel, RefRule, RefZoningLayer
from app.schemas.external_sources import ExternalSourceMetadata, ExternalSourceState
from app.services.agents.gps_property_logger import PropertyLogResult
from app.services.geocoding import Address, GeocodeLookupResult
from app.services.rules.zone_rules import SiteDevelopmentResult
from httpx import AsyncClient
from sqlalchemy import select

# Skip marker removed - market_demo_data fixture now properly cleans up test data


class _StubDeveloperLogger:
    def __init__(self, payload: PropertyLogResult) -> None:
        self._payload = payload
        self.calls: list[dict[str, Any]] = []

    async def log_property_from_gps(self, **kwargs: Any) -> PropertyLogResult:
        self.calls.append(kwargs)
        return self._payload


class _FakeOfficialSourceIngestionResult:
    resolved_count = 0

    def as_rule_corpus_payload(self) -> dict[str, Any]:
        return {
            "jurisdiction": "SG",
            "zone_code": "SG:commercial",
            "staged_count": 2,
            "resolved_count": 0,
            "existing_count": 1,
            "failed_count": 0,
            "candidates": [
                {
                    "field": "setbacks",
                    "authority": "URA",
                    "title": "Development Control Guidelines - setback controls",
                    "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
                    "status": "staged",
                    "rule_id": 101,
                    "message": None,
                }
            ],
        }


class _FakeOfficialSourceIngestionService:
    calls: list[dict[str, Any]] = []

    async def ingest_source_gaps(self, session, **kwargs: Any):
        self.calls.append(kwargs)
        return _FakeOfficialSourceIngestionResult()


class _ResolvingHeightLimitIngestionResult:
    resolved_count = 1

    def as_rule_corpus_payload(self) -> dict[str, Any]:
        return {
            "jurisdiction": "SG",
            "zone_code": "SG:commercial",
            "staged_count": 0,
            "resolved_count": 1,
            "existing_count": 0,
            "failed_count": 0,
            "candidates": [
                {
                    "field": "building_height_limit_m",
                    "authority": "URA",
                    "title": "Development Control Guidelines and control plans",
                    "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
                    "status": "resolved",
                    "rule_id": 202,
                    "message": "normalized height-limit rule approved from machine-readable source",
                }
            ],
        }


class _ResolvingHeightLimitIngestionService:
    calls: list[dict[str, Any]] = []

    async def ingest_source_gaps(self, session, **kwargs: Any):
        self.calls.append(kwargs)
        session.add(
            RefRule(
                jurisdiction="SG",
                authority="URA",
                topic="zoning",
                parameter_key="zoning.max_building_height_m",
                operator="<=",
                value="80",
                unit="m",
                applicability={"zone_code": kwargs["zone_code"]},
                source_provenance={
                    "ingestion_stage": "official_source_normalized",
                    "field": "building_height_limit_m",
                },
                review_status="approved",
                is_published=True,
            )
        )
        await session.flush()
        return _ResolvingHeightLimitIngestionResult()


@pytest.mark.asyncio
async def test_current_use_evidence_is_inferred_from_selected_place_metadata() -> None:
    request = developers_api.DeveloperGPSLogRequest.model_validate(
        {
            "latitude": 1.3008041,
            "longitude": 103.7881032,
            "placeName": "lyf one-north Singapore",
            "placeTypes": ["lodging", "point_of_interest"],
        }
    )

    evidence = await developers_api._resolve_current_use_evidence(
        request,
        existing_use="Unknown",
        ura_source=ExternalSourceMetadata(
            provider="ura",
            state=ExternalSourceState.LIVE,
            configured=True,
            synthetic=False,
        ),
    )

    assert evidence == [
        {
            "use": "Hotel / lodging",
            "source": "google_places_autocomplete",
            "confidence": "medium",
            "basis": "Selected place is tagged as lodging.",
            "place_name": "lyf one-north Singapore",
            "place_types": ["lodging", "point_of_interest"],
        }
    ]


def _build_stub_payload(property_id: UUID) -> PropertyLogResult:
    address = Address(
        full_address="1 Developer Way",
        street_name="Developer Way",
        building_name="Developer Hub",
        block_number="10",
        postal_code="049999",
        district="D01",
    )
    quick_analysis = {
        "generated_at": utcnow().isoformat(),
        "scenarios": [
            {
                "scenario": "raw_land",
                "headline": "Raw land redevelopment opportunity",
                "metrics": {"max_gfa": 18000, "nia_ratio": 0.82},
                "notes": ["Favourable CBD absorption outlook."],
            },
            {
                "scenario": "existing_building",
                "headline": "Review existing asset performance",
                "metrics": {"vacancy_rate": 0.18, "average_monthly_rent": 88},
                "notes": ["Elevated vacancy suggests repositioning requirement."],
            },
            {
                "scenario": "underused_asset",
                "headline": "Underutilised asset context",
                "metrics": {"nearby_mrt_count": 0},
                "notes": ["Limited transit access — plan for shuttle."],
            },
            {
                "scenario": "heritage_property",
                "headline": "Heritage sensitivity",
                "metrics": {"heritage_risk": "high"},
                "notes": ["Facade conservation required."],
            },
        ],
    }
    return PropertyLogResult(
        property_id=property_id,
        address=address,
        coordinates=(1.2801, 103.8198),
        ura_zoning={
            "zone_code": "C1",
            "zone_description": "Commercial",
            "plot_ratio": 4.0,
        },
        existing_use="commercial",
        property_info={
            "site_area_sqm": 4500,
            "gfa_approved": 12500,
            "is_conservation": True,
            "conservation_status": "National Monument",
            "heritage_overlay": "Telok Ayer Conservation",
            "heritage_constraints": [
                "Telok Ayer conservation area – facade retention mandatory.",
                "Consult URA Conservation Department prior to structural works.",
            ],
        },
        nearby_amenities={
            "mrt_stations": [],
            "bus_stops": [],
            "schools": [],
            "shopping_malls": [],
            "parks": [],
        },
        quick_analysis=quick_analysis,
        timestamp=utcnow(),
        heritage_overlay={
            "name": "Telok Ayer Conservation",
            "risk": "high",
            "notes": [
                "Telok Ayer conservation area – facade retention mandatory.",
                "Consult URA Conservation Department prior to structural works.",
            ],
            "heritage_premium_pct": 5.0,
            "source": "URA",
        },
        geocoding_source=ExternalSourceMetadata(
            provider="google_maps",
            state=ExternalSourceState.LIVE,
            configured=True,
            synthetic=False,
        ),
        amenities_source=ExternalSourceMetadata(
            provider="onemap",
            state=ExternalSourceState.LIVE,
            configured=True,
            synthetic=False,
        ),
        ura_source=ExternalSourceMetadata(
            provider="ura",
            state=ExternalSourceState.MOCK,
            configured=False,
            synthetic=True,
            reason="URA_ACCESS_KEY not configured",
        ),
    )


def _sg_zoning_layer(
    *,
    zone_code: str = "SG:commercial",
    lu_desc: str = "Commercial",
    gpr: str = "4.0",
    height_m: str | None = None,
    lat_min: float = 1.27,
    lat_max: float = 1.30,
    lon_min: float = 103.80,
    lon_max: float = 103.84,
) -> RefZoningLayer:
    attributes: dict[str, Any] = {"LU_DESC": lu_desc, "GPR": gpr}
    if height_m is not None:
        attributes["height_m"] = height_m
    return RefZoningLayer(
        jurisdiction="SG",
        layer_name="MasterPlanImported",
        zone_code=zone_code,
        bounds_json={
            "type": "Polygon",
            "coordinates": [
                [
                    [lon_min, lat_min],
                    [lon_max, lat_min],
                    [lon_max, lat_max],
                    [lon_min, lat_max],
                    [lon_min, lat_min],
                ]
            ],
        },
        attributes=attributes,
    )


def _sg_parcel(
    *,
    parcel_ref: str = "SG:LOT:MK01-00001",
    area_m2: float = 5000.0,
    lat_min: float = 1.27,
    lat_max: float = 1.30,
    lon_min: float = 103.80,
    lon_max: float = 103.84,
) -> RefParcel:
    return RefParcel(
        jurisdiction="SG",
        parcel_ref=parcel_ref,
        bounds_json={
            "type": "Polygon",
            "coordinates": [
                [
                    [lon_min, lat_min],
                    [lon_max, lat_min],
                    [lon_max, lat_max],
                    [lon_min, lat_max],
                    [lon_min, lat_min],
                ]
            ],
        },
        centroid_lat=(lat_min + lat_max) / 2,
        centroid_lon=(lon_min + lon_max) / 2,
        area_m2=area_m2,
        source="sla_onemap",
    )


def test_zone_use_groups_maps_hotel_zoning_to_hotel_program() -> None:
    assert developers_api._zone_use_groups("SG:hotel", "Hotel") == [
        "Hotel",
        "Retail",
    ]


def test_zone_use_groups_maps_business_park_white_to_business_park_program() -> None:
    assert developers_api._zone_use_groups(
        "SG:business_park_white",
        "Business Park - White",
    ) == ["Business park", "Office-lab"]


def test_zone_use_groups_keeps_transport_facilities_out_of_standard_programs() -> None:
    assert (
        developers_api._zone_use_groups(
            "SG:transport_facilities",
            "Transport Facilities",
        )
        == []
    )


def test_zone_use_groups_keeps_road_out_of_standard_programs() -> None:
    assert developers_api._zone_use_groups("SG:road", None) == []


def test_build_response_zoning_payload_marks_non_developable_controls() -> None:
    payload = developers_api._build_response_zoning_payload(
        {},
        developers_api.DeveloperBuildEnvelope(
            zone_code="SG:road",
            zone_description="Road",
            rule_corpus_status={
                "zoning_lookup_source": {
                    "kind": "point_zoning_layer",
                },
            },
        ),
    )

    assert payload["source"] == "ref_zoning_layer"
    assert payload["use_groups"] == []
    assert payload["special_conditions"] == "non_standard_or_non_developable_control"
    assert payload["development_control_status"] == "non_standard_or_non_developable"


def test_extract_heritage_context_does_not_flag_default_low_risk() -> None:
    envelope = developers_api.DeveloperBuildEnvelope(
        zone_code="B1",
        zone_description="Business 1",
        plot_ratio=2.5,
        assumptions=["No pollutive uses allowed"],
    )

    context = developers_api._extract_heritage_context(
        envelope=envelope,
        property_info={"site_area_sqm": 12000, "gfa_approved": 30000},
        quick_analysis={"scenarios": []},
        heritage_overlay=None,
    )

    assert context["flag"] is False
    assert context["risk"] == "low"
    assert context["constraints"] == []
    assert context["assumption"] is None
    assert context["overlay"] is None


def test_extract_heritage_context_ignores_low_risk_quick_scenario() -> None:
    envelope = developers_api.DeveloperBuildEnvelope(
        zone_code="B1",
        zone_description="Business 1",
        plot_ratio=2.5,
    )

    context = developers_api._extract_heritage_context(
        envelope=envelope,
        property_info={},
        quick_analysis={
            "scenarios": [
                {
                    "scenario": "heritage_property",
                    "metrics": {
                        "heritage_risk": "low",
                        "heritage_signal": False,
                    },
                    "notes": [
                        "2 planned projects nearby may influence planning context"
                    ],
                }
            ]
        },
        heritage_overlay=None,
    )

    assert context["flag"] is False
    assert context["risk"] == "low"
    assert context["constraints"] == []


def test_extract_heritage_context_flags_explicit_overlay() -> None:
    envelope = developers_api.DeveloperBuildEnvelope(
        zone_code="C1",
        zone_description="Commercial",
        plot_ratio=4.0,
    )

    context = developers_api._extract_heritage_context(
        envelope=envelope,
        property_info={},
        quick_analysis={"scenarios": []},
        heritage_overlay={
            "name": "Telok Ayer Conservation",
            "risk": "high",
            "notes": ["Facade retention required."],
            "source": "URA",
        },
    )

    assert context["flag"] is True
    assert context["risk"] == "high"
    assert context["overlay"]["name"] == "Telok Ayer Conservation"
    assert "Overlay: Telok Ayer Conservation" in context["constraints"]


@pytest.mark.asyncio
async def test_developer_log_property_returns_envelope(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(
        developers_api,
        "developer_gps_logger",
        stub_logger,
    )
    async with async_session_factory() as session:
        rule_defaults = {
            "jurisdiction": "SG",
            "authority": "URA",
            "topic": "zoning",
            "operator": "<=",
            "applicability": {"zone_code": "SG:commercial"},
            "review_status": "approved",
            "is_published": True,
        }
        session.add_all(
            [
                _sg_zoning_layer(),
                RefRule(
                    parameter_key="zoning.setback.front_min_m",
                    value="6",
                    unit="m",
                    **rule_defaults,
                ),
                RefRule(
                    parameter_key="zoning.setback.rear_min_m",
                    value="4",
                    unit="m",
                    **rule_defaults,
                ),
                RefRule(
                    parameter_key="zoning.setback.side_min_m",
                    value="3",
                    unit="m",
                    **rule_defaults,
                ),
                RefRule(
                    parameter_key="zoning.stepback.level_8_depth_m",
                    value="5",
                    unit="m",
                    applicability={"zone_code": "SG:commercial", "level": 8},
                    **{
                        key: value
                        for key, value in rule_defaults.items()
                        if key != "applicability"
                    },
                ),
                RefRule(
                    parameter_key="zoning.air_rights.note",
                    value="Subject to aviation height review.",
                    operator="=",
                    **{
                        key: value
                        for key, value in rule_defaults.items()
                        if key != "operator"
                    },
                ),
                RefRule(
                    parameter_key="zoning.site_coverage.max_percent",
                    value="50",
                    unit="%",
                    topic="building",
                    **{
                        key: value
                        for key, value in rule_defaults.items()
                        if key != "topic"
                    },
                ),
            ]
        )
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2801,
            "longitude": 103.8198,
            "development_scenarios": ["raw_land", "existing_building"],
            "currentGfaSqm": 12500,
            "currentGfaSource": "test approved plans",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["property_id"] == str(property_id)
    assert payload["existing_use"] == "commercial"
    assert payload["geocoding_source"]["state"] == "live"
    assert payload["amenities_source"]["provider"] == "onemap"
    assert payload["ura_source"]["state"] == "mock"
    assert payload["quick_analysis"]["scenarios"][0]["scenario"] == "raw_land"

    envelope = payload["build_envelope"]
    assert envelope["zone_code"] == "SG:commercial"
    assert envelope["allowable_plot_ratio"] == 4.0
    assert envelope["gross_plot_ratio"] == 4.0
    assert envelope["site_area_sqm"] == 4500.0
    assert envelope["max_buildable_gfa_sqm"] == 18000.0
    assert envelope["current_gfa_sqm"] == 12500.0
    assert envelope["additional_potential_gfa_sqm"] == pytest.approx(5500.0)
    assert envelope["setback_front_m"] == 6.0
    assert envelope["setback_rear_m"] == 4.0
    assert envelope["setback_side_m"] == 3.0
    assert envelope["step_backs"] == [{"level": 8.0, "depth_m": 5.0}]
    assert envelope["air_rights_note"] == "Subject to aviation height review."
    assert envelope["site_coverage_pct"] == 50.0
    assert envelope["assumptions"], "Assumptions should not be empty"
    assert envelope["source_reference"] == "SG Rule Registry (RefRule + zoning layers)"
    assert envelope["rule_corpus_status"]["zone_code"] == "SG:commercial"
    assert envelope["rule_corpus_status"]["resolved_by"]["land_use"] == (
        "ref_zoning_layer"
    )
    assert envelope["rule_corpus_status"]["resolved_by"]["plot_ratio"] == (
        "ref_zoning_layer"
    )
    assert envelope["rule_corpus_status"]["resolved_by"]["site_coverage_pct"] == (
        "ref_rule"
    )
    assert "plot_ratio" not in envelope["rule_corpus_status"]["unresolved_fields"]
    assert (
        "site_coverage_pct" not in envelope["rule_corpus_status"]["unresolved_fields"]
    )
    source_gap_fields = {
        gap["field"] for gap in envelope["rule_corpus_status"]["official_source_gaps"]
    }
    assert {"land_use", "plot_ratio", "site_coverage_pct"}.isdisjoint(source_gap_fields)
    assert "building_height_limit_m" in source_gap_fields
    assert "official_source_ingestion" not in envelope["rule_corpus_status"]
    assert envelope["rule_corpus_status"]["coverage_state"] in {
        "approved",
        "missing",
        "partial",
        "review_pending",
    }

    visualization = payload["visualization"]
    assert visualization["status"] in {"queued", "ready", "placeholder"}
    assert visualization["preview_available"] is (visualization["status"] == "ready")
    if visualization["status"] == "ready":
        assert visualization["concept_mesh_url"].endswith((".json", ".gltf", ".glb"))
    else:
        assert visualization["concept_mesh_url"] is None
    assert visualization["preview_job_id"]
    assert visualization["massing_layers"], "Massing layers should be included"
    assert visualization["color_legend"], "Colour legend should be populated"
    assert visualization["massing_layers"], "Massing layers should be included"
    assert visualization["color_legend"], "Colour legend should be populated"
    assert visualization["massing_layers"][0][
        "color"
    ], "Top massing layer should include colour token"

    optimizations = payload["optimizations"]
    assert optimizations, "Expected asset optimisation recommendations"
    assert optimizations[0]["asset_type"] == "office"
    assert optimizations[0]["allocation_pct"] > 0
    assert optimizations[0]["allocated_gfa_sqm"] is not None
    assert optimizations[0]["target_floor_height_m"] is not None
    assert optimizations[0]["rent_psm_month"] is not None
    assert optimizations[0]["stabilised_vacancy_pct"] is not None
    assert optimizations[0]["opex_pct_of_rent"] is not None
    assert optimizations[0]["estimated_revenue_sgd"] is not None
    assert optimizations[0]["absorption_months"] is not None
    assert optimizations[0]["fitout_cost_psm"] is not None
    assert any(
        "conservation" in note.lower() for opt in optimizations for note in opt["notes"]
    )

    financial_summary = payload["financial_summary"]
    assert financial_summary["total_estimated_revenue_sgd"] is not None
    assert financial_summary["total_estimated_capex_sgd"] is not None
    assert financial_summary["dominant_risk_profile"] == "elevated"
    blueprint = financial_summary.get("finance_blueprint")
    assert blueprint, "Finance blueprint should be included"
    assert blueprint[
        "capital_structure"
    ], "Capital structure scenarios should be populated"

    heritage_context = payload["heritage_context"]
    assert heritage_context["risk"] == "high"
    assert heritage_context["overlay"]["name"] == "Telok Ayer Conservation"
    assert any(
        "conservation area" in note.lower() for note in heritage_context["notes"]
    )

    preview_jobs = payload["preview_jobs"]
    assert preview_jobs and preview_jobs[0]["status"] in {
        "queued",
        "ready",
        "processing",
    }
    preview_job_id = preview_jobs[0]["id"]

    property_info = payload["property_info"]
    assert property_info["conservation_status"] == "National Monument"
    assert property_info["is_conservation"] is True
    assert property_info["heritage_overlay"] == "Telok Ayer Conservation"

    # Ensure the developer logger was invoked with development scenarios
    assert stub_logger.calls, "Expected capture service to be invoked"
    assert stub_logger.calls[0]["scenarios"] == [
        "raw_land",
        "existing_building",
    ]

    async with async_session_factory() as session:
        jobs = (await session.execute(select(PreviewJob))).scalars().all()
        assert jobs
        assert jobs[0].preview_url

    jobs_response = await app_client.get(
        f"/api/v1/developers/properties/{property_id}/preview-jobs"
    )
    assert jobs_response.status_code == 200
    jobs_payload = jobs_response.json()
    assert jobs_payload and jobs_payload[0]["id"] == preview_job_id

    job_response = await app_client.get(
        f"/api/v1/developers/preview-jobs/{preview_job_id}"
    )
    assert job_response.status_code == 200
    job_payload = job_response.json()
    assert job_payload["status"] in {"ready", "processing"}

    refresh_response = await app_client.post(
        f"/api/v1/developers/preview-jobs/{preview_job_id}/refresh"
    )
    assert refresh_response.status_code == 200
    refreshed_payload = refresh_response.json()
    assert refreshed_payload["status"] in {"ready", "processing"}


@pytest.mark.asyncio
async def test_developer_envelope_uses_reference_parcel_area_for_max_gfa(
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.property_info.pop("site_area_sqm", None)
    stub_payload.property_info.pop("gfa_approved", None)

    async with async_session_factory() as session:
        session.add_all(
            [
                _sg_zoning_layer(gpr="6.3"),
                _sg_parcel(
                    parcel_ref="SG:LOT:MK01-12345",
                    area_m2=4321.0,
                ),
            ]
        )
        await session.flush()

        envelope = await developers_api._derive_build_envelope(
            stub_payload,
            session,
            jurisdiction="SG",
        )

    assert envelope.site_area_sqm == pytest.approx(4321.0)
    assert envelope.allowable_plot_ratio == pytest.approx(6.3)
    assert envelope.max_buildable_gfa_sqm == pytest.approx(27222.3)
    assert envelope.current_gfa_sqm is None
    assert envelope.additional_potential_gfa_sqm is None
    assert envelope.rule_corpus_status is not None
    assert envelope.rule_corpus_status["resolved_by"]["site_area"] == "ref_parcel"
    assert (
        envelope.rule_corpus_status["site_area_lookup_source"]["parcel_ref"]
        == "SG:LOT:MK01-12345"
    )
    assert "site_area" not in envelope.rule_corpus_status["unresolved_fields"]
    assert any(
        "Site area resolved from imported parcel SG:LOT:MK01-12345." == assumption
        for assumption in envelope.assumptions
    )


@pytest.mark.asyncio
async def test_developer_log_property_prefers_point_zoning_layer_over_mock_ura(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.ura_zoning = {
        "zone_code": "C1",
        "zone_description": "Commercial",
        "plot_ratio": 12.0,
    }
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)

    async with async_session_factory() as session:
        session.add(
            _sg_zoning_layer(
                zone_code="SG:residential",
                lu_desc="Residential",
                gpr="2.8",
                height_m="36",
            )
        )
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2801,
            "longitude": 103.8198,
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    envelope = payload["build_envelope"]
    assert envelope["zone_code"] == "SG:residential"
    assert envelope["zone_description"] == "Residential"
    assert envelope["allowable_plot_ratio"] == 2.8
    assert envelope["building_height_limit_m"] == 36.0
    assert envelope["rule_corpus_status"]["zoning_lookup_source"] == {
        "kind": "point_zoning_layer",
        "layer_id": envelope["rule_corpus_status"]["applied_zoning_layer_id"],
        "layer_name": "MasterPlanImported",
        "zone_code": "SG:residential",
        "jurisdiction": "SG",
    }
    assert payload["ura_zoning"]["source"] == "ref_zoning_layer"
    assert payload["ura_zoning"]["zone_code"] == "SG:residential"
    assert payload["ura_zoning"]["use_groups"] == ["Residential", "Amenities"]
    optimizations = payload["optimizations"]
    assert optimizations[0]["asset_type"] == "residential"
    assert optimizations[0]["allocation_pct"] > 0
    assert optimizations[0]["allocated_gfa_sqm"] is not None


@pytest.mark.asyncio
async def test_developer_log_property_prefers_parcel_dominant_zoning_over_point_sliver(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.coordinates = (1.25, 103.805)
    stub_payload.property_info.pop("site_area_sqm", None)
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)

    async with async_session_factory() as session:
        session.add_all(
            [
                _sg_parcel(
                    parcel_ref="SG:LOT:MK01-DOMINANT",
                    area_m2=10_000,
                    lat_min=1.20,
                    lat_max=1.30,
                    lon_min=103.80,
                    lon_max=103.90,
                ),
                _sg_zoning_layer(
                    zone_code="SG:road",
                    lu_desc="Road",
                    gpr="NA",
                    lat_min=1.20,
                    lat_max=1.30,
                    lon_min=103.80,
                    lon_max=103.815,
                ),
                _sg_zoning_layer(
                    zone_code="SG:commercial",
                    lu_desc="Commercial",
                    gpr="4.0",
                    lat_min=1.20,
                    lat_max=1.30,
                    lon_min=103.815,
                    lon_max=103.90,
                ),
            ]
        )
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.25,
            "longitude": 103.805,
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    envelope = payload["build_envelope"]
    assert envelope["zone_code"] == "SG:commercial"
    assert envelope["allowable_plot_ratio"] == 4.0
    assert envelope["max_buildable_gfa_sqm"] == 40_000.0
    assert envelope["rule_corpus_status"]["zoning_lookup_source"] == {
        "kind": "parcel_dominant_zoning",
        "layer_id": envelope["rule_corpus_status"]["applied_zoning_layer_id"],
        "layer_name": "MasterPlanImported",
        "zone_code": "SG:commercial",
        "jurisdiction": "SG",
        "parcel_id": envelope["rule_corpus_status"]["site_area_lookup_source"][
            "parcel_id"
        ],
        "parcel_ref": "SG:LOT:MK01-DOMINANT",
        "parcel_lookup_source": "ref_parcel",
        "overlap_area": 0.01,
        "overlap_ratio": 0.85,
    }
    assert any(
        "dominant imported zoning layer across the matched parcel" in assumption
        for assumption in envelope["assumptions"]
    )
    assert payload["ura_zoning"]["source"] == "ref_zoning_layer"
    assert payload["ura_zoning"]["zone_code"] == "SG:commercial"
    assert payload["ura_zoning"]["use_groups"] == ["Office", "Retail"]


@pytest.mark.asyncio
async def test_developer_log_property_uses_nearest_parcel_when_geocoder_point_is_off_parcel(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.coordinates = (1.2001, 103.80035)
    stub_payload.property_info.pop("site_area_sqm", None)
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)

    async with async_session_factory() as session:
        session.add_all(
            [
                _sg_parcel(
                    parcel_ref="SG:LOT:MK01-NEAREST",
                    area_m2=500,
                    lat_min=1.2000,
                    lat_max=1.2002,
                    lon_min=103.8000,
                    lon_max=103.8002,
                ),
                _sg_zoning_layer(
                    zone_code="SG:residential",
                    lu_desc="Residential",
                    gpr="2.1",
                    lat_min=1.1999,
                    lat_max=1.2003,
                    lon_min=103.7999,
                    lon_max=103.8003,
                ),
            ]
        )
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2001,
            "longitude": 103.80035,
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    envelope = payload["build_envelope"]
    assert envelope["zone_code"] == "SG:residential"
    assert envelope["site_area_sqm"] == 500.0
    assert envelope["max_buildable_gfa_sqm"] == 1050.0
    assert (
        envelope["rule_corpus_status"]["site_area_lookup_source"]["lookup_source"]
        == "nearest_ref_parcel"
    )
    assert (
        envelope["rule_corpus_status"]["zoning_lookup_source"]["parcel_lookup_source"]
        == "nearest_ref_parcel"
    )


@pytest.mark.asyncio
async def test_developer_log_property_surfaces_eva_and_address_asset_evidence(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.coordinates = (1.2797934, 103.8538274)
    stub_payload.address = Address(
        full_address="10 Marina Boulevard, Singapore 018983",
        street_name="Marina Boulevard",
        block_number="10",
        postal_code="018983",
        district="D01",
    )
    stub_payload.property_info.pop("site_area_sqm", None)
    stub_payload.property_info.pop("gfa_approved", None)
    stub_payload.ura_zoning = None
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)

    async with async_session_factory() as session:
        session.add_all(
            [
                _sg_parcel(
                    parcel_ref="SG:LOT:TS30-00289N",
                    area_m2=15_251.57,
                    lat_min=1.2789,
                    lat_max=1.2807,
                    lon_min=103.8533,
                    lon_max=103.8551,
                ),
                _sg_zoning_layer(
                    zone_code="SG:mixed_use",
                    lu_desc="White",
                    gpr="EVA",
                    lat_min=1.2789,
                    lat_max=1.2807,
                    lon_min=103.8533,
                    lon_max=103.8551,
                ),
                RefBuildingFootprint(
                    jurisdiction="SG",
                    layer_name="MasterPlanBuilding",
                    footprint_ref="SG:BUILDING:DISTANT",
                    bounds_json={
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [103.70, 1.10],
                                [103.701, 1.10],
                                [103.701, 1.101],
                                [103.70, 1.101],
                                [103.70, 1.10],
                            ]
                        ],
                    },
                    centroid_lat=1.1005,
                    centroid_lon=103.7005,
                    area_m2=900.0,
                    source="ura_data_gov",
                ),
            ]
        )
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2797934,
            "longitude": 103.8538274,
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    envelope = payload["build_envelope"]
    rule_status = envelope["rule_corpus_status"]
    assert envelope["zone_code"] == "SG:mixed_use"
    assert envelope["zone_description"] == "White"
    assert envelope["allowable_plot_ratio"] is None
    assert envelope["max_buildable_gfa_sqm"] is None
    assert rule_status["zoning_layer_intensity_control"]["status"] == (
        "envelope_control_area"
    )
    plot_ratio_gap = next(
        gap
        for gap in rule_status["official_source_gaps"]
        if gap["field"] == "plot_ratio"
    )
    assert plot_ratio_gap["reason"] == (
        "envelope_control_area_requires_site_specific_controls"
    )
    assert plot_ratio_gap["source_value"] == "EVA"
    assert rule_status["site_development_status"] == "developed"
    assert rule_status["site_development_lookup_source"] == {
        "kind": "capture_address_evidence",
        "status": "developed",
        "building_count": 0,
        "footprint_area_sqm": None,
        "reason": "resolved_building_address_without_footprint_coverage",
        "jurisdiction": "SG",
    }
    assert any(
        "Resolved address evidence indicates an existing asset" in assumption
        for assumption in envelope["assumptions"]
    )


def test_capture_address_evidence_does_not_promote_non_developable_zones() -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.address = Address(
        full_address="25 Soon Lee Rd, Singapore 628083",
        street_name="Soon Lee Rd",
        block_number="25",
        postal_code="628083",
        district="D22",
    )
    sparse_result = SiteDevelopmentResult(
        status="uncertain",
        source="ref_building_footprints",
        reason="building_footprint_coverage_sparse_near_parcel",
    )

    promoted = developers_api._promote_site_development_from_capture_address(
        sparse_result,
        stub_payload,
        zone_code="SG:road",
        zone_description="Road",
    )

    assert promoted is sparse_result
    assert promoted.status == "uncertain"


def test_capture_address_evidence_overrides_absent_footprint_signal() -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.address = Address(
        full_address="80 Nepal Pk, Singapore 139409",
        street_name="Nepal Park",
        block_number="80",
        postal_code="139409",
        district="D05",
    )
    vacant_result = SiteDevelopmentResult(
        status="vacant",
        source="ref_building_footprints",
        reason="no_footprint_intersects_parcel",
    )

    promoted = developers_api._promote_site_development_from_capture_address(
        vacant_result,
        stub_payload,
        zone_code="SG:residential",
        zone_description="Residential",
    )

    assert promoted.status == "developed"
    assert promoted.source == "capture_address_evidence"
    assert (
        promoted.reason == "resolved_building_address_overrides_absent_footprint_signal"
    )


@pytest.mark.asyncio
async def test_developer_log_property_rejects_stale_submitted_address(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.address = Address(
        full_address="20 Soon Lee Rd, Singapore 628086",
        street_name="Soon Lee Rd",
        block_number="20",
        postal_code="628086",
        district="D22",
    )
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    monkeypatch.setattr(
        developers_api,
        "_resolve_submitted_sg_address_lookup",
        AsyncMock(return_value=None),
    )

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.3286413,
            "longitude": 103.698443,
            "submittedAddress": "25 Soon Lee Rd, Singapore 628083",
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 409
    payload = response.json()
    assert (
        "Submitted address does not match the resolved map point" in payload["detail"]
    )
    assert "25 Soon Lee Rd" in payload["detail"]
    assert "20 Soon Lee Rd" in payload["detail"]


@pytest.mark.asyncio
async def test_developer_log_property_accepts_number_alias_without_submitted_postal(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.address = Address(
        full_address="20 Soon Lee Rd, Singapore 628086",
        street_name="Soon Lee Rd",
        block_number="20",
        postal_code="628086",
        district="D22",
    )
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    monkeypatch.setattr(
        developers_api,
        "_resolve_submitted_sg_address_lookup",
        AsyncMock(return_value=None),
    )

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.3282813,
            "longitude": 103.6984406,
            "submittedAddress": "25 Soon Lee Rd, Singapore",
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["address"]["full_address"] == "25 Soon Lee Rd, Singapore"
    assert payload["address"]["block_number"] == "25"
    assert payload["address"]["postal_code"] == "628086"


@pytest.mark.asyncio
async def test_developer_log_property_prefers_onemap_submitted_address_coordinates(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.address = Address(
        full_address="20 Soon Lee Rd, Singapore 628086",
        street_name="Soon Lee Rd",
        block_number="20",
        postal_code="628086",
        district="D22",
    )
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    lookup = GeocodeLookupResult(
        latitude=1.3282813,
        longitude=103.6984406,
        formatted_address="25 SOON LEE ROAD SINGAPORE 628083",
        address=Address(
            full_address="25 SOON LEE ROAD SINGAPORE 628083",
            street_name="SOON LEE ROAD",
            block_number="25",
            postal_code="628083",
            district="D22 - Boon Lay, Jurong, Tuas",
        ),
        source=ExternalSourceMetadata(
            provider="onemap_address_search",
            state=ExternalSourceState.LIVE,
            configured=True,
            synthetic=False,
        ),
    )
    monkeypatch.setattr(
        developers_api,
        "_resolve_submitted_sg_address_lookup",
        AsyncMock(return_value=lookup),
    )

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.0,
            "longitude": 103.0,
            "submittedAddress": "25 Soon Lee Rd, Singapore 628083",
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert stub_logger.calls[0]["latitude"] == pytest.approx(1.3282813)
    assert stub_logger.calls[0]["longitude"] == pytest.approx(103.6984406)
    assert stub_logger.calls[0]["resolved_address"].postal_code == "628083"
    assert (
        stub_logger.calls[0]["geocoding_source_override"].provider
        == "onemap_address_search"
    )
    assert payload["address"]["full_address"] == "25 Soon Lee Rd, Singapore 628083"
    assert payload["address"]["postal_code"] == "628083"
    assert payload["geocoding_source"]["provider"] == "onemap_address_search"


@pytest.mark.asyncio
async def test_developer_log_property_accepts_selected_place_reverse_geocode_alias(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.address = Address(
        full_address="10 Tanglin Rd, Singapore 247908",
        street_name="Tanglin Rd",
        block_number="10",
        postal_code="247908",
        district="D10",
    )
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    monkeypatch.setattr(
        developers_api,
        "_resolve_submitted_sg_address_lookup",
        AsyncMock(return_value=None),
    )

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.3065566,
            "longitude": 103.8262787,
            "submittedAddress": "1 Nassim Rd, Singapore 258458",
            "placeId": "google-place-for-1-nassim",
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["address"]["full_address"] == "1 Nassim Rd, Singapore 258458"
    assert payload["address"]["postal_code"] == "258458"
    assert stub_logger.calls[0]["latitude"] == pytest.approx(1.3065566)


@pytest.mark.asyncio
async def test_developer_log_property_accepts_different_street_reverse_geocode_alias(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.address = Address(
        full_address="10 Tanglin Rd, Singapore 247908",
        street_name="Tanglin Rd",
        block_number="10",
        postal_code="247908",
        district="D10",
    )
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    monkeypatch.setattr(
        developers_api,
        "_resolve_submitted_sg_address_lookup",
        AsyncMock(return_value=None),
    )

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.3065566,
            "longitude": 103.8262787,
            "submittedAddress": "1 Nassim Rd, Singapore 258458",
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["address"]["full_address"] == "1 Nassim Rd, Singapore 258458"
    assert payload["address"]["postal_code"] == "258458"
    assert stub_logger.calls[0]["latitude"] == pytest.approx(1.3065566)


@pytest.mark.asyncio
async def test_developer_log_property_rejects_submitted_postal_code_mismatch(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.address = Address(
        full_address="20 Soon Lee Rd, Singapore 628086",
        street_name="Soon Lee Rd",
        block_number="20",
        postal_code="628086",
        district="D22",
    )
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    monkeypatch.setattr(
        developers_api,
        "_resolve_submitted_sg_address_lookup",
        AsyncMock(return_value=None),
    )

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.3286413,
            "longitude": 103.698443,
            "submittedAddress": "20 Soon Lee Rd, Singapore 628083",
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 409
    payload = response.json()
    assert (
        "Submitted address does not match the resolved map point" in payload["detail"]
    )
    assert "628083" in payload["detail"]
    assert "628086" in payload["detail"]


@pytest.mark.asyncio
async def test_developer_log_property_uses_current_gfa_evidence_from_request(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.property_info.pop("gfa_approved", None)
    stub_payload.property_info.pop("gross_floor_area_sqm", None)
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)

    async with async_session_factory() as session:
        session.add(_sg_zoning_layer())
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2801,
            "longitude": 103.8198,
            "development_scenarios": ["existing_building"],
            "currentGfaSqm": 16500,
            "currentGfaSource": "approved plans",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    envelope = payload["build_envelope"]
    assert envelope["current_gfa_sqm"] == 16500.0
    assert envelope["max_buildable_gfa_sqm"] == 18000.0
    assert envelope["additional_potential_gfa_sqm"] == 1500.0
    assert payload["property_info"]["gross_floor_area_sqm"] == 16500.0
    assert payload["property_info"]["current_gfa_source"] == "approved plans"
    assert envelope["rule_corpus_status"]["current_gfa_lookup_source"] == {
        "kind": "capture_user_evidence",
        "source": "approved plans",
        "area_sqm": 16500.0,
        "jurisdiction": "SG",
    }
    assert any(
        "Current GFA resolved from approved plans" in assumption
        for assumption in envelope["assumptions"]
    )


@pytest.mark.asyncio
async def test_developer_log_property_suppresses_untrusted_current_gfa_metadata(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.property_info["gfa_approved"] = 25000
    stub_payload.property_info.pop("current_gfa_source", None)
    stub_payload.property_info.pop("current_gfa_source_kind", None)
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)

    async with async_session_factory() as session:
        session.add(_sg_zoning_layer())
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2801,
            "longitude": 103.8198,
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    envelope = payload["build_envelope"]
    assert envelope["current_gfa_sqm"] is None
    assert envelope["additional_potential_gfa_sqm"] is None
    assert "gfa_approved" not in payload["property_info"]
    assert "gross_floor_area_sqm" not in payload["property_info"]
    assert payload["property_info"]["current_gfa_suppressed_reason"]
    assert envelope["rule_corpus_status"]["current_gfa_lookup_source"] == {
        "kind": "unavailable",
        "reason": "no_current_gfa_evidence_loaded",
        "jurisdiction": "SG",
    }


@pytest.mark.asyncio
async def test_developer_log_property_ignores_legacy_saved_current_gfa_without_reference(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.property_info.pop("gfa_approved", None)
    stub_payload.property_info.pop("gross_floor_area_sqm", None)
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)

    async with async_session_factory() as session:
        session.add_all(
            [
                _sg_zoning_layer(),
                Property(
                    id=property_id,
                    name="Legacy GFA Row",
                    address="45 Burghley Dr, Singapore 559022",
                    jurisdiction_code="SG",
                    property_type=PropertyType.RESIDENTIAL,
                    status=PropertyStatus.EXISTING,
                    location="POINT(103.8198 1.2801)",
                    gross_floor_area_sqm=Decimal("25000"),
                    external_references=None,
                ),
            ]
        )
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2801,
            "longitude": 103.8198,
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    envelope = response.json()["build_envelope"]
    assert envelope["current_gfa_sqm"] is None
    assert envelope["additional_potential_gfa_sqm"] is None
    assert envelope["rule_corpus_status"]["current_gfa_lookup_source"]["kind"] == (
        "unavailable"
    )


@pytest.mark.asyncio
async def test_developer_log_property_maps_hotel_zoning_to_hotel_use_groups(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.property_info.pop("gfa_approved", None)
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)

    async with async_session_factory() as session:
        session.add(
            _sg_zoning_layer(
                zone_code="SG:hotel",
                lu_desc="Hotel",
                gpr="4.2",
            )
        )
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2801,
            "longitude": 103.8198,
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["build_envelope"]["zone_code"] == "SG:hotel"
    assert payload["build_envelope"]["zone_description"] == "Hotel"
    assert payload["ura_zoning"]["source"] == "ref_zoning_layer"
    assert payload["ura_zoning"]["zone_code"] == "SG:hotel"
    assert payload["ura_zoning"]["use_groups"] == ["Hotel", "Retail"]


@pytest.mark.asyncio
async def test_developer_log_property_reports_unavailable_zoning_without_layer(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.ura_zoning = {
        "zone_code": "C1",
        "zone_description": "Commercial",
        "plot_ratio": 12.0,
    }
    stub_logger = _StubDeveloperLogger(stub_payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2801,
            "longitude": 103.8198,
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    envelope = payload["build_envelope"]
    assert envelope["zone_code"] is None
    assert envelope["allowable_plot_ratio"] is None
    assert envelope["max_buildable_gfa_sqm"] is None
    assert envelope["rule_corpus_status"]["coverage_state"] == "missing"
    assert envelope["rule_corpus_status"]["zoning_lookup_source"] == {
        "kind": "unavailable",
        "reason": "no_zoning_layer_contains_capture_point",
        "jurisdiction": "SG",
    }
    assert payload["ura_zoning"] == {
        "zone_code": None,
        "zone_description": None,
        "plot_ratio": None,
        "building_height_limit": None,
        "site_coverage": None,
        "use_groups": [],
        "special_conditions": None,
        "source": "unavailable",
        "source_reason": "no_zoning_layer_contains_capture_point",
    }


@pytest.mark.asyncio
async def test_derive_build_envelope_allows_saved_zoning_metadata_for_preview(
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_payload = _build_stub_payload(property_id)
    stub_payload.ura_zoning = {
        "zone_code": "C1",
        "zone_description": "Commercial",
        "plot_ratio": 4.0,
        "building_height_limit": 45.0,
        "site_coverage": 50.0,
    }
    stub_payload.property_info = {
        **stub_payload.property_info,
        "site_area_sqm": 4500,
        "gfa_approved": 12500,
    }

    async with async_session_factory() as session:
        envelope = await developers_api._derive_build_envelope(
            stub_payload,
            session,
            "SG",
            allow_captured_zoning_fallback=True,
        )

    assert envelope.zone_code == "C1"
    assert envelope.zone_description == "Commercial"
    assert envelope.allowable_plot_ratio == 4.0
    assert envelope.max_buildable_gfa_sqm == 18000.0
    assert envelope.building_height_limit_m == 45.0
    assert envelope.site_coverage_pct == 50.0
    assert envelope.rule_corpus_status is not None
    assert envelope.rule_corpus_status["zoning_lookup_source"] == {
        "kind": "captured_zoning_metadata",
        "reason": "persisted_property_or_non_gps_preview",
        "zone_code": "C1",
        "jurisdiction": "SG",
    }
    assert envelope.rule_corpus_status["resolved_by"]["land_use"] == (
        "captured_zoning_metadata"
    )
    assert envelope.rule_corpus_status["resolved_by"]["plot_ratio"] == (
        "captured_zoning_metadata"
    )


@pytest.mark.asyncio
async def test_developer_log_property_attaches_live_source_ingestion_when_enabled(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_logger = _StubDeveloperLogger(_build_stub_payload(property_id))
    _FakeOfficialSourceIngestionService.calls = []
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    monkeypatch.setattr(
        developers_api.settings,
        "CAPTURE_LIVE_SOURCE_SCAN_ENABLED",
        True,
    )

    from app.services.rules import official_source_ingestion

    monkeypatch.setattr(
        official_source_ingestion,
        "OfficialSourceIngestionService",
        _FakeOfficialSourceIngestionService,
    )

    async with async_session_factory() as session:
        session.add_all(
            [
                _sg_zoning_layer(),
                RefRule(
                    jurisdiction="SG",
                    authority="URA",
                    topic="building",
                    parameter_key="zoning.site_coverage.max_percent",
                    operator="<=",
                    value="50",
                    unit="%",
                    applicability={"zone_code": "SG:commercial"},
                    review_status="approved",
                    is_published=True,
                ),
            ]
        )
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2801,
            "longitude": 103.8198,
            "development_scenarios": ["raw_land", "existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    rule_status = response.json()["build_envelope"]["rule_corpus_status"]
    ingestion = rule_status["official_source_ingestion"]

    assert ingestion["staged_count"] == 2
    assert ingestion["existing_count"] == 1
    assert ingestion["failed_count"] == 0
    assert ingestion["candidates"][0]["status"] == "staged"
    assert _FakeOfficialSourceIngestionService.calls
    call = _FakeOfficialSourceIngestionService.calls[0]
    assert call["jurisdiction"] == "SG"
    assert call["zone_code"] == "SG:commercial"
    source_gap_fields = {gap["field"] for gap in call["source_gaps"]}
    assert "building_height_limit_m" in source_gap_fields
    assert "plot_ratio" not in source_gap_fields


@pytest.mark.asyncio
async def test_developer_log_property_resolves_configured_industrial_controls_without_live_scan(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    payload = _build_stub_payload(property_id)
    payload.ura_zoning = {
        "zone_code": "B1",
        "zone_description": "Business 1",
        "plot_ratio": 2.5,
        "site_coverage": 60.0,
    }
    payload.coordinates = (1.331096, 103.6977849)
    payload.property_info = {
        **payload.property_info,
        "site_area_sqm": 12000,
        "gfa_approved": 30000,
        "heritage_overlay": None,
        "is_conservation": False,
        "conservation_status": None,
        "heritage_constraints": [],
    }
    payload.heritage_overlay = None
    stub_logger = _StubDeveloperLogger(payload)
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    monkeypatch.setattr(
        developers_api.settings,
        "CAPTURE_LIVE_SOURCE_SCAN_ENABLED",
        False,
    )
    async with async_session_factory() as session:
        session.add(
            _sg_zoning_layer(
                zone_code="SG:industrial",
                lu_desc="Business 1",
                gpr="2.5",
                lat_min=1.30,
                lat_max=1.36,
                lon_min=103.66,
                lon_max=103.73,
            )
        )
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.331096,
            "longitude": 103.6977849,
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    envelope = response.json()["build_envelope"]
    rule_status = envelope["rule_corpus_status"]

    assert envelope["zone_code"] == "SG:industrial"
    assert envelope["building_height_limit_m"] == 80.0
    assert envelope["setback_front_m"] == 7.5
    assert envelope["setback_rear_m"] == 7.5
    assert envelope["setback_side_m"] == 3.0
    assert envelope["step_backs"] == [{"level": 8.0, "depth_m": 5.0}]
    assert envelope["max_buildable_gfa_sqm"] == 30000.0
    assert rule_status["resolved_by"]["building_height_limit_m"] == (
        "official_source_registry"
    )
    assert rule_status["resolved_by"]["setbacks"] == "official_source_registry"
    assert rule_status["resolved_by"]["step_backs"] == "official_source_registry"
    assert "building_height_limit_m" not in rule_status["unresolved_fields"]
    assert "setbacks" not in rule_status["unresolved_fields"]
    assert "step_backs" not in rule_status["unresolved_fields"]
    source_gap_fields = {gap["field"] for gap in rule_status["official_source_gaps"]}
    assert "building_height_limit_m" not in source_gap_fields
    assert "setbacks" not in source_gap_fields
    assert "step_backs" not in source_gap_fields
    project_clearance_fields = {
        gap["field"] for gap in rule_status["project_clearance_required"]
    }
    assert project_clearance_fields == {"air_rights_note"}
    air_rights_gap = rule_status["project_clearance_required"][0]
    assert air_rights_gap["reason"] == "project_specific_clearance_required"
    assert "official_source_ingestion" not in rule_status


@pytest.mark.asyncio
async def test_developer_log_property_resolves_configured_commercial_controls_without_live_scan(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_logger = _StubDeveloperLogger(_build_stub_payload(property_id))
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    monkeypatch.setattr(
        developers_api.settings,
        "CAPTURE_LIVE_SOURCE_SCAN_ENABLED",
        False,
    )
    async with async_session_factory() as session:
        session.add(_sg_zoning_layer())
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2801,
            "longitude": 103.8198,
            "development_scenarios": ["existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    envelope = response.json()["build_envelope"]
    rule_status = envelope["rule_corpus_status"]

    assert envelope["zone_code"] == "SG:commercial"
    assert envelope["setback_front_m"] == 7.5
    assert envelope["setback_rear_m"] == 7.5
    assert envelope["setback_side_m"] == 3.0
    assert envelope["step_backs"] == [{"level": 8.0, "depth_m": 5.0}]
    assert rule_status["resolved_by"]["setbacks"] == "official_source_registry"
    assert rule_status["resolved_by"]["step_backs"] == "official_source_registry"
    assert "setbacks" not in rule_status["unresolved_fields"]
    assert "step_backs" not in rule_status["unresolved_fields"]
    source_gap_fields = {gap["field"] for gap in rule_status["official_source_gaps"]}
    assert "setbacks" not in source_gap_fields
    assert "step_backs" not in source_gap_fields


@pytest.mark.asyncio
async def test_developer_log_property_re_resolves_height_limit_after_ingestion(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory,
) -> None:
    property_id = uuid4()
    stub_logger = _StubDeveloperLogger(_build_stub_payload(property_id))
    _ResolvingHeightLimitIngestionService.calls = []
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    monkeypatch.setattr(
        developers_api.settings,
        "CAPTURE_LIVE_SOURCE_SCAN_ENABLED",
        True,
    )

    from app.services.rules import official_source_ingestion

    monkeypatch.setattr(
        official_source_ingestion,
        "OfficialSourceIngestionService",
        _ResolvingHeightLimitIngestionService,
    )
    async with async_session_factory() as session:
        session.add(_sg_zoning_layer())
        await session.commit()

    response = await app_client.post(
        "/api/v1/developers/properties/log-gps",
        json={
            "latitude": 1.2801,
            "longitude": 103.8198,
            "development_scenarios": ["raw_land", "existing_building"],
        },
    )

    assert response.status_code == 200, response.text
    envelope = response.json()["build_envelope"]
    rule_status = envelope["rule_corpus_status"]

    assert envelope["building_height_limit_m"] == 80.0
    assert rule_status["resolved_by"]["building_height_limit_m"] == "ref_rule"
    assert "building_height_limit_m" not in rule_status["unresolved_fields"]
    source_gap_fields = {gap["field"] for gap in rule_status["official_source_gaps"]}
    assert "building_height_limit_m" not in source_gap_fields
    assert rule_status["official_source_ingestion"]["resolved_count"] == 1
    assert _ResolvingHeightLimitIngestionService.calls


@pytest.mark.asyncio
async def test_create_preview_job_for_scenario(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    property_id = uuid4()
    async with async_session_factory() as session:
        session.add(
            Property(
                id=property_id,
                name="Starter Model Tower",
                address="8 Scenario Way",
                jurisdiction_code="SG",
                property_type=PropertyType.OFFICE,
                status=PropertyStatus.EXISTING,
                location="POINT(103.8198 1.2801)",
                district="D01",
                land_area_sqm=Decimal("5000"),
                gross_floor_area_sqm=Decimal("18000"),
                building_height_m=Decimal("36"),
                zoning_code="C1",
                plot_ratio=Decimal("4.0"),
                is_conservation=False,
            )
        )
        await session.commit()

    response = await app_client.post(
        f"/api/v1/developers/properties/{property_id}/preview-jobs",
        json={
            "scenario": "existing_building",
            "geometry_detail_level": "medium",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["property_id"] == str(property_id)
    assert payload["scenario"] == "existing_building"
    assert payload["status"] in {"ready", "processing", "queued"}
    assert payload["geometry_detail_level"] == "medium"
    assert payload["starter_model_assumptions"]["retention_strategy"] == (
        "preserve_existing_bulk"
    )
    assert payload["starter_model_assumptions"]["floor_to_floor_m"] == 3.7
    assert payload["starter_model_assumptions"]["source"] == "rules"
    assert payload["starter_model_assumptions"]["provenance"]["summary"] == (
        "rules_only"
    )
    assert (
        payload["starter_model_assumptions"]["provenance"]["fields"]["floor_to_floor_m"]
        == "rules"
    )
    assert payload["starter_model_assumptions"]["asset_profiles"]
    assert any(
        profile["asset_type"] == "office"
        for profile in payload["starter_model_assumptions"]["asset_profiles"]
    )

    async with async_session_factory() as session:
        jobs = (
            (
                await session.execute(
                    select(PreviewJob).where(PreviewJob.property_id == property_id)
                )
            )
            .scalars()
            .all()
        )
        assert jobs
        assert any(job.scenario == "existing_building" for job in jobs)


@pytest.mark.asyncio
async def test_create_preview_job_exposes_property_specific_assumption_provenance(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    property_id = uuid4()
    async with async_session_factory() as session:
        session.add(
            Property(
                id=property_id,
                name="Conservation Retrofit House",
                address="88 Provenance Walk",
                jurisdiction_code="SG",
                property_type=PropertyType.OFFICE,
                status=PropertyStatus.EXISTING,
                location="POINT(103.8198 1.2801)",
                district="D01",
                land_area_sqm=Decimal("4000"),
                gross_floor_area_sqm=Decimal("12000"),
                building_height_m=Decimal("28"),
                floors_above_ground=8,
                year_built=1985,
                zoning_code="C1",
                plot_ratio=Decimal("3.5"),
                is_conservation=True,
            )
        )
        await session.commit()

    response = await app_client.post(
        f"/api/v1/developers/properties/{property_id}/preview-jobs",
        json={"scenario": "existing_building"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assumptions = payload["starter_model_assumptions"]
    provenance = assumptions["provenance"]

    assert assumptions["source"] == "hybrid"
    assert assumptions["retention_strategy"] == "conservation_retention"
    assert assumptions["floor_to_floor_m"] == 3.6
    assert assumptions["efficiency_factor"] == 0.93
    assert provenance["summary"] == "rules_with_property_adjustments"
    assert set(provenance["adjustments"]) == {
        "heritage_context",
        "older_building_age",
        "existing_floor_count",
    }
    assert provenance["fields"]["retention_strategy"] == "property_specific"
    assert provenance["fields"]["floor_to_floor_m"] == "property_specific"
    assert provenance["fields"]["efficiency_factor"] == "property_specific"
    assert provenance["fields"]["wall_thickness_mm"] == "rules"
    assert assumptions["asset_profiles"]
    assert any(
        profile["asset_type"] == "office" for profile in assumptions["asset_profiles"]
    )


@pytest.mark.asyncio
async def test_create_preview_jobs_differentiate_massing_by_scenario(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    property_id = uuid4()
    async with async_session_factory() as session:
        session.add(
            Property(
                id=property_id,
                name="Scenario Delta Tower",
                address="18 Scenario Way",
                jurisdiction_code="SG",
                property_type=PropertyType.OFFICE,
                status=PropertyStatus.EXISTING,
                location="POINT(103.8198 1.2801)",
                district="D01",
                land_area_sqm=Decimal("5000"),
                gross_floor_area_sqm=Decimal("18000"),
                building_height_m=Decimal("36"),
                zoning_code="C1",
                plot_ratio=Decimal("4.0"),
                is_conservation=False,
            )
        )
        await session.commit()

    for scenario in (
        "raw_land",
        "existing_building",
        "underused_asset",
        "heritage_property",
    ):
        response = await app_client.post(
            f"/api/v1/developers/properties/{property_id}/preview-jobs",
            json={"scenario": scenario},
        )
        assert response.status_code == 200, response.text

    async with async_session_factory() as session:
        jobs = (
            (
                await session.execute(
                    select(PreviewJob)
                    .where(PreviewJob.property_id == property_id)
                    .order_by(PreviewJob.requested_at.asc())
                )
            )
            .scalars()
            .all()
        )

        raw_land_job = next(job for job in jobs if job.scenario == "raw_land")
        renovation_job = next(
            job for job in jobs if job.scenario == "existing_building"
        )
        underused_job = next(job for job in jobs if job.scenario == "underused_asset")
        heritage_job = next(job for job in jobs if job.scenario == "heritage_property")

        raw_land_layers = (raw_land_job.metadata or {}).get("massing_layers") or []
        renovation_layers = (renovation_job.metadata or {}).get("massing_layers") or []
        underused_layers = (underused_job.metadata or {}).get("massing_layers") or []
        heritage_layers = (heritage_job.metadata or {}).get("massing_layers") or []
        assert raw_land_layers
        assert renovation_layers
        assert underused_layers
        assert heritage_layers

        raw_land_gfa = sum(
            float(layer.get("gfa_sqm") or 0.0) for layer in raw_land_layers
        )
        renovation_gfa = sum(
            float(layer.get("gfa_sqm") or 0.0) for layer in renovation_layers
        )
        underused_gfa = sum(
            float(layer.get("gfa_sqm") or 0.0) for layer in underused_layers
        )
        heritage_gfa = sum(
            float(layer.get("gfa_sqm") or 0.0) for layer in heritage_layers
        )

        raw_land_height = max(
            float(layer.get("estimated_height_m") or 0.0) for layer in raw_land_layers
        )
        heritage_height = max(
            float(layer.get("estimated_height_m") or 0.0) for layer in heritage_layers
        )

        assert raw_land_gfa > renovation_gfa
        assert underused_gfa > renovation_gfa
        assert heritage_gfa <= renovation_gfa
        assert heritage_height < raw_land_height
        assert raw_land_job.payload_checksum != renovation_job.payload_checksum
        assert underused_job.payload_checksum != renovation_job.payload_checksum
        assert heritage_job.payload_checksum != raw_land_job.payload_checksum

        def _allocation_map(layers: list[dict[str, Any]]) -> dict[str, float]:
            return {
                str(layer.get("asset_type")): float(layer.get("allocation_pct") or 0.0)
                for layer in layers
            }

        raw_land_allocations = _allocation_map(raw_land_layers)
        renovation_allocations = _allocation_map(renovation_layers)
        heritage_allocations = _allocation_map(heritage_layers)

        raw_land_assumptions = (raw_land_job.metadata or {}).get(
            "starter_model_assumptions"
        ) or {}
        renovation_assumptions = (renovation_job.metadata or {}).get(
            "starter_model_assumptions"
        ) or {}
        underused_assumptions = (underused_job.metadata or {}).get(
            "starter_model_assumptions"
        ) or {}
        heritage_assumptions = (heritage_job.metadata or {}).get(
            "starter_model_assumptions"
        ) or {}

        assert "retail" in raw_land_allocations
        assert renovation_allocations.get("office", 0.0) > renovation_allocations.get(
            "retail", 0.0
        )
        assert renovation_allocations.get("office", 0.0) > renovation_allocations.get(
            "amenities", 0.0
        )
        assert renovation_allocations.get("office", 0.0) > raw_land_allocations.get(
            "office", 0.0
        )
        assert renovation_allocations.get("retail", 0.0) < raw_land_allocations.get(
            "retail", 0.0
        )
        assert "amenities" in heritage_allocations
        assert heritage_allocations.get("office", 0.0) < renovation_allocations.get(
            "office", 0.0
        )
        assert raw_land_assumptions["retention_strategy"] == "ground_up_envelope"
        assert renovation_assumptions["retention_strategy"] == "preserve_existing_bulk"
        assert underused_assumptions["retention_strategy"] == "selective_repositioning"
        assert heritage_assumptions["retention_strategy"] == "conservation_retention"
        assert (
            raw_land_assumptions["floor_to_floor_m"]
            > renovation_assumptions["floor_to_floor_m"]
        )
        assert (
            heritage_assumptions["efficiency_factor"]
            < raw_land_assumptions["efficiency_factor"]
        )
        raw_land_profiles = raw_land_assumptions["asset_profiles"]
        renovation_profiles = renovation_assumptions["asset_profiles"]
        assert any(profile["asset_type"] == "retail" for profile in raw_land_profiles)
        assert any(profile["asset_type"] == "office" for profile in renovation_profiles)
        raw_land_retail = next(
            profile
            for profile in raw_land_profiles
            if profile["asset_type"] == "retail"
        )
        renovation_office = next(
            profile
            for profile in renovation_profiles
            if profile["asset_type"] == "office"
        )
        assert raw_land_retail["floor_to_floor_m"] >= 4.8
        assert renovation_office["floor_to_floor_m"] == pytest.approx(3.7)
        assert any(
            "Engineering defaults:" in note
            for note in ((heritage_job.metadata or {}).get("visualization_notes") or [])
        )


@pytest.mark.asyncio
async def test_create_preview_job_returns_404_for_unknown_property(
    app_client: AsyncClient,
) -> None:
    response = await app_client.post(
        f"/api/v1/developers/properties/{uuid4()}/preview-jobs",
        json={"scenario": "raw_land"},
    )

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Property not found"


@pytest.mark.asyncio
async def test_create_finance_project_requires_identity_headers(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    property_id = uuid4()
    async with async_session_factory() as session:
        session.add(
            Property(
                id=property_id,
                name="GPS Capture Tower",
                address="1 Developer Way",
                jurisdiction_code="SG",
                property_type=PropertyType.OFFICE,
                status=PropertyStatus.EXISTING,
                location="POINT(103.8198 1.2801)",
            )
        )
        await session.commit()

    response = await app_client.post(
        f"/api/v1/developers/properties/{property_id}/create-project",
        json={"projectName": "GPS Capture Tower"},
    )

    assert response.status_code == 403, response.text
    payload = response.json()
    assert "identity headers" in payload["detail"].lower()


@pytest.mark.asyncio
async def test_create_finance_project_from_capture_creates_finance_entities(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    property_id = uuid4()
    async with async_session_factory() as session:
        session.add(
            Property(
                id=property_id,
                name="GPS Capture Tower",
                address="1 Developer Way",
                jurisdiction_code="SG",
                property_type=PropertyType.OFFICE,
                status=PropertyStatus.EXISTING,
                location="POINT(103.8198 1.2801)",
            )
        )
        await session.commit()

    headers = {"X-Role": "admin", "X-User-Email": "qa@example.com"}
    response = await app_client.post(
        f"/api/v1/developers/properties/{property_id}/create-project",
        headers=headers,
        json={
            "projectName": "GPS Capture Tower",
            "scenarioName": "Base Case",
            "totalEstimatedCapexSgd": 1_000_000,
            "totalEstimatedRevenueSgd": 1_100_000,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()

    project_id = UUID(payload["project_id"])
    fin_project_id = int(payload["fin_project_id"])
    scenario_id = int(payload["scenario_id"])

    async with async_session_factory() as session:
        property_record = await session.get(Property, property_id)
        assert property_record is not None
        assert str(property_record.project_id) == str(project_id)
        assert property_record.owner_email == "qa@example.com"

        project = await session.get(Project, str(project_id))
        assert project is not None
        assert project.owner_email == "qa@example.com"

        fin_project = await session.get(FinProject, fin_project_id)
        assert fin_project is not None
        assert str(fin_project.project_id) == str(project_id)

        scenario = await session.get(FinScenario, scenario_id)
        assert scenario is not None
        assert str(scenario.project_id) == str(project_id)
        assert scenario.fin_project_id == fin_project_id
        assert scenario.assumptions.get("cost_escalation")
        assert scenario.assumptions.get("cash_flow")
        assert scenario.assumptions.get("capital_stack")

        stack_rows = (
            (
                await session.execute(
                    select(FinCapitalStack).where(
                        FinCapitalStack.scenario_id == scenario_id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(stack_rows) == 3
        stack_by_type = {row.source_type: row for row in stack_rows}
        assert stack_by_type["equity"].amount == Decimal("350000.00")
        assert stack_by_type["debt"].amount == Decimal("600000.00")
        assert stack_by_type["preferred"].amount == Decimal("50000.00")
        assert stack_by_type["preferred"].name == "Preferred"
