"""Overlay helpers to merge geometry graphs."""

from __future__ import annotations

import copy
from dataclasses import fields, replace

from app.core.models.geometry import (
    Door,
    Fixture,
    GeometryEntity,
    GeometryGraph,
    Level,
    Space,
    Wall,
)

_ENTITY_TYPES = (Level, Space, Wall, Door, Fixture)


def _merge_entities(
    existing: GeometryEntity, incoming: GeometryEntity
) -> GeometryEntity:
    if type(existing) is not type(incoming):  # noqa: E721 - dataclass type comparison
        raise TypeError(
            f"Cannot merge entity '{existing.id}' of type {type(existing).__name__} "
            f"with {type(incoming).__name__}"
        )

    updates: dict[str, object] = {"id": existing.id}
    for field in fields(existing):
        if field.name == "id":
            continue
        incoming_value = getattr(incoming, field.name)
        if field.name == "source":
            updates[field.name] = incoming_value or getattr(existing, field.name)
            continue
        if field.name == "metadata":
            merged_meta = dict(getattr(existing, field.name))
            merged_meta.update(getattr(incoming, field.name))
            updates[field.name] = merged_meta
            continue
        if incoming_value is None:
            updates[field.name] = getattr(existing, field.name)
        else:
            updates[field.name] = incoming_value
    return replace(existing, **updates)


def merge_graphs(base: GeometryGraph, overlay: GeometryGraph) -> GeometryGraph:
    """Merge two graphs, preserving base references when overlay omits them."""
    result = base.copy()

    for entity_type in _ENTITY_TYPES:
        overlay_collection = {
            entity.id: entity
            for entity in overlay.iter_entities()
            if isinstance(entity, entity_type)
        }
        for entity in overlay_collection.values():
            existing = result.get_entity(entity.id)
            if existing is None:
                result.add_entity(copy.deepcopy(entity))
            else:
                merged = _merge_entities(existing, entity)
                result.add_entity(merged)

    for relationship in overlay.relationships:
        result.add_relationship(copy.deepcopy(relationship))

    return result


__all__ = ["merge_graphs"]
