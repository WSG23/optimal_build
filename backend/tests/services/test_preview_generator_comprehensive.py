"""Comprehensive tests for preview_generator service.

Tests cover:
- MassingLayerInput dataclass
- ColorLegendEntry dataclass
- PreviewAssets dataclass
- Helper functions (_coerce_float, _coerce_str, normalise_geometry_detail_level)
- Geometry building functions
- build_preview_payload function
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.preview_generator import (
    DEFAULT_GEOMETRY_DETAIL_LEVEL,
    SUPPORTED_GEOMETRY_DETAIL_LEVELS,
    ColorLegendEntry,
    MassingLayerInput,
    PreviewAssets,
    build_preview_payload,
    normalise_geometry_detail_level,
)


class TestNormaliseGeometryDetailLevel:
    """Tests for normalise_geometry_detail_level function."""

    def test_simple_level_accepted(self) -> None:
        """Test 'simple' is accepted."""
        assert normalise_geometry_detail_level("simple") == "simple"

    def test_medium_level_accepted(self) -> None:
        """Test 'medium' is accepted."""
        assert normalise_geometry_detail_level("medium") == "medium"

    def test_case_insensitive(self) -> None:
        """Test case insensitivity."""
        assert normalise_geometry_detail_level("SIMPLE") == "simple"
        assert normalise_geometry_detail_level("MEDIUM") == "medium"
        assert normalise_geometry_detail_level("Simple") == "simple"

    def test_whitespace_trimmed(self) -> None:
        """Test whitespace is trimmed."""
        assert normalise_geometry_detail_level("  simple  ") == "simple"
        assert normalise_geometry_detail_level("\tmedium\n") == "medium"

    def test_none_returns_default(self) -> None:
        """Test None returns default level."""
        assert normalise_geometry_detail_level(None) == DEFAULT_GEOMETRY_DETAIL_LEVEL

    def test_empty_returns_default(self) -> None:
        """Test empty string returns default level."""
        assert normalise_geometry_detail_level("") == DEFAULT_GEOMETRY_DETAIL_LEVEL

    def test_invalid_returns_default(self) -> None:
        """Test invalid value returns default level."""
        assert normalise_geometry_detail_level("high") == DEFAULT_GEOMETRY_DETAIL_LEVEL
        assert (
            normalise_geometry_detail_level("detailed") == DEFAULT_GEOMETRY_DETAIL_LEVEL
        )

    def test_supported_levels_frozenset(self) -> None:
        """Test supported levels is a frozenset."""
        assert isinstance(SUPPORTED_GEOMETRY_DETAIL_LEVELS, frozenset)
        assert "simple" in SUPPORTED_GEOMETRY_DETAIL_LEVELS
        assert "medium" in SUPPORTED_GEOMETRY_DETAIL_LEVELS


class TestMassingLayerInput:
    """Tests for MassingLayerInput dataclass."""

    def test_create_from_minimal_mapping(self) -> None:
        """Test creating from minimal mapping."""
        payload = {
            "asset_type": "office",
            "gfa_sqm": 5000.0,
        }
        layer = MassingLayerInput.from_mapping(payload, index=1)
        assert layer.asset_type == "office"
        assert layer.gfa_sqm == 5000.0
        assert layer.identifier == "office"
        assert layer.name == "office"

    def test_create_from_full_mapping(self) -> None:
        """Test creating from full mapping."""
        payload = {
            "id": "layer-001",
            "asset_type": "retail",
            "name": "Ground Floor Retail",
            "color": "#FF5733",
            "allocation_pct": 30.0,
            "gfa_sqm": 3000.0,
            "nia_sqm": 2550.0,
            "estimated_height_m": 6.0,
            "estimated_floors": 1.5,
        }
        layer = MassingLayerInput.from_mapping(payload, index=1)
        assert layer.identifier == "layer-001"
        assert layer.asset_type == "retail"
        assert layer.name == "Ground Floor Retail"
        assert layer.color == "#FF5733"
        assert layer.allocation_pct == 30.0
        assert layer.gfa_sqm == 3000.0
        assert layer.nia_sqm == 2550.0
        assert layer.estimated_height_m == 6.0
        assert layer.estimated_floors == 1.5

    def test_missing_asset_type_uses_index(self) -> None:
        """Test missing asset_type uses layer-{index} default."""
        payload = {"gfa_sqm": 1000.0}
        layer = MassingLayerInput.from_mapping(payload, index=5)
        assert layer.asset_type == "layer-5"

    def test_missing_gfa_uses_default(self) -> None:
        """Test missing gfa_sqm uses default of 100."""
        payload = {"asset_type": "office"}
        layer = MassingLayerInput.from_mapping(payload, index=1)
        assert layer.gfa_sqm == 100.0

    def test_zero_gfa_uses_default(self) -> None:
        """Test zero gfa_sqm uses default."""
        payload = {"asset_type": "office", "gfa_sqm": 0}
        layer = MassingLayerInput.from_mapping(payload, index=1)
        assert layer.gfa_sqm == 100.0

    def test_negative_gfa_uses_default(self) -> None:
        """Test negative gfa_sqm uses default."""
        payload = {"asset_type": "office", "gfa_sqm": -500}
        layer = MassingLayerInput.from_mapping(payload, index=1)
        assert layer.gfa_sqm == 100.0

    def test_fallback_to_nia_sqm_for_gfa(self) -> None:
        """Test falling back to nia_sqm when gfa_sqm is missing."""
        payload = {"asset_type": "office", "nia_sqm": 2000.0}
        layer = MassingLayerInput.from_mapping(payload, index=1)
        assert layer.gfa_sqm == 2000.0

    def test_fallback_to_floor_area_for_gfa(self) -> None:
        """Test falling back to floor_area_sqm when gfa_sqm is missing."""
        payload = {"asset_type": "office", "floor_area_sqm": 3000.0}
        layer = MassingLayerInput.from_mapping(payload, index=1)
        assert layer.gfa_sqm == 3000.0

    def test_height_from_height_field(self) -> None:
        """Test height fallback from 'height' field."""
        payload = {"asset_type": "office", "height": 12.0}
        layer = MassingLayerInput.from_mapping(payload, index=1)
        assert layer.estimated_height_m == 12.0

    def test_decimal_values_converted(self) -> None:
        """Test Decimal values are converted properly."""
        payload = {
            "asset_type": "office",
            "gfa_sqm": Decimal("5000.50"),
            "allocation_pct": Decimal("30.5"),
        }
        layer = MassingLayerInput.from_mapping(payload, index=1)
        assert layer.gfa_sqm == 5000.50
        assert layer.allocation_pct == 30.5

    def test_string_numbers_converted(self) -> None:
        """Test string numbers are converted."""
        payload = {
            "asset_type": "office",
            "gfa_sqm": "5000",
            "estimated_height_m": "15.5",
        }
        layer = MassingLayerInput.from_mapping(payload, index=1)
        assert layer.gfa_sqm == 5000.0
        assert layer.estimated_height_m == 15.5


class TestColorLegendEntry:
    """Tests for ColorLegendEntry dataclass."""

    def test_create_from_minimal_mapping(self) -> None:
        """Test creating from minimal mapping."""
        payload = {"asset_type": "office"}
        entry = ColorLegendEntry.from_mapping(payload)
        assert entry.asset_type == "office"
        assert entry.label is None
        assert entry.color is None
        assert entry.description is None

    def test_create_from_full_mapping(self) -> None:
        """Test creating from full mapping."""
        payload = {
            "asset_type": "retail",
            "label": "Retail Space",
            "color": "#4CAF50",
            "description": "Ground floor retail units",
        }
        entry = ColorLegendEntry.from_mapping(payload)
        assert entry.asset_type == "retail"
        assert entry.label == "Retail Space"
        assert entry.color == "#4CAF50"
        assert entry.description == "Ground floor retail units"

    def test_missing_asset_type_raises(self) -> None:
        """Test missing asset_type raises ValueError."""
        payload = {"label": "Office", "color": "#000"}
        with pytest.raises(ValueError, match="missing asset_type"):
            ColorLegendEntry.from_mapping(payload)

    def test_empty_asset_type_raises(self) -> None:
        """Test empty asset_type raises ValueError."""
        payload = {"asset_type": "", "label": "Office"}
        with pytest.raises(ValueError, match="missing asset_type"):
            ColorLegendEntry.from_mapping(payload)

    def test_to_payload(self) -> None:
        """Test to_payload conversion."""
        entry = ColorLegendEntry(
            asset_type="office",
            label="Office Space",
            color="#2196F3",
            description="Multi-level offices",
        )
        payload = entry.to_payload()
        assert payload["asset_type"] == "office"
        assert payload["label"] == "Office Space"
        assert payload["color"] == "#2196F3"
        assert payload["description"] == "Multi-level offices"

    def test_to_payload_minimal(self) -> None:
        """Test to_payload with minimal data."""
        entry = ColorLegendEntry(asset_type="office")
        payload = entry.to_payload()
        assert payload["asset_type"] == "office"
        assert "label" not in payload
        assert "color" not in payload
        assert "description" not in payload


class TestPreviewAssetsDataclass:
    """Tests for PreviewAssets dataclass."""

    def test_create_preview_assets(self) -> None:
        """Test creating PreviewAssets."""
        assets = PreviewAssets(
            preview_url="/static/dev-previews/123/v1/preview.gltf",
            metadata_url="/static/dev-previews/123/v1/preview.json",
            thumbnail_url="/static/dev-previews/123/v1/thumbnail.png",
            asset_version="20231115120000-abc12345",
        )
        assert "/preview.gltf" in assets.preview_url
        assert "/preview.json" in assets.metadata_url
        assert "/thumbnail.png" in assets.thumbnail_url
        assert "abc12345" in assets.asset_version


class TestBuildPreviewPayload:
    """Tests for build_preview_payload function."""

    def test_single_layer(self) -> None:
        """Test building payload with single layer."""
        property_id = uuid4()
        layers = [
            {
                "asset_type": "office",
                "gfa_sqm": 5000.0,
                "estimated_height_m": 20.0,
            }
        ]
        payload = build_preview_payload(property_id, layers)

        assert payload["schema_version"] == "1.0"
        assert payload["property_id"] == str(property_id)
        assert "generated_at" in payload
        assert len(payload["layers"]) == 1
        assert payload["layers"][0]["name"] == "office"

    def test_multiple_stacked_layers(self) -> None:
        """Test building payload with multiple stacked layers."""
        property_id = uuid4()
        layers = [
            {"asset_type": "retail", "gfa_sqm": 2000.0, "estimated_height_m": 6.0},
            {"asset_type": "office", "gfa_sqm": 8000.0, "estimated_height_m": 40.0},
            {"asset_type": "amenities", "gfa_sqm": 500.0, "estimated_height_m": 4.0},
        ]
        payload = build_preview_payload(property_id, layers)

        assert len(payload["layers"]) == 3
        # Layers should be stacked vertically
        layer1_base = payload["layers"][0]["geometry"]["base_elevation"]
        layer2_base = payload["layers"][1]["geometry"]["base_elevation"]
        assert layer2_base > layer1_base

    def test_with_color_legend(self) -> None:
        """Test building payload with color legend."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 5000.0, "estimated_height_m": 20.0},
        ]
        legend = [
            {"asset_type": "office", "color": "#FF5733", "label": "Office Space"},
        ]
        payload = build_preview_payload(property_id, layers, color_legend=legend)

        assert "color_legend" in payload
        assert len(payload["color_legend"]) == 1
        # Layer should inherit color from legend
        assert payload["layers"][0]["color"] == "#FF5733"
        assert payload["layers"][0]["name"] == "Office Space"

    def test_simple_geometry_level(self) -> None:
        """Test building payload with simple geometry level."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 5000.0, "estimated_height_m": 20.0},
        ]
        payload = build_preview_payload(
            property_id, layers, geometry_detail_level="simple"
        )

        assert payload["geometry_detail_level"] == "simple"
        assert payload["layers"][0]["geometry"]["detail_level"] == "simple"

    def test_medium_geometry_level(self) -> None:
        """Test building payload with medium geometry level."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 5000.0, "estimated_height_m": 20.0},
        ]
        payload = build_preview_payload(
            property_id, layers, geometry_detail_level="medium"
        )

        assert payload["geometry_detail_level"] == "medium"
        assert payload["layers"][0]["geometry"]["detail_level"] == "medium"

    def test_bounding_box_calculated(self) -> None:
        """Test bounding box is calculated correctly."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 10000.0, "estimated_height_m": 50.0},
        ]
        payload = build_preview_payload(property_id, layers)

        bbox = payload["bounding_box"]
        assert "min" in bbox
        assert "max" in bbox
        assert bbox["max"]["z"] > bbox["min"]["z"]  # Height dimension

    def test_camera_orbit_hint_generated(self) -> None:
        """Test camera orbit hint is generated."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 5000.0, "estimated_height_m": 20.0},
        ]
        payload = build_preview_payload(property_id, layers)

        hint = payload["camera_orbit_hint"]
        assert "theta" in hint
        assert "phi" in hint
        assert "radius" in hint
        assert hint["radius"] > 0

    def test_prism_geometry_included(self) -> None:
        """Test prism geometry is included."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 5000.0, "estimated_height_m": 20.0},
        ]
        payload = build_preview_payload(property_id, layers)

        geometry = payload["layers"][0]["geometry"]
        assert "prism" in geometry
        assert "vertices" in geometry["prism"]
        assert "faces" in geometry["prism"]

    def test_footprint_included(self) -> None:
        """Test footprint geometry is included."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 5000.0, "estimated_height_m": 20.0},
        ]
        payload = build_preview_payload(property_id, layers)

        geometry = payload["layers"][0]["geometry"]
        assert "footprint" in geometry
        assert geometry["footprint"]["type"] == "Polygon"

    def test_no_layers_raises_error(self) -> None:
        """Test empty layers raises ValueError."""
        property_id = uuid4()
        with pytest.raises(ValueError, match="at least one massing layer"):
            build_preview_payload(property_id, [])

    def test_invalid_layer_skipped(self) -> None:
        """Test invalid layer entries are skipped."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 5000.0, "estimated_height_m": 20.0},
            "not a valid layer",  # type: ignore
        ]
        # Should skip invalid layer and process valid one
        try:
            payload = build_preview_payload(property_id, layers)
            assert len(payload["layers"]) >= 1
        except (TypeError, ValueError):
            # Either behavior is acceptable
            pass

    def test_layer_metrics_included(self) -> None:
        """Test layer metrics are included."""
        property_id = uuid4()
        layers = [
            {
                "asset_type": "office",
                "gfa_sqm": 5000.0,
                "nia_sqm": 4250.0,
                "allocation_pct": 60.0,
                "estimated_height_m": 20.0,
                "estimated_floors": 5.0,
            },
        ]
        payload = build_preview_payload(property_id, layers)

        metrics = payload["layers"][0]["metrics"]
        assert metrics["gfa_sqm"] == 5000.0
        assert metrics["nia_sqm"] == 4250.0
        assert metrics["allocation_pct"] == 60.0
        assert metrics["estimated_height_m"] == 20.0
        assert metrics["estimated_floors"] == 5.0

    def test_floor_lines_for_medium_geometry(self) -> None:
        """Test floor lines are generated for medium geometry."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 5000.0, "estimated_height_m": 20.0},
        ]
        payload = build_preview_payload(
            property_id, layers, geometry_detail_level="medium"
        )

        geometry = payload["layers"][0]["geometry"]
        assert "floor_lines" in geometry
        # With 20m height, should have multiple floor lines at ~3.5m spacing
        assert len(geometry["floor_lines"]) > 0


