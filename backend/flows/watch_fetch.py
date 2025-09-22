"""Prefect flow that monitors reference sources and fetches updated documents."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from prefect import flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.rkp import RefDocument, RefSource
from app.services.reference_sources import FetchedDocument, ReferenceSourceFetcher
from app.services.reference_storage import ReferenceStorage


@flow(name="watch-reference-sources")
async def watch_reference_sources(
    session_factory: "async_sessionmaker[AsyncSession]",
    *,
    fetcher: Optional[ReferenceSourceFetcher] = None,
    storage: Optional[ReferenceStorage] = None,
) -> List[Dict[str, Any]]:
    """Iterate active ``RefSource`` entries and persist changed documents."""

    fetcher = fetcher or ReferenceSourceFetcher()
    storage = storage or ReferenceStorage()
    results: List[Dict[str, Any]] = []

    async with session_factory() as session:
        sources = (
            await session.execute(
                select(RefSource).where(RefSource.is_active.is_(True)).order_by(RefSource.id)
            )
        ).scalars().all()

        for source in sources:
            latest = await _latest_document(session, source.id)
            fetched = await fetcher.fetch(source, latest)
            if fetched is None:
                continue

            file_hash = hashlib.sha256(fetched.content).hexdigest()
            duplicate = await _document_by_hash(session, source.id, file_hash)
            if duplicate:
                duplicate.http_etag = fetched.etag or duplicate.http_etag
                duplicate.http_last_modified = fetched.last_modified or duplicate.http_last_modified
                duplicate.suspected_update = False
                await session.flush()
                continue

            suffix = _determine_suffix(source.fetch_kind, fetched)
            location = await storage.write_document(
                source_id=source.id,
                payload=fetched.content,
                suffix=suffix,
            )
            document = RefDocument(
                source_id=source.id,
                version_label=_derive_version_label(fetched, file_hash),
                storage_path=location.storage_path,
                file_hash=file_hash,
                http_etag=fetched.etag,
                http_last_modified=fetched.last_modified,
                suspected_update=True,
            )
            session.add(document)
            await session.flush()
            results.append(
                {
                    "document_id": document.id,
                    "source_id": source.id,
                    "storage_path": document.storage_path,
                    "uri": location.uri,
                }
            )

        await session.commit()

    return results


async def _latest_document(session: AsyncSession, source_id: int) -> Optional[RefDocument]:
    stmt = (
        select(RefDocument)
        .where(RefDocument.source_id == source_id)
        .order_by(RefDocument.id.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def _document_by_hash(
    session: AsyncSession,
    source_id: int,
    file_hash: str,
) -> Optional[RefDocument]:
    stmt = (
        select(RefDocument)
        .where(RefDocument.source_id == source_id)
        .where(RefDocument.file_hash == file_hash)
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def _determine_suffix(fetch_kind: Optional[str], fetched: FetchedDocument) -> str:
    kind = (fetch_kind or "").lower()
    if kind == "pdf":
        return ".pdf"
    if kind in {"html", "sitemap"}:
        return ".html"
    content_type = (fetched.content_type or "").lower()
    if "pdf" in content_type:
        return ".pdf"
    if "html" in content_type or "xml" in content_type:
        return ".html"
    return ".bin"


def _derive_version_label(fetched: FetchedDocument, file_hash: str) -> str:
    for candidate in (fetched.last_modified, fetched.etag):
        if candidate:
            return candidate
    return file_hash[:12]


__all__ = ["watch_reference_sources"]
