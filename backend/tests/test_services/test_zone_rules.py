from __future__ import annotations

import pytest

from app.models.rkp import RefBuildingFootprint, RefParcel, RefRule, RefZoningLayer
from app.services.rules.zone_rules import (
    classify_site_development_for_parcel,
    find_dominant_zoning_layer_for_parcel,
    find_nearest_parcel_for_point,
    find_parcel_for_point,
    find_zoning_layer_for_point,
    get_zoning_rules_for_zone,
)


@pytest.mark.asyncio
async def test_get_zoning_rules_for_zone_extracts_deeper_controls(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        defaults = {
            "jurisdiction": "SG",
            "authority": "URA",
            "topic": "zoning",
            "operator": "<=",
            "applicability": {"zone_code": "SG:test_controls"},
            "review_status": "approved",
            "is_published": True,
        }
        session.add_all(
            [
                RefRule(parameter_key="zoning.max_far", value="3.5", **defaults),
                RefRule(
                    parameter_key="zoning.max_building_height_m",
                    value="36",
                    unit="m",
                    **defaults,
                ),
                RefRule(
                    parameter_key="zoning.site_coverage.max_percent",
                    value="55",
                    unit="%",
                    **defaults,
                ),
                RefRule(
                    parameter_key="zoning.setback.front_min_m",
                    value="7.5",
                    unit="m",
                    **defaults,
                ),
                RefRule(
                    parameter_key="zoning.setback.side_min_m",
                    value="3",
                    unit="m",
                    **defaults,
                ),
                RefRule(
                    parameter_key="zoning.stepback.level_6_depth_m",
                    value="4",
                    unit="m",
                    applicability={"zone_code": "SG:test_controls", "level": 6},
                    **{
                        key: value
                        for key, value in defaults.items()
                        if key != "applicability"
                    },
                ),
                RefRule(
                    parameter_key="zoning.air_rights.note",
                    value="Subject to aviation height review.",
                    operator="=",
                    **{
                        key: value
                        for key, value in defaults.items()
                        if key != "operator"
                    },
                ),
            ]
        )
        await session.flush()

        result = await get_zoning_rules_for_zone(session, "test_controls")

    assert result.has_data is True
    assert result.plot_ratio == 3.5
    assert result.building_height_limit_m == 36
    assert result.site_coverage_pct == 55
    assert result.setback_front_m == 7.5
    assert result.setback_side_m == 3
    assert result.setback_rear_m is None
    assert result.step_backs == [{"level": 6.0, "depth_m": 4.0}]
    assert result.air_rights_note == "Subject to aviation height review."
    assert result.rule_corpus_status is not None
    assert result.rule_corpus_status["resolved_by"]["setbacks"] == "ref_rule"


@pytest.mark.asyncio
async def test_get_zoning_rules_for_zone_uses_singapore_zoning_layer_gpr(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        layer = RefZoningLayer(
            jurisdiction="SG",
            layer_name="MasterPlan2019",
            zone_code="SG:mixed_use",
            attributes={
                "LU_DESC": "Mixed Use",
                "GPR": "3.2",
                "height_m": "80",
            },
        )
        session.add(layer)
        await session.flush()

        result = await get_zoning_rules_for_zone(session, "mixed_use")

    assert result.has_data is True
    assert result.plot_ratio == 3.2
    assert result.building_height_limit_m == 80
    assert result.zone_description == "Mixed Use"
    assert result.source_reference == "SG Rule Registry (RefRule + zoning layers)"
    assert result.rule_corpus_status is not None
    assert result.rule_corpus_status["coverage_state"] == "partial"
    assert result.rule_corpus_status["counts"]["zoning_layers"] == 1
    assert result.rule_corpus_status["resolved_by"] == {
        "land_use": "ref_zoning_layer",
        "plot_ratio": "ref_zoning_layer",
        "building_height_limit_m": "ref_zoning_layer",
    }
    source_gaps = result.rule_corpus_status["official_source_gaps"]
    assert any(gap["field"] == "setbacks" for gap in source_gaps)


@pytest.mark.asyncio
async def test_get_zoning_rules_for_zone_surfaces_ura_eva_intensity_control(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        layer = RefZoningLayer(
            jurisdiction="SG",
            layer_name="MasterPlan2019",
            zone_code="SG:mixed_use",
            attributes={
                "LU_DESC": "White",
                "GPR": "EVA",
            },
        )
        session.add(layer)
        await session.flush()

        result = await get_zoning_rules_for_zone(session, "mixed_use")

    assert result.has_data is False
    assert result.plot_ratio is None
    assert result.zone_description == "White"
    assert result.rule_corpus_status is not None
    intensity_control = result.rule_corpus_status["zoning_layer_intensity_control"]
    assert intensity_control == {
        "field": "GPR",
        "raw_value": "EVA",
        "status": "envelope_control_area",
        "reason": (
            "URA Master Plan records this site with envelope controls instead of "
            "a numeric GPR."
        ),
    }
    plot_ratio_gap = next(
        gap
        for gap in result.rule_corpus_status["official_source_gaps"]
        if gap["field"] == "plot_ratio"
    )
    assert plot_ratio_gap["reason"] == (
        "envelope_control_area_requires_site_specific_controls"
    )
    assert plot_ratio_gap["source_value"] == "EVA"
    assert plot_ratio_gap["review_note"] == intensity_control["reason"]


@pytest.mark.asyncio
async def test_find_zoning_layer_for_point_uses_imported_geojson_bounds(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        session.add(
            RefZoningLayer(
                jurisdiction="SG",
                layer_name="MasterPlanImported",
                zone_code="SG:residential",
                bounds_json={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [103.80, 1.20],
                            [103.90, 1.20],
                            [103.90, 1.30],
                            [103.80, 1.30],
                            [103.80, 1.20],
                        ]
                    ],
                },
                attributes={"LU_DESC": "Residential", "GPR": "2.8"},
            )
        )
        await session.flush()

        layer = await find_zoning_layer_for_point(
            session,
            latitude=1.25,
            longitude=103.85,
            jurisdiction="SG",
        )
        outside = await find_zoning_layer_for_point(
            session,
            latitude=1.35,
            longitude=103.85,
            jurisdiction="SG",
        )

    assert layer is not None
    assert layer.zone_code == "SG:residential"
    assert outside is None


@pytest.mark.asyncio
async def test_find_parcel_for_point_uses_imported_geojson_bounds(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        session.add(
            RefParcel(
                jurisdiction="SG",
                parcel_ref="SG:LOT:MK01-00001",
                bounds_json={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [103.80, 1.20],
                            [103.90, 1.20],
                            [103.90, 1.30],
                            [103.80, 1.30],
                            [103.80, 1.20],
                        ]
                    ],
                },
                centroid_lat=1.25,
                centroid_lon=103.85,
                area_m2=4321.0,
                source="sla_onemap",
            )
        )
        await session.flush()

        parcel = await find_parcel_for_point(
            session,
            latitude=1.25,
            longitude=103.85,
            jurisdiction="SG",
        )
        outside = await find_parcel_for_point(
            session,
            latitude=1.35,
            longitude=103.85,
            jurisdiction="SG",
        )

    assert parcel is not None
    assert parcel.parcel_ref == "SG:LOT:MK01-00001"
    assert float(parcel.area_m2) == pytest.approx(4321.0)
    assert outside is None


@pytest.mark.asyncio
async def test_find_nearest_parcel_for_point_recovers_nearby_geocoder_offset(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        session.add(
            RefParcel(
                jurisdiction="SG",
                parcel_ref="SG:LOT:MK01-NEAR",
                bounds_json={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [103.8000, 1.2000],
                            [103.8002, 1.2000],
                            [103.8002, 1.2002],
                            [103.8000, 1.2002],
                            [103.8000, 1.2000],
                        ]
                    ],
                },
                centroid_lat=1.2001,
                centroid_lon=103.8001,
                area_m2=500.0,
                source="sla_onemap",
            )
        )
        await session.flush()

        near = await find_nearest_parcel_for_point(
            session,
            latitude=1.2001,
            longitude=103.80035,
            jurisdiction="SG",
            max_distance_m=25,
        )
        far = await find_nearest_parcel_for_point(
            session,
            latitude=1.2001,
            longitude=103.8010,
            jurisdiction="SG",
            max_distance_m=25,
        )

    assert near is not None
    assert near.parcel_ref == "SG:LOT:MK01-NEAR"
    assert far is None


