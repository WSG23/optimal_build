"""Comprehensive backend tests covering the AEC overlay workflow."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from app.api.v1.imports import _build_parse_summary
from app.core.export import (
    ExportFormat,
    ExportOptions,
    LayerMapping,
    LocalExportStorage,
    generate_project_export,
)
from app.core.geometry.builder import GraphBuilder
from app.core.metrics.roi import compute_project_roi
from app.core.models.geometry import CanonicalGeometry, GeometryNode
from app.models.audit import AuditLog
from app.models.imports import ImportRecord
from app.models.overlay import OverlaySourceGeometry, OverlaySuggestion
from app.models.rkp import RefRule, RefZoningLayer
from backend.jobs.overlay_run import run_overlay_for_project
from sqlalchemy import select

SAMPLE_PATH = Path(__file__).resolve().parents[1] / "samples" / "sample_floorplan.json"
GOLDEN_MANIFEST_PATH = (
    Path(__file__).resolve().parents[1] / "samples" / "golden_export_manifest.json"
)


def _load_sample_payload() -> dict[str, object]:
    return json.loads(SAMPLE_PATH.read_text("utf-8"))


def _build_geometry_from_sample(
    sample: dict[str, object],
) -> tuple[CanonicalGeometry, dict[str, dict[str, object]]]:
    builder = GraphBuilder.new()
    level_lookup: dict[str, dict[str, object]] = {}

    for index, layer in enumerate(sample.get("layers", []), start=1):
        if not isinstance(layer, dict):
            continue
        level_id = f"L{index:02d}"
        metadata = dict(layer.get("metadata") or {})
        metadata.setdefault("layer_type", layer.get("type"))
        builder.add_level(
            {
                "id": level_id,
                "name": layer.get("name"),
                "elevation": metadata.get("elevation", 0.0),
                "metadata": metadata,
            }
        )
        level_lookup[level_id] = layer
        units: Iterable[dict] = layer.get("units", [])  # type: ignore[assignment]
        for unit_index, unit in enumerate(units, start=1):
            if not isinstance(unit, dict):
                continue
            space_id = f"{level_id}-U{unit_index:02d}"
            area = float(unit.get("area_m2", 1.0))
            side = max(area**0.5, 1.0)
            boundary = [
                {"x": 0.0, "y": 0.0},
                {"x": side, "y": 0.0},
                {"x": side, "y": side},
                {"x": 0.0, "y": side},
            ]
            space_metadata = {key: value for key, value in unit.items() if key != "id"}
            space_metadata.setdefault("status", unit.get("status", "pending"))
            builder.add_space(
                {
                    "id": space_id,
                    "name": unit.get("id"),
                    "level_id": level_id,
                    "boundary": boundary,
                    "metadata": space_metadata,
                }
            )
            builder.add_relationship(
                {"type": "contains", "source_id": level_id, "target_id": space_id}
            )

    graph = builder.graph
    builder.validate_integrity()

    site_layer = next(
        (
            layer
            for layer in sample.get("layers", [])
            if isinstance(layer, dict) and layer.get("type") in {"site", "reference"}
        ),
        None,
    )
    root_properties: dict[str, object] = {"project": sample.get("project")}
    if isinstance(site_layer, dict):
        root_properties.update(site_layer.get("metadata", {}))

    root = GeometryNode(node_id="site-root", kind="site", properties=root_properties)

    for level_id, layer in level_lookup.items():
        if not isinstance(layer, dict) or layer.get("type") != "floor":
            continue
        units = list(layer.get("units", []))
        floor_metadata = {
            "name": layer.get("name"),
            "unit_count": len(units),
        }
        layer_meta = layer.get("metadata")
        if isinstance(layer_meta, dict) and "elevation" in layer_meta:
            floor_metadata["elevation"] = layer_meta["elevation"]
        floor_node = root.add_child(
            GeometryNode(node_id=level_id, kind="floor", properties=floor_metadata)
        )
        for unit_index, unit in enumerate(units, start=1):
            if not isinstance(unit, dict):
                continue
            space_id = f"{level_id}-U{unit_index:02d}"
            unit_properties = {
                "label": unit.get("id"),
                "area_m2": unit.get("area_m2"),
                "status": unit.get("status", "pending"),
            }
            if "height_m" in unit:
                unit_properties["height_m"] = unit["height_m"]
            floor_node.add_child(
                GeometryNode(node_id=space_id, kind="unit", properties=unit_properties)
            )

    canonical = CanonicalGeometry(
        root=root,
        metadata={"project": sample.get("project")},
        graph=graph.to_dict(),
    )
    return canonical, level_lookup


async def _seed_overlay_project(
    async_session_factory, canonical: CanonicalGeometry, *, project_id: int = 101
) -> int:
    async with async_session_factory() as session:
        source = OverlaySourceGeometry(
            project_id=project_id,
            source_geometry_key="primary",
            graph=canonical.to_dict(),
            metadata={"source": "test-suite"},
            checksum=canonical.fingerprint(),
        )
        session.add(source)
        await session.commit()

    async with async_session_factory() as session:
        await run_overlay_for_project(session, project_id=project_id)
        suggestions = (
            (
                await session.execute(
                    select(OverlaySuggestion).where(
                        OverlaySuggestion.project_id == project_id
                    )
                )
            )
            .scalars()
            .all()
        )
        ten_minutes_ago = datetime.now(UTC) - timedelta(minutes=10)
        for suggestion in suggestions:
            suggestion.created_at = ten_minutes_ago
        await session.commit()
    return project_id


@pytest.mark.asyncio
async def test_import_parse_summary_uses_sample_fixture(session):
    sample = _load_sample_payload()
    floors = [
        {
            "name": layer.get("name"),
            "units": [unit.get("id") for unit in layer.get("units", [])],
        }
        for layer in sample.get("layers", [])
        if isinstance(layer, dict) and layer.get("type") == "floor"
    ]
    units = [
        {
            "id": unit.get("id"),
            "floor": layer.get("name"),
            "area_m2": unit.get("area_m2"),
        }
        for layer in sample.get("layers", [])
        if isinstance(layer, dict) and layer.get("type") == "floor"
        for unit in layer.get("units", [])
        if isinstance(unit, dict)
    ]

    record = ImportRecord(
        filename="mock-floorplan.dwg",
        content_type="application/json",
        size_bytes=4096,
        storage_path="local://imports/mock-floorplan.dwg",
        layer_metadata=sample.get("layers", []),
        detected_floors=floors,
        detected_units=units,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    summary = _build_parse_summary(record)
    assert summary["floors"] == len(floors)
    assert summary["units"] == len(units)
    assert summary["floor_breakdown"][0]["name"] == floors[0]["name"]


@pytest.mark.asyncio
async def test_overlay_generation_from_sample(async_session_factory):
    sample = _load_sample_payload()
    canonical, _ = _build_geometry_from_sample(sample)
    project_id = await _seed_overlay_project(
        async_session_factory, canonical, project_id=201
    )

    async with async_session_factory() as session:
        suggestions = (
            (
                await session.execute(
                    select(OverlaySuggestion).where(
                        OverlaySuggestion.project_id == project_id
                    )
                )
            )
            .scalars()
            .all()
        )
    codes = {suggestion.code for suggestion in suggestions}
    assert {
        "heritage_conservation",
        "flood_mitigation",
        "large_site_review",
        "tall_building_review",
        "coastal_evacuation_plan",
    }.issubset(codes)


@pytest.mark.asyncio
async def test_decision_handling_records_audit(async_session_factory, client):
    sample = _load_sample_payload()
    canonical, _ = _build_geometry_from_sample(sample)
    project_id = await _seed_overlay_project(
        async_session_factory, canonical, project_id=301
    )

    async with async_session_factory() as session:
        first_suggestion = (
            (
                await session.execute(
                    select(OverlaySuggestion)
                    .where(OverlaySuggestion.project_id == project_id)
                    .order_by(OverlaySuggestion.id)
                )
            )
            .scalars()
            .first()
        )
        assert first_suggestion is not None

    payload = {
        "suggestion_id": first_suggestion.id,
        "decision": "approve",
        "decided_by": "pytest",
        "notes": "Automated approval",
    }
    response = await client.post(f"/api/v1/overlay/{project_id}/decision", json=payload)
    assert response.status_code == 200

    async with async_session_factory() as session:
        refreshed = await session.get(OverlaySuggestion, first_suggestion.id)
        assert refreshed is not None
        assert refreshed.status == "approved"
        logs = (
            (
                await session.execute(
                    select(AuditLog)
                    .where(AuditLog.project_id == project_id)
                    .order_by(AuditLog.id)
                )
            )
            .scalars()
            .all()
        )
    events = {log.event_type for log in logs}
    assert "overlay_run" in events
    assert "overlay_decision" in events


@pytest.mark.asyncio
async def test_export_roundtrip_matches_golden_manifest(
    async_session_factory, tmp_path
):
    sample = _load_sample_payload()
    canonical, _ = _build_geometry_from_sample(sample)
    project_id = await _seed_overlay_project(
        async_session_factory, canonical, project_id=401
    )

    async with async_session_factory() as session:
        options = ExportOptions(
            format=ExportFormat.DWG,
            include_pending_overlays=True,
            layer_mapping=LayerMapping(
                source={"floor": "A-FLOOR"},
                overlays={
                    "heritage_conservation": "A-OVER-HERITAGE",
                    "pending": "A-OVER-PENDING",
                },
            ),
        )
        storage = LocalExportStorage(base_dir=tmp_path)
        artifact = await generate_project_export(
            session,
            project_id=project_id,
            options=options,
            storage=storage,
        )

    manifest = dict(artifact.manifest)
    generated_at = manifest.pop("generated_at", None)
    assert generated_at is not None

    expected_manifest = json.loads(GOLDEN_MANIFEST_PATH.read_text("utf-8"))
    assert manifest == expected_manifest

    payload_bytes = artifact.open().read()
    payload = json.loads(payload_bytes.decode("utf-8"))
    payload.pop("generated_at", None)
    assert payload == expected_manifest

    async with async_session_factory() as session:
        audit_events = (
            (
                await session.execute(
                    select(AuditLog)
                    .where(AuditLog.project_id == project_id)
                    .order_by(AuditLog.id)
                )
            )
            .scalars()
            .all()
        )
    assert any(log.event_type == "export_generated" for log in audit_events)


@pytest.mark.asyncio
async def test_roi_snapshot_reports_saved_hours(async_session_factory):
    sample = _load_sample_payload()
    canonical, _ = _build_geometry_from_sample(sample)
    project_id = await _seed_overlay_project(
        async_session_factory, canonical, project_id=501
    )

    async with async_session_factory() as session:
        first = (
            (
                await session.execute(
                    select(OverlaySuggestion)
                    .where(OverlaySuggestion.project_id == project_id)
                    .order_by(OverlaySuggestion.id)
                )
            )
            .scalars()
            .first()
        )
        assert first is not None
        first.status = "approved"
        first.decided_by = "pytest"
        first.decided_at = datetime.now(UTC)
        await session.commit()

    async with async_session_factory() as session:
        snapshot = await compute_project_roi(session, project_id=project_id)
    assert snapshot.total_suggestions >= 5
    assert snapshot.decided_suggestions == 1
    assert snapshot.acceptance_rate == 1.0
    assert snapshot.review_hours_saved >= 0.0
    assert snapshot.savings_percent >= 0


@pytest.mark.asyncio
async def test_ruleset_serialisation_includes_overlays(async_session_factory, client):
    layer = RefZoningLayer(
        jurisdiction="SG",
        layer_name="MasterPlan",
        zone_code="RA",
        attributes={
            "overlays": ["heritage_conservation"],
            "advisory_hints": ["Submit heritage impact assessment"],
        },
    )
    rule = RefRule(
        jurisdiction="SG",
        authority="URA",
        topic="Zoning",
        parameter_key="parking.min_car_spaces_per_unit",
        operator=">=",
        value="1.5",
        unit="spaces",
        applicability={"zone_code": "RA"},
        notes="Provide 1.5 car spaces per dwelling unit to comply with parking minimums.",
        review_status="needs_review",
    )

    async with async_session_factory() as session:
        session.add_all([layer, rule])
        await session.commit()

    response = await client.get("/api/v1/rules")
    assert response.status_code == 200
    payload = response.json()
    items = payload.get("items", [])
    assert items, "Expected at least one rule to be returned"
    overlays = items[0].get("overlays")
    hints = items[0].get("advisory_hints")
    assert "heritage_conservation" in overlays
    assert any("parking spaces" in hint for hint in hints)
