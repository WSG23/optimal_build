"""Prefect flow that monitors reference sources and fetches updated documents."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from prefect import flow
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import AsyncSessionLocal
from app.models.rkp import RefDocument, RefSource
from app.services.reference_sources import FetchedDocument, ReferenceSourceFetcher
from app.services.reference_storage import ReferenceStorage


SUPPORTED_FETCH_KINDS = {"pdf", "html", "sitemap"}


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
    seen_document_ids: set[int] = set()
    seen_hashes: Dict[Tuple[int, str], int] = {}

    async with session_factory() as session:
        sources = (
            await session.execute(
                select(RefSource)
                .where(RefSource.is_active.is_(True))
                .order_by(RefSource.id)
            )
        ).scalars().all()

        for source in sources:
            await _process_source(
                session,
                source,
                fetcher,
                storage,
                results,
                seen_document_ids,
                seen_hashes,
            )

        await session.commit()

    return results


async def _process_source(
    session: AsyncSession,
    source: RefSource,
    fetcher: ReferenceSourceFetcher,
    storage: ReferenceStorage,
    results: List[Dict[str, Any]],
    seen_document_ids: set[int],
    seen_hashes: Dict[Tuple[int, str], int],
) -> None:
    fetch_kind = (source.fetch_kind or "pdf").lower()
    if fetch_kind not in SUPPORTED_FETCH_KINDS:
        return
    latest = await _latest_document(session, source.id)
    if latest and latest.suspected_update:
        # Skip sources that already have an unprocessed update to avoid
        # repeatedly flagging the same document across flow runs.
        return
    fetched = await fetcher.fetch(source, latest)
    if fetched is None:
        return

    file_hash = hashlib.sha256(fetched.content).hexdigest()
    dedupe_key = (source.id, file_hash)
    existing_id = seen_hashes.get(dedupe_key)
    if existing_id is not None:
        existing_document = await session.get(RefDocument, existing_id)
        if existing_document:
            existing_document.http_etag = fetched.etag or existing_document.http_etag
            existing_document.http_last_modified = (
                fetched.last_modified or existing_document.http_last_modified
            )
            existing_document.suspected_update = False
            await session.flush()
        return

    duplicate = await _document_by_hash(session, source.id, file_hash)
    if duplicate:
        duplicate.http_etag = fetched.etag or duplicate.http_etag
        duplicate.http_last_modified = fetched.last_modified or duplicate.http_last_modified
        duplicate.suspected_update = False
        await session.flush()
        seen_hashes[dedupe_key] = duplicate.id
        seen_document_ids.add(duplicate.id)
        return

    suffix = _determine_suffix(fetch_kind, fetched)
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
    seen_hashes[dedupe_key] = document.id
    if document.id in seen_document_ids:
        return
    seen_document_ids.add(document.id)
    results.append(
        {
            "document_id": document.id,
            "source_id": source.id,
            "storage_path": document.storage_path,
            "uri": location.uri,
        }
    )


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


@dataclass(slots=True)
class OfflineReferenceFixture:
    """Sample payload returned by the offline reference fetcher."""

    content: bytes
    content_type: str
    etag_suffix: str


class OfflineReferenceFetcher:
    """Serve deterministic reference payloads without performing HTTP requests."""

    def __init__(
        self,
        fixtures: Optional[Mapping[str, OfflineReferenceFixture]] = None,
    ) -> None:
        default_fixtures = _default_offline_fixtures()
        self._fixtures: Dict[str, OfflineReferenceFixture] = {
            key.upper(): value for key, value in (fixtures or default_fixtures).items()
        }

    async def fetch(
        self,
        source: RefSource,
        existing: Optional[RefDocument] = None,
    ) -> Optional[FetchedDocument]:
        if not getattr(source, "is_active", True):
            return None

        authority = (source.authority or "").upper()
        fixture = self._fixtures.get(authority)
        if not fixture:
            return None

        etag = f"{fixture.etag_suffix}-offline"
        return FetchedDocument(
            content=fixture.content,
            etag=etag,
            last_modified=f"{fixture.etag_suffix}-offline",
            content_type=fixture.content_type,
        )


def _default_offline_fixtures() -> Mapping[str, OfflineReferenceFixture]:
    html_payload = b"""
    <html>
      <body>
        <h2>Section 5.1 Height Controls</h2>
        <p>Maximum height is governed by the surrounding heritage character.</p>
        <h3>5.2 Daylight Plane</h3>
        <p>Maintain a 45 degree daylight plane from the opposite property line.</p>
      </body>
    </html>
    """
    pdf_payload = (
        "1.1 Fire Safety Obligations\n"
        "Provide active fire protection systems in accordance with Table 3.\n"
        "1.2 Egress Provision\n"
        "Buildings must support two independent means of egress.\n"
    ).encode("utf-8")
    drainage_payload = (
        "2.1 Stormwater Capacity\n"
        "Design attenuation tanks to accommodate a 100-year storm event.\n"
    ).encode("utf-8")
    return {
        "URA": OfflineReferenceFixture(
            content=html_payload,
            content_type="text/html; charset=utf-8",
            etag_suffix="ura",
        ),
        "BCA": OfflineReferenceFixture(
            content=pdf_payload,
            content_type="application/pdf",
            etag_suffix="bca",
        ),
        "SCDF": OfflineReferenceFixture(
            content=pdf_payload,
            content_type="application/pdf",
            etag_suffix="scdf",
        ),
        "PUB": OfflineReferenceFixture(
            content=drainage_payload,
            content_type="application/pdf",
            etag_suffix="pub",
        ),
    }


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the watch_reference_sources flow once and optionally emit a summary."
        ),
    )
    parser.add_argument(
        "--storage-path",
        type=Path,
        default=None,
        help="Directory used by ReferenceStorage (defaults to REF_STORAGE_LOCAL_PATH).",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use deterministic offline fixtures instead of performing HTTP requests.",
    )
    parser.add_argument(
        "--summary-path",
        type=Path,
        default=None,
        help="Optional path to write a JSON summary of the ingestion run.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Present for CLI parity; the flow always runs once.",
    )
    parser.add_argument(
        "--min-documents",
        type=int,
        default=1,
        help="Fail the run if fewer than this number of documents exist after execution.",
    )
    return parser


async def _run_once(
    *,
    storage: ReferenceStorage,
    fetcher: Optional[ReferenceSourceFetcher] = None,
) -> List[Dict[str, Any]]:
    return await watch_reference_sources(
        AsyncSessionLocal,
        fetcher=fetcher,
        storage=storage,
    )


async def _summarise_ingestion(
    results: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "results": list(results),
    }
    async with AsyncSessionLocal() as session:
        document_count = await session.scalar(select(func.count()).select_from(RefDocument))
        source_count = await session.scalar(select(func.count()).select_from(RefSource))
        summary["document_count"] = int(document_count or 0)
        summary["source_count"] = int(source_count or 0)
    unique_document_ids = {
        item.get("document_id")
        for item in summary["results"]
        if item.get("document_id") is not None
    }
    summary["inserted_unique"] = len(unique_document_ids)
    summary["results_total"] = len(summary["results"])
    summary["inserted"] = summary["inserted_unique"]
    return summary


def main(argv: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """CLI entry point used by CI smoke tests."""

    parser = _build_cli_parser()
    args = parser.parse_args(argv)
    storage = ReferenceStorage(
        base_path=args.storage_path if args.storage_path is not None else None,
    )

    fetcher: Optional[ReferenceSourceFetcher]
    if args.offline:
        fetcher = OfflineReferenceFetcher()  # type: ignore[assignment]
    else:
        fetcher = ReferenceSourceFetcher()

    results = asyncio.run(_run_once(storage=storage, fetcher=fetcher))
    summary = asyncio.run(_summarise_ingestion(results))

    if summary["document_count"] < args.min_documents:
        raise SystemExit(
            f"Expected at least {args.min_documents} documents after ingestion; "
            f"observed {summary['document_count']}."
        )

    if args.summary_path:
        args.summary_path.parent.mkdir(parents=True, exist_ok=True)
        args.summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True))

    return summary


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()


__all__ = ["OfflineReferenceFetcher", "OfflineReferenceFixture", "watch_reference_sources"]
