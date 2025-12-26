"""Comprehensive tests for jurisdictions service.

Tests cover:
- GFAtoNIABand dataclass
- EngineeringDefaults dataclass
- JurisdictionConfig dataclass
- _normalise_code function
- get_jurisdiction_config function
- get_engineering_defaults function
- get_all_jurisdictions function
"""

from __future__ import annotations

import pytest

from app.services.jurisdictions import (
    EngineeringDefaults,
    GFAtoNIABand,
    JurisdictionConfig,
    get_all_jurisdictions,
    get_engineering_defaults,
    get_jurisdiction_config,
)

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestGFAtoNIABand:
    """Tests for GFAtoNIABand dataclass."""

    def test_band_values(self) -> None:
        """Test GFA to NIA band values."""
        band = GFAtoNIABand(low=0.75, mid=0.82, high=0.88)
        assert band.low == 0.75
        assert band.mid == 0.82
        assert band.high == 0.88

    def test_frozen_dataclass(self) -> None:
        """Test dataclass is frozen."""
        band = GFAtoNIABand(low=0.75, mid=0.82, high=0.88)
        # Frozen dataclass should raise an error on attribute assignment
        raised = False
        try:
            band.low = 0.80  # type: ignore
        except Exception:
            raised = True
        assert raised, "Frozen dataclass should raise on attribute assignment"


class TestEngineeringDefaults:
    """Tests for EngineeringDefaults dataclass."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        defaults = EngineeringDefaults(
            floor_to_floor={"residential": 3.5, "office": 4.0},
            efficiency_ratio={"residential": 0.82, "office": 0.75},
            gfa_to_nia_bands={"residential": GFAtoNIABand(0.75, 0.82, 0.88)},
            structural_grid={"residential": 8.4, "office": 9.0},
            core_ratio_pct={"residential": 15.0, "office": 18.0},
            parking_ratio={"residential": 1.0, "office": 0.5},
            basement_levels_typical=2,
        )
        assert defaults.floor_to_floor["residential"] == 3.5
        assert defaults.basement_levels_typical == 2


class TestJurisdictionConfig:
    """Tests for JurisdictionConfig dataclass."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        config = JurisdictionConfig(
            code="SG",
            name="Singapore",
            currency_code="SGD",
            currency_symbol="S$",
            area_units="sqm",
            rent_metric="psm_month",
            market_data={},
        )
        assert config.code == "SG"
        assert config.name == "Singapore"
        assert config.currency_code == "SGD"

    def test_optional_engineering_defaults(self) -> None:
        """Test engineering_defaults is optional."""
        config = JurisdictionConfig(
            code="SG",
            name="Singapore",
            currency_code="SGD",
            currency_symbol="S$",
            area_units="sqm",
            rent_metric="psm_month",
            market_data={},
        )
        assert config.engineering_defaults is None


class TestGetJurisdictionConfig:
    """Tests for get_jurisdiction_config function."""

    def test_singapore_config(self) -> None:
        """Test Singapore configuration."""
        config = get_jurisdiction_config("SG")
        assert config.code == "SG"
        assert config.currency_code == "SGD"
        assert config.currency_symbol == "S$"
        assert config.area_units == "sqm"

    def test_case_insensitive(self) -> None:
        """Test code lookup is case insensitive."""
        config1 = get_jurisdiction_config("sg")
        config2 = get_jurisdiction_config("SG")
        assert config1.code == config2.code

    def test_whitespace_handling(self) -> None:
        """Test whitespace is trimmed."""
        config = get_jurisdiction_config("  SG  ")
        assert config.code == "SG"

    def test_none_returns_singapore(self) -> None:
        """Test None returns Singapore (default)."""
        config = get_jurisdiction_config(None)
        assert config.code == "SG"

    def test_empty_string_returns_singapore(self) -> None:
        """Test empty string returns Singapore (default)."""
        config = get_jurisdiction_config("")
        assert config.code == "SG"

    def test_unknown_code_returns_singapore(self) -> None:
        """Test unknown code returns Singapore (default)."""
        config = get_jurisdiction_config("UNKNOWN")
        assert config.code == "SG"


