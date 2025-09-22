"""Integration tests for CAD/BIM sample fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from jobs.parse_cad import _parse_dxf_payload, _parse_ifc_payload
from jobs.raster_vector import _vectorize_pdf

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "samples"


def test_ifc_sample_detects_multiple_storeys() -> None:
    """The IFC fixture should surface distinct storeys and associated spaces."""

    pytest.importorskip("ifcopenshell", reason="ifcopenshell is required for IFC parsing")

    payload = (SAMPLES_DIR / "ifc" / "office_small.ifc").read_bytes()
    parsed = _parse_ifc_payload(payload)

    assert len(parsed.floors) == 2
    floor_names = {floor["name"] for floor in parsed.floors}
    assert {"Ground Floor", "Level 02"} <= floor_names
    assert len(parsed.units) == 3
    assert parsed.metadata["source"] == "ifc"
    assert isinstance(parsed.layers, list)


def test_dxf_sample_exposes_layered_units() -> None:
    """The DXF fixture should surface unit counts and retain layer naming."""

    pytest.importorskip("ezdxf", reason="ezdxf is required for DXF parsing")

    path = SAMPLES_DIR / "dxf" / "flat_two_bed.dxf"
    payload = path.read_bytes()
    parsed = _parse_dxf_payload(payload)

    assert len(parsed.units) == 2
    assert parsed.metadata["entities"] == 2
    assert parsed.layers
    parsed_layer_names = {entry["name"].upper() for entry in parsed.layers}
    assert {"LEVEL_01", "LEVEL_02"}.issubset(parsed_layer_names)

    import ezdxf  # type: ignore  # noqa: WPS433

    doc = ezdxf.readfile(str(path))
    if hasattr(doc.layers, "names"):
        layer_names = {name.upper() for name in doc.layers.names()}
    else:
        layer_names = {layer.dxf.name.upper() for layer in doc.layers}
    assert {"LEVEL_01", "LEVEL_02"}.issubset(layer_names)


def test_pdf_sample_vectorizes_multiple_pages() -> None:
    """The PDF fixture should yield vector paths per page for wall detection."""

    pytest.importorskip("fitz", reason="PyMuPDF is required for PDF vectorization")

    payload = (SAMPLES_DIR / "pdf" / "floor_simple.pdf").read_bytes()
    result = _vectorize_pdf(payload)

    assert len(result.paths) >= 2
    layers = {path.layer for path in result.paths}
    assert {"0", "1"}.issubset(layers)
    assert result.walls, "Vector paths should produce baseline wall candidates"
