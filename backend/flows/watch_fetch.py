"""Prefect flow that monitors reference sources for updated documents."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Mapping, Optional

from prefect import flow
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.rkp import RefDocument, RefSource
from app.services.ref_documents import (
    DocumentStorageService,
    compute_document_checksum,
    get_document_storage_service,
)
from app.services.ref_fetcher import DocumentFetcher, FetchResponse, get_document_fetcher


@dataclass(slots=True)
class FetchedPayload:
    """Payload returned when a reference document is fetched."""

    payload: bytes
    etag: str | None
    last_modified: str | None
    content_type: str | None


@dataclass(slots=True)
class FetchResult:
    """Summary describing a newly created :class:`RefDocument`."""

    source_id: int
    document_id: int
    storage_path: str
    checksum: str
    suspected_update: bool
    etag: str | None
    last_modified: str | None


_EXTENSION_BY_KIND = {"pdf": "pdf", "html": "html", "sitemap": "xml"}


def _extension_for_kind(kind: str | None) -> str:
    return _EXTENSION_BY_KIND.get((kind or "pdf").lower(), "bin")


def _normalize_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    return {str(key).lower(): str(value) for key, value in headers.items()}


def _header_lookup(headers: Iterable[Mapping[str, str]], key: str) -> str | None:
    key_lower = key.lower()
    for mapping in headers:
        for header_key, value in mapping.items():
            if str(header_key).lower() == key_lower:
                return str(value)
    return None


async def _latest_document(session: AsyncSession, source_id: int) -> RefDocument | None:
    stmt: Select[RefDocument] = (
        select(RefDocument)
        .where(RefDocument.source_id == source_id)
        .order_by(RefDocument.retrieved_at.desc(), RefDocument.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def _fetch_source_document(
    source: RefSource,
    fetcher: DocumentFetcher,
    previous: RefDocument | None,
) -> FetchedPayload | None:
    conditional_headers: Dict[str, str] = {}
    if previous and previous.http_etag:
        conditional_headers["If-None-Match"] = previous.http_etag
    if previous and previous.http_last_modified:
        conditional_headers["If-Modified-Since"] = previous.http_last_modified

    head_headers: Dict[str, str] = {}
    if source.fetch_kind in {"pdf", "html", "sitemap"}:
        try:
            head_response: FetchResponse = await fetcher.head(
                source.landing_url, headers=conditional_headers or None
            )
        except Exception:  # pragma: no cover - defensive; network errors are mocked in tests
            head_response = None  # type: ignore[assignment]
        if head_response is not None:
            head_headers = _normalize_headers(head_response.headers)
            if head_response.status_code == 304:
                return None
            if (
                previous
                and conditional_headers
                and head_response.status_code == 200
                and (
                    (
                        previous.http_etag
                        and head_headers.get("etag") == previous.http_etag
                    )
                    or (
                        not head_headers.get("etag")
                        and previous.http_last_modified
                        and head_headers.get("last-modified")
                        == previous.http_last_modified
                    )
                )
            ):
                return None
            if head_response.status_code >= 400 and head_response.status_code not in {405, 501}:
                return None

    try:
        get_response = await fetcher.get(
            source.landing_url, headers=conditional_headers or None
        )
    except Exception:  # pragma: no cover - defensive
        return None

    if get_response.status_code in {304, 412}:
        return None
    if get_response.status_code >= 400:
        return None

    payload = get_response.content
    if not payload:
        return None

    response_headers = _normalize_headers(get_response.headers)
    etag = _header_lookup((response_headers, head_headers), "etag")
    last_modified = _header_lookup((response_headers, head_headers), "last-modified")
    content_type = _header_lookup((response_headers, head_headers), "content-type")
    return FetchedPayload(
        payload=payload,
        etag=etag,
        last_modified=last_modified,
        content_type=content_type,
    )


def _derive_version_label(fetched: FetchedPayload) -> str:
    if fetched.last_modified:
        return fetched.last_modified
    if fetched.etag:
        return fetched.etag.strip('"')
    return datetime.utcnow().isoformat()


@flow(name="watch-reference-sources")
async def watch_reference_sources(
    session_factory: "async_sessionmaker[AsyncSession]",
    *,
    fetcher: Optional[DocumentFetcher] = None,
    storage_service: Optional[DocumentStorageService] = None,
    limit: Optional[int] = None,
) -> List[FetchResult]:
    """Iterate active :class:`RefSource` rows and record refreshed documents."""

    created_fetcher = False
    if fetcher is None:
        fetcher = get_document_fetcher()
        created_fetcher = True
    storage = storage_service or get_document_storage_service()

    results: List[FetchResult] = []
    try:
        async with session_factory() as session:
            stmt = select(RefSource).where(RefSource.is_active.is_(True)).order_by(RefSource.id)
            if limit is not None:
                stmt = stmt.limit(limit)
            sources = (await session.execute(stmt)).scalars().all()

            for source in sources:
                previous = await _latest_document(session, source.id)
                fetched = await _fetch_source_document(source, fetcher, previous)
                if fetched is None:
                    continue

                checksum = compute_document_checksum(fetched.payload)
                if previous and previous.file_hash == checksum:
                    continue

                extension = _extension_for_kind(source.fetch_kind)
                stored = await storage.write_document(
                    source=source,
                    payload=fetched.payload,
                    extension=extension,
                )

                document = RefDocument(
                    source_id=source.id,
                    version_label=_derive_version_label(fetched),
                    storage_path=stored.storage_path,
                    file_hash=checksum,
                    http_etag=fetched.etag,
                    http_last_modified=fetched.last_modified,
                    suspected_update=True,
                )
                session.add(document)
                await session.flush()
                await session.commit()

                results.append(
                    FetchResult(
                        source_id=source.id,
                        document_id=document.id,
                        storage_path=document.storage_path,
                        checksum=document.file_hash,
                        suspected_update=document.suspected_update,
                        etag=document.http_etag,
                        last_modified=document.http_last_modified,
                    )
                )
    finally:
        if created_fetcher and hasattr(fetcher, "aclose"):
            await fetcher.aclose()  # type: ignore[func-returns-value]

    return results


__all__ = ["FetchResult", "watch_reference_sources"]
