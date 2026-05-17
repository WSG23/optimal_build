from __future__ import annotations

import json

import pytest
from backend.scripts import ingest_sg_zones as sg_zones


def test_sg_zone_code_normalisation_maps_master_plan_land_uses() -> None:
    assert sg_zones._normalise_zone_code("Residential") == "SG:residential"
    assert sg_zones._normalise_zone_code("Commercial") == "SG:commercial"
    assert sg_zones._normalise_zone_code("Business 1") == "SG:business_1"
    assert sg_zones._normalise_zone_code("Business Park") == "SG:business_park"
    assert sg_zones._normalise_zone_code("White") == "SG:mixed_use"


def test_sg_zone_feature_normalisation_extracts_land_use_and_gpr() -> None:
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [103.80, 1.28],
                    [103.81, 1.28],
                    [103.81, 1.29],
                    [103.80, 1.29],
                    [103.80, 1.28],
                ]
            ],
        },
        "properties": {"LU_DESC": "Residential", "GPR": "2.8"},
    }

    record = sg_zones._normalise_zone_feature(feature)

    assert record.zone_code == "SG:residential"
    assert record.attributes["LU_DESC"] == "Residential"
    assert record.attributes["GPR"] == "2.8"
    assert record.geometry_feature["properties"]["zone_code"] == "SG:residential"
    assert record.geometry_feature["geometry"]["type"] == "MultiPolygon"


def test_sg_description_html_attributes_are_parsed() -> None:
    description = """
    <table>
      <tr><th>LU_DESC</th><td>Commercial</td></tr>
      <tr><th>GPR</th><td>4.2</td></tr>
    </table>
    """

    attrs = sg_zones._extract_description_attributes(description)

    assert attrs == {"LU_DESC": "Commercial", "GPR": "4.2"}


@pytest.mark.asyncio
async def test_sg_zone_ingestion_reads_local_geojson_without_persisting(
    tmp_path,
) -> None:
    input_path = tmp_path / "master_plan_land_use.geojson"
    input_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [103.80, 1.28],
                                    [103.81, 1.28],
                                    [103.81, 1.29],
                                    [103.80, 1.29],
                                    [103.80, 1.28],
                                ]
                            ],
                        },
                        "properties": {"LU_DESC": "Commercial", "GPR": "4.0"},
                    },
                    {
                        "type": "Feature",
                        "geometry": None,
                        "properties": {"LU_DESC": "Residential"},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = await sg_zones.ingest_sg_zones(
        sg_zones.SGZoneIngestionOptions(
            input_path=input_path,
            output_path=tmp_path / "unused.geojson",
            layer_name="test_layer",
            max_features=None,
            persist=False,
            reset_layer=True,
            download=False,
        )
    )

    assert result["status"] == "success"
    assert result["processed_records"] == 2
    assert result["persisted_records"] == 0
    assert result["skipped_records"] == 1
    assert result["layer_name"] == "test_layer"
