"""Vector payload parsing tests for the CAD parser job."""

import json
from typing import Dict

import pytest
from sqlalchemy import select

from app.models.imports import ImportRecord
from app.models.overlay import OverlaySourceGeometry
from backend.app.services.storage import reset_storage_service
from backend.jobs.parse_cad import parse_import_job


@pytest.mark.asyncio
async def test_parse_job_uses_vector_payload(
    async_session_factory,
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(tmp_path))
    reset_storage_service()

    pdf_path = tmp_path / "vector" / "plan.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_bytes = b"%PDF-1.4\n%"
    pdf_path.write_bytes(pdf_bytes)

    vector_payload: Dict[str, object] = {
        "source": "vector",
        "paths": [
            {
                "points": [[0, 0], [6, 0], [6, 5], [0, 5], [0, 0]],
                "layer": "1",
                "stroke_width": 0.25,
            },
            {
                "points": [[0, 0], [3, 0]],
                "layer": "sketch",
                "stroke_width": 0.1,
            },
        ],
        "walls": [
            {
                "start": [0, 0],
                "end": [6, 0],
                "thickness": 0.2,
                "confidence": 0.95,
                "source": "vector",
            },
            {
                "start": [6, 0],
                "end": [6, 5],
                "thickness": 0.2,
                "confidence": 0.9,
                "source": "vector",
            },
        ],
        "bounds": {"width": 12, "height": 8},
        "options": {"infer_walls": True},
    }
    vector_path = pdf_path.with_suffix(pdf_path.suffix + ".vectors.json")
    vector_path.write_text(json.dumps(vector_payload))

    import_id = "vector-import"
    project_id = 101

    try:
        async with async_session_factory() as session:
            record = ImportRecord(
                id=import_id,
                project_id=project_id,
                filename=pdf_path.name,
                content_type="application/pdf",
                size_bytes=len(pdf_bytes),
                storage_path=str(pdf_path),
                vector_storage_path=str(vector_path),
            )
            session.add(record)
            await session.commit()

        result = await parse_import_job(import_id)

        async with async_session_factory() as session:
            refreshed = await session.get(ImportRecord, import_id)
            assert refreshed is not None
            assert refreshed.parse_status == "completed"
            assert refreshed.parse_result is not None
            graph = refreshed.parse_result["graph"]
            assert graph["walls"], "Wall entities should be present in parsed graph"
            assert graph["spaces"], "Closed vector paths should produce spaces"
            assert refreshed.parse_result["floors"] == 1
            assert refreshed.parse_result["units"] == len(graph["spaces"])

            overlay_record = (
                await session.execute(select(OverlaySourceGeometry))
            ).scalars().one()
            metadata = refreshed.parse_result["metadata"]
            assert metadata["source"] == "vector_payload"
            assert metadata["overlay_source_id"] == overlay_record.id
            assert metadata["overlay_checksum"] == overlay_record.checksum

        assert result["metadata"]["source"] == "vector_payload"
        assert result["graph"]["walls"], "Job result should expose wall geometry"
    finally:
        reset_storage_service()
