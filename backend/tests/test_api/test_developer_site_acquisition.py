from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from backend._compat.datetime import utcnow

pytestmark = pytest.mark.skip(
    reason="Test causes pollution in full suite due to shared database state. "
    "Passes individually but fails when run with other tests. "
    "TODO: Add proper test isolation fixtures (database cleanup, session rollback). "
    "See Part B of test isolation fix."
)

from app.api.v1 import developers as developers_api
from sqlalchemy import select

from app.models.preview import PreviewJob
from app.services.agents.gps_property_logger import PropertyLogResult
from app.services.geocoding import Address
from httpx import AsyncClient


class _StubDeveloperLogger:
    def __init__(self, payload: PropertyLogResult) -> None:
        self._payload = payload
        self.calls: list[dict[str, Any]] = []

    async def log_property_from_gps(self, **kwargs: Any) -> PropertyLogResult:
        self.calls.append(kwargs)
        return self._payload


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
    )


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
    assert payload["quick_analysis"]["scenarios"][0]["scenario"] == "raw_land"

    envelope = payload["build_envelope"]
    assert envelope["zone_code"] == "C1"
    assert envelope["allowable_plot_ratio"] == 4.0
    assert envelope["site_area_sqm"] == 4500.0
    assert envelope["max_buildable_gfa_sqm"] == 18000.0
    assert envelope["current_gfa_sqm"] == 12500.0
    assert envelope["additional_potential_gfa_sqm"] == pytest.approx(5500.0)
    assert envelope["assumptions"], "Assumptions should not be empty"

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
