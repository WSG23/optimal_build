from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.property import PropertyType
from app.services.agents import gps_property_logger as gps_module
from app.services.agents.gps_property_logger import (
    DevelopmentScenario,
    GPSPropertyLogger,
    PropertyLogResult,
)
from app.services.geocoding import Address


def _result_with_scalar(value=None):
    return SimpleNamespace(
        scalar_one_or_none=lambda: value,
        scalars=lambda: SimpleNamespace(all=lambda: []),
    )


def make_address(**overrides):
    defaults = {
        "full_address": "123 Example Street, Singapore",
        "street_name": "Example Street",
        "building_name": "Example Tower",
        "district": "CBD",
        "postal_code": "048123",
    }
    defaults.update(overrides)
    return Address(**defaults)


def make_property_info(**overrides):
    defaults = dict(
        property_name="Example Tower",
        site_area_sqm=1000,
        gfa_approved=2500,
        building_height=120,
        completion_year=1998,
        tenure="Freehold",
    )
    defaults.update(overrides)
    return SimpleNamespace(
        model_dump=lambda: defaults,
        **defaults,
    )


def make_zoning(**overrides):
    defaults = {
        "zone_code": "C1",
        "plot_ratio": Decimal("3.5"),
        "zone_description": "Commercial",
    }
    defaults.update(overrides)

    return SimpleNamespace(
        **defaults,
        model_dump=lambda: {
            "zone_code": defaults["zone_code"],
            "plot_ratio": str(defaults["plot_ratio"]),
            "zone_description": defaults["zone_description"],
        },
    )


class StubSession:
    def __init__(self, execute_returns=None):
        self.execute_returns = list(execute_returns or [])
        self.executed = []
        self.committed = False
        self.rolled_back = False

    async def execute(self, stmt, params=None):
        self.executed.append((stmt, params))
        if self.execute_returns:
            return self.execute_returns.pop(0)
        return _result_with_scalar()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


@pytest.fixture
def stub_services(monkeypatch):
    monkeypatch.setenv("GPCS_SKIP_CHECKLIST_SEED", "1")
    geocoding = AsyncMock()
    geocoding.reverse_geocode = AsyncMock(return_value=make_address())
    geocoding.get_nearby_amenities = AsyncMock(return_value={"coffee": 3})

    ura = AsyncMock()
    ura.get_zoning_info = AsyncMock(return_value=make_zoning())
    ura.get_existing_use = AsyncMock(return_value="Office tower")
    ura.get_property_info = AsyncMock(return_value=make_property_info())
    ura.get_development_plans = AsyncMock(return_value=[{"plan": "LTA upgrade"}])
    ura.get_transaction_data = AsyncMock(return_value=[{"price": 2_000_000}])
    ura.get_rental_data = AsyncMock(return_value=[{"rent": 12_000}])

    monkeypatch.setattr(
        gps_module,
        "HeritageOverlayService",
        MagicMock(return_value=MagicMock(lookup=lambda lat, lng: {"status": "none"})),
    )

    logger = GPSPropertyLogger(geocoding_service=geocoding, ura_service=ura)
    ensure_seeded = AsyncMock(return_value=False)
    auto_populate = AsyncMock(return_value=[{"id": "check"}])
    monkeypatch.setattr(
        gps_module.DeveloperChecklistService,
        "ensure_templates_seeded",
        ensure_seeded,
    )
    monkeypatch.setattr(
        gps_module.DeveloperChecklistService,
        "auto_populate_checklist",
        auto_populate,
    )
    return logger, geocoding, ura, ensure_seeded, auto_populate


@pytest.mark.asyncio
async def test_log_property_creates_record(monkeypatch, stub_services):
    logger, geocoding, ura, ensure_seeded, auto_populate = stub_services

    # Ensure property not found
    session = StubSession(
        execute_returns=[
            _result_with_scalar(None),  # _find_existing_property
        ]
    )

    property_id = uuid4()
    monkeypatch.setattr(
        logger,
        "_create_property",
        AsyncMock(return_value=property_id),
    )
    monkeypatch.setattr(logger, "_update_property", AsyncMock())
    monkeypatch.setattr(logger, "_log_property_access", AsyncMock())
    monkeypatch.setattr(
        logger,
        "_generate_quick_analysis",
        MagicMock(return_value={"summary": "analysis"}),
    )

    result = await logger.log_property_from_gps(
        latitude=1.3,
        longitude=103.8,
        session=session,
        user_id=uuid4(),
    )

    assert isinstance(result, PropertyLogResult)
    assert result.property_id == property_id
    assert result.ura_zoning["zone_code"] == "C1"
    assert session.committed is True
    logger._create_property.assert_awaited_once()  # type: ignore[attr-defined]
    ensure_seeded.assert_awaited()
    auto_populate.assert_awaited_once()


