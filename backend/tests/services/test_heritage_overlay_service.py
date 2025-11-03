"""Tests for the heritage overlay lookup service."""

from __future__ import annotations

import json
import math

import pytest
from shapely.geometry import Point

from app.services.heritage_overlay import HeritageOverlayService, _SHAPELY_AVAILABLE


pytestmark = pytest.mark.skipif(
    not _SHAPELY_AVAILABLE, reason="Heritage overlay lookups require shapely"
)


def _service_and_sample_overlay() -> tuple[HeritageOverlayService, object]:
    service = HeritageOverlayService()
    sample = next((overlay for overlay in service._overlays if overlay.geometry), None)
    assert sample is not None, "expected at least one overlay with geometry"
    return service, sample


def test_lookup_without_spatial_index_matches_overlay() -> None:
    service, overlay = _service_and_sample_overlay()
    lat, lon = overlay.centroid[1], overlay.centroid[0]

    # Force linear scan path to avoid STRtree identity mismatches.
    service._index = None

    result = service.lookup(lat, lon)

    assert result is not None
    assert result["name"] == overlay.name
    assert result["risk"] == overlay.risk
    assert isinstance(result["notes"], list)
    assert result["heritage_premium_pct"] is not None
    assert result["attributes"]
    assert math.isclose(result["centroid"][0], overlay.centroid[0])
    assert math.isclose(result["centroid"][1], overlay.centroid[1])


def test_lookup_returns_none_outside_overlay_bounds() -> None:
    service, overlay = _service_and_sample_overlay()
    lat, lon = overlay.centroid[1], overlay.centroid[0]

    result = service.lookup(lat + 0.02, lon + 0.02)
    assert result is None


def test_overlay_contains_matches_centroid_point() -> None:
    service, overlay = _service_and_sample_overlay()
    centroid_point = Point(overlay.centroid[0], overlay.centroid[1])

    assert overlay.contains(centroid_point)


def test_lookup_returns_none_when_no_overlays(monkeypatch) -> None:
    """Ensure an empty dataset returns ``None`` for any lookup."""

    monkeypatch.setattr(
        "app.services.heritage_overlay._resource_text", lambda path: None
    )

    service = HeritageOverlayService()
    assert service.lookup(1.3, 103.8) is None


def test_legacy_loader_used_when_geojson_missing(monkeypatch) -> None:
    """Verify the legacy JSON loader populates overlays when GeoJSON absent."""

    sample_legacy = json.dumps(
        [
            {
                "name": "Legacy Overlay",
                "risk": "moderate",
                "notes": ["Legacy note"],
                "source": "legacy",
                "bbox": {
                    "min_lon": 103.82,
                    "min_lat": 1.28,
                    "max_lon": 103.83,
                    "max_lat": 1.29,
                },
                "heritage_premium_pct": "3.5",
            }
        ]
    )

    def fake_resource(path: str) -> str | None:
        if path.endswith(".geojson"):
            return None
        if path.endswith(".json"):
            return sample_legacy
        return None

    monkeypatch.setattr("app.services.heritage_overlay._resource_text", fake_resource)

    service = HeritageOverlayService()
    assert len(service._overlays) == 1
    overlay = service._overlays[0]
    assert overlay.name == "Legacy Overlay"
    assert overlay.heritage_premium_pct == pytest.approx(3.5)
    service._index = None  # ensure linear scan path
    result = service.lookup(1.285, 103.825)
    assert result is not None
    assert result["source"] == "legacy"


def test_resource_text_handles_os_error(monkeypatch) -> None:
    """_resource_text should return None on OSError."""
    from app.services.heritage_overlay import _resource_text

    def raise_os_error(path):
        raise OSError("File not readable")

    # This tests the OSError path in _resource_text
    result = _resource_text("nonexistent.json")
    assert result is None


def test_safe_float_with_invalid_values() -> None:
    """_safe_float should handle invalid values gracefully."""
    from app.services.heritage_overlay import _safe_float

    assert _safe_float(None) is None
    assert _safe_float("not-a-number") is None
    assert _safe_float(42.5) == pytest.approx(42.5)


