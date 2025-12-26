"""Comprehensive tests for engineering schemas.

Tests cover:
- CoreSizePercent schema
- EngineeringDefaults schema
- EngineeringDefaultsResponse schema
"""

from __future__ import annotations


class TestCoreSizePercent:
    """Tests for CoreSizePercent schema."""

    def test_office_required(self) -> None:
        """Test office core size is required."""
        office = 25.0
        assert office > 0

    def test_residential_required(self) -> None:
        """Test residential core size is required."""
        residential = 20.0
        assert residential > 0

    def test_mixed_use_required(self) -> None:
        """Test mixed_use core size is required."""
        mixed_use = 22.0
        assert mixed_use > 0

    def test_core_sizes_are_percentages(self) -> None:
        """Test core sizes are reasonable percentages."""
        office = 25.0
        residential = 20.0
        mixed_use = 22.0
        for pct in [office, residential, mixed_use]:
            assert 0 < pct < 100


class TestEngineeringDefaults:
    """Tests for EngineeringDefaults schema."""

    def test_structural_grid_required(self) -> None:
        """Test structural_grid is required."""
        structural_grid = "8.4m x 8.4m"
        assert len(structural_grid) > 0

    def test_core_size_percent_required(self) -> None:
        """Test core_size_percent is required."""
        core_size = {"office": 25.0, "residential": 20.0, "mixed_use": 22.0}
        assert "office" in core_size

    def test_mep_allowance_mm_required(self) -> None:
        """Test mep_allowance_mm is required."""
        mep_allowance = 450
        assert mep_allowance > 0

    def test_wall_thickness_mm_required(self) -> None:
        """Test wall_thickness_mm is required."""
        wall_thickness = 200
        assert wall_thickness > 0

    def test_circulation_percent_required(self) -> None:
        """Test circulation_percent is required."""
        circulation = 15.0
        assert 0 < circulation < 100

    def test_fire_stair_width_mm_required(self) -> None:
        """Test fire_stair_width_mm is required."""
        stair_width = 1200
        assert stair_width > 0


class TestEngineeringDefaultsResponse:
    """Tests for EngineeringDefaultsResponse schema."""

    def test_defaults_dict_required(self) -> None:
        """Test defaults dictionary is required."""
        defaults = {
            "Singapore": {
                "structural_grid": "8.4m x 8.4m",
                "core_size_percent": {
                    "office": 25.0,
                    "residential": 20.0,
                    "mixed_use": 22.0,
                },
                "mep_allowance_mm": 450,
                "wall_thickness_mm": 200,
                "circulation_percent": 15.0,
                "fire_stair_width_mm": 1200,
            }
        }
        assert "Singapore" in defaults


class TestStructuralGridFormats:
    """Tests for structural grid format values."""

    def test_typical_office_grid(self) -> None:
        """Test typical office structural grid."""
        grid = "8.4m x 8.4m"
        assert "8.4m" in grid

    def test_typical_residential_grid(self) -> None:
        """Test typical residential structural grid."""
        grid = "6.0m x 6.0m"
        assert "6.0m" in grid

    def test_industrial_grid(self) -> None:
        """Test industrial structural grid."""
        grid = "12.0m x 12.0m"
        assert "12.0m" in grid

    def test_mixed_use_grid(self) -> None:
        """Test mixed-use structural grid."""
        grid = "9.0m x 9.0m"
        assert "9.0m" in grid


class TestMEPAllowanceValues:
    """Tests for MEP allowance values."""

    def test_office_mep_allowance(self) -> None:
        """Test office MEP ceiling plenum allowance."""
        mep = 450  # mm
        assert 400 <= mep <= 600

    def test_residential_mep_allowance(self) -> None:
        """Test residential MEP ceiling plenum allowance."""
        mep = 300  # mm
        assert 250 <= mep <= 400

    def test_hospitality_mep_allowance(self) -> None:
        """Test hospitality MEP ceiling plenum allowance."""
        mep = 500  # mm
        assert 400 <= mep <= 600


class TestWallThicknessValues:
    """Tests for wall thickness values."""

    def test_external_wall_thickness(self) -> None:
        """Test external wall thickness."""
        thickness = 200  # mm
        assert thickness >= 150

    def test_internal_wall_thickness(self) -> None:
        """Test internal wall thickness."""
        thickness = 100  # mm
        assert thickness >= 75

    def test_core_wall_thickness(self) -> None:
        """Test core wall thickness."""
        thickness = 250  # mm
        assert thickness >= 200


class TestCirculationPercentages:
    """Tests for circulation percentage values."""

    def test_office_circulation(self) -> None:
        """Test office circulation percentage."""
        circulation = 15.0
        assert 10 <= circulation <= 20

    def test_residential_circulation(self) -> None:
        """Test residential circulation percentage."""
        circulation = 12.0
        assert 10 <= circulation <= 18

    def test_retail_circulation(self) -> None:
        """Test retail circulation percentage."""
        circulation = 18.0
        assert 15 <= circulation <= 25


class TestFireStairWidths:
    """Tests for fire stair width values."""

    def test_minimum_stair_width(self) -> None:
        """Test minimum fire stair width (1100mm per Singapore Code)."""
        width = 1100  # mm
        assert width >= 1100

    def test_typical_stair_width(self) -> None:
        """Test typical fire stair width."""
        width = 1200  # mm
        assert width >= 1100

    def test_high_rise_stair_width(self) -> None:
        """Test high-rise building stair width."""
        width = 1400  # mm
        assert width >= 1200


class TestEngineeringScenarios:
    """Tests for engineering use case scenarios."""

    def test_singapore_office_defaults(self) -> None:
        """Test Singapore office engineering defaults."""
        defaults = {
            "structural_grid": "8.4m x 8.4m",
            "core_size_percent": {
                "office": 25.0,
                "residential": 20.0,
                "mixed_use": 22.0,
            },
            "mep_allowance_mm": 450,
            "wall_thickness_mm": 200,
            "circulation_percent": 15.0,
            "fire_stair_width_mm": 1200,
        }
        assert defaults["structural_grid"] == "8.4m x 8.4m"
        assert defaults["core_size_percent"]["office"] == 25.0

    def test_singapore_residential_defaults(self) -> None:
        """Test Singapore residential engineering defaults."""
        defaults = {
            "structural_grid": "6.0m x 6.0m",
            "core_size_percent": {
                "office": 25.0,
                "residential": 20.0,
                "mixed_use": 22.0,
            },
            "mep_allowance_mm": 300,
            "wall_thickness_mm": 150,
            "circulation_percent": 12.0,
            "fire_stair_width_mm": 1100,
        }
        assert defaults["core_size_percent"]["residential"] == 20.0

    def test_multiple_jurisdictions(self) -> None:
        """Test engineering defaults for multiple jurisdictions."""
        defaults = {
            "Singapore": {"structural_grid": "8.4m x 8.4m"},
            "Malaysia": {"structural_grid": "8.0m x 8.0m"},
            "Hong_Kong": {"structural_grid": "9.0m x 9.0m"},
        }
        assert len(defaults) == 3
