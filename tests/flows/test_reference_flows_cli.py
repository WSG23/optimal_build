"""Integration tests for Prefect-compatible reference flows."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.app.models.base import BaseModel
from backend.app.models.rkp import RefClause, RefDocument, RefSource
from backend.flows import parse_segment as parse_segment_flow
from backend.flows import watch_fetch as watch_fetch_flow


async def _initialise_schema(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


async def _seed_offline_sources(
    session_factory: async_sessionmaker,
) -> Dict[str, int]:
    async with session_factory() as session:
        ura = RefSource(
            jurisdiction="SG",
            authority="URA",
            topic="planning",
            doc_title="URA Master Plan",
            landing_url="https://example.com/ura.html",
            fetch_kind="html",
            is_active=True,
        )
        bca = RefSource(
            jurisdiction="SG",
            authority="BCA",
            topic="fire",
            doc_title="BCA Fire Code",
            landing_url="https://example.com/bca.pdf",
            fetch_kind="pdf",
            is_active=True,
        )
        scdf = RefSource(
            jurisdiction="SG",
            authority="SCDF",
            topic="fire",
            doc_title="SCDF Fire Code",
            landing_url="https://example.com/scdf.pdf",
            fetch_kind="pdf",
            is_active=True,
        )
        session.add_all([ura, bca, scdf])
        await session.commit()
        return {source.authority: source.id for source in (ura, bca, scdf)}


def test_prefect_shim_flow_decorator_preserves_callable() -> None:
    """The vendored Prefect shim should expose usable flow decorators."""

    import prefect

    captured: list[int] = []

    @prefect.flow(name="shim-test")
    async def sample(value: int) -> int:
        captured.append(value)
        return value

    assert sample.name == "shim-test"
    assert sample.with_options() is sample

    result = asyncio.run(sample(3))
    assert result == 3
    assert captured == [3]


def test_watch_fetch_cli_offline_deduplicates_summary(
    flow_session_factory: async_sessionmaker,
    tmp_path: Path,
) -> None:
    authority_ids = asyncio.run(_seed_offline_sources(flow_session_factory))

    summary = watch_fetch_flow.main(
        [
            "--storage-path",
            str(tmp_path),
            "--offline",
            "--min-documents",
            "0",
        ]
    )

    assert summary["document_count"] == 3
    assert len(summary["results"]) == 2
    seen_document_ids = {entry["document_id"] for entry in summary["results"]}
    assert len(seen_document_ids) == len(summary["results"])

    async def _load_documents() -> list[RefDocument]:
        async with flow_session_factory() as session:
            rows = await session.execute(select(RefDocument).order_by(RefDocument.id))
            return list(rows.scalars())

    documents = asyncio.run(_load_documents())
    assert len(documents) == 3
    file_hashes = {document.file_hash for document in documents}
    assert len(file_hashes) == 2

    docs_by_source = {document.source_id: document for document in documents}
    assert authority_ids["BCA"] in docs_by_source
    assert authority_ids["SCDF"] in docs_by_source

    # Only one of the duplicate hashes should be present in the summary payload.
    duplicate_source_ids = {authority_ids["BCA"], authority_ids["SCDF"]}
    assert len(duplicate_source_ids & {entry["source_id"] for entry in summary["results"]}) == 1


def test_parse_segment_cli_parses_watch_fetch_results(
    flow_session_factory: async_sessionmaker,
    tmp_path: Path,
) -> None:
    asyncio.run(_seed_offline_sources(flow_session_factory))

    watch_fetch_flow.main(
        [
            "--storage-path",
            str(tmp_path),
            "--offline",
            "--min-documents",
            "0",
        ]
    )

    summary = parse_segment_flow.main(
        [
            "--storage-path",
            str(tmp_path),
            "--min-documents",
            "0",
            "--min-clauses",
            "0",
        ]
    )

    processed = summary.get("processed_documents", [])
    assert len(processed) == 3
    assert summary.get("document_count") == 3
    assert summary.get("clause_count", 0) > 0

    async def _load_state():
        async with flow_session_factory() as session:
            documents = (
                await session.execute(select(RefDocument).order_by(RefDocument.id))
            ).scalars().all()
            clauses = (await session.execute(select(RefClause))).scalars().all()
            return documents, clauses

    documents, clauses = asyncio.run(_load_state())
    assert all(document.suspected_update is False for document in documents)
    assert {document.id for document in documents} == set(processed)
    assert clauses, "Expected reference clauses to be persisted"


def test_watch_fetch_cli_invocation_via_python_m(tmp_path: Path) -> None:
    """The flow should be executable via ``python -m`` without import failures."""

    database_path = tmp_path / "cli.sqlite"
    database_uri = f"sqlite+aiosqlite:///{database_path}"
    engine = create_async_engine(database_uri, future=True)

    asyncio.run(_initialise_schema(engine))

    storage_path = tmp_path / "storage"
    summary_path = tmp_path / "summary.json"

    env = os.environ.copy()
    env["SQLALCHEMY_DATABASE_URI"] = database_uri
    project_root = Path(__file__).resolve().parents[2]
    python_path_entries = [
        str(project_root),
        str(project_root / "backend"),
        env.get("PYTHONPATH"),
    ]
    env["PYTHONPATH"] = os.pathsep.join(
        [entry for entry in python_path_entries if entry]
    )

    command = [
        sys.executable,
        "-m",
        "backend.flows.watch_fetch",
        "--once",
        "--offline",
        "--storage-path",
        str(storage_path),
        "--summary-path",
        str(summary_path),
        "--min-documents",
        "0",
    ]

    subprocess.run(command, check=True, cwd=project_root, env=env)

    assert summary_path.exists(), "Expected CLI to write a summary payload"
    summary = json.loads(summary_path.read_text())
    assert "document_count" in summary
    assert "results" in summary

    asyncio.run(engine.dispose())
