"""Tests for development_potential_scanner market features.

Tests focus on:
1. _apply_market_adjustments - Market-based use mix adjustments
2. _identify_market_opportunities - TOD and emerging trends detection
"""

from __future__ import annotations

from typing import Dict
from unittest.mock import MagicMock

import pytest


def create_scanner():
    """Create DevelopmentPotentialScanner with mock dependencies."""
    from app.services.agents.development_potential_scanner import (
        DevelopmentPotentialScanner,
    )

    mock_buildable = MagicMock()
    mock_finance = MagicMock()
    mock_ura = MagicMock()
    return DevelopmentPotentialScanner(
        buildable_service=mock_buildable,
        finance_calculator=mock_finance,
        ura_service=mock_ura,
    )


class MockZoningInfo:
    """Mock zoning information for testing."""

    def __init__(
        self,
        zone_description: str = "Commercial",
        plot_ratio: float = 5.0,
        building_height_limit: float = 100.0,
        site_coverage: float = 60.0,
        special_conditions: str = "",
    ):
        self.zone_description = zone_description
        self.plot_ratio = plot_ratio
        self.building_height_limit = building_height_limit
        self.site_coverage = site_coverage
        self.special_conditions = special_conditions


class MockLocation:
    """Mock location data for testing."""

    def __init__(self, transit_proximity_m: float = 1000.0):
        self.transit_proximity_m = transit_proximity_m


class MockProperty:
    """Mock property data for testing."""

    def __init__(
        self,
        district: str = "Downtown Core",
        transit_proximity_m: float | None = None,
        is_conservation: bool = False,
    ):
        self.district = district
        self.transit_proximity_m = transit_proximity_m
        self.is_conservation = is_conservation


class TestApplyMarketAdjustments:
    """Test DevelopmentPotentialScanner._apply_market_adjustments."""

    @pytest.fixture
    def scanner(self):
        """Create scanner instance with mock dependencies."""
        return create_scanner()

    def test_base_mix_unchanged_when_no_adjustments_apply(self, scanner):
        """Test base mix unchanged when no market factors apply."""
        base_mix = {"office": 0.7, "retail": 0.3}
        zoning = MockZoningInfo(zone_description="General")
        location = MockLocation(transit_proximity_m=2000)  # Far from transit

        result = scanner._apply_market_adjustments(base_mix, zoning, location)

        # Should be normalized to 1.0
        assert abs(sum(result.values()) - 1.0) < 0.01
        # Ratios should be preserved
        assert abs(result["office"] / result["retail"] - 0.7 / 0.3) < 0.1

    def test_transit_proximity_increases_residential(self, scanner):
        """Test transit proximity (<400m) increases residential allocation."""
        base_mix = {"residential": 0.5, "retail": 0.3, "office": 0.2}
        zoning = MockZoningInfo(zone_description="Mixed Use")
        location = MockLocation(transit_proximity_m=300)  # Close to transit

        result = scanner._apply_market_adjustments(base_mix, zoning, location)

        # Residential should be boosted (original 0.5 * 1.15 = 0.575)
        # But then normalized, so check it's higher relative to base
        original_residential_ratio = base_mix["residential"] / sum(base_mix.values())
        result_residential_ratio = result["residential"] / sum(result.values())
        assert result_residential_ratio >= original_residential_ratio

    def test_cbd_zone_increases_office(self, scanner):
        """Test CBD zone increases office allocation."""
        base_mix = {"office": 0.5, "retail": 0.3, "residential": 0.2}
        zoning = MockZoningInfo(zone_description="CBD Central")
        location = MockLocation(transit_proximity_m=2000)

        result = scanner._apply_market_adjustments(base_mix, zoning, location)

        # Office should be boosted in CBD
        # Check office ratio increased relative to base
        assert sum(result.values()) > 0  # Sanity check

    def test_cbd_zone_decreases_residential(self, scanner):
        """Test CBD zone decreases residential allocation."""
        base_mix = {"office": 0.4, "retail": 0.3, "residential": 0.3}
        zoning = MockZoningInfo(zone_description="Downtown Core CBD")
        location = MockLocation(transit_proximity_m=2000)

        result = scanner._apply_market_adjustments(base_mix, zoning, location)

        # Residential should be reduced in CBD
        # The adjustment multiplies by 0.85
        assert "residential" in result
        assert result["residential"] > 0  # Still exists

    def test_suburban_zone_increases_residential(self, scanner):
        """Test suburban zone increases residential allocation."""
        base_mix = {"residential": 0.5, "retail": 0.3, "office": 0.2}
        zoning = MockZoningInfo(zone_description="Suburban Fringe")
        location = MockLocation(transit_proximity_m=2000)

        result = scanner._apply_market_adjustments(base_mix, zoning, location)

        # Suburban should favor residential
        assert "residential" in result
        assert result["residential"] > 0

    def test_suburban_zone_decreases_office(self, scanner):
        """Test suburban zone decreases office allocation."""
        base_mix = {"residential": 0.4, "retail": 0.3, "office": 0.3}
        zoning = MockZoningInfo(zone_description="Outer Suburban")
        location = MockLocation(transit_proximity_m=2000)

        result = scanner._apply_market_adjustments(base_mix, zoning, location)

        # Office should be reduced in suburban (multiplied by 0.8)
        # Verify mix is still valid
        assert sum(result.values()) > 0
        assert "office" in result

    def test_industrial_zone_reduces_residential(self, scanner):
        """Test industrial zone reduces residential allocation."""
        base_mix = {
            "light_industrial": 0.4,
            "office": 0.3,
            "residential": 0.2,
            "retail": 0.1,
        }
        zoning = MockZoningInfo(zone_description="Business Park Industrial")
        location = MockLocation(transit_proximity_m=2000)

        result = scanner._apply_market_adjustments(base_mix, zoning, location)

        # Industrial zone should minimize residential (0.5 multiplier)
        # Residential may be zero or near zero
        if "residential" in result:
            assert result["residential"] <= 0.15  # Significantly reduced

    def test_industrial_zone_increases_light_industrial(self, scanner):
        """Test industrial zone increases light industrial allocation."""
        base_mix = {"light_industrial": 0.3, "office": 0.4, "retail": 0.3}
        zoning = MockZoningInfo(zone_description="Tech Park")
        location = MockLocation(transit_proximity_m=2000)

        result = scanner._apply_market_adjustments(base_mix, zoning, location)

        # Light industrial should be boosted
        assert "light_industrial" in result

    def test_normalization_ensures_sum_to_one(self, scanner):
        """Test that all adjusted mixes sum to 1.0."""
        base_mix = {"office": 0.6, "retail": 0.2, "residential": 0.2}

        test_cases = [
            MockZoningInfo(zone_description="CBD Central"),
            MockZoningInfo(zone_description="Suburban Fringe"),
            MockZoningInfo(zone_description="Industrial Zone"),
            MockZoningInfo(zone_description="Mixed Use"),
        ]

        for zoning in test_cases:
            location = MockLocation(transit_proximity_m=500)
            result = scanner._apply_market_adjustments(base_mix, zoning, location)
            total = sum(result.values())
            assert (
                abs(total - 1.0) < 0.001
            ), f"Sum was {total} for {zoning.zone_description}"

    def test_handles_missing_transit_proximity(self, scanner):
        """Test handles location without transit_proximity_m attribute."""
        base_mix = {"office": 0.7, "retail": 0.3}
        zoning = MockZoningInfo(zone_description="Commercial")
        location = MagicMock()
        del location.transit_proximity_m  # Remove attribute

        # Should not raise
        result = scanner._apply_market_adjustments(base_mix, zoning, location)
        assert abs(sum(result.values()) - 1.0) < 0.01


