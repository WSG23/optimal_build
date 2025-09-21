"""Unit tests for the rules engine predicate evaluation."""

from __future__ import annotations

from app.core.rules.engine import RuleEngine


def test_rule_engine_produces_explainable_results() -> None:
    """The engine should evaluate predicates and record detailed traces."""

    engine = RuleEngine()
    rules = [
        {
            "id": "height_limit",
            "title": "Maximum tower height",
            "applies_to": ["tower_a", "tower_b"],
            "predicate": {"property": "height_m", "operator": "<=", "value": 24},
            "citations": [
                {"text": "URA Envelope Control 4.2", "url": "https://example.com/ura"}
            ],
        },
        {
            "id": "setback_or_sprinklers",
            "applies_to": ["tower_b"],
            "predicate": {
                "any": [
                    {"property": "front_setback_m", "operator": ">=", "value": 6},
                    {"property": "has_sprinklers", "equals": True},
                ]
            },
            "citations": ["Fire Code 5.1"],
        },
        {
            "id": "site_controls",
            "applies_to": ["site"],
            "predicate": {
                "all": [
                    {
                        "property": "coverage_ratio",
                        "between": {"min": 0.3, "max": 0.5},
                    },
                    {"property": "zoning", "in": ["residential", "mixed"]},
                ]
            },
            "citations": [{"text": "Site Coverage Table"}],
        },
        {
            "id": "no_hazardous_use",
            "applies_to": ["site"],
            "predicate": {"not": {"property": "usage", "equals": "industrial"}},
        },
    ]

    geometries = {
        "tower_a": {"height_m": 22, "front_setback_m": 8, "has_sprinklers": True},
        "tower_b": {"height_m": 26, "front_setback_m": 5, "has_sprinklers": True},
        "site": {
            "coverage_ratio": 0.42,
            "zoning": "residential",
            "usage": "residential",
        },
    }

    outcome = engine.validate(rules, geometries)
    assert outcome["valid"] is False
    assert len(outcome["results"]) == 4

    height_rule = next(item for item in outcome["results"] if item["rule_id"] == "height_limit")
    assert height_rule["passed"] is False
    assert height_rule["offending_geometry_ids"] == ["tower_b"]

    tower_b_eval = next(ev for ev in height_rule["evaluations"] if ev["geometry_id"] == "tower_b")
    assert tower_b_eval["passed"] is False
    assert tower_b_eval["trace"]["type"] == "comparison"
    assert tower_b_eval["trace"]["details"]["actual"] == 26
    assert tower_b_eval["trace"]["details"]["expected"] == 24

    setback_rule = next(
        item for item in outcome["results"] if item["rule_id"] == "setback_or_sprinklers"
    )
    assert setback_rule["passed"] is True
    assert setback_rule["evaluations"][0]["trace"]["type"] == "any"

    coverage_rule = next(
        item for item in outcome["results"] if item["rule_id"] == "site_controls"
    )
    assert coverage_rule["passed"] is True
    coverage_trace = coverage_rule["evaluations"][0]["trace"]
    assert coverage_trace["type"] == "all"
    comparison_details = coverage_trace["children"][0]["details"]
    assert comparison_details["operator"] == "between"
    assert comparison_details["minimum"] == 0.3
    assert comparison_details["maximum"] == 0.5

    hazard_rule = next(
        item for item in outcome["results"] if item["rule_id"] == "no_hazardous_use"
    )
    assert hazard_rule["passed"] is True
    assert hazard_rule["evaluations"][0]["trace"]["type"] == "not"