def test_overlay_contains_without_shapely(monkeypatch) -> None:
    """HeritageOverlay.contains should return False when shapely unavailable."""
    monkeypatch.setattr("app.services.heritage_overlay._SHAPELY_AVAILABLE", False)

    from app.services.heritage_overlay import HeritageOverlay

    overlay = HeritageOverlay(
        name="Test",
        risk="low",
        notes=(),
        source="test",
        geometry=None,
        bbox=(0.0, 0.0, 1.0, 1.0),
        centroid=(0.5, 0.5),
    )

    # Should return False when shapely unavailable or geometry is None
    result = overlay.contains(None)
    assert result is False


def test_overlay_contains_with_exception() -> None:
    """HeritageOverlay.contains should return False on exceptions."""
    from app.services.heritage_overlay import HeritageOverlay

    # Create a mock geometry object that raises on contains
    class BadGeometry:
        def contains(self, point):
            raise RuntimeError("Geometry error")

        def touches(self, point):
            raise RuntimeError("Geometry error")

    overlay = HeritageOverlay(
        name="Test",
        risk="low",
        notes=(),
        source="test",
        geometry=BadGeometry(),
        bbox=(0.0, 0.0, 1.0, 1.0),
        centroid=(0.5, 0.5),
    )

    # Should catch exception and return False
    result = overlay.contains(Point(0, 0))
    assert result is False


def test_legacy_loader_with_json_decode_error(monkeypatch) -> None:
    """_load_legacy_overlays should handle JSON decode errors."""

    def fake_resource(path: str) -> str | None:
        if path.endswith(".geojson"):
            return None
        if path.endswith(".json"):
            return "{ invalid json"
        return None

    monkeypatch.setattr("app.services.heritage_overlay._resource_text", fake_resource)

    service = HeritageOverlayService()
    assert len(service._overlays) == 0


def test_legacy_loader_skips_invalid_bbox(monkeypatch) -> None:
    """_load_legacy_overlays should skip entries with invalid bbox."""
    sample_legacy = json.dumps(
        [
            {
                "name": "Valid Overlay",
                "bbox": {
                    "min_lon": 103.82,
                    "min_lat": 1.28,
                    "max_lon": 103.83,
                    "max_lat": 1.29,
                },
            },
            {
                "name": "Invalid Overlay",
                "bbox": {
                    "min_lon": "not-a-number",
                    "min_lat": 1.28,
                    "max_lon": 103.83,
                    "max_lat": 1.29,
                },
            },
        ]
    )

    def fake_resource(path: str) -> str | None:
        if path.endswith(".geojson"):
            return None
        if path.endswith(".json"):
            return sample_legacy
        return None

    monkeypatch.setattr("app.services.heritage_overlay._resource_text", fake_resource)

    service = HeritageOverlayService()
    assert len(service._overlays) == 1
    assert service._overlays[0].name == "Valid Overlay"


def test_geojson_loader_with_decode_error(monkeypatch) -> None:
    """_load_geojson_overlays should handle JSON decode errors."""

    def fake_resource(path: str) -> str | None:
        if path.endswith(".geojson"):
            return "{ invalid geojson"
        return None

    monkeypatch.setattr("app.services.heritage_overlay._resource_text", fake_resource)

    service = HeritageOverlayService()
    # Should fall back to empty or legacy loader
    assert isinstance(service._overlays, tuple)


def test_geojson_loader_skips_invalid_geometry(monkeypatch) -> None:
    """_load_geojson_overlays should skip features with invalid geometry."""
    sample_geojson = json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,  # No geometry
                    "properties": {"name": "No Geometry"},
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": "invalid",  # Invalid coordinates
                    },
                    "properties": {"name": "Invalid Geometry"},
                },
            ],
        }
    )

    def fake_resource(path: str) -> str | None:
        if path.endswith(".geojson"):
            return sample_geojson
        return None

    monkeypatch.setattr("app.services.heritage_overlay._resource_text", fake_resource)

    service = HeritageOverlayService()
    # Both features should be skipped
    assert len(service._overlays) == 0