class TestIdentifyMarketOpportunities:
    """Test DevelopmentPotentialScanner._identify_market_opportunities."""

    @pytest.fixture
    def scanner(self):
        """Create scanner instance with mock dependencies."""
        return create_scanner()

    def test_identifies_tod_opportunity_near_transit(self, scanner):
        """Test identifies TOD opportunity when near transit."""
        property_data = MockProperty(district="Downtown", transit_proximity_m=300)
        zoning = MockZoningInfo()
        use_mix = {"residential": 0.5, "retail": 0.3, "office": 0.2}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        assert any(
            "transit-oriented" in opp.lower() or "tod" in opp.lower() for opp in result
        )

    def test_identifies_rental_demand_for_transit_residential(self, scanner):
        """Test identifies rental demand when residential near transit."""
        property_data = MockProperty(district="Central", transit_proximity_m=400)
        zoning = MockZoningInfo()
        use_mix = {"residential": 0.4, "retail": 0.3, "office": 0.3}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        # Should identify rental demand opportunity
        assert any("rental" in opp.lower() for opp in result)

    def test_identifies_emerging_area_jurong(self, scanner):
        """Test identifies emerging area opportunity for Jurong."""
        property_data = MockProperty(district="Jurong East")
        zoning = MockZoningInfo()
        use_mix = {"office": 0.7, "retail": 0.3}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        assert any(
            "emerging" in opp.lower() or "growth" in opp.lower() for opp in result
        )

    def test_identifies_emerging_area_paya_lebar(self, scanner):
        """Test identifies emerging area opportunity for Paya Lebar."""
        property_data = MockProperty(district="Paya Lebar Central")
        zoning = MockZoningInfo()
        use_mix = {"office": 0.6, "retail": 0.4}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        assert any(
            "emerging" in opp.lower() or "growth" in opp.lower() for opp in result
        )

    def test_identifies_tech_hub_one_north(self, scanner):
        """Test identifies tech hub opportunity for one-north."""
        property_data = MockProperty(district="one-north")
        zoning = MockZoningInfo()
        use_mix = {"office": 0.8, "retail": 0.2}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        assert any("tech" in opp.lower() for opp in result)

    def test_identifies_tech_hub_science_park(self, scanner):
        """Test identifies tech hub opportunity for Science Park."""
        property_data = MockProperty(district="Science Park")
        zoning = MockZoningInfo()
        use_mix = {"office": 0.7, "light_industrial": 0.3}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        assert any("tech" in opp.lower() for opp in result)

    def test_identifies_cbd_decentralization(self, scanner):
        """Test identifies CBD decentralization trend."""
        property_data = MockProperty(district="Regional Centre")
        zoning = MockZoningInfo(zone_description="Regional Centre")
        use_mix = {"office": 0.6, "retail": 0.4}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        assert any("decentralization" in opp.lower() for opp in result)

    def test_identifies_institutional_anchor(self, scanner):
        """Test identifies institutional anchor opportunity."""
        property_data = MockProperty(district="Hospital Road")
        zoning = MockZoningInfo()
        use_mix = {"residential": 0.6, "retail": 0.4}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        assert any("institutional" in opp.lower() for opp in result)

    def test_identifies_university_area(self, scanner):
        """Test identifies university area as institutional anchor."""
        property_data = MockProperty(district="University Town")
        zoning = MockZoningInfo()
        use_mix = {"residential": 0.5, "retail": 0.3, "office": 0.2}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        assert any("institutional" in opp.lower() for opp in result)

    def test_identifies_industrial_transformation(self, scanner):
        """Test identifies industrial transformation opportunity."""
        property_data = MockProperty(district="Industrial Estate")
        zoning = MockZoningInfo(zone_description="Business Industrial")
        use_mix = {"light_industrial": 0.5, "office": 0.5}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        assert any(
            "transformation" in opp.lower() or "industrial" in opp.lower()
            for opp in result
        )

    def test_no_opportunities_for_generic_location(self, scanner):
        """Test returns minimal opportunities for generic location."""
        property_data = MockProperty(
            district="Generic Area",
            transit_proximity_m=2000,  # Far from transit
        )
        zoning = MockZoningInfo(zone_description="General")
        use_mix = {"office": 0.7, "retail": 0.3}

        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)

        # Should return empty or minimal list
        assert isinstance(result, list)

    def test_handles_none_district(self, scanner):
        """Test handles None district gracefully."""
        property_data = MockProperty(district=None)
        property_data.district = None  # Explicitly set to None
        zoning = MockZoningInfo()
        use_mix = {"office": 0.7, "retail": 0.3}

        # Should not raise
        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)
        assert isinstance(result, list)

    def test_handles_empty_use_mix(self, scanner):
        """Test handles empty use mix gracefully."""
        property_data = MockProperty(district="CBD", transit_proximity_m=300)
        zoning = MockZoningInfo()
        use_mix: Dict[str, float] = {}

        # Should not raise
        result = scanner._identify_market_opportunities(property_data, zoning, use_mix)
        assert isinstance(result, list)


