"""Tests for the geometry graph helpers."""

from __future__ import annotations

import pytest

from backend.app.core.geometry import GeometrySerializer, GraphBuilder
from backend.app.core.models.geometry import Fixture, GeometryGraph, Relationship, Space
from backend.app.core.overlay import merge_graphs


@pytest.fixture
def cad_payload() -> dict:
    return {
        "levels": [
            {
                "id": "L1",
                "name": "Level 1",
                "elevation": 0.0,
                "height": 3.5,
                "source": {"system": "cad", "id": "lvl-ext-1"},
            }
        ],
        "walls": [
            {
                "id": "W1",
                "name": "North Wall",
                "start": {"x": 0.0, "y": 0.0},
                "end": {"x": 10.0, "y": 0.0},
                "level_id": "L1",
                "thickness": 0.2,
                "metadata": {"fire_rating": "2h"},
            }
        ],
        "spaces": [
            {
                "id": "S1",
                "name": "Lobby",
                "level_id": "L1",
                "boundary": [
                    {"x": 0.0, "y": 0.0},
                    {"x": 10.0, "y": 0.0},
                    {"x": 10.0, "y": 5.0},
                    {"x": 0.0, "y": 5.0},
                ],
                "wall_ids": ["W1"],
                "metadata": {"usage": "public"},
                "source": {"system": "cad", "id": "space-ext-1"},
            }
        ],
        "doors": [
            {
                "id": "D1",
                "name": "Main Entrance",
                "wall_id": "W1",
                "position": 4.0,
                "width": 1.2,
                "swing": "in",
                "level_id": "L1",
            }
        ],
        "fixtures": [
            {
                "id": "F1",
                "category": "sprinkler",
                "location": {"x": 2.0, "y": 1.0},
                "level_id": "L1",
            }
        ],
        "relationships": [
            {"type": "contains", "source_id": "L1", "target_id": "S1"},
            {"type": "bounded_by", "source_id": "S1", "target_id": "W1"},
        ],
    }


@pytest.fixture
def geometry_graph(cad_payload: dict) -> GeometryGraph:
    return GeometrySerializer.from_cad(cad_payload)


def test_serializer_builds_graph_from_cad(geometry_graph: GeometryGraph) -> None:
    assert "L1" in geometry_graph.levels
    assert geometry_graph.levels["L1"].source is not None
    assert geometry_graph.levels["L1"].source.system == "cad"
    assert geometry_graph.spaces["S1"].boundary[2] == (10.0, 5.0)
    assert geometry_graph.doors["D1"].wall_id == "W1"
    assert len(geometry_graph.relationships) == 2


def test_export_roundtrip_preserves_graph(geometry_graph: GeometryGraph) -> None:
    export_payload = GeometrySerializer.to_export(geometry_graph)
    assert export_payload["spaces"][0]["boundary"][0] == [0.0, 0.0]

    roundtrip_graph = GeometrySerializer.from_export(export_payload)
    assert roundtrip_graph.to_dict() == export_payload


def test_overlay_merge_preserves_sources(geometry_graph: GeometryGraph) -> None:
    base_space = geometry_graph.spaces["S1"]
    assert base_space.source is not None

    overlay_graph = GeometryGraph(
        spaces=[
            Space(
                id="S1",
                name="Lobby Renovated",
                level_id="L1",
                boundary=[(0.0, 0.0), (12.0, 0.0), (12.0, 6.0), (0.0, 6.0)],
                metadata={"phase": "renovation"},
            )
        ],
        fixtures=[
            Fixture(
                id="F2",
                category="sink",
                location=(3.0, 1.0),
                level_id="L1",
            )
        ],
        doors=[],
        walls=[],
        levels=[],
        relationships=[Relationship(rel_type="contains", source_id="L1", target_id="F2")],
    )

    merged = merge_graphs(geometry_graph, overlay_graph)
    merged_space = merged.spaces["S1"]
    assert merged_space.name == "Lobby Renovated"
    assert merged_space.boundary[1] == (12.0, 0.0)
    assert merged_space.metadata["usage"] == "public"
    assert merged_space.metadata["phase"] == "renovation"
    assert merged_space.source == base_space.source
    assert "F2" in merged.fixtures
    assert any(rel.target_id == "F2" for rel in merged.relationships)


def test_serializer_to_cad_uses_point_mappings(geometry_graph: GeometryGraph) -> None:
    cad_export = GeometrySerializer.to_cad(geometry_graph)
    first_space_point = cad_export["spaces"][0]["boundary"][0]
    assert first_space_point == {"x": 0.0, "y": 0.0}
    first_wall_start = cad_export["walls"][0]["start"]
    assert first_wall_start == {"x": 0.0, "y": 0.0}
    assert cad_export["fixtures"][0]["location"] == {"x": 2.0, "y": 1.0}


def test_builder_validates_missing_references(cad_payload: dict) -> None:
    builder = GraphBuilder.new()
    builder.add_level(cad_payload["levels"][0])
    with pytest.raises(ValueError):
        builder.add_space({"id": "S-missing", "level_id": "unknown"})
