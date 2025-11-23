from __future__ import annotations

from app.core.config import Settings

from backend.scripts import ingest_seattle_parcels as sea_parcels
from backend.scripts import ingest_seattle_zones as sea_zones


def test_seattle_token_default(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-key")
    monkeypatch.delenv("SEATTLE_SODA_APP_TOKEN", raising=False)
    settings = Settings()
    assert settings.SEATTLE_SODA_APP_TOKEN == "public"


def test_resolve_parcel_identifier_prefers_pin():
    props = {"PIN": "123456", "parcel_id": "ABC"}
    assert sea_parcels._resolve_parcel_identifier(props) == "123456"  # type: ignore[attr-defined]


def test_should_transform_detects_stateplane():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [1260000, 250000]},
                "properties": {},
            }
        ],
    }
    needs_transform, reason = sea_zones._should_transform_to_wgs84(
        geojson
    )  # type: ignore[attr-defined]
    assert needs_transform is True
    assert reason in {"sample_outside_wgs84_range", "declared_crs=EPSG:2926"}


def test_should_transform_skips_wgs84():
    geojson = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-122.33, 47.61]},
                "properties": {},
            }
        ],
    }
    needs_transform, reason = sea_zones._should_transform_to_wgs84(
        geojson
    )  # type: ignore[attr-defined]
    assert needs_transform is False
    assert "4326" in reason
