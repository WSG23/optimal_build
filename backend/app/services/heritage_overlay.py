"""Lightweight heritage overlay lookup service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class HeritageOverlay:
    """A single conservation overlay with bounding box metadata."""

    name: str
    risk: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    notes: tuple[str, ...]

    def contains(self, latitude: float, longitude: float) -> bool:
        return (
            self.min_lat <= latitude <= self.max_lat
            and self.min_lon <= longitude <= self.max_lon
        )


class HeritageOverlayService:
    """Loads heritage overlays and provides lookup helpers."""

    def __init__(self) -> None:
        self._overlays: tuple[HeritageOverlay, ...] = tuple(self._load_overlays())

    def _load_overlays(self) -> Iterable[HeritageOverlay]:
        try:
            text = (
                resources.files("app.data")
                .joinpath("heritage_overlays.json")
                .read_text(encoding="utf-8")
            )
        except FileNotFoundError:
            return []
        except OSError:
            return []

        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            return []

        overlays: list[HeritageOverlay] = []
        for entry in raw:
            bbox = entry.get("bbox") or {}
            try:
                overlays.append(
                    HeritageOverlay(
                        name=str(entry.get("name", "Unknown Heritage Overlay")),
                        risk=str(entry.get("risk", "medium")),
                        min_lat=float(bbox.get("min_lat")),
                        max_lat=float(bbox.get("max_lat")),
                        min_lon=float(bbox.get("min_lon")),
                        max_lon=float(bbox.get("max_lon")),
                        notes=tuple(
                            str(note) for note in entry.get("notes", []) if note
                        ),
                    )
                )
            except (TypeError, ValueError):
                continue
        return overlays

    def lookup(self, latitude: float, longitude: float) -> Optional[dict[str, Any]]:
        for overlay in self._overlays:
            if overlay.contains(latitude, longitude):
                return {
                    "name": overlay.name,
                    "risk": overlay.risk,
                    "notes": list(overlay.notes),
                }
        return None


__all__ = ["HeritageOverlayService", "HeritageOverlay"]
