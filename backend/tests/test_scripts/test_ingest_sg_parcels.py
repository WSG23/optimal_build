from __future__ import annotations

from backend.scripts import ingest_sg_parcels as sg_parcels
from pyproj import Transformer


def test_resolve_lot_identifier_prefers_named_fields() -> None:
    props = {"LOT_NO": "MK01-12345A", "OBJECTID": 77, "LOT_ID": "fallback"}
    assert sg_parcels._resolve_lot_identifier(props) == "MK01-12345A"


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

    record = sg_parcels._normalise_feature(
        feature,
        transformer,
        source_label="test",
    )

    assert record.parcel_ref == "SG:LOT:MK01-99999X"
    assert record.source_label == "test"
    assert record.geometry_feature["properties"]["lot_no"] == "MK01-99999X"


def test_parser_defaults_to_data_gov_wgs84_source() -> None:
    parser = sg_parcels._build_arg_parser()
    args = parser.parse_args([])

    assert args.source_epsg == 4326
    assert args.source_label == "sla_data_gov"
    assert args.download is False
