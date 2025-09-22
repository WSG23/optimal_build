"""Prefect flow that parses stored reference documents into clauses."""

from __future__ import annotations

from typing import List, Optional

from prefect import flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.models.rkp import RefClause, RefDocument, RefSource
from app.services.reference_parsers import ClauseParser, ParsedClause
from app.services.reference_storage import ReferenceStorage


@flow(name="parse-reference-documents")
async def parse_reference_documents(
    session_factory: "async_sessionmaker[AsyncSession]",
    *,
    storage: Optional[ReferenceStorage] = None,
    parser: Optional[ClauseParser] = None,
) -> List[int]:
    """Parse pending ``RefDocument`` records into ``RefClause`` entries."""

    storage = storage or ReferenceStorage()
    parser = parser or ClauseParser()
    processed: List[int] = []

    async with session_factory() as session:
        documents = (
            await session.execute(
                select(RefDocument)
                .options(selectinload(RefDocument.source))
                .where(RefDocument.suspected_update.is_(True))
                .order_by(RefDocument.id)
            )
        ).scalars().all()

        for document in documents:
            payload = await storage.read_document(document.storage_path)
            fetch_kind = await _resolve_fetch_kind(session, document)
            clauses = parser.parse(fetch_kind, payload)
            await _replace_clauses(session, document, clauses)
            document.suspected_update = False
            processed.append(document.id)

        await session.commit()

    return processed


async def _replace_clauses(
    session: AsyncSession,
    document: RefDocument,
    clauses: List[ParsedClause],
) -> None:
    existing = (
        await session.execute(select(RefClause).where(RefClause.document_id == document.id))
    ).scalars().all()
    for clause_row in existing:
        await session.delete(clause_row)
    for clause in clauses:
        session.add(
            RefClause(
                document_id=document.id,
                clause_ref=clause.clause_ref,
                section_heading=clause.heading,
                text_span=clause.text,
                page_from=clause.page_from,
                page_to=clause.page_to,
                extraction_quality=clause.quality,
            )
        )
    await session.flush()


async def _resolve_fetch_kind(session: AsyncSession, document: RefDocument) -> str:
    source = getattr(document, "source", None)
    kind = getattr(source, "fetch_kind", None)
    if isinstance(kind, str) and kind:
        return kind
    result = await session.execute(
        select(RefSource).where(RefSource.id == document.source_id).limit(1)
    )
    source_row = result.scalar_one_or_none()
    if source_row and getattr(source_row, "fetch_kind", None):
        return source_row.fetch_kind
    return "pdf"


__all__ = ["parse_reference_documents"]
