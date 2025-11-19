from app.core.config import Settings

from backend.scripts import ingest_hk_zones as hk_ingest


def test_hk_config_defaults(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-key")
    monkeypatch.delenv("HK_DATA_GOV_API_KEY", raising=False)
    monkeypatch.delenv("HK_GEOSPATIAL_TOKEN", raising=False)
    settings = Settings()
    assert settings.HK_DATA_GOV_API_KEY == "public"
    assert settings.HK_GEOSPATIAL_TOKEN == ""


def test_should_transform_detection_uses_declared_crs():
    geojson = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [114.16, 22.3]},
                "properties": {},
            }
        ],
    }

    needs_transform, reason = hk_ingest._should_transform_to_wgs84(geojson)
    assert needs_transform is False
    assert "4326" in reason


def test_should_transform_detects_hk80_grid():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [835000.0, 816000.0],
                },
                "properties": {},
            }
        ],
    }

    needs_transform, reason = hk_ingest._should_transform_to_wgs84(geojson)
    assert needs_transform is True
    assert reason in {"sample_outside_wgs84_range", "declared_crs=EPSG:2326"}