@pytest.mark.asyncio
async def test_log_property_updates_existing_record(monkeypatch, stub_services):
    logger, geocoding, ura, ensure_seeded, auto_populate = stub_services
    session = StubSession()
    existing_id = uuid4()

    monkeypatch.setattr(
        logger,
        "_find_existing_property",
        AsyncMock(return_value=SimpleNamespace(id=existing_id)),
    )
    monkeypatch.setattr(logger, "_create_property", AsyncMock())
    monkeypatch.setattr(logger, "_update_property", AsyncMock())
    monkeypatch.setattr(logger, "_log_property_access", AsyncMock())
    monkeypatch.setattr(
        logger,
        "_generate_quick_analysis",
        MagicMock(return_value={"summary": "analysis"}),
    )

    result = await logger.log_property_from_gps(
        latitude=1.3,
        longitude=103.8,
        session=session,
        user_id=uuid4(),
    )

    logger._create_property.assert_not_called()  # type: ignore[attr-defined]
    logger._update_property.assert_awaited_once()  # type: ignore[attr-defined]
    assert result.property_id == existing_id
    assert result.heritage_overlay == {"status": "none"}
    assert session.committed is True
    ensure_seeded.assert_awaited()
    assert auto_populate.await_args.kwargs["property_id"] == existing_id


@pytest.mark.asyncio
async def test_log_property_rolls_back_on_geocode_failure(stub_services):
    logger, geocoding, ura, ensure_seeded, auto_populate = stub_services
    session = StubSession()
    geocoding.reverse_geocode = AsyncMock(return_value=None)

    with pytest.raises(ValueError):
        await logger.log_property_from_gps(
            latitude=0.0,
            longitude=0.0,
            session=session,
            user_id=uuid4(),
        )

    assert session.committed is False
    assert session.rolled_back is True
    ensure_seeded.assert_not_called()
    auto_populate.assert_not_awaited()


def test_property_log_result_dict():
    address = make_address()
    result = PropertyLogResult(
        property_id=uuid4(),
        address=address,
        coordinates=(1.3, 103.8),
        ura_zoning={"zone_code": "C1"},
        existing_use="Office",
        quick_analysis={"summary": "analysis"},
        heritage_overlay={"status": "none"},
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
    )

    payload = result.to_dict()
    assert payload["address"]["full_address"] == address.full_address
    assert payload["heritage_overlay"]["status"] == "none"
    assert payload["timestamp"] == "2025-01-01T12:00:00"


def test_development_scenario_default_order():
    assert DevelopmentScenario.default_set() == [
        DevelopmentScenario.RAW_LAND,
        DevelopmentScenario.EXISTING_BUILDING,
        DevelopmentScenario.HERITAGE_PROPERTY,
        DevelopmentScenario.UNDERUSED_ASSET,
        DevelopmentScenario.MIXED_USE_REDEVELOPMENT,
    ]


def test_determine_property_type_mapping(stub_services):
    logger, *_ = stub_services
    assert (
        logger._determine_property_type("Premium office tower") is PropertyType.OFFICE
    )
    assert (
        logger._determine_property_type("Light industrial warehouse")
        is PropertyType.INDUSTRIAL
    )


def test_generate_quick_analysis_covers_all_scenarios(stub_services):
    logger, *_ = stub_services
    scenarios = [
        DevelopmentScenario.RAW_LAND,
        DevelopmentScenario.EXISTING_BUILDING,
        DevelopmentScenario.HERITAGE_PROPERTY,
        DevelopmentScenario.UNDERUSED_ASSET,
        DevelopmentScenario.MIXED_USE_REDEVELOPMENT,
    ]
    ura_zoning = SimpleNamespace(
        plot_ratio=3.5,
        zone_description="Commercial",
        special_conditions="Transit adjacency premium",
    )
    property_info = SimpleNamespace(
        site_area_sqm=2000,
        gfa_approved=1500,
        building_height=60,
        completion_year=1988,
    )
    development_plans = [
        {"distance_km": 1.2, "expected_completion": "2027"},
        {"distance_km": 2.4, "expected_completion": "2026"},
    ]
    transactions = [{"sale_price": 2_000_000, "psf": 2100}]
    rentals = [{"rent": 9000}]
    nearby_amenities = {"coffee": 2}
    heritage_overlay = {"status": "protected"}

    analysis = logger._generate_quick_analysis(
        scenarios,
        ura_zoning=ura_zoning,
        property_info=property_info,
        existing_use="Industrial warehouse",
        nearby_amenities=nearby_amenities,
        property_type=PropertyType.INDUSTRIAL,
        development_plans=development_plans,
        transactions=transactions,
        rentals=rentals,
        heritage_overlay=heritage_overlay,
    )

    headlines = {entry["scenario"] for entry in analysis["scenarios"]}
    assert headlines == {
        DevelopmentScenario.RAW_LAND.value,
        DevelopmentScenario.EXISTING_BUILDING.value,
        DevelopmentScenario.HERITAGE_PROPERTY.value,
        DevelopmentScenario.UNDERUSED_ASSET.value,
        DevelopmentScenario.MIXED_USE_REDEVELOPMENT.value,
    }
    raw_land = next(
        entry
        for entry in analysis["scenarios"]
        if entry["scenario"] == DevelopmentScenario.RAW_LAND.value
    )
    assert raw_land["metrics"]["potential_gfa_sqm"] == 7000.0


def test_map_tenure_type_variants():
    geocoding = AsyncMock()
    ura = AsyncMock()
    logger = GPSPropertyLogger(geocoding, ura)
    assert logger._map_tenure_type("Freehold Estate") == "freehold"
    assert logger._map_tenure_type("Leasehold 999") == "leasehold_999"
    assert logger._map_tenure_type("Leasehold 30 years") == "leasehold_30"
    assert logger._map_tenure_type("some other form") == "leasehold_other"
