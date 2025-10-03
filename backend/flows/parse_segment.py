"""Prefect flow that parses stored reference documents into clauses."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from prefect import flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import AsyncSessionLocal
from app.models.rkp import RefClause, RefDocument, RefSource
from app.services.reference_parsers import ClauseParser, ParsedClause
from app.services.reference_storage import ReferenceStorage

from ._prefect_utils import resolve_flow_callable


@flow(name="parse-reference-documents")
async def parse_reference_documents(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    storage: ReferenceStorage | None = None,
    parser: ClauseParser | None = None,
) -> list[int]:
    """Parse pending ``RefDocument`` records into ``RefClause`` entries."""

    storage = storage or ReferenceStorage()
    parser = parser or ClauseParser()
    processed: list[int] = []

    async with session_factory() as session:
        documents = (
            (
                await session.execute(
                    select(RefDocument)
                    .options(selectinload(RefDocument.source))
                    .where(RefDocument.suspected_update.is_(True))
                    .order_by(RefDocument.id)
                )
            )
            .scalars()
            .all()
        )

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
    clauses: list[ParsedClause],
) -> None:
    existing = (
        (
            await session.execute(
                select(RefClause).where(RefClause.document_id == document.id)
            )
        )
        .scalars()
        .all()
    )
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


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse reference documents that are marked for updates.",
    )
    parser.add_argument(
        "--storage-path",
        type=Path,
        default=None,
        help="Directory where reference documents are stored.",
    )
    parser.add_argument(
        "--summary-path",
        type=Path,
        default=None,
        help="Optional path to write a JSON summary after parsing.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Present for CLI parity; the flow always runs once.",
    )
    parser.add_argument(
        "--min-clauses",
        type=int,
        default=1,
        help="Minimum number of clauses required for a successful run.",
    )
    parser.add_argument(
        "--min-documents",
        type=int,
        default=1,
        help="Minimum number of documents required for a successful run.",
    )
    return parser


async def _run_once(
    *, storage: ReferenceStorage, parser: ClauseParser | None = None
) -> list[int]:
    flow_callable = resolve_flow_callable(parse_reference_documents)
    return await flow_callable(
        AsyncSessionLocal,
        storage=storage,
        parser=parser,
    )


async def _collect_counts() -> tuple[int, int]:
    async with AsyncSessionLocal() as session:
        documents = (await session.execute(select(RefDocument))).scalars().all()
        clauses = (await session.execute(select(RefClause))).scalars().all()
    return len(documents), len(clauses)


def main(argv: Sequence[str] | None = None) -> dict[str, int | list[int]]:
    parser = _build_cli_parser()
    args = parser.parse_args(argv)
    storage = ReferenceStorage(
        base_path=args.storage_path if args.storage_path is not None else None,
    )

    processed = asyncio.run(_run_once(storage=storage))
    document_count, clause_count = asyncio.run(_collect_counts())

    summary: dict[str, int | list[int]] = {
        "processed_documents": processed,
        "document_count": document_count,
        "clause_count": clause_count,
    }

    if document_count < args.min_documents:
        raise SystemExit(
            f"Expected at least {args.min_documents} reference documents; "
            f"observed {document_count}."
        )
    if clause_count < args.min_clauses:
        raise SystemExit(
            f"Expected at least {args.min_clauses} reference clauses; "
            f"observed {clause_count}."
        )

    if args.summary_path:
        args.summary_path.parent.mkdir(parents=True, exist_ok=True)
        args.summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True))

    return summary


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()


__all__ = ["parse_reference_documents"]
