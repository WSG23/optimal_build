"""Tests for raster to vector worker utilities."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest

pytest.importorskip("PIL")
from PIL import Image, ImageDraw

from backend.jobs.raster_vector import (
    RasterVectorOptions,
    _vectorize_bitmap_image,
    vectorize_floorplan,
)

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


def test_vectorize_bitmap_image_detects_walls() -> None:
    image = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 28, 56, 36), fill="black")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    payload = buffer.getvalue()

    options = RasterVectorOptions(infer_walls=True)
    result = _vectorize_bitmap_image(payload, options)

    assert result.source == "bitmap"
    assert result.bounds == (64.0, 64.0)
    assert result.walls
