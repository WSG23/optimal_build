from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from backend._compat.datetime import utcnow

from app.api.v1 import developers_gps as developers_api
from app.models.finance import FinCapitalStack, FinProject, FinScenario
from app.models.preview import PreviewJob
from app.models.projects import Project
from app.models.property import Property, PropertyStatus, PropertyType
from app.models.rkp import RefRule
from app.schemas.external_sources import ExternalSourceMetadata, ExternalSourceState
from app.services.agents.gps_property_logger import PropertyLogResult
from app.services.geocoding import Address
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
    assert envelope["zone_code"] == "C1"
    assert envelope["allowable_plot_ratio"] == 4.0
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
    assert envelope["source_reference"] == "SG Rule Registry (RefRule)"
    assert envelope["rule_corpus_status"]["zone_code"] == "SG:commercial"
    assert envelope["rule_corpus_status"]["resolved_by"]["land_use"] == (
        "captured_zoning_metadata"
    )
    assert envelope["rule_corpus_status"]["resolved_by"]["plot_ratio"] == (
        "captured_zoning_metadata"
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
    assert visualization["status"] in {"ready", "placeholder"}
    assert visualization["preview_available"] is True
    assert visualization["concept_mesh_url"].endswith((".json", ".gltf", ".glb"))
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
    assert preview_jobs and preview_jobs[0]["status"] in {"ready", "processing"}
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
        session.add(
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
            )
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
) -> None:
    property_id = uuid4()
    payload = _build_stub_payload(property_id)
    payload.ura_zoning = {
        "zone_code": "B1",
        "zone_description": "Business 1",
        "plot_ratio": 2.5,
        "site_coverage": 60.0,
    }
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

    assert envelope["zone_code"] == "B1"
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
) -> None:
    property_id = uuid4()
    stub_logger = _StubDeveloperLogger(_build_stub_payload(property_id))
    monkeypatch.setattr(developers_api, "developer_gps_logger", stub_logger)
    monkeypatch.setattr(
        developers_api.settings,
        "CAPTURE_LIVE_SOURCE_SCAN_ENABLED",
        False,
    )

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

    assert envelope["zone_code"] == "C1"
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
