from __future__ import annotations

import json
from datetime import datetime
from types import SimpleNamespace

import pytest

from app.api.v1 import imports as imports_api


def test_extract_unit_id_and_normalise_floor_track_unique_units():
    seen: dict[str, None] = {}
    unit = imports_api._extract_unit_id({"label": "A1"})
    assert unit == "A1"
    floor = imports_api._normalise_floor(
        name="Level 1", unit_ids=["A1", 2], seen_units=seen
    )
    assert floor["unit_ids"] == ["A1", 2]
    assert list(seen.keys()) == ["A1", 2]
    assert imports_api._extract_unit_id({"name": ""}) is None


def test_collect_layer_and_declared_floors_accumulate_metadata():
    seen: dict[str, None] = {}
    raw_layers = [
        {"type": "floor", "name": "L1", "units": [{"id": "U1"}, "U2"]},
        {"type": "roof", "units": [{"id": "IGNORE"}]},
        "invalid",
    ]
    floors, metadata = imports_api._collect_layer_floors(raw_layers, seen)
    assert floors[0]["unit_ids"] == ["U1", "U2"]
    assert metadata[0]["name"] == "L1"

    declared = imports_api._collect_declared_floors(
        [{"name": "Podium", "units": [{"name": "P1"}]}, "Annex"], seen
    )
    assert declared[0]["unit_ids"] == ["P1"]
    assert declared[1]["name"] == "Annex"


def test_detect_json_payload_combines_sources():
    payload = {
        "layers": [{"type": "floor", "name": "L1", "units": [{"id": "A"}]}],
        "floors": ["Penthouse"],
        "units": [{"label": "Retail-1"}],
    }
    floors, units, layer_metadata = imports_api._detect_json_payload(payload)
    assert len(floors) == 2
    assert units == ["A", "Retail-1"]
    assert layer_metadata[0]["name"] == "L1"


def test_detect_import_metadata_routes_formats(monkeypatch):
    json_payload = json.dumps({"layers": [{"type": "floor", "units": [{"id": "U1"}]}]})
    floors, units, _ = imports_api._detect_import_metadata(
        "plan.JSON", "application/json", json_payload.encode()
    )
    assert units == ["U1"]

    sentinel = ([{"name": "DXF"}], ["dxf-unit"], [])
    monkeypatch.setattr(imports_api, "detect_dxf_metadata", lambda payload: sentinel)
    result = imports_api._detect_import_metadata("drawing.dxf", None, b"dxfdx")
    assert result == sentinel

    def _boom(payload: bytes):
        raise RuntimeError("bad dxf")

    monkeypatch.setattr(imports_api, "detect_dxf_metadata", _boom)
    empty = imports_api._detect_import_metadata("drawing.dxf", None, b"broken")
    assert empty == ([], [], [])


def test_import_media_flags_and_vector_helpers():
    assert imports_api._is_supported_import("model.ifc", None) is True
    assert imports_api._is_supported_import(None, "application/vnd.ifc") is True
    assert imports_api._is_vectorizable("sheet.pdf", None) is True
    assert imports_api._is_vectorizable(None, "image/png") is True

    summary = imports_api._summarise_vector_payload(
        {
            "paths": [{"id": 1}, {"id": 2}],
            "walls": [{"id": 1}],
            "bounds": {"x": 1},
            "options": {"bitmap_walls": True},
        },
        infer_walls=False,
        requested=True,
    )
    assert summary["paths"] == 2
    assert summary["options"]["bitmap_walls"] is True

    layers = imports_api._derive_vector_layers(
        {"paths": [{"layer": "A"}, {"layer": "A"}, {"layer": "B"}, {"layer": None}]}
    )
    assert layers == [
        {"name": "A", "path_count": 2, "source": "vector_paths"},
        {"name": "B", "path_count": 1, "source": "vector_paths"},
    ]


