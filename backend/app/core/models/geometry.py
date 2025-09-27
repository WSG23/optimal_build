"""Core geometry data models used to build spatial graphs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

Point2D = Tuple[float, float]


@dataclass(frozen=True)
class SourceReference:
    """Reference to the originating system of a geometry entity."""

    system: str
    identifier: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the reference to a mapping."""
        data: Dict[str, Any] = {"system": self.system, "identifier": self.identifier}
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data

    @staticmethod
    def from_mapping(
        payload: Optional[MutableMapping[str, Any]],
    ) -> Optional["SourceReference"]:
        """Create a reference from an arbitrary mapping.

        The method is defensive: it tolerates missing keys and additional metadata
        emitted by CAD parsers. When no payload is provided the method returns
        ``None``.
        """

        if not payload:
            return None
        system = str(payload.get("system") or payload.get("source") or "unknown")
        identifier_value = payload.get("identifier")
        if identifier_value is None:
            identifier_value = payload.get("id") or payload.get("external_id")
        identifier = str(identifier_value) if identifier_value is not None else ""
        metadata = {
            key: value
            for key, value in payload.items()
            if key not in {"system", "source", "identifier", "id", "external_id"}
        }
        return SourceReference(system=system, identifier=identifier, metadata=metadata)


@dataclass
class GeometryEntity:
    """Base class for every spatial entity stored in :class:`GeometryGraph`."""

    id: str
    name: Optional[str] = None
    source: Optional[SourceReference] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entity to a JSON-compatible mapping."""
        data: Dict[str, Any] = {"id": self.id}
        if self.name:
            data["name"] = self.name
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        if self.source:
            data["source"] = self.source.to_dict()
        return data


@dataclass
class Level(GeometryEntity):
    """Floor plane of the building."""

    elevation: float = 0.0
    height: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["elevation"] = self.elevation
        if self.height is not None:
            data["height"] = self.height
        return data


@dataclass
class Space(GeometryEntity):
    """Enclosed space located on a level."""

    level_id: str = ""
    boundary: List[Point2D] = field(default_factory=list)
    wall_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["level_id"] = self.level_id
        if self.boundary:
            data["boundary"] = [[pt[0], pt[1]] for pt in self.boundary]
        if self.wall_ids:
            data["wall_ids"] = list(self.wall_ids)
        return data


@dataclass
class Wall(GeometryEntity):
    """Wall segment optionally associated with spaces and a level."""

    start: Point2D = (0.0, 0.0)
    end: Point2D = (0.0, 0.0)
    thickness: Optional[float] = None
    level_id: Optional[str] = None
    space_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "start": [self.start[0], self.start[1]],
                "end": [self.end[0], self.end[1]],
            }
        )
        if self.thickness is not None:
            data["thickness"] = self.thickness
        if self.level_id:
            data["level_id"] = self.level_id
        if self.space_ids:
            data["space_ids"] = list(self.space_ids)
        return data


@dataclass
class Door(GeometryEntity):
    """Door object anchored to a wall."""

    wall_id: Optional[str] = None
    position: float = 0.0
    width: Optional[float] = None
    swing: Optional[str] = None
    level_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if self.wall_id:
            data["wall_id"] = self.wall_id
        data["position"] = self.position
        if self.width is not None:
            data["width"] = self.width
        if self.swing:
            data["swing"] = self.swing
        if self.level_id:
            data["level_id"] = self.level_id
        return data


@dataclass
class Fixture(GeometryEntity):
    """Fixed equipment such as sprinklers or plumbing fixtures."""

    category: str = "generic"
    location: Point2D = (0.0, 0.0)
    level_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["category"] = self.category
        data["location"] = [self.location[0], self.location[1]]
        if self.level_id:
            data["level_id"] = self.level_id
        return data


@dataclass
class Relationship:
    """Typed connection between two geometry entities."""

    rel_type: str
    source_id: str
    target_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "type": self.rel_type,
            "source_id": self.source_id,
            "target_id": self.target_id,
        }
        if self.attributes:
            data["attributes"] = dict(self.attributes)
        return data

    def key(self) -> Tuple[str, str, str]:
        """Return a tuple uniquely identifying the relationship."""
        return (self.rel_type, self.source_id, self.target_id)


EntityType = TypeVar("EntityType", bound=GeometryEntity)


class GeometryGraph:
    """In-memory representation of a building geometry graph."""

    def __init__(
        self,
        *,
        levels: Optional[Iterable[Level]] = None,
        spaces: Optional[Iterable[Space]] = None,
        walls: Optional[Iterable[Wall]] = None,
        doors: Optional[Iterable[Door]] = None,
        fixtures: Optional[Iterable[Fixture]] = None,
        relationships: Optional[Iterable[Relationship]] = None,
    ) -> None:
        self.levels: Dict[str, Level] = {entity.id: entity for entity in levels or []}
        self.spaces: Dict[str, Space] = {entity.id: entity for entity in spaces or []}
        self.walls: Dict[str, Wall] = {entity.id: entity for entity in walls or []}
        self.doors: Dict[str, Door] = {entity.id: entity for entity in doors or []}
        self.fixtures: Dict[str, Fixture] = {
            entity.id: entity for entity in fixtures or []
        }
        self.relationships: List[Relationship] = list(relationships or [])

    def copy(self) -> "GeometryGraph":
        """Return a deep copy of the graph."""
        import copy

        return GeometryGraph(
            levels=[copy.deepcopy(level) for level in self.levels.values()],
            spaces=[copy.deepcopy(space) for space in self.spaces.values()],
            walls=[copy.deepcopy(wall) for wall in self.walls.values()],
            doors=[copy.deepcopy(door) for door in self.doors.values()],
            fixtures=[copy.deepcopy(fixture) for fixture in self.fixtures.values()],
            relationships=[copy.deepcopy(rel) for rel in self.relationships],
        )

    def fingerprint(self) -> str:
        """Return a stable fingerprint for immutability checks."""

        raw = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _get_collection_for(self, entity: GeometryEntity) -> Dict[str, GeometryEntity]:
        if isinstance(entity, Level):
            return self.levels
        if isinstance(entity, Space):
            return self.spaces
        if isinstance(entity, Wall):
            return self.walls
        if isinstance(entity, Door):
            return self.doors
        if isinstance(entity, Fixture):
            return self.fixtures
        raise TypeError(f"Unsupported entity type: {type(entity)!r}")

    def add_entity(self, entity: EntityType) -> EntityType:
        """Insert a new entity into the graph, replacing any existing one."""
        collection = self._get_collection_for(entity)
        collection[entity.id] = entity
        return entity

    def get_entity(self, entity_id: str) -> Optional[GeometryEntity]:
        """Return the entity with the provided identifier if present."""
        for collection in (
            self.levels,
            self.spaces,
            self.walls,
            self.doors,
            self.fixtures,
        ):
            if entity_id in collection:
                return collection[entity_id]
        return None

    def iter_entities(self) -> Iterator[GeometryEntity]:
        """Iterate over every entity in the graph."""
        for collection in (
            self.levels,
            self.spaces,
            self.walls,
            self.doors,
            self.fixtures,
        ):
            yield from collection.values()

    def add_relationship(self, relationship: Relationship) -> Relationship:
        """Add a new relationship if it is not already present."""
        existing = self.find_relationship(
            relationship.rel_type, relationship.source_id, relationship.target_id
        )
        if existing:
            existing.attributes.update(relationship.attributes)
            return existing
        self.relationships.append(relationship)
        return relationship

    def find_relationship(
        self, rel_type: str, source_id: str, target_id: str
    ) -> Optional[Relationship]:
        """Retrieve an existing relationship matching the key."""
        key = (rel_type, source_id, target_id)
        for relationship in self.relationships:
            if relationship.key() == key:
                return relationship
        return None

    def remove_relationship(
        self, rel_type: str, source_id: str, target_id: str
    ) -> None:
        """Remove a relationship from the graph if present."""
        key = (rel_type, source_id, target_id)
        self.relationships = [rel for rel in self.relationships if rel.key() != key]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire graph to primitives suitable for JSON."""
        return {
            "levels": [level.to_dict() for level in self.levels.values()],
            "spaces": [space.to_dict() for space in self.spaces.values()],
            "walls": [wall.to_dict() for wall in self.walls.values()],
            "doors": [door.to_dict() for door in self.doors.values()],
            "fixtures": [fixture.to_dict() for fixture in self.fixtures.values()],
            "relationships": [
                relationship.to_dict() for relationship in self.relationships
            ],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GeometryGraph":
        """Recreate a :class:`GeometryGraph` from its serialized representation."""
        levels = [
            Level(
                id=item["id"],
                name=item.get("name"),
                source=SourceReference.from_mapping(item.get("source")),
                metadata=item.get("metadata", {}),
                elevation=float(item.get("elevation", 0.0)),
                height=item.get("height"),
            )
            for item in payload.get("levels", [])
        ]
        spaces = [
            Space(
                id=item["id"],
                name=item.get("name"),
                source=SourceReference.from_mapping(item.get("source")),
                metadata=item.get("metadata", {}),
                level_id=item.get("level_id", ""),
                boundary=[
                    (float(point[0]), float(point[1]))
                    for point in item.get("boundary", [])
                ],
                wall_ids=list(item.get("wall_ids", [])),
            )
            for item in payload.get("spaces", [])
        ]
        walls = [
            Wall(
                id=item["id"],
                name=item.get("name"),
                source=SourceReference.from_mapping(item.get("source")),
                metadata=item.get("metadata", {}),
                start=_point_from_sequence(item.get("start", (0.0, 0.0))),
                end=_point_from_sequence(item.get("end", (0.0, 0.0))),
                thickness=item.get("thickness"),
                level_id=item.get("level_id"),
                space_ids=list(item.get("space_ids", [])),
            )
            for item in payload.get("walls", [])
        ]
        doors = [
            Door(
                id=item["id"],
                name=item.get("name"),
                source=SourceReference.from_mapping(item.get("source")),
                metadata=item.get("metadata", {}),
                wall_id=item.get("wall_id"),
                position=float(item.get("position", 0.0)),
                width=item.get("width"),
                swing=item.get("swing"),
                level_id=item.get("level_id"),
            )
            for item in payload.get("doors", [])
        ]
        fixtures = [
            Fixture(
                id=item["id"],
                name=item.get("name"),
                source=SourceReference.from_mapping(item.get("source")),
                metadata=item.get("metadata", {}),
                category=item.get("category", "generic"),
                location=_point_from_sequence(item.get("location", (0.0, 0.0))),
                level_id=item.get("level_id"),
            )
            for item in payload.get("fixtures", [])
        ]
        relationships = [
            Relationship(
                rel_type=item["type"],
                source_id=item["source_id"],
                target_id=item["target_id"],
                attributes=item.get("attributes", {}),
            )
            for item in payload.get("relationships", [])
        ]
        return cls(
            levels=levels,
            spaces=spaces,
            walls=walls,
            doors=doors,
            fixtures=fixtures,
            relationships=relationships,
        )


@dataclass
class GeometryNode:
    """Tree node representing canonical geometry elements."""

    node_id: str
    kind: str
    properties: Dict[str, Any] = field(default_factory=dict)
    children: List["GeometryNode"] = field(default_factory=list)

    def add_child(self, node: "GeometryNode") -> "GeometryNode":
        """Append ``node`` as a child and return it."""

        self.children.append(node)
        return node

    def iter_nodes(self) -> Iterator["GeometryNode"]:
        """Yield the current node followed by all descendants."""

        yield self
        for child in self.children:
            yield from child.iter_nodes()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the node to a JSON-compatible mapping."""

        payload: Dict[str, Any] = {
            "id": self.node_id,
            "kind": self.kind,
            "properties": dict(self.properties),
        }
        if self.children:
            payload["children"] = [child.to_dict() for child in self.children]
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GeometryNode":
        """Instantiate a node from a mapping, tolerating partial data."""

        if not isinstance(payload, Mapping):
            raise TypeError("GeometryNode payload must be a mapping")
        node_id = str(
            payload.get("id") or payload.get("node_id") or payload.get("name") or "node"
        )
        kind = str(payload.get("kind") or payload.get("type") or "entity")
        properties_raw = payload.get("properties")
        if isinstance(properties_raw, Mapping):
            properties = dict(properties_raw)
        else:
            metadata = payload.get("metadata")
            properties = dict(metadata) if isinstance(metadata, Mapping) else {}
        children_payload = payload.get("children") or []
        children: List[GeometryNode] = []
        for item in children_payload:
            if isinstance(item, Mapping):
                children.append(cls.from_dict(item))
        return cls(node_id=node_id, kind=kind, properties=properties, children=children)


@dataclass
class CanonicalGeometry:
    """Canonical representation combining a tree and raw graph payload."""

    root: GeometryNode
    metadata: Dict[str, Any] = field(default_factory=dict)
    graph: Dict[str, Any] = field(default_factory=dict)

    def iter_nodes(self) -> Iterator[GeometryNode]:
        """Iterate over the canonical geometry tree."""

        yield from self.root.iter_nodes()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the canonical representation for persistence."""

        payload: Dict[str, Any] = {"root": self.root.to_dict()}
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        for key, value in self.graph.items():
            payload[key] = value
        return payload

    def fingerprint(self) -> str:
        """Return a deterministic fingerprint for change detection."""

        raw = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CanonicalGeometry":
        """Rehydrate a :class:`CanonicalGeometry` instance from ``payload``."""

        if not isinstance(payload, Mapping):
            raise TypeError("CanonicalGeometry payload must be a mapping")

        root_payload = payload.get("root")
        if not isinstance(root_payload, Mapping):
            root_payload = {
                "id": "root",
                "kind": str(payload.get("kind", "site")),
                "properties": (
                    dict(payload.get("metadata", {}))
                    if isinstance(payload.get("metadata"), Mapping)
                    else {}
                ),
                "children": [],
            }
        root = GeometryNode.from_dict(root_payload)

        metadata_raw = payload.get("metadata")
        metadata = dict(metadata_raw) if isinstance(metadata_raw, Mapping) else {}

        graph_keys = ("levels", "spaces", "walls", "doors", "fixtures", "relationships")
        graph_section: Dict[str, Any] = {}

        nested_graph = payload.get("graph")
        if isinstance(nested_graph, Mapping):
            for key in graph_keys:
                if key in nested_graph:
                    graph_section[key] = nested_graph[key]

        for key in graph_keys:
            if key in payload:
                graph_section[key] = payload[key]

        return cls(root=root, metadata=metadata, graph=graph_section)


def _point_from_sequence(data: Sequence[Any]) -> Point2D:
    if len(data) != 2:
        raise ValueError(f"Expected a 2D point, received: {data!r}")
    return (float(data[0]), float(data[1]))
