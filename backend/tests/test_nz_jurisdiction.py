"""Tests for New Zealand jurisdiction configuration and ingestion scripts."""

from decimal import Decimal

from app.core.config import Settings
from app.services.jurisdictions import get_jurisdiction_config

from app.api.v1.developers import (
    DeveloperAssetOptimization,
    DeveloperGPSLogRequest,
    _build_finance_asset_mix_inputs,
)
from backend.scripts import ingest_nz_zones as nz_ingest


def test_nz_config_defaults(monkeypatch):
    """Test NZ_LINZ_API_KEY defaults to 'public' when not set."""
    monkeypatch.setenv("SECRET_KEY", "test-key")
    monkeypatch.delenv("NZ_LINZ_API_KEY", raising=False)
    settings = Settings()
    assert settings.NZ_LINZ_API_KEY == "public"


def test_should_transform_detection_uses_declared_crs():
    """Test CRS detection uses declared CRS metadata when available."""
    geojson = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [174.76, -36.84]},
                "properties": {},
            }
        ],
    }

    needs_transform, reason = nz_ingest._should_transform_to_wgs84(geojson)
    assert needs_transform is False
    assert "4326" in reason


def test_should_transform_detects_nztm_grid():
    """Test CRS detection identifies NZTM coordinates needing transformation."""
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [1754467.0, 5915969.0],  # NZTM coordinates
                },
                "properties": {},
            }
        ],
    }

    needs_transform, reason = nz_ingest._should_transform_to_wgs84(geojson)
    assert needs_transform is True
    assert reason in {"sample_outside_wgs84_range", "declared_crs=EPSG:2193"}


def test_jurisdiction_config_exposes_nz_defaults():
    """Test NZ jurisdiction config returns correct currency and units."""
    config = get_jurisdiction_config("nz")
    assert config.currency_code == "NZD"
    assert config.currency_symbol == "NZ$"
    assert config.area_units == "sqm"


def test_developer_gps_request_normalises_jurisdiction_code():
    """Test DeveloperGPSLogRequest normalizes 'nz' to 'NZ'."""
    request = DeveloperGPSLogRequest(
        latitude=-36.84,
        longitude=174.76,
        development_scenarios=None,
        jurisdiction_code="nz",
    )
    assert request.jurisdiction_code == "NZ"


def test_finance_asset_mix_inputs_nz_uses_sqm():
    """Test NZ jurisdiction uses sqm (no unit conversion from internal sqm)."""
    optimization = DeveloperAssetOptimization(
        asset_type="office",
        allocation_pct=60.0,
        nia_sqm=1000.0,
        rent_psm_month=33.0,
        notes=[],
        constraint_violations=[],
    )

    payload = _build_finance_asset_mix_inputs([optimization], jurisdiction_code="NZ")[0]

    # NZ uses sqm internally, so no conversion needed
    assert Decimal(str(payload["nia_sqm"])).quantize(Decimal("0.01")) == Decimal(
        "1000.00"
    )
    assert Decimal(str(payload["rent_psm_month"])).quantize(Decimal("0.01")) == Decimal(
        "33.00"
    )


def test_nz_market_data_loaded():
    """Test NZ market data is properly loaded from jurisdictions.json."""
    config = get_jurisdiction_config("NZ")

    # Verify market data structure
    assert "rent_psm_month" in config.market_data
    assert "office" in config.market_data["rent_psm_month"]
    assert config.market_data["rent_psm_month"]["office"] == 33.0

    assert "vacancy_rates_pct" in config.market_data
    assert config.market_data["vacancy_rates_pct"]["office"] == 12.0

    assert "finance_assumptions" in config.market_data
    assert (
        config.market_data["finance_assumptions"]["construction_loan_rate_pct"] == 6.3
    )
