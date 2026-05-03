from __future__ import annotations

import pytest

from app.models.rkp import RefRule, RefZoningLayer
from app.services.rules.zone_rules import get_zoning_rules_for_zone


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
async def test_get_zoning_rules_for_zone_exposes_configured_industrial_sources(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        result = await get_zoning_rules_for_zone(session, "B1")

    assert result.rule_corpus_status is not None
    assert result.rule_corpus_status["zone_code"] == "SG:industrial"
    source_gaps = result.rule_corpus_status["official_source_gaps"]
    height_gap = next(
        gap for gap in source_gaps if gap["field"] == "building_height_limit_m"
    )
    height_source = height_gap["candidate_sources"][0]
    assert height_source["authority"] == "URA"
    assert height_source["configured_values_by_zone"] == {"SG:industrial": "80"}
    assert height_source["unit"] == "m"
    setbacks_gap = next(gap for gap in source_gaps if gap["field"] == "setbacks")
    setbacks_source = setbacks_gap["candidate_sources"][0]
    assert setbacks_source["authority"] == "URA"
    assert setbacks_source["configured_values_by_zone"] == {
        "SG:industrial": {
            "front": "7.5",
            "rear": "7.5",
            "side": "3",
        }
    }
    assert setbacks_source["unit"] == "m"
