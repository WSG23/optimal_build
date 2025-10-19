import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

import pytest_asyncio
from app.core.models.geometry import Door, GeometryGraph, Level, Space
from app.models.rulesets import RulePack
from httpx import AsyncClient

PACK_DEFINITION = {
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


def _geometry_payload() -> dict:
    graph = GeometryGraph(
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
        ],
        doors=[
            Door(id="D1", name="Bedroom Door", width=0.8, level_id="L1"),
            Door(id="D2", name="Entry Door", width=1.2, level_id="L1"),
        ],
    )
    return graph.to_dict()


@pytest_asyncio.fixture
async def seeded_ruleset(session) -> dict:
    pack = RulePack(
        slug="sg-residential",
        name="Singapore Residential Compliance",
        description="Minimum bedroom and door clearances",
        jurisdiction="SG",
        authority="URA",
        version=1,
        definition=PACK_DEFINITION,
        metadata={"topics": ["space", "door"]},
    )
    session.add(pack)
    await session.commit()
    await session.refresh(pack)
    return {"id": pack.id, "slug": pack.slug, "version": pack.version}


@pytest.mark.asyncio
async def test_list_rulesets_returns_catalogue(
    app_client: AsyncClient, seeded_ruleset
) -> None:
    response = await app_client.get("/api/v1/rulesets")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    item = payload["items"][0]
    assert item["slug"] == "sg-residential"
    assert item["jurisdiction"] == "SG"
    assert item["version"] == 1
    assert item["definition"]["rules"]


@pytest.mark.asyncio
async def test_validate_ruleset_reports_citations_and_violations(
    app_client: AsyncClient,
    seeded_ruleset,
) -> None:
    geometry_payload = _geometry_payload()
    response = await app_client.post(
        "/api/v1/rulesets/validate",
        json={"ruleset_slug": seeded_ruleset["slug"], "geometry": geometry_payload},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["ruleset"]["slug"] == seeded_ruleset["slug"]
    assert payload["summary"]["violations"] == 3
    assert payload["citations"]
    assert any(citation.get("code") == "RES-12.4" for citation in payload["citations"])

    area_result = next(
        item for item in payload["results"] if item["rule_id"] == "min-bedroom-area"
    )
    assert area_result["violations"][0]["entity_id"] == "S1"
    assert any(
        "bedroom" in msg.lower() for msg in area_result["violations"][0]["messages"]
    )

    door_result = next(
        item for item in payload["results"] if item["rule_id"] == "door-clearance"
    )
    assert any(
        violation["entity_id"] == "D1" for violation in door_result["violations"]
    )
