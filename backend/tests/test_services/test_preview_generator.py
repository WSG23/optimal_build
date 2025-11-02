"""Tests for the Phase 2B preview payload generator."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.services import preview_generator


def test_build_preview_payload_returns_prism(monkeypatch):
    property_id = UUID("00000000-0000-0000-0000-000000000123")
    layers = [
        {
            "asset_type": "Residential",
            "allocation_pct": 0.6,
            "gfa_sqm": 900.0,
            "estimated_height_m": 45.0,
            "color": "#ff0000",
        },
        {
            "asset_type": "Retail",
            "allocation_pct": 0.4,
            "gfa_sqm": 400.0,
            "estimated_height_m": 18.0,
            "color": "#00ff00",
        },
    ]

    monkeypatch.setattr(
        preview_generator,
        "utcnow",
        lambda: datetime(2025, 1, 1, tzinfo=timezone.utc),
    )

    payload = preview_generator.build_preview_payload(property_id, layers)

    assert payload["property_id"] == str(property_id)
    assert payload["generated_at"] == "2025-01-01T00:00:00Z"
    assert payload["schema_version"] == "1.0"
    assert payload["layers"][0]["geometry"]["prism"]["vertices"][0] == [
        -15.0,
        -15.0,
        0.0,
    ]
    assert payload["layers"][0]["metrics"]["gfa_sqm"] == 900.0
    assert payload["layers"][0]["metrics"]["estimated_height_m"] == 45.0
    assert payload["bounding_box"]["max"]["z"] == 45.0
    assert payload["camera_orbit_hint"]["radius"] > 0


def test_ensure_preview_asset_writes_artifacts(monkeypatch, tmp_path):
    property_id = UUID("00000000-0000-0000-0000-00000000c0de")
    layers = [
        {
            "asset_type": "Residential",
            "gfa_sqm": 256.0,
            "estimated_height_m": 32.0,
        }
    ]

    preview_dir = tmp_path / "dev-previews"
    preview_dir.mkdir()

    monkeypatch.setattr(preview_generator, "_PREVIEW_DIR", preview_dir)

    assets = preview_generator.ensure_preview_asset(property_id, layers)

    assert assets.preview_url.endswith(f"{property_id}.json")
    assert assets.thumbnail_url.endswith(f"{property_id}.png")

    payload_path = preview_dir / f"{property_id}.json"
    thumbnail_path = preview_dir / f"{property_id}.png"

    payload = payload_path.read_text(encoding="utf-8")
    assert "schema_version" in payload
    assert thumbnail_path.exists()


def test_build_preview_payload_requires_layers():
    property_id = UUID("00000000-0000-0000-0000-000000000000")

    with pytest.raises(ValueError):
        preview_generator.build_preview_payload(property_id, [])
