from pathlib import Path

from pyproj import Transformer

from backend.scripts import ingest_hk_parcels as hk_parcels

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "hk" / "lots_sample.geojson"
)


def test_iter_geojson_features_streams_fixture():
    features = list(hk_parcels._iter_geojson_features(FIXTURE_PATH))  # noqa: SLF001
    assert len(features) == 2
    assert features[0]["properties"]["LOTCSUID"] == "HKLOT0001"
    assert features[1]["properties"]["LOTCSUID"] == "HKLOT0002"


def test_normalise_feature_projects_geometry():
    transformer = Transformer.from_crs("EPSG:2326", "EPSG:4326", always_xy=True)
    features = list(hk_parcels._iter_geojson_features(FIXTURE_PATH))  # noqa: SLF001

    record = hk_parcels._normalise_feature(  # noqa: SLF001
        features[0], transformer, source_label="unit_test"
    )
    assert record.parcel_ref == "HK:LOT:HKLOT0001"
    assert record.area_m2 == 100.0
    assert record.geometry_feature["geometry"]["type"] == "MultiPolygon"
    assert record.geometry_feature["properties"]["lot_id"] == 123456
    assert record.geometry_feature.get("zone_code") is None

    # Centroid close to transformed midpoint of the square
    expected_lon, expected_lat = transformer.transform(835005.0, 815005.0)
    assert abs(record.centroid_lon - expected_lon) < 1e-6
    assert abs(record.centroid_lat - expected_lat) < 1e-6

    record_with_zone = hk_parcels._normalise_feature(  # noqa: SLF001
        features[1], transformer, source_label="unit_test"
    )
    assert record_with_zone.geometry_feature["zone_code"] == "HK:COMMERCIAL"
    assert record_with_zone.area_m2 == 400.0
