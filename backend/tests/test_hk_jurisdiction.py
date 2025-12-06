from decimal import Decimal

from app.core.config import Settings
from app.services.jurisdictions import get_jurisdiction_config

from app.api.v1.developers import (
    DeveloperAssetOptimization,
    DeveloperGPSLogRequest,
)
from app.api.v1.developers_gps import (
    _build_finance_asset_mix_inputs,
)
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


def test_jurisdiction_config_exposes_hk_defaults():
    config = get_jurisdiction_config("hk")
    assert config.currency_code == "HKD"
    assert config.currency_symbol == "HK$"
    assert config.area_units == "sqft"


def test_developer_gps_request_normalises_jurisdiction_code():
    request = DeveloperGPSLogRequest(
        latitude=22.3,
        longitude=114.1,
        development_scenarios=None,
        jurisdiction_code="hk",
    )
    assert request.jurisdiction_code == "HK"


def test_finance_asset_mix_inputs_convert_hk_units():
    optimization = DeveloperAssetOptimization(
        asset_type="office",
        allocation_pct=60.0,
        nia_sqm=1000.0,
        rent_psm_month=12.0,
        notes=[],
        constraint_violations=[],
    )

    payload = _build_finance_asset_mix_inputs([optimization], jurisdiction_code="HK")[0]

    assert Decimal(str(payload["nia_sqm"])).quantize(Decimal("0.01")) == Decimal(
        "92.90"
    )
    assert Decimal(str(payload["rent_psm_month"])).quantize(Decimal("0.01")) == Decimal(
        "129.17"
    )
