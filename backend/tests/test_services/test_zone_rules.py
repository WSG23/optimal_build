from __future__ import annotations

import pytest

from app.models.rkp import RefRule
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
