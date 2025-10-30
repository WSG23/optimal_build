"""Utility helpers for generating developer preview assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping
from uuid import UUID

_BASE_DIR = Path(__file__).resolve().parents[2]
_PREVIEW_DIR = _BASE_DIR / "static" / "dev-previews"
_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)


def ensure_preview_asset(
    property_id: UUID, massing_layers: Iterable[Mapping[str, object]]
) -> str:
    """Persist a lightweight preview asset and return the web path."""

    payload = {
        "property_id": str(property_id),
        "layers": [dict(layer) for layer in massing_layers],
    }
    file_path = _PREVIEW_DIR / f"{property_id}.json"
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return f"/static/dev-previews/{property_id}.json"


__all__ = ["ensure_preview_asset"]
