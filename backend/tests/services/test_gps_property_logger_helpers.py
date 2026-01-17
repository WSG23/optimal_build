"""Additional unit tests for GPS property logger helper functions."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.property import PropertyType
from app.services.agents.gps_property_logger import (
    ASSET_CLASS_ACCURACY_MODIFIERS,
    QUICK_ANALYSIS_ACCURACY_BANDS,
    DevelopmentScenario,
    GPSPropertyLogger,
    PropertyLogResult,
    _add_accuracy_bands_to_metrics,
    _get_accuracy_band,
)
from app.services.geocoding import Address


def _mock_geocoding():
    """Create a mock geocoding service."""
    return SimpleNamespace(
        reverse_geocode=lambda lat, lon: None,
        get_nearby_amenities=lambda lat, lon, radius_m: {},
    )


def _mock_ura():
    """Create a mock URA service."""
    return SimpleNamespace(
        get_zoning_info=lambda addr: None,
        get_existing_use=lambda addr: None,
        get_property_info=lambda addr: None,
    )


def _logger():
    """Create a GPSPropertyLogger instance."""
    return GPSPropertyLogger(
        geocoding_service=_mock_geocoding(),
        ura_service=_mock_ura(),
    )


# -----------------------------------------------------------
# DevelopmentScenario tests
# -----------------------------------------------------------


def test_development_scenario_default_set():
    """Test default scenario set returns all scenarios in order."""
    scenarios = DevelopmentScenario.default_set()

    assert len(scenarios) == 5
    assert scenarios[0] == DevelopmentScenario.RAW_LAND
    assert scenarios[1] == DevelopmentScenario.EXISTING_BUILDING
    assert scenarios[2] == DevelopmentScenario.HERITAGE_PROPERTY
    assert scenarios[3] == DevelopmentScenario.UNDERUSED_ASSET
    assert scenarios[4] == DevelopmentScenario.MIXED_USE_REDEVELOPMENT


def test_development_scenario_values():
    """Test development scenario enum values."""
    assert DevelopmentScenario.RAW_LAND.value == "raw_land"
    assert DevelopmentScenario.EXISTING_BUILDING.value == "existing_building"
    assert DevelopmentScenario.HERITAGE_PROPERTY.value == "heritage_property"
    assert DevelopmentScenario.UNDERUSED_ASSET.value == "underused_asset"
    assert (
        DevelopmentScenario.MIXED_USE_REDEVELOPMENT.value == "mixed_use_redevelopment"
    )


# -----------------------------------------------------------
# _get_accuracy_band tests
# -----------------------------------------------------------


def test_get_accuracy_band_gfa():
    """Test accuracy band for GFA-related metrics."""
    band = _get_accuracy_band("potential_gfa_sqm")

    assert band is not None
    assert band["low_pct"] == -10
    assert band["high_pct"] == 8
    assert band["source"] == "plot_ratio_variance"


def test_get_accuracy_band_price_psf():
    """Test accuracy band for price metrics."""
    band = _get_accuracy_band("average_psf")

    assert band is not None
    assert band["low_pct"] == -12
    assert band["high_pct"] == 10
    assert band["source"] == "transaction_variance"


def test_get_accuracy_band_noi():
    """Test accuracy band for NOI metrics."""
    band = _get_accuracy_band("est_noi")

    assert band is not None
    assert band["low_pct"] == -15
    assert band["high_pct"] == 10
    assert band["source"] == "income_projection"


def test_get_accuracy_band_unknown_metric():
    """Test accuracy band returns None for unknown metrics."""
    band = _get_accuracy_band("unknown_metric")

    assert band is None


def test_get_accuracy_band_with_asset_class_office():
    """Test accuracy band with office asset class (baseline modifier)."""
    band = _get_accuracy_band("potential_gfa_sqm", asset_class="office")

    assert band is not None
    assert band["low_pct"] == -10  # 1.0 modifier
    assert band["high_pct"] == 8
    assert band["asset_class"] == "office"


def test_get_accuracy_band_with_asset_class_retail():
    """Test accuracy band with retail asset class (1.15 modifier)."""
    band = _get_accuracy_band("potential_gfa_sqm", asset_class="retail")

    assert band is not None
    assert band["low_pct"] == pytest.approx(-11.5, rel=0.01)  # -10 * 1.15
    assert band["high_pct"] == pytest.approx(9.2, rel=0.01)  # 8 * 1.15
    assert band["asset_class"] == "retail"


def test_get_accuracy_band_with_asset_class_heritage():
    """Test accuracy band with heritage asset class (widest bands)."""
    band = _get_accuracy_band("heritage_risk_score", asset_class="heritage")

    assert band is not None
    assert band["low_pct"] == pytest.approx(-10.0, rel=0.01)  # -8 * 1.25
    assert band["high_pct"] == pytest.approx(18.8, rel=0.01)  # 15 * 1.25


def test_get_accuracy_band_with_unknown_asset_class():
    """Test accuracy band with unknown asset class uses default modifier."""
    band = _get_accuracy_band("potential_gfa_sqm", asset_class="unknown")

    assert band is not None
    assert band["low_pct"] == -10  # 1.0 default modifier
    assert band["high_pct"] == 8


# -----------------------------------------------------------
# _add_accuracy_bands_to_metrics tests
# -----------------------------------------------------------


def test_add_accuracy_bands_to_metrics_basic():
    """Test adding accuracy bands to metrics dict."""
    metrics = {
        "potential_gfa_sqm": 50000,
        "site_area_sqm": 10000,
    }

    result = _add_accuracy_bands_to_metrics(metrics)

    assert "accuracy_bands" in result
    assert "potential_gfa_sqm" in result["accuracy_bands"]
    assert "site_area_sqm" in result["accuracy_bands"]


def test_add_accuracy_bands_to_metrics_ignores_none():
    """Test accuracy bands are not added for None values."""
    metrics = {
        "potential_gfa_sqm": None,
        "site_area_sqm": 10000,
    }

    result = _add_accuracy_bands_to_metrics(metrics)

    assert "accuracy_bands" in result
    assert "potential_gfa_sqm" not in result["accuracy_bands"]
    assert "site_area_sqm" in result["accuracy_bands"]


def test_add_accuracy_bands_to_metrics_ignores_strings():
    """Test accuracy bands are not added for string values."""
    metrics = {
        "current_use": "office",
        "site_area_sqm": 10000,
    }

    result = _add_accuracy_bands_to_metrics(metrics)

    assert "accuracy_bands" in result
    assert "current_use" not in result["accuracy_bands"]


def test_add_accuracy_bands_to_metrics_no_bands():
    """Test returns original metrics if no bands apply."""
    metrics = {
        "unknown_metric": 100,
        "current_use": "office",
    }

    result = _add_accuracy_bands_to_metrics(metrics)

    assert "accuracy_bands" not in result


def test_add_accuracy_bands_with_asset_class():
    """Test accuracy bands use asset class modifier."""
    metrics = {"potential_gfa_sqm": 50000}

    result = _add_accuracy_bands_to_metrics(metrics, asset_class="heritage")

    assert "accuracy_bands" in result
    band = result["accuracy_bands"]["potential_gfa_sqm"]
    assert band["asset_class"] == "heritage"


# -----------------------------------------------------------
# PropertyLogResult tests
# -----------------------------------------------------------


def test_property_log_result_to_dict():
    """Test PropertyLogResult to_dict conversion."""
    property_id = uuid4()
    address = Address(
        full_address="123 Test Street",
        postal_code="123456",
        district="D01",
        street_name="Test Street",
        building_name="Test Building",
        country="Singapore",
    )
    timestamp = datetime(2025, 1, 1, 12, 0, 0)

    result = PropertyLogResult(
        property_id=property_id,
        address=address,
        coordinates=(1.3, 103.8),
        ura_zoning={"zone_code": "CR"},
        existing_use="Office",
        property_info={"name": "Test Property"},
        nearby_amenities={"mrt_stations": []},
        quick_analysis={"scenarios": []},
        timestamp=timestamp,
        heritage_overlay=None,
        jurisdiction_code="SG",
    )

    output = result.to_dict()

    assert output["property_id"] == str(property_id)
    assert output["coordinates"]["latitude"] == 1.3
    assert output["coordinates"]["longitude"] == 103.8
    assert output["ura_zoning"] == {"zone_code": "CR"}
    assert output["existing_use"] == "Office"
    assert output["timestamp"] == "2025-01-01T12:00:00"
    assert output["jurisdiction_code"] == "SG"


def test_property_log_result_to_dict_with_heritage():
    """Test PropertyLogResult to_dict with heritage overlay."""
    property_id = uuid4()
    address = Address(
        full_address="456 Heritage Street",
        postal_code="654321",
        district="D02",
        street_name="Heritage Street",
        building_name=None,
        country="Singapore",
    )

    result = PropertyLogResult(
        property_id=property_id,
        address=address,
        coordinates=(1.35, 103.85),
        ura_zoning={},
        existing_use="Retail",
        heritage_overlay={"name": "Conservation Area", "risk": "high"},
    )

    output = result.to_dict()

    assert output["heritage_overlay"]["name"] == "Conservation Area"
    assert output["heritage_overlay"]["risk"] == "high"


# -----------------------------------------------------------
# GPSPropertyLogger._safe_float tests
# -----------------------------------------------------------


def test_safe_float_with_valid_float():
    """Test safe_float with valid float."""
    assert GPSPropertyLogger._safe_float(3.14) == 3.14


def test_safe_float_with_valid_int():
    """Test safe_float with valid int."""
    assert GPSPropertyLogger._safe_float(42) == 42.0


def test_safe_float_with_string_number():
    """Test safe_float with string number."""
    assert GPSPropertyLogger._safe_float("123.45") == 123.45


def test_safe_float_with_none():
    """Test safe_float with None."""
    assert GPSPropertyLogger._safe_float(None) is None


def test_safe_float_with_invalid_string():
    """Test safe_float with invalid string."""
    assert GPSPropertyLogger._safe_float("not a number") is None


def test_safe_float_with_empty_string():
    """Test safe_float with empty string."""
    assert GPSPropertyLogger._safe_float("") is None


# -----------------------------------------------------------
# GPSPropertyLogger._safe_int tests
# -----------------------------------------------------------


def test_safe_int_with_valid_int():
    """Test safe_int with valid int."""
    assert GPSPropertyLogger._safe_int(42) == 42


def test_safe_int_with_valid_float():
    """Test safe_int with valid float rounds properly."""
    assert GPSPropertyLogger._safe_int(3.7) == 4
    assert GPSPropertyLogger._safe_int(3.2) == 3


def test_safe_int_with_none():
    """Test safe_int with None."""
    assert GPSPropertyLogger._safe_int(None) is None


def test_safe_int_with_string_number():
    """Test safe_int with string number."""
    assert GPSPropertyLogger._safe_int("42.5") == 42


def test_safe_int_with_invalid():
    """Test safe_int with invalid input."""
    assert GPSPropertyLogger._safe_int("invalid") is None


# -----------------------------------------------------------
# GPSPropertyLogger._average tests
# -----------------------------------------------------------


def test_average_with_values():
    """Test average with valid values."""
    result = GPSPropertyLogger._average([10.0, 20.0, 30.0])
    assert result == pytest.approx(20.0)


def test_average_with_single_value():
    """Test average with single value."""
    result = GPSPropertyLogger._average([42.0])
    assert result == pytest.approx(42.0)


def test_average_with_none_values():
    """Test average ignores None values."""
    result = GPSPropertyLogger._average([10.0, None, 30.0, None])
    assert result == pytest.approx(20.0)


def test_average_with_all_none():
    """Test average returns None if all values are None."""
    result = GPSPropertyLogger._average([None, None, None])
    assert result is None


def test_average_with_empty_list():
    """Test average returns None for empty list."""
    result = GPSPropertyLogger._average([])
    assert result is None


# -----------------------------------------------------------
# GPSPropertyLogger._nearest_plan_completion tests
# -----------------------------------------------------------


def test_nearest_plan_completion_with_plans():
    """Test finding nearest development plan completion."""
    plans = [
        {"distance_km": 1.5, "expected_completion": "2026-Q4"},
        {"distance_km": 0.5, "expected_completion": "2027-Q2"},
        {"distance_km": 2.0, "expected_completion": "2025-Q1"},
    ]

    result = GPSPropertyLogger._nearest_plan_completion(plans)

    assert result == "2027-Q2"  # Nearest at 0.5km


def test_nearest_plan_completion_empty_list():
    """Test nearest plan with empty list."""
    result = GPSPropertyLogger._nearest_plan_completion([])

    assert result is None


def test_nearest_plan_completion_missing_distance():
    """Test nearest plan handles missing distance."""
    plans = [
        {"expected_completion": "2026-Q4"},
        {"distance_km": 1.0, "expected_completion": "2027-Q1"},
    ]

    result = GPSPropertyLogger._nearest_plan_completion(plans)

    assert result == "2027-Q1"


def test_nearest_plan_completion_missing_completion():
    """Test nearest plan handles missing completion."""
    plans = [
        {"distance_km": 0.5},
        {"distance_km": 1.0, "expected_completion": "2027-Q1"},
    ]

    result = GPSPropertyLogger._nearest_plan_completion(plans)

    assert result == "2027-Q1"


# -----------------------------------------------------------
# GPSPropertyLogger._determine_property_type tests
# -----------------------------------------------------------


def test_determine_property_type_office():
    """Test determining office property type."""
    logger = _logger()

    assert logger._determine_property_type("Office Space") == PropertyType.OFFICE
    assert logger._determine_property_type("Grade A Office") == PropertyType.OFFICE


def test_determine_property_type_retail():
    """Test determining retail property type."""
    logger = _logger()

    assert logger._determine_property_type("Retail Shop") == PropertyType.RETAIL
    assert logger._determine_property_type("Shopping Mall") == PropertyType.RETAIL


def test_determine_property_type_industrial():
    """Test determining industrial property type."""
    logger = _logger()

    assert logger._determine_property_type("Industrial") == PropertyType.INDUSTRIAL
    assert logger._determine_property_type("Warehouse") == PropertyType.INDUSTRIAL
    assert logger._determine_property_type("Factory") == PropertyType.INDUSTRIAL


def test_determine_property_type_residential():
    """Test determining residential property type."""
    logger = _logger()

    assert logger._determine_property_type("Residential") == PropertyType.RESIDENTIAL
    assert logger._determine_property_type("Condo") == PropertyType.RESIDENTIAL
    assert logger._determine_property_type("Apartment") == PropertyType.RESIDENTIAL


def test_determine_property_type_hotel():
    """Test determining hotel property type."""
    logger = _logger()

    assert logger._determine_property_type("Hotel") == PropertyType.HOTEL


def test_determine_property_type_mixed_use():
    """Test determining mixed use property type."""
    logger = _logger()

    assert logger._determine_property_type("Mixed Use") == PropertyType.MIXED_USE


def test_determine_property_type_unknown():
    """Test determining property type for unknown use."""
    logger = _logger()

    assert (
        logger._determine_property_type("Specialty Facility")
        == PropertyType.SPECIAL_PURPOSE
    )
    assert logger._determine_property_type("Unknown") == PropertyType.SPECIAL_PURPOSE


# -----------------------------------------------------------
# GPSPropertyLogger._map_tenure_type tests
# -----------------------------------------------------------


def test_map_tenure_type_freehold():
    """Test mapping freehold tenure."""
    logger = _logger()

    assert logger._map_tenure_type("Freehold") == "freehold"
    assert logger._map_tenure_type("FREEHOLD ESTATE") == "freehold"


def test_map_tenure_type_leasehold_999():
    """Test mapping 999-year leasehold."""
    logger = _logger()

    assert logger._map_tenure_type("999-year Leasehold") == "leasehold_999"
    assert logger._map_tenure_type("Leasehold 999 years") == "leasehold_999"


def test_map_tenure_type_leasehold_99():
    """Test mapping 99-year leasehold."""
    logger = _logger()

    assert logger._map_tenure_type("99-year Leasehold") == "leasehold_99"
    assert logger._map_tenure_type("99 years from 2020") == "leasehold_99"


def test_map_tenure_type_leasehold_60():
    """Test mapping 60-year leasehold."""
    logger = _logger()

    assert logger._map_tenure_type("60-year Leasehold") == "leasehold_60"


def test_map_tenure_type_leasehold_30():
    """Test mapping 30-year leasehold."""
    logger = _logger()

    assert logger._map_tenure_type("30-year Leasehold") == "leasehold_30"


def test_map_tenure_type_other():
    """Test mapping other tenure types."""
    logger = _logger()

    assert logger._map_tenure_type("45-year Leasehold") == "leasehold_other"
    assert logger._map_tenure_type("Unknown Tenure") == "leasehold_other"


# -----------------------------------------------------------
# GPSPropertyLogger._quick_raw_land_analysis tests
# -----------------------------------------------------------


def test_quick_raw_land_analysis_with_data():
    """Test quick raw land analysis with complete data."""
    logger = _logger()
    ura_zoning = SimpleNamespace(
        plot_ratio=3.0,
        zone_description="Commercial",
        special_conditions=None,
    )
    property_info = SimpleNamespace(site_area_sqm=10000.0)
    development_plans = [
        {"distance_km": 1.0, "expected_completion": "2026-Q4"},
    ]

    result = logger._quick_raw_land_analysis(
        ura_zoning, property_info, development_plans
    )

    assert result["scenario"] == "raw_land"
    assert "30,000" in result["headline"]  # 10000 * 3.0
    assert result["metrics"]["potential_gfa_sqm"] == 30000.0
    assert result["metrics"]["site_area_sqm"] == 10000.0
    assert result["metrics"]["plot_ratio"] == 3.0
    assert result["metrics"]["nearby_development_count"] == 1


def test_quick_raw_land_analysis_missing_data():
    """Test quick raw land analysis with missing data."""
    logger = _logger()

    result = logger._quick_raw_land_analysis(None, None, [])

    assert result["scenario"] == "raw_land"
    assert "manual GFA check needed" in result["headline"]
    assert result["metrics"]["potential_gfa_sqm"] is None


# -----------------------------------------------------------
# GPSPropertyLogger._quick_existing_asset_analysis tests
# -----------------------------------------------------------


def test_quick_existing_asset_analysis_with_uplift():
    """Test existing asset analysis with uplift potential."""
    logger = _logger()
    ura_zoning = SimpleNamespace(plot_ratio=4.0)
    property_info = SimpleNamespace(
        site_area_sqm=10000.0,
        gfa_approved=35000.0,
    )
    transactions = [
        {"psf_price": 2000},
        {"psf_price": 2200},
    ]

    result = logger._quick_existing_asset_analysis(
        ura_zoning, property_info, transactions
    )

    assert result["scenario"] == "existing_building"
    assert "5,000" in result["headline"]  # 40000 - 35000 uplift
    assert result["metrics"]["gfa_uplift_sqm"] == 5000.0
    assert result["metrics"]["average_psf_price"] == pytest.approx(2100.0)


def test_quick_existing_asset_analysis_no_uplift():
    """Test existing asset analysis with no uplift."""
    logger = _logger()
    ura_zoning = SimpleNamespace(plot_ratio=3.0)
    property_info = SimpleNamespace(
        site_area_sqm=10000.0,
        gfa_approved=31000.0,  # Already near limit
    )

    result = logger._quick_existing_asset_analysis(ura_zoning, property_info, [])

    assert "near zoning limit" in result["headline"]


# -----------------------------------------------------------
# GPSPropertyLogger._quick_heritage_analysis tests
# -----------------------------------------------------------


def test_quick_heritage_analysis_old_building():
    """Test heritage analysis for old building."""
    logger = _logger()
    property_info = SimpleNamespace(completion_year=1960)

    result = logger._quick_heritage_analysis(property_info, "Office", None, [], None)

    assert result["scenario"] == "heritage_property"
    assert "HIGH" in result["headline"]
    assert any("1970" in note for note in result["notes"])


def test_quick_heritage_analysis_with_overlay():
    """Test heritage analysis with heritage overlay data."""
    logger = _logger()
    property_info = SimpleNamespace(completion_year=2000)
    heritage_overlay = {
        "risk": "high",
        "notes": ["Building within conservation area"],
    }

    result = logger._quick_heritage_analysis(
        property_info, "Office", None, [], heritage_overlay
    )

    assert "HIGH" in result["headline"]
    assert "Building within conservation area" in result["notes"]


def test_quick_heritage_analysis_conservation_use():
    """Test heritage analysis with conservation existing use."""
    logger = _logger()
    property_info = SimpleNamespace(completion_year=2010)

    result = logger._quick_heritage_analysis(
        property_info, "Conservation Building", None, [], None
    )

    assert "HIGH" in result["headline"]
    assert any("conservation" in note.lower() for note in result["notes"])


# -----------------------------------------------------------
# GPSPropertyLogger._quick_underused_analysis tests
# -----------------------------------------------------------


def test_quick_underused_analysis_good_transit():
    """Test underused analysis with good transit."""
    logger = _logger()
    nearby_amenities = {
        "mrt_stations": [{"name": "Station A"}],
    }
    property_info = SimpleNamespace(building_height=15.0)
    rentals = [
        {"monthly_rent": 5000},
        {"monthly_rent": 6000},
    ]

    result = logger._quick_underused_analysis(
        "Office", nearby_amenities, property_info, rentals, PropertyType.OFFICE
    )

    assert result["scenario"] == "underused_asset"
    assert result["metrics"]["nearby_mrt_count"] == 1
    assert result["metrics"]["average_monthly_rent"] == pytest.approx(5500.0)
    assert any("transit" in note.lower() for note in result["notes"])


def test_quick_underused_analysis_no_transit():
    """Test underused analysis with no transit."""
    logger = _logger()

    result = logger._quick_underused_analysis(
        "Warehouse", {}, None, [], PropertyType.INDUSTRIAL
    )

    assert any("Limited transit" in note for note in result["notes"])
    assert any("No nearby rental" in note for note in result["notes"])


def test_quick_underused_analysis_low_rise():
    """Test underused analysis for low-rise building."""
    logger = _logger()
    property_info = SimpleNamespace(building_height=10.0)

    result = logger._quick_underused_analysis(
        "Office", {"mrt_stations": []}, property_info, [], PropertyType.OFFICE
    )

    assert any("Low-rise" in note for note in result["notes"])


# -----------------------------------------------------------
# GPSPropertyLogger._quick_mixed_use_analysis tests
# -----------------------------------------------------------


def test_quick_mixed_use_analysis_multiple_uses():
    """Test mixed use analysis with multiple permitted uses."""
    logger = _logger()
    ura_zoning = SimpleNamespace(
        plot_ratio=4.5,
        use_groups=["residential", "commercial", "retail"],
    )
    property_info = SimpleNamespace(site_area_sqm=8000.0)
    nearby_amenities = {
        "mrt_stations": [{"name": "A"}, {"name": "B"}],
        "shopping_malls": [{"name": "Mall"}],
    }
    transactions = [
        {"transaction_date": "2024-06-15", "psf_price": 2000},
    ]

    result = logger._quick_mixed_use_analysis(
        ura_zoning, property_info, "Office", nearby_amenities, transactions
    )

    assert result["scenario"] == "mixed_use_redevelopment"
    assert "3-use" in result["headline"]
    assert result["metrics"]["permitted_use_groups"] == 3
    assert result["metrics"]["potential_gfa_sqm"] == pytest.approx(36000.0)
    assert result["metrics"]["nearby_amenities_count"] == 3


def test_quick_mixed_use_analysis_single_use():
    """Test mixed use analysis with single use zoning."""
    logger = _logger()
    ura_zoning = SimpleNamespace(
        plot_ratio=3.0,
        use_groups=["commercial"],
    )

    result = logger._quick_mixed_use_analysis(ura_zoning, None, "Office", None, [])

    assert "Single-use" in result["headline"]
    assert any("limit" in note.lower() for note in result["notes"])


def test_quick_mixed_use_analysis_no_zoning():
    """Test mixed use analysis with no zoning data."""
    logger = _logger()

    result = logger._quick_mixed_use_analysis(None, None, "Unknown", None, [])

    assert "unavailable" in result["headline"]


def test_quick_mixed_use_analysis_recent_transactions():
    """Test mixed use analysis counts recent transactions."""
    logger = _logger()
    ura_zoning = SimpleNamespace(plot_ratio=3.0, use_groups=[])
    transactions = [
        {"transaction_date": "2024-01-01"},
        {"transaction_date": "2023-06-15"},
        {"transaction_date": "2022-03-01"},
        {"transaction_date": "2021-01-01"},
        {"transaction_date": "2020-06-15"},
        {"transaction_date": "2019-01-01"},  # Before 2020
    ]

    result = logger._quick_mixed_use_analysis(
        ura_zoning, None, "Office", None, transactions
    )

    assert result["metrics"]["recent_transactions"] == 5


# -----------------------------------------------------------
# Accuracy band configuration tests
# -----------------------------------------------------------


def test_accuracy_bands_config_has_required_keys():
    """Test accuracy bands configuration has all required keys."""
    required_metrics = [
        "gfa",
        "site_area",
        "plot_ratio",
        "price_psf",
        "rent_psm",
        "valuation",
        "noi",
        "heritage_risk",
        "uplift",
    ]

    for metric in required_metrics:
        assert metric in QUICK_ANALYSIS_ACCURACY_BANDS
        band = QUICK_ANALYSIS_ACCURACY_BANDS[metric]
        assert "low_pct" in band
        assert "high_pct" in band
        assert "source" in band


def test_asset_class_modifiers_config():
    """Test asset class modifiers configuration."""
    assert ASSET_CLASS_ACCURACY_MODIFIERS["office"] == 1.0
    assert ASSET_CLASS_ACCURACY_MODIFIERS["retail"] > 1.0
    assert ASSET_CLASS_ACCURACY_MODIFIERS["industrial"] < 1.0
    assert ASSET_CLASS_ACCURACY_MODIFIERS["heritage"] == 1.25


# -----------------------------------------------------------
# GPSPropertyLogger._generate_quick_analysis tests
# -----------------------------------------------------------


def test_generate_quick_analysis_all_scenarios():
    """Test generate quick analysis with all scenarios."""
    logger = _logger()
    scenarios = DevelopmentScenario.default_set()
    ura_zoning = SimpleNamespace(
        plot_ratio=3.0,
        zone_description="Commercial",
        special_conditions=None,
        use_groups=["commercial", "retail"],
    )
    property_info = SimpleNamespace(
        site_area_sqm=10000.0,
        gfa_approved=25000.0,
        completion_year=2010,
        building_height=50.0,
    )
    nearby_amenities = {"mrt_stations": [{"name": "A"}], "shopping_malls": []}
    transactions = [{"psf_price": 2000, "transaction_date": "2024-01-01"}]
    rentals = [{"monthly_rent": 5000}]
    development_plans = [{"distance_km": 1.0, "expected_completion": "2026-Q4"}]

    result = logger._generate_quick_analysis(
        scenarios,
        ura_zoning=ura_zoning,
        property_info=property_info,
        existing_use="Office",
        nearby_amenities=nearby_amenities,
        property_type=PropertyType.OFFICE,
        development_plans=development_plans,
        transactions=transactions,
        rentals=rentals,
        heritage_overlay=None,
        jurisdiction_code="SG",
    )

    assert "generated_at" in result
    assert "scenarios" in result
    assert len(result["scenarios"]) == 5

    scenario_types = [s["scenario"] for s in result["scenarios"]]
    assert "raw_land" in scenario_types
    assert "existing_building" in scenario_types
    assert "heritage_property" in scenario_types
    assert "underused_asset" in scenario_types
    assert "mixed_use_redevelopment" in scenario_types


def test_generate_quick_analysis_single_scenario():
    """Test generate quick analysis with single scenario."""
    logger = _logger()
    scenarios = [DevelopmentScenario.RAW_LAND]

    result = logger._generate_quick_analysis(
        scenarios,
        ura_zoning=None,
        property_info=None,
        existing_use=None,
        nearby_amenities=None,
        property_type=PropertyType.LAND,
        development_plans=[],
        transactions=[],
        rentals=[],
        heritage_overlay=None,
        jurisdiction_code="SG",
    )

    assert len(result["scenarios"]) == 1
    assert result["scenarios"][0]["scenario"] == "raw_land"


def test_generate_quick_analysis_empty_scenarios():
    """Test generate quick analysis with empty scenario list."""
    logger = _logger()

    result = logger._generate_quick_analysis(
        scenarios=[],
        ura_zoning=None,
        property_info=None,
        existing_use=None,
        nearby_amenities=None,
        property_type=PropertyType.LAND,
        development_plans=[],
        transactions=[],
        rentals=[],
        heritage_overlay=None,
        jurisdiction_code="SG",
    )

    assert result["scenarios"] == []


def test_generate_quick_analysis_with_heritage_overlay():
    """Test generate quick analysis with heritage overlay data."""
    logger = _logger()
    scenarios = [DevelopmentScenario.HERITAGE_PROPERTY]
    heritage_overlay = {
        "name": "Conservation Area",
        "risk": "high",
        "notes": ["Protected building"],
    }

    result = logger._generate_quick_analysis(
        scenarios,
        ura_zoning=None,
        property_info=SimpleNamespace(completion_year=1950),
        existing_use="Heritage Building",
        nearby_amenities=None,
        property_type=PropertyType.SPECIAL_PURPOSE,
        development_plans=[],
        transactions=[],
        rentals=[],
        heritage_overlay=heritage_overlay,
        jurisdiction_code="SG",
    )

    heritage_result = result["scenarios"][0]
    assert heritage_result["scenario"] == "heritage_property"
    assert "HIGH" in heritage_result["headline"]


# -----------------------------------------------------------
# Additional edge case tests for better coverage
# -----------------------------------------------------------


def test_quick_existing_asset_analysis_no_approved_gfa():
    """Test existing asset analysis with no approved GFA."""
    logger = _logger()
    ura_zoning = SimpleNamespace(plot_ratio=3.0)
    property_info = SimpleNamespace(
        site_area_sqm=10000.0,
        gfa_approved=None,  # No approved GFA
    )

    result = logger._quick_existing_asset_analysis(ura_zoning, property_info, [])

    assert "assess existing building efficiency" in result["headline"]


def test_quick_heritage_analysis_with_development_plans():
    """Test heritage analysis mentions development plans."""
    logger = _logger()
    property_info = SimpleNamespace(completion_year=2000)
    development_plans = [
        {"distance_km": 0.5, "expected_completion": "2026-Q1"},
        {"distance_km": 1.0, "expected_completion": "2027-Q2"},
    ]

    result = logger._quick_heritage_analysis(
        property_info, "Office", None, development_plans, None
    )

    assert any("2 planned projects" in note for note in result["notes"])


def test_quick_heritage_analysis_with_ura_special_conditions():
    """Test heritage analysis uses URA special conditions."""
    logger = _logger()
    property_info = SimpleNamespace(completion_year=2000)
    ura_zoning = SimpleNamespace(special_conditions="Subject to heritage review")

    result = logger._quick_heritage_analysis(
        property_info, "Office", ura_zoning, [], None
    )

    assert "Subject to heritage review" in result["notes"]


def test_quick_heritage_analysis_low_risk_overlay():
    """Test heritage analysis with low risk overlay."""
    logger = _logger()
    property_info = SimpleNamespace(completion_year=2015)
    heritage_overlay = {
        "risk": "low",
        "notes": [],
    }

    result = logger._quick_heritage_analysis(
        property_info, "Office", None, [], heritage_overlay
    )

    assert "LOW" in result["headline"]


def test_quick_underused_analysis_with_building_height():
    """Test underused analysis with medium building height."""
    logger = _logger()
    property_info = SimpleNamespace(building_height=30.0)  # Not low-rise
    nearby_amenities = {"mrt_stations": [{"name": "A"}]}

    result = logger._quick_underused_analysis(
        "Office", nearby_amenities, property_info, [], PropertyType.OFFICE
    )

    # Should not have "Low-rise" note since height is 30m
    assert not any("Low-rise" in note for note in result["notes"])


def test_quick_mixed_use_analysis_moderate_amenities():
    """Test mixed use analysis with moderate amenities."""
    logger = _logger()
    ura_zoning = SimpleNamespace(plot_ratio=3.0, use_groups=["commercial", "retail"])
    nearby_amenities = {
        "mrt_stations": [{"name": "A"}],
        "shopping_malls": [],
    }

    result = logger._quick_mixed_use_analysis(
        ura_zoning, None, "Office", nearby_amenities, []
    )

    # Amenity count = 1 (moderate, not >= 3)
    assert any("Moderate amenity" in note for note in result["notes"])


def test_quick_mixed_use_analysis_high_transactions():
    """Test mixed use analysis signals active market."""
    logger = _logger()
    ura_zoning = SimpleNamespace(plot_ratio=3.0, use_groups=[])
    transactions = [
        {"transaction_date": "2024-01-01"},
        {"transaction_date": "2023-06-15"},
        {"transaction_date": "2022-03-01"},
        {"transaction_date": "2021-06-01"},
        {"transaction_date": "2020-12-01"},
    ]

    result = logger._quick_mixed_use_analysis(
        ura_zoning, None, "Office", None, transactions
    )

    # Should signal active market with 5 recent transactions
    assert any("signal active market" in note for note in result["notes"])
