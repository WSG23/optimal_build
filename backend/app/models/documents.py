"""Document corpus + extraction pipeline (PR2).

CRE workflows live on PDFs — valuations, term sheets, lease abstracts,
zoning letters, environmental reports. ``imports`` already handles CAD/BIM
specifically; this is the general-purpose dropbox for everything else.

Design:

* :class:`Document` is the immutable upload record. It carries metadata about
  the file and a pointer to wherever the bytes live (S3 key, local path).
* :class:`DocumentExtraction` is the mutable processing record — one row per
  extraction pass. Re-running the extractor (newer model, different config)
  creates a new row rather than overwriting. ``status`` reflects async
  pipeline state so workers can pick up pending rows safely.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import UUID, BaseModel
from app.models.types import FlexibleJSONB


class Document(BaseModel):
    """Uploaded artefact (PDF, image, term sheet, valuation report)."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    organization_id = mapped_column(UUID(), nullable=True, index=True)
    uploaded_by = mapped_column(UUID(), nullable=True)

    related_entity_type: Mapped[Optional[str]] = mapped_column(String(80))
    related_entity_id: Mapped[Optional[str]] = mapped_column(String(64))

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[Optional[str]] = mapped_column(String(64))

    source: Mapped[str] = mapped_column(String(40), nullable=False, default="upload")
    classification: Mapped[Optional[str]] = mapped_column(String(60))
    language: Mapped[Optional[str]] = mapped_column(String(10))
    page_count: Mapped[Optional[int]] = mapped_column(Integer)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )

    extractions: Mapped[list["DocumentExtraction"]] = relationship(
        "DocumentExtraction",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "idx_documents_related_entity",
            "related_entity_type",
            "related_entity_id",
        ),
        Index(
            "idx_documents_org_uploaded",
            "organization_id",
            "uploaded_at",
        ),
        Index(
            "idx_documents_classification",
            "classification",
            "uploaded_at",
        ),
        Index("uq_documents_sha256", "sha256"),
    )


class DocumentExtraction(BaseModel):
    """One processing pass over a :class:`Document` — OCR, NLP, structuring."""

    __tablename__ = "document_extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    extractor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(60), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    text: Mapped[Optional[str]] = mapped_column(Text)
    structured: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    entities: Mapped[Optional[list]] = mapped_column(FlexibleJSONB)
    embedding_storage_key: Mapped[Optional[str]] = mapped_column(String(255))

    error: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped[Document] = relationship("Document", back_populates="extractions")

    __table_args__ = (
        Index(
            "idx_doc_extractions_status_created",
            "status",
            "created_at",
        ),
        Index(
            "idx_doc_extractions_doc_extractor",
            "document_id",
            "extractor_name",
            "extractor_version",
        ),
    )


__all__ = ["Document", "DocumentExtraction"]
