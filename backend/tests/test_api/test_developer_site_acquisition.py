from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from backend._compat.datetime import utcnow

from app.api.v1 import developers as developers_api
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
            }
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
    )


@pytest.mark.asyncio
async def test_developer_log_property_returns_envelope(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
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
    assert visualization["status"] == "placeholder"
    assert visualization["preview_available"] is False
    assert any(
        "3D previews" in note for note in visualization["notes"]
    ), "Visualization notes should mention 3D preview roadmap"

    optimizations = payload["optimizations"]
    assert optimizations, "Expected asset optimisation recommendations"
    assert optimizations[0]["asset_type"] == "office"
    assert optimizations[0]["allocation_pct"] > 0
    assert optimizations[0]["allocated_gfa_sqm"] is not None
    assert optimizations[0]["target_floor_height_m"] is not None
    assert optimizations[0]["estimated_revenue_sgd"] is not None
    assert optimizations[0]["absorption_months"] is not None

    financial_summary = payload["financial_summary"]
    assert financial_summary["total_estimated_revenue_sgd"] is not None
    assert financial_summary["total_estimated_capex_sgd"] is not None
    assert financial_summary["dominant_risk_profile"] == "moderate"

    # Ensure the developer logger was invoked with development scenarios
    assert stub_logger.calls, "Expected capture service to be invoked"
    assert stub_logger.calls[0]["scenarios"] == [
        "raw_land",
        "existing_building",
    ]
