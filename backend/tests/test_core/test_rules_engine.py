import pytest

from app.core.models.geometry import Door, GeometryGraph, Level, Space
from app.core.rules.engine import RulesEngine

RULE_PACK = {
    "metadata": {"jurisdiction": "SG", "version": 1},
    "rules": [
        {
            "id": "min-bedroom-area",
            "title": "Bedrooms must be at least 10 square metres",
            "target": "spaces",
            "where": {
                "all": [
                    {
                        "field": "metadata.category",
                        "operator": "==",
                        "value": "bedroom",
                    },
                    {"field": "level_id", "operator": "==", "value": "L1"},
                ]
            },
            "predicate": {
                "field": "computed.area",
                "operator": ">=",
                "value": 10.0,
                "message": "Bedroom area below minimum requirement",
            },
            "citation": {"code": "RES-12.4", "section": "4.2"},
        },
        {
            "id": "bedroom-ventilation",
            "title": "Bedrooms require natural light or mechanical ventilation",
            "target": "spaces",
            "where": {
                "field": "metadata.category",
                "operator": "==",
                "value": "bedroom",
            },
            "predicate": {
                "any": [
                    {"field": "metadata.window_count", "operator": ">=", "value": 1},
                    {
                        "field": "metadata.has_mechanical_ventilation",
                        "operator": "==",
                        "value": True,
                    },
                ],
                "message": "Bedroom must provide a window or mechanical ventilation",
            },
            "citation": {"code": "RES-12.4", "section": "4.3"},
        },
        {
            "id": "door-clearance",
            "title": "Doors must be at least one metre wide",
            "target": "doors",
            "predicate": {"field": "width", "operator": ">=", "value": 1.0},
            "citation": {"code": "ACCESS-7"},
        },
    ],
}


@pytest.fixture
def geometry_graph() -> GeometryGraph:
    return GeometryGraph(
        levels=[Level(id="L1", name="Level 1", elevation=0.0)],
        spaces=[
            Space(
                id="S1",
                name="Bedroom A",
                level_id="L1",
                boundary=[(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)],
                metadata={
                    "category": "bedroom",
                    "window_count": 0,
                    "has_mechanical_ventilation": False,
                },
            ),
            Space(
                id="S2",
                name="Bedroom B",
                level_id="L1",
                boundary=[(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)],
                metadata={"category": "bedroom", "window_count": 2},
            ),
            Space(
                id="S3",
                name="Kitchen",
                level_id="L1",
                boundary=[(0.0, 0.0), (2.0, 0.0), (2.0, 3.0), (0.0, 3.0)],
                metadata={"category": "kitchen", "window_count": 0},
            ),
        ],
        doors=[
            Door(id="D1", name="Bedroom Door", width=0.8, level_id="L1"),
            Door(id="D2", name="Entry Door", width=1.2, level_id="L1"),
        ],
    )


def test_rules_engine_reports_rule_outcomes(geometry_graph: GeometryGraph) -> None:
    engine = RulesEngine(RULE_PACK)
    report = engine.evaluate(geometry_graph)

    assert report["summary"]["total_rules"] == 3
    assert report["summary"]["checked_entities"] == 6
    assert report["summary"]["violations"] == 3

    results_by_id = {item["rule_id"]: item for item in report["results"]}
    assert set(results_by_id.keys()) == {
        "min-bedroom-area",
        "bedroom-ventilation",
        "door-clearance",
    }

    area_result = results_by_id["min-bedroom-area"]
    assert area_result["checked"] == 2
    assert area_result["violations"]
    area_violation = area_result["violations"][0]
    assert area_violation["entity_id"] == "S1"
    assert any(
        "bedroom area" in message.lower() for message in area_violation["messages"]
    )
    area_fact = area_violation["facts"][0]
    assert area_fact["field"] == "computed.area"
    assert pytest.approx(area_fact["actual"], rel=1e-6) == 9.0
    assert pytest.approx(area_fact["expected"], rel=1e-6) == 10.0

    ventilation_result = results_by_id["bedroom-ventilation"]
    ventilation_violation = ventilation_result["violations"][0]
    assert ventilation_violation["entity_id"] == "S1"
    assert any(
        "window" in message.lower() for message in ventilation_violation["messages"]
    )
    assert ventilation_violation["facts"]

    door_result = results_by_id["door-clearance"]
    assert door_result["checked"] == 2
    assert door_result["violations"]
    door_violation = door_result["violations"][0]
    assert door_violation["entity_id"] == "D1"
    assert any("width" in message.lower() for message in door_violation["messages"])
