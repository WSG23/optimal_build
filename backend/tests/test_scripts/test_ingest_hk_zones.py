import json
from pathlib import Path

import pytest

from backend.scripts import ingest_hk_zones as hk_zones

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "hk"
    / "regulated_area_sample.geojson"
)


def _load_fixture_feature(index: int = 0):
    with FIXTURE_PATH.open() as handle:
        data = json.load(handle)
    return data["features"][index]


def test_normalise_zone_feature_builds_attributes():
    feature = _load_fixture_feature(0)
    record = hk_zones._normalise_zone_feature(feature)

    assert record.zone_code == "RA/HK/001"
    assert record.geometry_feature["geometry"]["type"] == "MultiPolygon"
    assert record.attributes["name_en"] == "Central District"
    assert (
        record.attributes["download_links"]["geojson"] == "https://example.com/geojson"
    )


def test_normalise_zone_feature_requires_plan_number():
    feature = _load_fixture_feature(1)
    feature["properties"].pop("RA_PLAN_NO", None)
    with pytest.raises(ValueError):
        hk_zones._normalise_zone_feature(feature)
