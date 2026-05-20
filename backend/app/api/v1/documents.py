"""Document corpus endpoints (PR2).

Thin layer over the ``documents`` and ``document_extractions`` tables:

* ``POST /documents`` — register an uploaded document. The actual bytes are
  expected to land via the existing storage backend (S3/MinIO) — this route
  just persists the metadata and creates a ``pending`` extraction row so a
  worker can pick it up.
* ``GET /documents/{id}`` — return the document plus its extraction history.
* ``PATCH /documents/{id}/extractions/{extraction_id}`` — worker callback
  to set ``status``, ``text``, ``structured``, ``error``.

The extraction worker itself lives outside this PR — this is the schema
contract the worker will speak to.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import RequestIdentity, get_db, get_identity, require_reviewer
from app.models.documents import Document, DocumentExtraction
from app.services.analytics_capture import (
    capture_raw_artifact,
    capture_status_transition,
    capture_success,
)

router = APIRouter(prefix="/documents", tags=["telemetry"])


class DocumentIn(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str | None = Field(default=None, max_length=100)
    size_bytes: int | None = Field(default=None, ge=0)
    storage_key: str = Field(min_length=1)
    sha256: str | None = Field(default=None, max_length=64)
    source: str = Field(default="upload", max_length=40)
    classification: str | None = Field(default=None, max_length=60)
    language: str | None = Field(default=None, max_length=10)
    page_count: int | None = Field(default=None, ge=0)
    related_entity_type: str | None = Field(default=None, max_length=80)
    related_entity_id: str | None = Field(default=None, max_length=64)
    extractor_name: str | None = Field(default=None, max_length=120)
    extractor_version: str | None = Field(default=None, max_length=60)


class ExtractionOut(BaseModel):
    id: int
    extractor_name: str
    extractor_version: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error: str | None
    created_at: datetime


class DocumentOut(BaseModel):
    id: int
    filename: str
    mime_type: str | None
    size_bytes: int | None
    storage_key: str
    sha256: str | None
    source: str
    classification: str | None
    language: str | None
    page_count: int | None
    related_entity_type: str | None
    related_entity_id: str | None
    uploaded_at: datetime
    extractions: list[ExtractionOut]


class ExtractionPatch(BaseModel):
    status: str = Field(min_length=1, max_length=20)
    text: str | None = None
    structured: dict[str, Any] | None = None
    entities: list[dict[str, Any]] | None = None
    embedding_storage_key: str | None = Field(default=None, max_length=255)
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


def _serialize_extraction(row: DocumentExtraction) -> ExtractionOut:
    return ExtractionOut(
        id=row.id,
        extractor_name=row.extractor_name,
        extractor_version=row.extractor_version,
        status=row.status,
        started_at=row.started_at,
        completed_at=row.completed_at,
        error=row.error,
        created_at=row.created_at,
    )


def _serialize_document(row: Document) -> DocumentOut:
    return DocumentOut(
        id=row.id,
        filename=row.filename,
        mime_type=row.mime_type,
        size_bytes=row.size_bytes,
        storage_key=row.storage_key,
        sha256=row.sha256,
        source=row.source,
        classification=row.classification,
        language=row.language,
        page_count=row.page_count,
        related_entity_type=row.related_entity_type,
        related_entity_id=row.related_entity_id,
        uploaded_at=row.uploaded_at,
        extractions=[_serialize_extraction(e) for e in row.extractions],
    )


@router.post(
    "",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_document(
    body: DocumentIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    identity: RequestIdentity = Depends(get_identity),
) -> DocumentOut:
    """Register an uploaded document and queue a pending extraction row."""

    doc = Document(
        uploaded_by=identity.user_id,
        filename=body.filename,
        mime_type=body.mime_type,
        size_bytes=body.size_bytes,
        storage_key=body.storage_key,
        sha256=body.sha256,
        source=body.source,
        classification=body.classification,
        language=body.language,
        page_count=body.page_count,
        related_entity_type=body.related_entity_type,
        related_entity_id=body.related_entity_id,
    )
    db.add(doc)
    await db.flush()

    if body.extractor_name:
        extraction = DocumentExtraction(
            document_id=doc.id,
            extractor_name=body.extractor_name,
            extractor_version=body.extractor_version or "v0",
            status="pending",
        )
        db.add(extraction)
        await db.flush()
        await capture_status_transition(
            db,
            entity_type="document_extraction",
            entity_id=str(extraction.id),
            status_field="status",
            from_status=None,
            to_status="pending",
            reason="document_registered",
            identity=identity,
            request_id=request.headers.get("x-request-id"),
            correlation_id=request.scope.get("correlation_id"),
            metadata={"document_id": doc.id},
        )

    await capture_raw_artifact(
        db,
        artifact_type="document_upload",
        source="documents.register",
        storage_key=body.storage_key,
        sha256=body.sha256,
        size_bytes=body.size_bytes,
        mime_type=body.mime_type,
        entity_type="document",
        entity_id=str(doc.id),
        request_id=request.headers.get("x-request-id"),
        metadata={
            "filename": body.filename,
            "source": body.source,
            "classification": body.classification,
            "language": body.language,
            "page_count": body.page_count,
        },
    )
    await capture_success(
        db,
        source="documents.register",
        capture_type="ingestion",
        operation="register_document",
        request=request,
        identity=identity,
        request_payload=body.model_dump(mode="json"),
        entity_type="document",
        entity_id=str(doc.id),
        status_code=status.HTTP_201_CREATED,
    )

    await db.commit()
    fetched = await db.execute(
        select(Document)
        .options(selectinload(Document.extractions))
        .where(Document.id == doc.id)
    )
    return _serialize_document(fetched.scalar_one())


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    _: RequestIdentity = Depends(get_identity),
) -> DocumentOut:
    """Return a document and its extraction history."""

    result = await db.execute(
        select(Document)
        .options(selectinload(Document.extractions))
        .where(Document.id == document_id, Document.deleted_at.is_(None))
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return _serialize_document(doc)


@router.patch(
    "/{document_id}/extractions/{extraction_id}",
    response_model=ExtractionOut,
)
async def update_extraction(
    document_id: int,
    extraction_id: int,
    body: ExtractionPatch,
    request: Request,
    db: AsyncSession = Depends(get_db),
    identity: RequestIdentity = Depends(require_reviewer),
) -> ExtractionOut:
    """Update an extraction row; intended for worker callbacks."""

    result = await db.execute(
        select(DocumentExtraction).where(
            DocumentExtraction.id == extraction_id,
            DocumentExtraction.document_id == document_id,
        )
    )
    extraction = result.scalar_one_or_none()
    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found",
        )

    previous_status = extraction.status
    extraction.status = body.status
    if body.text is not None:
        extraction.text = body.text
    if body.structured is not None:
        extraction.structured = body.structured
    if body.entities is not None:
        extraction.entities = body.entities
    if body.embedding_storage_key is not None:
        extraction.embedding_storage_key = body.embedding_storage_key
    if body.error is not None:
        extraction.error = body.error
    if body.started_at is not None:
        extraction.started_at = body.started_at
    if body.completed_at is not None:
        extraction.completed_at = body.completed_at

    if previous_status != body.status:
        await capture_status_transition(
            db,
            entity_type="document_extraction",
            entity_id=str(extraction.id),
            status_field="status",
            from_status=previous_status,
            to_status=body.status,
            reason="extraction_patch",
            identity=identity,
            request_id=request.headers.get("x-request-id"),
            correlation_id=request.scope.get("correlation_id"),
            metadata={"document_id": document_id},
        )
    await capture_success(
        db,
        source="documents.extraction",
        capture_type="computation",
        operation="update_extraction",
        request=request,
        identity=identity,
        request_payload=body.model_dump(mode="json"),
        response_payload={
            "document_id": document_id,
            "extraction_id": extraction_id,
            "status": body.status,
        },
        raw_payload={
            "text": body.text,
            "structured": body.structured,
            "entities": body.entities,
            "error": body.error,
        },
        entity_type="document_extraction",
        entity_id=str(extraction.id),
    )
    await db.commit()
    await db.refresh(extraction)
    return _serialize_extraction(extraction)


__all__ = ["router"]