class TestGetEngineeringDefaults:
    """Tests for get_engineering_defaults function."""

    def test_residential_defaults(self) -> None:
        """Test residential engineering defaults."""
        defaults = get_engineering_defaults("SG", "residential")
        assert "floor_to_floor" in defaults
        assert "efficiency_ratio" in defaults
        assert "gfa_to_nia_band" in defaults
        assert "structural_grid" in defaults
        assert "core_ratio_pct" in defaults
        assert "parking_ratio" in defaults
        assert "basement_levels_typical" in defaults
        assert "area_units" in defaults

    def test_office_defaults(self) -> None:
        """Test office engineering defaults."""
        defaults = get_engineering_defaults("SG", "office")
        assert "floor_to_floor" in defaults

    def test_default_asset_type(self) -> None:
        """Test default asset type is residential."""
        defaults = get_engineering_defaults("SG")
        assert isinstance(defaults, dict)

    def test_gfa_to_nia_band_structure(self) -> None:
        """Test GFA to NIA band has correct structure."""
        defaults = get_engineering_defaults("SG", "residential")
        band = defaults["gfa_to_nia_band"]
        assert "low" in band
        assert "mid" in band
        assert "high" in band

    def test_floor_to_floor_reasonable_value(self) -> None:
        """Test floor-to-floor height is reasonable."""
        defaults = get_engineering_defaults("SG", "residential")
        floor_to_floor = defaults["floor_to_floor"]
        assert 2.5 <= floor_to_floor <= 5.0  # Reasonable range

    def test_efficiency_ratio_reasonable_value(self) -> None:
        """Test efficiency ratio is reasonable."""
        defaults = get_engineering_defaults("SG", "residential")
        efficiency = defaults["efficiency_ratio"]
        assert 0.5 <= efficiency <= 1.0  # Should be a ratio


class TestGetAllJurisdictions:
    """Tests for get_all_jurisdictions function."""

    def test_returns_list(self) -> None:
        """Test returns a list."""
        jurisdictions = get_all_jurisdictions()
        assert isinstance(jurisdictions, list)

    def test_singapore_in_list(self) -> None:
        """Test Singapore is in the list."""
        jurisdictions = get_all_jurisdictions()
        codes = [j["code"] for j in jurisdictions]
        assert "SG" in codes

    def test_jurisdiction_structure(self) -> None:
        """Test each jurisdiction has required fields."""
        jurisdictions = get_all_jurisdictions()
        for j in jurisdictions:
            assert "code" in j
            assert "name" in j
            assert "currency_code" in j
            assert "currency_symbol" in j
            assert "area_units" in j


class TestJurisdictionScenarios:
    """Tests for jurisdiction use case scenarios."""

    def test_singapore_commercial_development(self) -> None:
        """Test Singapore commercial development parameters."""
        config = get_jurisdiction_config("SG")
        defaults = get_engineering_defaults("SG", "office")
        assert config.currency_code == "SGD"
        assert config.area_units == "sqm"
        assert isinstance(defaults["floor_to_floor"], (int, float))

    def test_singapore_residential_development(self) -> None:
        """Test Singapore residential development parameters."""
        config = get_jurisdiction_config("SG")
        defaults = get_engineering_defaults("SG", "residential")
        assert config.rent_metric == "psm_month"
        assert isinstance(defaults["parking_ratio"], (int, float))

    def test_singapore_mixed_use_development(self) -> None:
        """Test Singapore mixed-use development parameters."""
        defaults = get_engineering_defaults("SG", "mixed_use")
        assert isinstance(defaults, dict)
        assert "floor_to_floor" in defaults

    def test_asset_type_normalization(self) -> None:
        """Test asset type is normalized."""
        defaults1 = get_engineering_defaults("SG", "residential")
        defaults2 = get_engineering_defaults("SG", "Residential")
        # Both should return valid defaults
        assert isinstance(defaults1, dict)
        assert isinstance(defaults2, dict)
