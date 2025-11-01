"""Tests for the heritage overlay lookup service."""

from __future__ import annotations

import json
import math

import pytest

try:
    from shapely.geometry import Point
except ModuleNotFoundError:  # pragma: no cover - optional dependency guard
    pytest.skip("shapely not installed", allow_module_level=True)

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
