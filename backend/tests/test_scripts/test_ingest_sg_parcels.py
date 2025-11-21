from __future__ import annotations

from pyproj import Transformer

from backend.scripts import ingest_sg_parcels as sg_parcels


def test_resolve_lot_identifier_prefers_named_fields() -> None:
    props = {"LOT_NO": "MK01-12345A", "OBJECTID": 77, "LOT_ID": "fallback"}
    assert sg_parcels._resolve_lot_identifier(props) == "MK01-12345A"  # type: ignore[attr-defined]


def test_normalise_feature_creates_parcel_record() -> None:
    transformer = Transformer.from_crs(
        "EPSG:4326", "EPSG:4326", always_xy=True
    )  # identity for test
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [103.8, 1.28],
                    [103.8, 1.29],
                    [103.81, 1.29],
                    [103.81, 1.28],
                    [103.8, 1.28],
                ]
            ],
        },
        "properties": {
            "LOT_NO": "MK01-99999X",
            "MK_TS_NO": "MK01",
            "TENURE": "Freehold",
        },
    }

    record = sg_parcels._normalise_feature(  # type: ignore[attr-defined]
        feature,
        transformer,
        source_label="test",
    )

    assert record.parcel_ref == "SG:LOT:MK01-99999X"
    assert record.source_label == "test"
    assert record.geometry_feature["properties"]["lot_no"] == "MK01-99999X"
