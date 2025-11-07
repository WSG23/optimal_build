from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.rules.engine import RulesEngine


class DummyGraph:
    def __init__(self, spaces: dict[str, object], levels: dict[str, object]):
        self.spaces = spaces
        self.levels = levels
        self.walls: dict[str, object] = {}
        self.doors: dict[str, object] = {}
        self.fixtures: dict[str, object] = {}


def _make_space(**kwargs):
    defaults = {
        "id": "S1",
        "name": "Atrium",
        "height": 3.2,
        "level_id": "L1",
        "metadata": {"usage": "residential", "include": True, "reference_height": 3.2},
        "boundary": [(0, 0), (0, 4), (4, 4), (4, 0)],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_rules_engine_evaluates_complex_predicates():
    primary = _make_space()
    secondary = _make_space(
        id="S2",
        name="Lobby",
        height=4.0,
        metadata={"usage": "commercial", "include": False, "reference_height": 4.0},
        boundary=[(0, 0), (0, 3), (3, 3), (3, 0)],
    )
    graph = DummyGraph(
        spaces={"S1": primary, "S2": secondary},
        levels={"L1": {"metadata": {"min_perimeter": 16}}},
    )
    pack = {
        "rules": [
            {
                "id": "HEIGHT_OR_USAGE",
                "target": "spaces",
                "where": {"field": "metadata.include", "operator": "==", "value": True},
                "predicate": {
                    "any": [
                        {
                            "field": "height",
                            "operator": ">=",
                            "value": 3.5,
                            "message": "Height must exceed 3.5m",
                        },
                        {
                            "not": {
                                "field": "metadata.usage",
                                "operator": "==",
                                "value": "residential",
                            }
                        },
                    ],
                    "message": "Space failed height/usage criteria",
                },
            },
            {
                "id": "COMPUTED_LIMITS",
                "target": "spaces",
                "where": {"field": "metadata.include", "operator": "==", "value": True},
                "predicate": {
                    "all": [
                        {"field": "computed.area", "operator": ">", "value": 10},
                        {
                            "field": "height",
                            "operator": "==",
                            "value_field": "metadata.reference_height",
                        },
                        {
                            "field": "computed.perimeter",
                            "operator": ">=",
                            "value_path": "graph.levels.L1.metadata.min_perimeter",
                        },
                    ]
                },
            },
        ]
    }
    engine = RulesEngine(pack)
    outcome = engine.evaluate(graph)
    assert outcome["summary"]["total_rules"] == 2
    assert outcome["summary"]["violations"] == 1
    first_rule = outcome["results"][0]
    assert first_rule["checked"] == 1  # secondary space filtered by where clause
    assert first_rule["violations"][0]["attributes"]["name"] == "Atrium"


def test_rules_engine_private_helpers_cover_iterables_and_geometry():
    engine = RulesEngine({"rules": []})
    graph = DummyGraph(spaces={}, levels={})
    with pytest.raises(ValueError):
        list(engine._iter_target_entities(graph, "unknown"))

    passed, _, _, reason = engine._apply_operator("in", "A", ["A", "B"])
    assert passed is True
    failure = engine._apply_operator("in", "A", None)
    assert failure[0] is False and "container" in (failure[3] or "")
    contains = engine._apply_operator("contains", ["A", "B"], "B")
    assert contains[0] is True
    not_contains = engine._apply_operator("not_contains", ["A"], "B")
    assert not_contains[0] is True
    truthy = engine._apply_operator("is_truthy", 1, None)
    assert truthy[0] is True

    polygon = SimpleNamespace(boundary=[(0, 0), (0, 2), (2, 2), (2, 0)])
    assert engine._space_area(polygon) == pytest.approx(4.0)
    assert engine._space_perimeter(polygon) == pytest.approx(8.0)
