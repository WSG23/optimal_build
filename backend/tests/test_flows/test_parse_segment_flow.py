"""Tests for the reference document parsing flow."""

from __future__ import annotations

import hashlib

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select

from app.models.rkp import RefClause, RefDocument, RefSource
from app.services.reference_storage import ReferenceStorage
from flows.parse_segment import parse_reference_documents


@pytest.mark.asyncio
async def test_parse_reference_documents_from_pdf(
    async_session_factory, tmp_path
) -> None:
    storage = ReferenceStorage(base_path=tmp_path, bucket="")
    payload = (
        b"1.1 Scope\n"
        b"The scope clause describes the coverage.\n\n"
        b"1.2 Requirements\n"
        b"All exits must remain unobstructed."
    )

    async with async_session_factory() as session:
        source = RefSource(
            jurisdiction="SG",
            authority="BCA",
            topic="fire",
            doc_title="Fire Code",
            landing_url="https://example.com/fire.pdf",
            fetch_kind="pdf",
            is_active=True,
        )
        session.add(source)
        await session.flush()
        location = await storage.write_document(
            source_id=source.id, payload=payload, suffix=".pdf"
        )
        assert storage.resolve_path(location.storage_path).exists()
        assert await storage.read_document(location.storage_path) == payload
        document = RefDocument(
            source_id=source.id,
            version_label="v1",
            storage_path=location.storage_path,
            file_hash=hashlib.sha256(payload).hexdigest(),
            http_etag="etag-v1",
            http_last_modified="Wed, 01 Jan 2024 00:00:00 GMT",
            suspected_update=True,
        )
        session.add(document)
        await session.commit()
        document_id = document.id

    # Ensure the persisted file remains accessible after the session closes.
    assert await storage.read_document(location.storage_path) == payload

    processed = await parse_reference_documents(async_session_factory, storage=storage)
    assert processed == [document_id]

    async with async_session_factory() as session:
        document = await session.get(RefDocument, document_id)
        assert document is not None
        assert document.suspected_update is False
        clauses = (
            (
                await session.execute(
                    select(RefClause)
                    .where(RefClause.document_id == document_id)
                    .order_by(RefClause.clause_ref)
                )
            )
            .scalars()
            .all()
        )
        assert len(clauses) == 2
        assert clauses[0].clause_ref == "1.1"
        assert "scope" in clauses[0].section_heading.lower()
        assert "coverage" in clauses[0].text_span.lower()
        assert clauses[1].clause_ref == "1.2"
        assert "exits" in clauses[1].text_span.lower()


@pytest.mark.asyncio
async def test_parse_reference_documents_from_html(
    async_session_factory, tmp_path
) -> None:
    storage = ReferenceStorage(base_path=tmp_path, bucket="")
    html_payload = (
        b"<html><body>"
        b"<h2>Clause 2.1 Fire Resistance</h2>"
        b"<p>Walls must achieve a two hour rating.</p>"
        b"<p>Doors shall be self-closing.</p>"
        b"<h2>2.2 Means of Escape</h2>"
        b"<p>Paths must remain clear at all times.</p>"
        b"</body></html>"
    )

    async with async_session_factory() as session:
        source = RefSource(
            jurisdiction="SG",
            authority="BCA",
            topic="fire",
            doc_title="Fire Code",
            landing_url="https://example.com/fire.html",
            fetch_kind="html",
            is_active=True,
        )
        session.add(source)
        await session.flush()
        location = await storage.write_document(
            source_id=source.id, payload=html_payload, suffix=".html"
        )
        assert storage.resolve_path(location.storage_path).exists()
        assert await storage.read_document(location.storage_path) == html_payload
        document = RefDocument(
            source_id=source.id,
            version_label="html-v1",
            storage_path=location.storage_path,
            file_hash=hashlib.sha256(html_payload).hexdigest(),
            http_etag="etag-html",
            http_last_modified="Thu, 02 Jan 2024 00:00:00 GMT",
            suspected_update=True,
        )
        session.add(document)
        await session.commit()
        document_id = document.id

    assert await storage.read_document(location.storage_path) == html_payload

    processed = await parse_reference_documents(async_session_factory, storage=storage)
    assert processed == [document_id]

    async with async_session_factory() as session:
        document = await session.get(RefDocument, document_id)
        assert document is not None
        assert document.suspected_update is False
        clauses = (
            (
                await session.execute(
                    select(RefClause)
                    .where(RefClause.document_id == document_id)
                    .order_by(RefClause.clause_ref)
                )
            )
            .scalars()
            .all()
        )
        assert len(clauses) == 2
        assert clauses[0].clause_ref == "2.1"
        assert "fire resistance" in clauses[0].section_heading.lower()
        assert "two hour rating" in clauses[0].text_span.lower()
        assert clauses[1].clause_ref == "2.2"
        assert "paths" in clauses[1].text_span.lower()
