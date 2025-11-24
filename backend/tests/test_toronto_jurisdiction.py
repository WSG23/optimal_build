from __future__ import annotations

from app.core.config import Settings

from backend.scripts import ingest_toronto_parcels as tor_parcels
from backend.scripts import ingest_toronto_zones as tor_zones


def test_toronto_token_default(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-key")
    monkeypatch.delenv("TORONTO_SODA_APP_TOKEN", raising=False)
    settings = Settings()
    assert settings.TORONTO_SODA_APP_TOKEN == "public"


def test_resolve_parcel_identifier_prefers_roll_num():
    props = {"ROLL_NUM": "123-456-789", "OBJECTID": 77}
    result = tor_parcels._resolve_parcel_identifier(props)  # type: ignore
    assert result == "123-456-789"


def test_zones_should_transform_detects_projected_coords():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [630000, 4840000],  # projected-like values
                },
                "properties": {},
            }
        ],
    }
    result = tor_zones._should_transform_to_wgs84(geojson)  # type: ignore
    needs_transform, reason = result
    assert needs_transform is True
    assert reason in {"sample_outside_wgs84_range", "declared_crs=EPSG:26917"}


def test_zones_should_transform_skips_wgs84():
    geojson = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-79.38, 43.65]},
                "properties": {},
            }
        ],
    }
    result = tor_zones._should_transform_to_wgs84(geojson)  # type: ignore
    needs_transform, reason = result
    assert needs_transform is False
    assert "4326" in reason
