"""Prefect flow that parses stored reference documents into clauses."""

from __future__ import annotations

from typing import Dict, List, Optional

from prefect import flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.models.rkp import RefClause, RefDocument, RefSource
from app.services.ref_documents import DocumentStorageService, get_document_storage_service
from app.services.ref_parsers import ClauseSegment, parse_document_clauses


def _classify_quality(segment: ClauseSegment) -> str:
    if segment.heading and segment.text_span:
        return "high"
    if segment.text_span:
        return "medium"
    return "low"


@flow(name="parse-reference-documents")
async def parse_reference_documents(
    session_factory: "async_sessionmaker[AsyncSession]",
    *,
    storage_service: Optional[DocumentStorageService] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, int]]:
    """Parse pending :class:`RefDocument` rows into :class:`RefClause` entries."""

    storage = storage_service or get_document_storage_service()
    summaries: List[Dict[str, int]] = []

    async with session_factory() as session:
        stmt = (
            select(RefDocument)
            .options(selectinload(RefDocument.source))
            .where(RefDocument.suspected_update.is_(True))
            .order_by(RefDocument.id)
        )
        if limit is not None:
            stmt = stmt.limit(limit)

        documents = (await session.execute(stmt)).scalars().unique().all()
        for document in documents:
            source = await _resolve_source(session, document)
            if source is None:
                continue

            payload = await storage.read_document(document.storage_path)
            segments = parse_document_clauses(payload, source.fetch_kind or "pdf")

            await _clear_existing_clauses(session, document.id)
            for segment in segments:
                clause = RefClause(
                    document_id=document.id,
                    clause_ref=segment.clause_ref,
                    section_heading=segment.heading,
                    text_span=segment.text_span,
                    page_from=segment.page_from,
                    page_to=segment.page_to,
                    extraction_quality=_classify_quality(segment),
                )
                session.add(clause)

            document.suspected_update = False
            await session.flush()
            await session.commit()
            summaries.append({"document_id": document.id, "clauses": len(segments)})

    return summaries


async def _resolve_source(session: AsyncSession, document: RefDocument):
    source = getattr(document, "source", None)
    if isinstance(source, list):
        if source:
            return source[0]
        source = None
    if source is not None:
        return source
    source_id = getattr(document, "source_id", None)
    if source_id is None:
        return None
    return await session.get(RefSource, source_id)


async def _clear_existing_clauses(session: AsyncSession, document_id: int) -> None:
    database = getattr(session, "_database", None)
    if database is not None and hasattr(database, "_data"):
        rows = list(database._data.get(RefClause, []))  # type: ignore[attr-defined]
        database._data[RefClause] = [  # type: ignore[attr-defined]
            row for row in rows if getattr(row, "document_id", None) != document_id
        ]
        return

    existing = (
        await session.execute(select(RefClause).where(RefClause.document_id == document_id))
    ).scalars().all()
    delete_method = getattr(session, "delete", None)
    if delete_method is None:
        return
    for clause in existing:
        await delete_method(clause)


__all__ = ["parse_reference_documents"]