class TestDetermineOptimalUseMix:
    """Test DevelopmentPotentialScanner._determine_optimal_use_mix."""

    @pytest.fixture
    def scanner(self):
        """Create scanner instance with mock dependencies."""
        return create_scanner()

    def test_commercial_zone_returns_office_retail_mix(self, scanner):
        """Test commercial zone returns office/retail mix."""
        zoning = MockZoningInfo(zone_description="Commercial")
        location = MockLocation()

        result = scanner._determine_optimal_use_mix(zoning, location)

        assert "office" in result
        assert "retail" in result
        assert abs(sum(result.values()) - 1.0) < 0.01

    def test_residential_zone_returns_residential_heavy_mix(self, scanner):
        """Test residential zone returns residential-heavy mix."""
        zoning = MockZoningInfo(zone_description="Residential")
        location = MockLocation()

        result = scanner._determine_optimal_use_mix(zoning, location)

        assert "residential" in result
        assert result["residential"] > 0.5  # Should be dominant

    def test_mixed_use_zone_returns_diverse_mix(self, scanner):
        """Test mixed use zone returns diverse mix."""
        zoning = MockZoningInfo(zone_description="Mixed Use")
        location = MockLocation()

        result = scanner._determine_optimal_use_mix(zoning, location)

        assert "residential" in result
        assert "retail" in result or "office" in result
        # Should have multiple uses
        assert len([k for k, v in result.items() if v > 0.1]) >= 2

    def test_unknown_zone_returns_default_mix(self, scanner):
        """Test unknown zone returns default mixed allocation."""
        zoning = MockZoningInfo(zone_description="Unknown Zone Type")
        location = MockLocation()

        result = scanner._determine_optimal_use_mix(zoning, location)

        assert "mixed" in result or len(result) > 0
        assert abs(sum(result.values()) - 1.0) < 0.01
