"""Tests for raster to vector worker utilities."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest

from backend.jobs.raster_vector import vectorize_floorplan

SAMPLE_PDF = (
    Path(__file__).resolve().parents[3] / "samples" / "pdf" / "floor_simple.pdf"
)


@pytest.mark.asyncio
async def test_vectorize_pdf_produces_paths_and_walls() -> None:
    pytest.importorskip("fitz")
    payload = SAMPLE_PDF.read_bytes()
    result = await vectorize_floorplan(
        payload,
        content_type="application/pdf",
        filename="floor_simple.pdf",
        infer_walls=True,
    )

    assert result["source"] == "pdf"
    assert result["options"]["infer_walls"] is True
    assert isinstance(result["paths"], list) and result["paths"]
    assert all("points" in entry for entry in result["paths"])
    assert isinstance(result["walls"], list)
    json.dumps(result)


@pytest.mark.asyncio
async def test_wall_inference_toggle_expands_results() -> None:
    pytest.importorskip("fitz")
    payload = SAMPLE_PDF.read_bytes()
    baseline = await vectorize_floorplan(
        payload,
        content_type="application/pdf",
        filename="floor_simple.pdf",
        infer_walls=False,
    )
    enhanced = await vectorize_floorplan(
        payload,
        content_type="application/pdf",
        filename="floor_simple.pdf",
        infer_walls=True,
    )

    assert baseline["options"]["infer_walls"] is False
    assert enhanced["options"]["infer_walls"] is True
    assert len(enhanced["walls"]) >= len(baseline["walls"])


@pytest.mark.asyncio
async def test_vectorize_jpeg_detects_bitmap_walls() -> None:
    Image = pytest.importorskip("PIL.Image")

    image = Image.new("L", (24, 24), color=255)
    for x in range(4, 20):
        image.putpixel((x, 12), 0)
    for y in range(6, 18):
        image.putpixel((12, y), 0)

    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    payload = buffer.getvalue()

    result = await vectorize_floorplan(
        payload,
        content_type="image/jpeg",
        filename="floorplan.jpg",
        infer_walls=True,
    )

    assert result["source"] == "jpeg"
    assert result["options"]["infer_walls"] is True
    assert result["paths"] == []
    assert result["bounds"] == {"width": 24.0, "height": 24.0}
    assert result["walls"]
