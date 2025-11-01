"""Tests for geometry utility functions."""

from app.core.geometry.utils import _coerce_float, derive_setback_overrides
from app.core.models.geometry import GeometryGraph, Space


class TestCoerceFloat:
    """Tests for the _coerce_float helper function."""

    def test_coerce_float_with_none_returns_none(self):
        """Test that None input returns None."""
        result = _coerce_float(None)
        assert result is None

    def test_coerce_float_with_int(self):
        """Test converting int to float."""
        result = _coerce_float(42)
        assert result == 42.0
        assert isinstance(result, float)

    def test_coerce_float_with_float(self):
        """Test float passes through."""
        result = _coerce_float(3.14)
        assert result == 3.14
        assert isinstance(result, float)

    def test_coerce_float_with_string_number(self):
        """Test converting numeric string to float."""
        result = _coerce_float("42.5")
        assert result == 42.5
        assert isinstance(result, float)

    def test_coerce_float_with_zero(self):
        """Test that zero is handled correctly."""
        result = _coerce_float(0)
        assert result == 0.0
        assert isinstance(result, float)

    def test_coerce_float_with_negative(self):
        """Test negative numbers."""
        result = _coerce_float(-99.9)
        assert result == -99.9
        assert isinstance(result, float)

    def test_coerce_float_with_invalid_string_returns_none(self):
        """Test that non-numeric string returns None."""
        result = _coerce_float("not-a-number")
        assert result is None

    def test_coerce_float_with_object_returns_none(self):
        """Test that non-numeric object returns None."""
        result = _coerce_float({"not": "numeric"})
        assert result is None

    def test_coerce_float_with_list_returns_none(self):
        """Test that list returns None."""
        result = _coerce_float([1, 2, 3])
        assert result is None