@pytest.mark.asyncio
async def test_find_dominant_zoning_layer_for_parcel_uses_largest_overlap(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        parcel = RefParcel(
            jurisdiction="SG",
            parcel_ref="SG:LOT:MK01-00002",
            bounds_json={
                "type": "Polygon",
                "coordinates": [
                    [
                        [103.80, 1.20],
                        [103.90, 1.20],
                        [103.90, 1.30],
                        [103.80, 1.30],
                        [103.80, 1.20],
                    ]
                ],
            },
            centroid_lat=1.25,
            centroid_lon=103.85,
            area_m2=4321.0,
            source="sla_onemap",
        )
        road_sliver = RefZoningLayer(
            jurisdiction="SG",
            layer_name="MasterPlanImported",
            zone_code="SG:road",
            bounds_json={
                "type": "Polygon",
                "coordinates": [
                    [
                        [103.80, 1.20],
                        [103.815, 1.20],
                        [103.815, 1.30],
                        [103.80, 1.30],
                        [103.80, 1.20],
                    ]
                ],
            },
            attributes={"LU_DESC": "Road", "GPR": "NA"},
        )
        commercial_majority = RefZoningLayer(
            jurisdiction="SG",
            layer_name="MasterPlanImported",
            zone_code="SG:commercial",
            bounds_json={
                "type": "Polygon",
                "coordinates": [
                    [
                        [103.815, 1.20],
                        [103.90, 1.20],
                        [103.90, 1.30],
                        [103.815, 1.30],
                        [103.815, 1.20],
                    ]
                ],
            },
            attributes={"LU_DESC": "Commercial", "GPR": "4.2"},
        )
        session.add_all([parcel, road_sliver, commercial_majority])
        await session.flush()

        resolution = await find_dominant_zoning_layer_for_parcel(
            session,
            parcel,
            jurisdiction="SG",
        )

    assert resolution.layer is not None
    assert resolution.layer.zone_code == "SG:commercial"
    assert resolution.source == "parcel_dominant_zoning"
    assert resolution.overlap_ratio == pytest.approx(0.85)


@pytest.mark.asyncio
async def test_classify_site_development_for_parcel_uses_building_footprints(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        parcel = RefParcel(
            jurisdiction="SG",
            parcel_ref="SG:LOT:MK01-00001",
            bounds_json={
                "type": "Polygon",
                "coordinates": [
                    [
                        [103.80, 1.20],
                        [103.90, 1.20],
                        [103.90, 1.30],
                        [103.80, 1.30],
                        [103.80, 1.20],
                    ]
                ],
            },
            centroid_lat=1.25,
            centroid_lon=103.85,
            area_m2=4321.0,
            source="sla_onemap",
        )
        session.add_all(
            [
                parcel,
                RefBuildingFootprint(
                    jurisdiction="SG",
                    layer_name="MasterPlanBuilding",
                    footprint_ref="SG:BUILDING:1",
                    bounds_json={
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [103.82, 1.22],
                                [103.84, 1.22],
                                [103.84, 1.24],
                                [103.82, 1.24],
                                [103.82, 1.22],
                            ]
                        ],
                    },
                    centroid_lat=1.23,
                    centroid_lon=103.83,
                    area_m2=900.0,
                    source="ura_data_gov",
                ),
            ]
        )
        await session.flush()

        result = await classify_site_development_for_parcel(session, parcel)

    assert result.status == "developed"
    assert result.building_count == 1
    assert result.footprint_area_sqm == pytest.approx(900.0)


