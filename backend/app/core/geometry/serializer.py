"""Serialization helpers for :class:`GeometryGraph` instances."""

from __future__ import annotations

from typing import Any, Dict, Mapping

from app.core.geometry.builder import GraphBuilder
from app.core.models.geometry import GeometryGraph


def _point_to_mapping(point: tuple[float, float]) -> Dict[str, float]:
    return {"x": float(point[0]), "y": float(point[1])}


class GeometrySerializer:
    """Translate geometry graphs between CAD payloads and export formats."""

    @staticmethod
    def from_cad(payload: Mapping[str, Any]) -> GeometryGraph:
        """Build a graph from CAD derived payloads."""
        builder = GraphBuilder.new()
        builder.build_from_payload(payload)
        builder.validate_integrity()
        return builder.graph

    @staticmethod
    def from_export(payload: Mapping[str, Any]) -> GeometryGraph:
        """Rehydrate a graph from the exported representation."""
        graph = GeometryGraph.from_dict(payload)
        builder = GraphBuilder(graph=graph)
        builder.validate_integrity()
        return graph

    @staticmethod
    def to_export(graph: GeometryGraph) -> Dict[str, Any]:
        """Serialize the graph to a neutral JSON representation."""
        return graph.to_dict()

    @staticmethod
    def to_cad(graph: GeometryGraph) -> Dict[str, Any]:
        """Serialize the graph to a CAD friendly payload using point mappings."""
        payload = graph.to_dict()
        payload["levels"] = [dict(item) for item in payload.get("levels", [])]
        payload["spaces"] = []
        for space in graph.spaces.values():
            data = space.to_dict()
            data["boundary"] = [_point_to_mapping(point) for point in space.boundary]
            payload["spaces"].append(data)
        payload["walls"] = []
        for wall in graph.walls.values():
            data = wall.to_dict()
            data["start"] = _point_to_mapping(wall.start)
            data["end"] = _point_to_mapping(wall.end)
            payload["walls"].append(data)
        payload["fixtures"] = []
        for fixture in graph.fixtures.values():
            data = fixture.to_dict()
            data["location"] = _point_to_mapping(fixture.location)
            payload["fixtures"].append(data)
        payload["doors"] = [door.to_dict() for door in graph.doors.values()]
        payload["relationships"] = [rel.to_dict() for rel in graph.relationships]
        return payload


__all__ = ["GeometrySerializer"]