class TestDeriveSetbackOverrides:
    """Tests for the derive_setback_overrides function."""

    def test_returns_empty_dict_when_site_bounds_none(self):
        """Test returns empty dict when site_bounds is None."""
        graph = GeometryGraph()
        result = derive_setback_overrides(graph, None)
        assert result == {}

    def test_returns_empty_dict_when_site_bounds_not_mapping(self):
        """Test returns empty dict when site_bounds is not a mapping."""
        graph = GeometryGraph()
        result = derive_setback_overrides(graph, "not-a-mapping")
        assert result == {}

    def test_returns_empty_dict_when_bounds_missing_coords(self):
        """Test returns empty dict when site_bounds missing coordinates."""
        graph = GeometryGraph()
        site_bounds = {"min_x": 0.0, "max_x": 100.0}  # Missing min_y, max_y
        result = derive_setback_overrides(graph, site_bounds)
        assert result == {}

    def test_returns_empty_dict_when_bounds_have_none_values(self):
        """Test returns empty dict when any bound is None."""
        graph = GeometryGraph()
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": None, "max_y": 100.0}
        result = derive_setback_overrides(graph, site_bounds)
        assert result == {}

    def test_returns_empty_dict_when_no_spaces(self):
        """Test returns empty dict when graph has no spaces."""
        graph = GeometryGraph()
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}
        result = derive_setback_overrides(graph, site_bounds)
        assert result == {}

    def test_skips_site_layer_spaces(self):
        """Test skips spaces on SITE layer."""
        # Create a space on SITE layer
        site_space = Space(
            id="site1",
            boundary=[(10.0, 10.0), (90.0, 10.0), (90.0, 90.0), (10.0, 90.0)],
            metadata={"source_layer": "SITE"},
        )

        graph = GeometryGraph(spaces=[site_space])
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}

        result = derive_setback_overrides(graph, site_bounds)

        # Should return empty dict since SITE spaces are skipped
        assert result == {}

    def test_calculates_setbacks_for_single_building_space(self):
        """Test calculates setbacks for a single building space."""
        # Building space centered in site with 10m setbacks all around
        building_space = Space(
            id="building1",
            boundary=[(10.0, 10.0), (90.0, 10.0), (90.0, 90.0), (10.0, 90.0)],
            metadata={"source_layer": "BUILDING"},
        )

        graph = GeometryGraph(spaces=[building_space])
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}

        result = derive_setback_overrides(graph, site_bounds)

        assert "front_setback_m" in result
        assert "side_setback_m" in result
        assert "rear_setback_m" in result

        assert result["front_setback_m"] == 10.0
        assert result["rear_setback_m"] == 10.0
        assert result["side_setback_m"] == 10.0  # min of left=10, right=10

    def test_uses_unit_scale_metadata(self):
        """Test applies unit_scale_to_m from metadata."""
        # Building in mm units (1000mm = 1m)
        building_space = Space(
            id="building1",
            boundary=[
                (10000.0, 10000.0),
                (90000.0, 10000.0),
                (90000.0, 90000.0),
                (10000.0, 90000.0),
            ],
            metadata={"source_layer": "BUILDING", "unit_scale_to_m": 0.001},
        )

        graph = GeometryGraph(spaces=[building_space])
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}

        result = derive_setback_overrides(graph, site_bounds)

        # After scaling: 10000 * 0.001 = 10m
        assert result["front_setback_m"] == 10.0
        assert result["side_setback_m"] == 10.0

    def test_handles_zero_or_negative_scale_as_1(self):
        """Test treats zero or negative scale as 1.0."""
        building_space = Space(
            id="building1",
            boundary=[(10.0, 10.0), (90.0, 10.0), (90.0, 90.0), (10.0, 90.0)],
            metadata={"source_layer": "BUILDING", "unit_scale_to_m": 0},
        )

        graph = GeometryGraph(spaces=[building_space])
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}

        result = derive_setback_overrides(graph, site_bounds)

        # Scale of 0 should be treated as 1.0
        assert result["front_setback_m"] == 10.0

    def test_calculates_side_setback_as_minimum_of_left_and_right(self):
        """Test side_setback is minimum of left and right gaps."""
        # Building closer to left edge (5m) than right edge (15m)
        building_space = Space(
            id="building1",
            boundary=[(5.0, 10.0), (85.0, 10.0), (85.0, 90.0), (5.0, 90.0)],
            metadata={"source_layer": "BUILDING"},
        )

        graph = GeometryGraph(spaces=[building_space])
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}

        result = derive_setback_overrides(graph, site_bounds)

        # Left gap: 5 - 0 = 5m
        # Right gap: 100 - 85 = 15m
        # Side setback should be min(5, 15) = 5
        assert result["side_setback_m"] == 5.0

    def test_rounds_setbacks_to_two_decimals(self):
        """Test that setback values are rounded to 2 decimal places."""
        building_space = Space(
            id="building1",
            boundary=[
                (10.333333, 10.666666),
                (90.777777, 10.666666),
                (90.777777, 90.888888),
                (10.333333, 90.888888),
            ],
            metadata={"source_layer": "BUILDING"},
        )

        graph = GeometryGraph(spaces=[building_space])
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}

        result = derive_setback_overrides(graph, site_bounds)

        # All values should be rounded to 2 decimals
        for value in result.values():
            assert round(value, 2) == value

    def test_skips_spaces_without_boundaries(self):
        """Test ignores spaces with empty boundaries."""
        building_space_no_boundary = Space(
            id="building1",
            boundary=[],
            metadata={"source_layer": "BUILDING"},
        )

        graph = GeometryGraph(spaces=[building_space_no_boundary])
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}

        result = derive_setback_overrides(graph, site_bounds)

        assert result == {}

    def test_handles_multiple_spaces_finds_min_and_max_extents(self):
        """Test processes multiple spaces and finds overall building extents."""
        # Two separate buildings
        building1 = Space(
            id="building1",
            boundary=[(10.0, 10.0), (40.0, 10.0), (40.0, 40.0), (10.0, 40.0)],
            metadata={"source_layer": "BUILDING"},
        )
        building2 = Space(
            id="building2",
            boundary=[(60.0, 60.0), (90.0, 60.0), (90.0, 90.0), (60.0, 90.0)],
            metadata={"source_layer": "BUILDING"},
        )

        graph = GeometryGraph(spaces=[building1, building2])
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}

        result = derive_setback_overrides(graph, site_bounds)

        # Overall building extents: min_x=10, max_x=90, min_y=10, max_y=90
        assert result["front_setback_m"] == 10.0  # 10 - 0
        assert result["rear_setback_m"] == 10.0  # 100 - 90
        assert result["side_setback_m"] == 10.0  # min(10-0, 100-90)

    def test_clamps_negative_gaps_to_zero(self):
        """Test that negative gaps are clamped to 0.0."""
        # Building extends beyond site bounds (shouldn't happen in practice)
        building_space = Space(
            id="building1",
            boundary=[(-5.0, -5.0), (105.0, -5.0), (105.0, 105.0), (-5.0, 105.0)],
            metadata={"source_layer": "BUILDING"},
        )

        graph = GeometryGraph(spaces=[building_space])
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}

        result = derive_setback_overrides(graph, site_bounds)

        # Negative gaps are clamped to 0.0 by max(gap, 0.0)
        assert result["front_setback_m"] == 0.0
        assert result["rear_setback_m"] == 0.0
        assert result["side_setback_m"] == 0.0

    def test_case_insensitive_site_layer_check(self):
        """Test that SITE layer check is case-insensitive."""
        # Test with lowercase "site"
        site_space = Space(
            id="site1",
            boundary=[(10.0, 10.0), (90.0, 10.0), (90.0, 90.0), (10.0, 90.0)],
            metadata={"source_layer": "site"},
        )

        graph = GeometryGraph(spaces=[site_space])
        site_bounds = {"min_x": 0.0, "max_x": 100.0, "min_y": 0.0, "max_y": 100.0}

        result = derive_setback_overrides(graph, site_bounds)

        # Should skip since it's a SITE layer (case-insensitive)
        assert result == {}