@pytest.mark.asyncio
async def test_classify_site_development_is_uncertain_when_footprint_coverage_sparse(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        parcel = RefParcel(
            jurisdiction="SG",
            parcel_ref="SG:LOT:MK18-BURGHLEY",
            bounds_json={
                "type": "Polygon",
                "coordinates": [
                    [
                        [103.8610, 1.3588],
                        [103.8613, 1.3588],
                        [103.8613, 1.3591],
                        [103.8610, 1.3591],
                        [103.8610, 1.3588],
                    ]
                ],
            },
            centroid_lat=1.35895,
            centroid_lon=103.86115,
            area_m2=300.0,
            source="sla_onemap",
        )
        session.add_all(
            [
                parcel,
                RefBuildingFootprint(
                    jurisdiction="SG",
                    layer_name="MasterPlanBuilding",
                    footprint_ref="SG:BUILDING:DISTANT",
                    bounds_json={
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [103.8578, 1.3623],
                                [103.8580, 1.3623],
                                [103.8580, 1.3625],
                                [103.8578, 1.3625],
                                [103.8578, 1.3623],
                            ]
                        ],
                    },
                    centroid_lat=1.3624,
                    centroid_lon=103.8579,
                    area_m2=1200.0,
                    source="ura_data_gov",
                ),
            ]
        )
        await session.flush()

        result = await classify_site_development_for_parcel(session, parcel)

    assert result.status == "uncertain"
    assert result.building_count == 0
    assert result.reason == "building_footprint_coverage_sparse_near_parcel"


