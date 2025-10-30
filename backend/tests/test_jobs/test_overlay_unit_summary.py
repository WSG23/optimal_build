from app.core.models.geometry import GeometryGraph, Level, Space
import pytest

pytest.importorskip("sqlalchemy")

from app.models.rkp import RefRule
from backend.jobs.overlay_run import (
    RuleContext,
    _build_rule_metrics,
    _evaluate_geometry,
)


def test_evaluate_geometry_emits_unit_overlays():
    level = Level(id="L1", name="Ground Floor")
    spaces = [
        Space(
            id="S1",
            name="Unit A",
            level_id="L1",
            boundary=[(0.0, 0.0), (8.0, 0.0), (8.0, 5.0), (0.0, 5.0)],
            metadata={"category": "residential", "height_m": 50},
        ),
        Space(
            id="S2",
            name="Unit B",
            level_id="L1",
            boundary=[(8.0, 0.0), (15.0, 0.0), (15.0, 4.0), (8.0, 4.0)],
        ),
    ]
    graph = GeometryGraph(levels=[level], spaces=spaces)

    suggestions = _evaluate_geometry(graph)
    summary = {item["code"]: item for item in suggestions}

    unit_overlay_codes = [code for code in summary if code.startswith("unit_space_")]
    assert sorted(unit_overlay_codes) == ["unit_space_S1", "unit_space_S2"]
    assert summary["unit_space_S1"]["props"]["area_sqm"] == 40.0
    assert summary["unit_space_S2"]["props"]["area_sqm"] == 28.0

    aggregate = summary.get("unit_area_summary")
    assert aggregate is not None
    assert aggregate["engine_payload"]["unit_count"] == 2
    assert aggregate["props"]["total_unit_area_sqm"] == 68.0

    rule = RefRule(
        jurisdiction="SG",
        authority="URA",
        topic="zoning",
        parameter_key="zoning.max_building_height_m",
        operator="<=",
        value="30",
        unit="m",
        review_status="approved",
        is_published=True,
        applicability={"zone_code": "SG:residential"},
    )
    rule.id = 101

    metrics = _build_rule_metrics(graph, {})
    context = RuleContext(
        zone_code="SG:residential",
        rules=[rule],
        metrics=metrics,
    )
    suggestions_with_rules = _evaluate_geometry(graph, rule_context=context)
    codes_with_rules = {item["code"] for item in suggestions_with_rules}
    assert "rule_violation_zoning_max_building_height_m" in codes_with_rules