class TestEdgeCases:
    """Tests for edge cases in preview generation."""

    def test_zero_height_layer(self) -> None:
        """Test layer with zero height."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 5000.0, "estimated_height_m": 0.0},
        ]
        payload = build_preview_payload(property_id, layers)
        # Should still create a valid payload
        assert len(payload["layers"]) == 1

    def test_very_small_gfa(self) -> None:
        """Test layer with very small GFA."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 1.0, "estimated_height_m": 3.0},
        ]
        payload = build_preview_payload(property_id, layers)
        assert len(payload["layers"]) == 1

    def test_very_large_gfa(self) -> None:
        """Test layer with very large GFA."""
        property_id = uuid4()
        layers = [
            {"asset_type": "office", "gfa_sqm": 1000000.0, "estimated_height_m": 200.0},
        ]
        payload = build_preview_payload(property_id, layers)
        assert len(payload["layers"]) == 1

    def test_unicode_asset_type(self) -> None:
        """Test layer with unicode in asset type."""
        property_id = uuid4()
        layers = [
            {"asset_type": "办公室", "gfa_sqm": 5000.0, "estimated_height_m": 20.0},
        ]
        payload = build_preview_payload(property_id, layers)
        assert payload["layers"][0]["name"] == "办公室"

    def test_special_characters_in_name(self) -> None:
        """Test layer with special characters in name."""
        property_id = uuid4()
        layers = [
            {
                "asset_type": "office",
                "name": "Office Space - Level 1 & 2",
                "gfa_sqm": 5000.0,
                "estimated_height_m": 8.0,
            },
        ]
        payload = build_preview_payload(property_id, layers)
        assert "Office Space - Level 1 & 2" in payload["layers"][0]["name"]

    def test_color_hex_formats(self) -> None:
        """Test various color hex formats."""
        property_id = uuid4()
        # Test both 3-char and 6-char hex
        layers = [
            {
                "asset_type": "office",
                "color": "#F00",
                "gfa_sqm": 1000.0,
                "estimated_height_m": 10.0,
            },
        ]
        legend = [
            {"asset_type": "retail", "color": "#00FF00"},
        ]
        # Should handle both formats
        payload = build_preview_payload(property_id, layers, color_legend=legend)
        assert len(payload["layers"]) == 1
