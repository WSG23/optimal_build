from __future__ import annotations

from backend.scripts import ingest_sg_building_footprints as sg_buildings


def test_normalise_building_feature_creates_footprint_record() -> None:
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
            "OBJECTID": 123,
            "BLDG_TYPE": 1,
            "SHAPE.AREA": 500.0,
        },
    }

    record = sg_buildings._normalise_feature(
        feature,
        source_label="test",
    )

    assert record.footprint_ref == "SG:BUILDING:123"
    assert record.area_m2 == 500.0
    assert record.attributes["source_dataset_id"] == (
        sg_buildings.SG_MASTER_PLAN_2019_BUILDING_DATASET_ID
    )
    assert record.geometry_feature["properties"]["footprint_ref"] == ("SG:BUILDING:123")


def test_parser_defaults_to_data_gov_building_source() -> None:
    parser = sg_buildings._build_arg_parser()
    args = parser.parse_args([])

    assert args.source_label == "ura_data_gov"
    assert args.download is False
