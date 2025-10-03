"""Utilities to construct :class:`GeometryGraph` instances from raw data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from app.core.models.geometry import (
    Door,
    Fixture,
    GeometryGraph,
    Level,
    Relationship,
    SourceReference,
    Space,
    Wall,
)


def _as_point(value: Any) -> tuple[float, float]:
    if isinstance(value, Mapping):
        x = value.get("x")
        y = value.get("y")
        if x is None or y is None:
            raise ValueError(f"Invalid point mapping: {value!r}")
        return float(x), float(y)
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        value_list = list(value)
        if len(value_list) != 2:
            raise ValueError(f"Invalid point sequence: {value!r}")
        return float(value_list[0]), float(value_list[1])
    raise TypeError(f"Unsupported point representation: {value!r}")


def _as_metadata(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f"Metadata must be a mapping, received: {value!r}")


def _ensure_source(value: Any) -> SourceReference | None:
    if value is None:
        return None
    if isinstance(value, SourceReference):
        return value
    if isinstance(value, Mapping):
        return SourceReference.from_mapping(dict(value))
    raise TypeError(f"Invalid source reference payload: {value!r}")


@dataclass
class GraphBuilder:
    """Builder responsible for validating and inserting geometry entities."""

    graph: GeometryGraph

    @classmethod
    def new(cls) -> GraphBuilder:
        return cls(graph=GeometryGraph())

    def add_level(self, payload: Mapping[str, Any]) -> Level:
        level_id = str(payload["id"])
        if level_id in self.graph.levels:
            raise ValueError(f"Level '{level_id}' already exists in graph")
        metadata = _as_metadata(payload.get("metadata"))
        level = Level(
            id=level_id,
            name=payload.get("name"),
            elevation=float(payload.get("elevation", 0.0)),
            height=payload.get("height"),
            metadata=metadata,
            source=_ensure_source(payload.get("source")),
        )
        self.graph.add_entity(level)
        return level

    def add_space(self, payload: Mapping[str, Any]) -> Space:
        space_id = str(payload["id"])
        if space_id in self.graph.spaces:
            raise ValueError(f"Space '{space_id}' already exists in graph")
        level_id = payload.get("level_id") or payload.get("level")
        if not level_id:
            raise ValueError("Space payload missing level reference")
        level_id = str(level_id)
        if level_id not in self.graph.levels:
            raise ValueError(
                f"Space '{space_id}' references unknown level '{level_id}'"
            )
        boundary_raw = payload.get("boundary") or payload.get("polygon") or []
        boundary = [_as_point(point) for point in boundary_raw]
        wall_ids = [
            str(item) for item in payload.get("wall_ids", payload.get("walls", []))
        ]
        for wall_id in wall_ids:
            if wall_id not in self.graph.walls:
                raise ValueError(
                    f"Space '{space_id}' references unknown wall '{wall_id}'"
                )
        space = Space(
            id=space_id,
            name=payload.get("name"),
            level_id=level_id,
            boundary=boundary,
            wall_ids=wall_ids,
            metadata=_as_metadata(payload.get("metadata")),
            source=_ensure_source(payload.get("source")),
        )
        self.graph.add_entity(space)
        return space

    def add_wall(self, payload: Mapping[str, Any]) -> Wall:
        wall_id = str(payload["id"])
        if wall_id in self.graph.walls:
            raise ValueError(f"Wall '{wall_id}' already exists in graph")
        start = _as_point(payload.get("start") or payload.get("from"))
        end = _as_point(payload.get("end") or payload.get("to"))
        level_id = payload.get("level_id") or payload.get("level")
        if level_id is not None:
            level_id = str(level_id)
            if level_id not in self.graph.levels:
                raise ValueError(
                    f"Wall '{wall_id}' references unknown level '{level_id}'"
                )
        space_ids = [
            str(item) for item in payload.get("space_ids", payload.get("spaces", []))
        ]
        wall = Wall(
            id=wall_id,
            name=payload.get("name"),
            start=start,
            end=end,
            thickness=payload.get("thickness"),
            level_id=level_id,
            space_ids=space_ids,
            metadata=_as_metadata(payload.get("metadata")),
            source=_ensure_source(payload.get("source")),
        )
        self.graph.add_entity(wall)
        return wall

    def add_door(self, payload: Mapping[str, Any]) -> Door:
        door_id = str(payload["id"])
        if door_id in self.graph.doors:
            raise ValueError(f"Door '{door_id}' already exists in graph")
        wall_id = payload.get("wall_id") or payload.get("wall")
        if wall_id:
            wall_id = str(wall_id)
            if wall_id not in self.graph.walls:
                raise ValueError(
                    f"Door '{door_id}' references unknown wall '{wall_id}'"
                )
        level_id = payload.get("level_id") or payload.get("level")
        if level_id is not None:
            level_id = str(level_id)
            if level_id not in self.graph.levels:
                raise ValueError(
                    f"Door '{door_id}' references unknown level '{level_id}'"
                )
        door = Door(
            id=door_id,
            name=payload.get("name"),
            wall_id=wall_id,
            position=float(payload.get("position", 0.0)),
            width=payload.get("width"),
            swing=payload.get("swing"),
            level_id=level_id,
            metadata=_as_metadata(payload.get("metadata")),
            source=_ensure_source(payload.get("source")),
        )
        self.graph.add_entity(door)
        return door

    def add_fixture(self, payload: Mapping[str, Any]) -> Fixture:
        fixture_id = str(payload["id"])
        if fixture_id in self.graph.fixtures:
            raise ValueError(f"Fixture '{fixture_id}' already exists in graph")
        level_id = payload.get("level_id") or payload.get("level")
        if level_id is not None:
            level_id = str(level_id)
            if level_id not in self.graph.levels:
                raise ValueError(
                    f"Fixture '{fixture_id}' references unknown level '{level_id}'"
                )
        location = payload.get("location") or payload.get("point")
        fixture = Fixture(
            id=fixture_id,
            name=payload.get("name"),
            category=payload.get("category", payload.get("kind", "generic")),
            location=_as_point(location) if location is not None else (0.0, 0.0),
            level_id=level_id,
            metadata=_as_metadata(payload.get("metadata")),
            source=_ensure_source(payload.get("source")),
        )
        self.graph.add_entity(fixture)
        return fixture

    def add_relationship(self, payload: Mapping[str, Any]) -> Relationship:
        rel_type = payload.get("type") or payload.get("relationship")
        if not rel_type:
            raise ValueError("Relationship payload missing type")
        source_id = str(
            payload.get("source_id") or payload.get("source") or payload.get("from")
        )
        target_id = str(
            payload.get("target_id") or payload.get("target") or payload.get("to")
        )
        if not self.graph.get_entity(source_id):
            raise ValueError(f"Relationship references unknown source '{source_id}'")
        if not self.graph.get_entity(target_id):
            raise ValueError(f"Relationship references unknown target '{target_id}'")
        relationship = Relationship(
            rel_type=str(rel_type),
            source_id=source_id,
            target_id=target_id,
            attributes=dict(payload.get("attributes", {})),
        )
        self.graph.add_relationship(relationship)
        return relationship

    def build_from_payload(self, payload: Mapping[str, Any]) -> GeometryGraph:
        for level in payload.get("levels", []):
            self.add_level(level)
        for wall in payload.get("walls", []):
            self.add_wall(wall)
        for space in payload.get("spaces", []):
            self.add_space(space)
        for door in payload.get("doors", []):
            self.add_door(door)
        for fixture in payload.get("fixtures", []):
            self.add_fixture(fixture)
        for relationship in payload.get("relationships", []):
            self.add_relationship(relationship)
        self.validate_integrity()
        return self.graph

    def validate_integrity(self) -> None:
        """Ensure cross references between entities remain valid."""
        seen: dict[str, str] = {}
        for entity in self.graph.iter_entities():
            if entity.id in seen and seen[entity.id] != entity.__class__.__name__:
                raise ValueError(
                    f"Identifier '{entity.id}' used for both {seen[entity.id]} and {entity.__class__.__name__}"
                )
            seen[entity.id] = entity.__class__.__name__

        for space in self.graph.spaces.values():
            if space.level_id not in self.graph.levels:
                raise ValueError(
                    f"Space '{space.id}' references unknown level '{space.level_id}'"
                )
            for wall_id in space.wall_ids:
                if wall_id not in self.graph.walls:
                    raise ValueError(
                        f"Space '{space.id}' references unknown wall '{wall_id}'"
                    )

        for wall in self.graph.walls.values():
            if wall.level_id and wall.level_id not in self.graph.levels:
                raise ValueError(
                    f"Wall '{wall.id}' references unknown level '{wall.level_id}'"
                )
            for space_id in wall.space_ids:
                if space_id not in self.graph.spaces:
                    raise ValueError(
                        f"Wall '{wall.id}' references unknown space '{space_id}'"
                    )

        for door in self.graph.doors.values():
            if door.wall_id and door.wall_id not in self.graph.walls:
                raise ValueError(
                    f"Door '{door.id}' references unknown wall '{door.wall_id}'"
                )
            if door.level_id and door.level_id not in self.graph.levels:
                raise ValueError(
                    f"Door '{door.id}' references unknown level '{door.level_id}'"
                )

        for fixture in self.graph.fixtures.values():
            if fixture.level_id and fixture.level_id not in self.graph.levels:
                raise ValueError(
                    f"Fixture '{fixture.id}' references unknown level '{fixture.level_id}'"
                )

        for relationship in self.graph.relationships:
            if not self.graph.get_entity(relationship.source_id):
                raise ValueError(
                    f"Relationship '{relationship.rel_type}' references unknown source '{relationship.source_id}'"
                )
            if not self.graph.get_entity(relationship.target_id):
                raise ValueError(
                    f"Relationship '{relationship.rel_type}' references unknown target '{relationship.target_id}'"
                )