def test_normalise_units_and_coerce_payloads():
    assert imports_api._normalise_units({"a": {"id": "U1"}}) == ["U1"]
    assert imports_api._normalise_units(["B1", {"ref": "B2"}]) == ["B1", "B2"]
    assert imports_api._normalise_units("Solo") == ["Solo"]

    class WithModelDump:
        def model_dump(self):
            return {"seen": True}

    coerced = imports_api._coerce_mapping_payload(WithModelDump())
    assert coerced == {"seen": True}

    class WithDict:
        def dict(self):
            return {"legacy": 1}

    assert imports_api._coerce_mapping_payload(WithDict()) == {"legacy": 1}


def test_metric_override_payload_normalized_filters_none():
    payload = imports_api.MetricOverridePayload(
        site_area_sqm=1200.0,
        gross_floor_area_sqm=None,
        max_height_m=55.5,
    )
    assert payload.normalized() == {"site_area_sqm": 1200.0, "max_height_m": 55.5}


def test_zone_normalisation_and_positive_coercion():
    assert imports_api._normalise_zone_code("  ura:Central ") == "URA:central"
    assert imports_api._normalise_zone_code("downtown") == "SG:downtown"
    assert imports_api._normalise_zone_code("   ") is None
    assert imports_api._coerce_positive("10") == 10.0
    assert imports_api._coerce_positive(-5) is None
    assert imports_api._coerce_positive("oops") is None


def test_import_result_from_record_and_parse_summary():
    uploaded_at = datetime.utcnow()
    record = SimpleNamespace(
        id="imp-1",
        filename="model.dxf",
        content_type="application/dxf",
        size_bytes=1024,
        storage_path="s3://bucket/model.dxf",
        vector_storage_path=None,
        uploaded_at=uploaded_at,
        layer_metadata=[{"name": "Level 1"}],
        detected_floors=[{"name": "Level 1", "unit_ids": ["U1"]}],
        detected_units=["U1"],
        vector_summary={"paths": 10},
        zone_code="SG:central",
        metric_overrides={"site_area_sqm": 1200.0},
        parse_status="parsed",
    )
    result = imports_api._import_result_from_record(record)
    assert result.import_id == "imp-1"
    assert result.detected_floors[0].unit_ids == ["U1"]

    summary_record = SimpleNamespace(
        detected_floors=[{"name": "Level 1", "unit_ids": ["U1"]}],
        detected_units=["U1"],
        layer_metadata=[{"name": "L1"}],
        parse_result={
            "detected_floors": [],
            "detected_units": [],
            "layer_metadata": [],
        },
        parse_status="parsed",
    )
    summary = imports_api._build_parse_summary(summary_record)
    assert summary["floors"] == 1
    assert summary["layers"] == 1
    assert summary["status"] == "parsed"


@pytest.mark.asyncio
async def test_vectorize_payload_if_requested_handles_async_job(monkeypatch):
    dispatch = SimpleNamespace(
        result={"paths": [{"layer": "A"}], "walls": []}, status="completed"
    )

    async def fake_enqueue(*_args, **_kwargs):
        return dispatch

    async def fake_vectorize(*_args, **_kwargs):
        return {"paths": [{"layer": "B"}]}

    monkeypatch.setattr(imports_api.job_queue, "enqueue", fake_enqueue)
    monkeypatch.setattr(imports_api, "vectorize_floorplan", fake_vectorize)

    (
        vector_payload,
        summary,
        derived_layers,
    ) = await imports_api._vectorize_payload_if_requested(
        enable_raster_processing=True,
        raw_payload=b"bytes",
        filename="plan.pdf",
        content_type="application/pdf",
        infer_walls=True,
        import_id="imp-1",
        layer_metadata=[],
    )
    assert vector_payload["paths"]
    assert summary["paths"] >= 0
    assert derived_layers is not None


@pytest.mark.asyncio
async def test_vectorize_payload_returns_none_when_disabled():
    result = await imports_api._vectorize_payload_if_requested(
        enable_raster_processing=False,
        raw_payload=b"bytes",
        filename="plan.pdf",
        content_type="application/pdf",
        infer_walls=False,
        import_id="imp-1",
        layer_metadata=[],
    )
    assert result == (None, None, None)