@pytest.mark.asyncio
async def test_classify_site_development_reports_vacant_only_with_nearby_coverage(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        parcel = RefParcel(
            jurisdiction="SG",
            parcel_ref="SG:LOT:MK01-VACANT",
            bounds_json={
                "type": "Polygon",
                "coordinates": [
                    [
                        [103.8000, 1.2000],
                        [103.8010, 1.2000],
                        [103.8010, 1.2010],
                        [103.8000, 1.2010],
                        [103.8000, 1.2000],
                    ]
                ],
            },
            centroid_lat=1.2005,
            centroid_lon=103.8005,
            area_m2=900.0,
            source="sla_onemap",
        )
        nearby_footprints = [
            RefBuildingFootprint(
                jurisdiction="SG",
                layer_name="MasterPlanBuilding",
                footprint_ref=f"SG:BUILDING:NEARBY:{index}",
                bounds_json={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [103.8015 + index * 0.0001, 1.2002],
                            [103.8016 + index * 0.0001, 1.2002],
                            [103.8016 + index * 0.0001, 1.2003],
                            [103.8015 + index * 0.0001, 1.2003],
                            [103.8015 + index * 0.0001, 1.2002],
                        ]
                    ],
                },
                centroid_lat=1.20025,
                centroid_lon=103.80155 + index * 0.0001,
                area_m2=150.0,
                source="ura_data_gov",
            )
            for index in range(3)
        ]
        session.add_all([parcel, *nearby_footprints])
        await session.flush()

        result = await classify_site_development_for_parcel(session, parcel)

    assert result.status == "vacant"
    assert result.building_count == 0
    assert result.reason == "no_footprint_intersects_parcel"


@pytest.mark.asyncio
async def test_find_zoning_layer_for_point_supports_multipolygon_bounds(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        session.add(
            RefZoningLayer(
                jurisdiction="SG",
                layer_name="MasterPlanImported",
                zone_code="SG:commercial",
                bounds_json={
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [103.70, 1.20],
                                [103.72, 1.20],
                                [103.72, 1.22],
                                [103.70, 1.22],
                                [103.70, 1.20],
                            ]
                        ],
                        [
                            [
                                [103.80, 1.28],
                                [103.82, 1.28],
                                [103.82, 1.30],
                                [103.80, 1.30],
                                [103.80, 1.28],
                            ]
                        ],
                    ],
                },
                attributes={"LU_DESC": "Commercial", "GPR": "4.0"},
            )
        )
        await session.flush()

        layer = await find_zoning_layer_for_point(
            session,
            latitude=1.29,
            longitude=103.81,
            jurisdiction="SG",
        )
        outside = await find_zoning_layer_for_point(
            session,
            latitude=1.25,
            longitude=103.81,
            jurisdiction="SG",
        )

    assert layer is not None
    assert layer.zone_code == "SG:commercial"
    assert outside is None


