from typing import Any
from uuid import UUID

import pytest

from backend.app.services.agents.gps_property_logger import (
    DevelopmentScenario,
    GPSPropertyLogger,
)
from backend.app.services.agents.ura_integration import URAPropertyInfo, URAZoningInfo
from backend.app.services.geocoding import Address


class StubGeocodingService:
    async def reverse_geocode(self, latitude: float, longitude: float) -> Address:
        return Address(
            full_address="1 Example Street",
            street_name="Example Street",
            building_name="Example Tower",
            block_number="01",
            postal_code="123456",
            district="D01 - Raffles Place",
            country="Singapore",
        )

    async def get_nearby_amenities(
        self, latitude: float, longitude: float, radius_m: int = 1000
    ) -> dict[str, Any]:
        return {
            "mrt_stations": [{"name": "Raffles MRT", "distance_m": 180}],
            "bus_stops": [{"name": "Bus Stop", "distance_m": 90}],
            "schools": [{"name": "Primary", "distance_m": 500}],
            "shopping_malls": [{"name": "Mall", "distance_m": 400}],
            "parks": [{"name": "Park", "distance_m": 320}],
        }


class StubURAService:
    async def get_zoning_info(self, address: str) -> URAZoningInfo:
        return URAZoningInfo(
            zone_code="C",
            zone_description="Commercial",
            plot_ratio=4.0,
            building_height_limit=160.0,
            site_coverage=80.0,
            use_groups=["Office", "Retail"],
            special_conditions="Subject to urban design guidelines",
        )

    async def get_existing_use(self, address: str) -> str:
        return "Office Building"

    async def get_property_info(self, address: str) -> URAPropertyInfo:
        return URAPropertyInfo(
            property_name="Example Tower",
            tenure="99-year leasehold",
            site_area_sqm=5000.0,
            gfa_approved=18000.0,
            building_height=18.0,
            completion_year=1965,
        )

    async def get_development_plans(
        self, latitude: float, longitude: float, radius_km: float = 2.0
    ) -> list[dict[str, Any]]:
        return [
            {
                "project_name": "Mock Mix-Use",
                "distance_km": 0.6,
                "expected_completion": "2026",
            }
        ]

    async def get_transaction_data(
        self, property_type: str, district: str | None = None, months_back: int = 12
    ) -> list[dict[str, Any]]:
        return [
            {"psf_price": 2500},
            {"psf_price": 2700},
        ]

    async def get_rental_data(
        self, property_type: str, district: str | None = None
    ) -> list[dict[str, Any]]:
        return [
            {"monthly_rent": 4500},
            {"monthly_rent": 5200},
        ]


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


class LoggerUnderTest(GPSPropertyLogger):
    def __init__(self) -> None:
        super().__init__(StubGeocodingService(), StubURAService())
        self._created_ids: list[UUID] = []

    async def _find_existing_property(self, *args: Any, **kwargs: Any) -> None:
        return None

    async def _create_property(self, *args: Any, **kwargs: Any) -> UUID:
        new_id = UUID("00000000-0000-0000-0000-000000000123")
        self._created_ids.append(new_id)
        return new_id

    async def _log_property_access(self, *args: Any, **kwargs: Any) -> None:
        return None


@pytest.mark.asyncio
async def test_gps_logging_generates_quick_analysis() -> None:
    logger = LoggerUnderTest()
    session = FakeSession()

    result = await logger.log_property_from_gps(
        latitude=1.301,
        longitude=103.832,
        session=session,
        user_id=None,
        scenarios=DevelopmentScenario.default_set(),
    )

    assert session.committed is True
    quick_analysis = result.quick_analysis
    assert quick_analysis is not None
    scenarios = {entry["scenario"] for entry in quick_analysis["scenarios"]}
    assert scenarios == {
        DevelopmentScenario.RAW_LAND.value,
        DevelopmentScenario.EXISTING_BUILDING.value,
        DevelopmentScenario.HERITAGE_PROPERTY.value,
        DevelopmentScenario.UNDERUSED_ASSET.value,
    }

    raw_land = next(
        item
        for item in quick_analysis["scenarios"]
        if item["scenario"] == DevelopmentScenario.RAW_LAND.value
    )
    assert raw_land["metrics"]["potential_gfa_sqm"] == pytest.approx(20000.0)
    assert raw_land["metrics"]["nearby_development_count"] == 1

    existing = next(
        item
        for item in quick_analysis["scenarios"]
        if item["scenario"] == DevelopmentScenario.EXISTING_BUILDING.value
    )
    assert existing["metrics"]["average_psf_price"] == pytest.approx(2600.0)

    underused = next(
        item
        for item in quick_analysis["scenarios"]
        if item["scenario"] == DevelopmentScenario.UNDERUSED_ASSET.value
    )
    assert underused["metrics"]["average_monthly_rent"] == pytest.approx(4850.0)

    payload = result.to_dict()
    assert payload["quick_analysis"] == quick_analysis


@pytest.mark.asyncio
async def test_gps_logging_respects_requested_scenarios() -> None:
    logger = LoggerUnderTest()
    session = FakeSession()

    result = await logger.log_property_from_gps(
        latitude=1.301,
        longitude=103.832,
        session=session,
        user_id=None,
        scenarios=[DevelopmentScenario.HERITAGE_PROPERTY],
    )

    quick_analysis = result.quick_analysis
    assert quick_analysis is not None
    assert len(quick_analysis["scenarios"]) == 1
    assert (
        quick_analysis["scenarios"][0]["scenario"]
        == DevelopmentScenario.HERITAGE_PROPERTY.value
    )
    assert quick_analysis["scenarios"][0]["metrics"]["heritage_risk"] == "high"
