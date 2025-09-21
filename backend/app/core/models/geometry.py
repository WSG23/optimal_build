"""Canonical geometry graph helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class GeometryNode:
    """Node within a canonical geometry graph."""

    node_id: str
    kind: str
    properties: Dict[str, Any] = field(default_factory=dict)
    children: List["GeometryNode"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the node into a JSON-compatible dict."""

        return {
            "id": self.node_id,
            "kind": self.kind,
            "properties": self.properties,
            "children": [child.to_dict() for child in self.children],
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "GeometryNode":
        """Construct a node from a dictionary payload."""

        node_id = payload.get("id")
        kind = payload.get("kind")
        if not node_id or not kind:
            raise ValueError("Geometry node requires 'id' and 'kind' fields")
        properties = payload.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        children_payload = payload.get("children") or []
        children: List[GeometryNode] = []
        for child in children_payload:
            if isinstance(child, dict):
                children.append(cls.from_dict(child))
        return cls(node_id=str(node_id), kind=str(kind), properties=properties, children=children)

    def iter_nodes(self) -> Iterator["GeometryNode"]:
        """Yield the node and all of its descendants."""

        yield self
        for child in self.children:
            yield from child.iter_nodes()

    def find(self, *, kind: Optional[str] = None) -> List["GeometryNode"]:
        """Return nodes matching the requested kind."""

        if kind is None:
            return list(self.iter_nodes())
        return [node for node in self.iter_nodes() if node.kind == kind]

    def get(self, key: str, default: Any | None = None) -> Any | None:
        """Helper to access properties with a default."""

        return self.properties.get(key, default)


@dataclass
class CanonicalGeometry:
    """Wrapper containing the canonical geometry graph."""

    root: GeometryNode
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "v1"

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the geometry graph."""

        return {
            "version": self.version,
            "metadata": self.metadata,
            "root": self.root.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CanonicalGeometry":
        """Load geometry graph from a dictionary payload."""

        if "root" not in payload:
            raise ValueError("Canonical geometry payload missing 'root'")
        root_payload = payload["root"]
        if not isinstance(root_payload, dict):
            raise ValueError("Canonical geometry root must be a dictionary")
        metadata_payload = payload.get("metadata")
        if not isinstance(metadata_payload, dict):
            metadata_payload = {}
        version = payload.get("version") or "v1"
        return cls(
            root=GeometryNode.from_dict(root_payload),
            metadata=metadata_payload,
            version=str(version),
        )

    def fingerprint(self) -> str:
        """Return a stable fingerprint for immutability checks."""

        raw = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(raw.encode("utf-8")).hexdigest()

    def find_nodes(self, *, kind: Optional[str] = None) -> List[GeometryNode]:
        """Convenience wrapper to locate nodes of a certain kind."""

        return self.root.find(kind=kind)

    def iter_nodes(self) -> Iterator[GeometryNode]:
        """Yield all nodes in the geometry graph."""

        return self.root.iter_nodes()


def serialize_geometry(geometry: CanonicalGeometry) -> Dict[str, Any]:
    """Serialise a canonical geometry graph to a JSON-compatible dict."""

    return geometry.to_dict()


def deserialize_geometry(payload: Dict[str, Any]) -> CanonicalGeometry:
    """Deserialize a geometry payload into a canonical geometry graph."""

    return CanonicalGeometry.from_dict(payload)


__all__ = [
    "CanonicalGeometry",
    "GeometryNode",
    "serialize_geometry",
    "deserialize_geometry",
]