@pytest.mark.asyncio
async def test_get_zoning_rules_for_zone_can_prefer_point_resolved_layer(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        commercial = RefZoningLayer(
            jurisdiction="SG",
            layer_name="GenericCommercial",
            zone_code="SG:commercial",
            attributes={"LU_DESC": "Commercial", "GPR": "4.0"},
        )
        residential = RefZoningLayer(
            jurisdiction="SG",
            layer_name="PointResolvedResidential",
            zone_code="SG:residential",
            attributes={"LU_DESC": "Residential", "GPR": "2.1"},
        )
        session.add_all([commercial, residential])
        await session.flush()

        result = await get_zoning_rules_for_zone(
            session,
            "SG:residential",
            preferred_zoning_layer=residential,
        )

    assert result.zone_code == "SG:residential"
    assert result.zone_description == "Residential"
    assert result.plot_ratio == 2.1
    assert result.rule_corpus_status is not None
    assert result.rule_corpus_status["applied_zoning_layer_id"] == residential.id


@pytest.mark.asyncio
async def test_get_zoning_rules_for_zone_uses_zoning_layer_deeper_controls(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        layer = RefZoningLayer(
            jurisdiction="SG",
            layer_name="CapturedURAControls",
            zone_code="SG:commercial",
            attributes={
                "LU_DESC": "Commercial",
                "GPR": "4.2",
                "setbacks": {"front": "6", "rear": "4.5", "side": "3"},
                "stepBacks": [
                    {"level": "8", "depthM": "5"},
                    {"storey": "12", "depth_m": "7.5"},
                ],
            },
        )
        session.add(layer)
        await session.flush()

        result = await get_zoning_rules_for_zone(session, "commercial")

    assert result.plot_ratio == 4.2
    assert result.setback_front_m == 6
    assert result.setback_rear_m == 4.5
    assert result.setback_side_m == 3
    assert result.step_backs == [
        {"level": 8.0, "depth_m": 5.0},
        {"level": 12.0, "depth_m": 7.5},
    ]
    assert result.rule_corpus_status is not None
    assert result.rule_corpus_status["resolved_by"]["setbacks"] == "ref_zoning_layer"
    assert result.rule_corpus_status["resolved_by"]["step_backs"] == "ref_zoning_layer"
    assert "setbacks" not in result.rule_corpus_status["unresolved_fields"]
    assert "step_backs" not in result.rule_corpus_status["unresolved_fields"]
    source_gap_fields = {
        gap["field"] for gap in result.rule_corpus_status["official_source_gaps"]
    }
    assert "setbacks" not in source_gap_fields
    assert "step_backs" not in source_gap_fields


@pytest.mark.asyncio
async def test_get_zoning_rules_for_zone_reads_building_topic_site_coverage(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        session.add(
            RefRule(
                jurisdiction="SG",
                authority="URA",
                topic="building",
                parameter_key="zoning.site_coverage.max_percent",
                operator="<=",
                value="45",
                unit="%",
                applicability={"zone_code": "SG:mixed_use"},
                review_status="approved",
                is_published=True,
            )
        )
        await session.flush()

        result = await get_zoning_rules_for_zone(session, "mixed_use")

    assert result.site_coverage_pct == 45
    assert result.rule_corpus_status is not None
    assert result.rule_corpus_status["resolved_by"]["site_coverage_pct"] == "ref_rule"


@pytest.mark.asyncio
async def test_get_zoning_rules_for_zone_resolves_configured_industrial_sources(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        result = await get_zoning_rules_for_zone(session, "B1")

    assert result.rule_corpus_status is not None
    assert result.rule_corpus_status["zone_code"] == "SG:industrial"
    assert result.building_height_limit_m == 80
    assert result.setback_front_m == 7.5
    assert result.setback_rear_m == 7.5
    assert result.setback_side_m == 3
    assert result.step_backs == [{"level": 8.0, "depth_m": 5.0}]
    assert result.rule_corpus_status["resolved_by"]["building_height_limit_m"] == (
        "official_source_registry"
    )
    assert result.rule_corpus_status["resolved_by"]["setbacks"] == (
        "official_source_registry"
    )
    assert result.rule_corpus_status["resolved_by"]["step_backs"] == (
        "official_source_registry"
    )
    assert (
        "building_height_limit_m" not in result.rule_corpus_status["unresolved_fields"]
    )
    assert "setbacks" not in result.rule_corpus_status["unresolved_fields"]
    assert "step_backs" not in result.rule_corpus_status["unresolved_fields"]
    source_gaps = result.rule_corpus_status["official_source_gaps"]
    assert "building_height_limit_m" not in {gap["field"] for gap in source_gaps}
    assert "setbacks" not in {gap["field"] for gap in source_gaps}
    assert "step_backs" not in {gap["field"] for gap in source_gaps}
    air_rights_gap = next(
        gap for gap in source_gaps if gap["field"] == "air_rights_note"
    )
    assert air_rights_gap["reason"] == "project_specific_clearance_required"
    assert result.rule_corpus_status["project_clearance_required"] == [air_rights_gap]
    air_rights_source = air_rights_gap["candidate_sources"][0]
    assert air_rights_source["authority"] == "URA/CAAS"
    assert air_rights_source["resolution_workflow"] == "project_specific_clearance"
    assert "site-specific aviation" in air_rights_source["review_note"]


@pytest.mark.asyncio
async def test_get_zoning_rules_for_zone_resolves_configured_commercial_deeper_controls(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        result = await get_zoning_rules_for_zone(session, "C1")

    assert result.rule_corpus_status is not None
    assert result.rule_corpus_status["zone_code"] == "SG:commercial"
    assert result.setback_front_m == 7.5
    assert result.setback_rear_m == 7.5
    assert result.setback_side_m == 3
    assert result.step_backs == [{"level": 8.0, "depth_m": 5.0}]
    assert result.rule_corpus_status["resolved_by"]["setbacks"] == (
        "official_source_registry"
    )
    assert result.rule_corpus_status["resolved_by"]["step_backs"] == (
        "official_source_registry"
    )
    assert "setbacks" not in result.rule_corpus_status["unresolved_fields"]
    assert "step_backs" not in result.rule_corpus_status["unresolved_fields"]
    source_gap_fields = {
        gap["field"] for gap in result.rule_corpus_status["official_source_gaps"]
    }
    assert "setbacks" not in source_gap_fields
    assert "step_backs" not in source_gap_fields
