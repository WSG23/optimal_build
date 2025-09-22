"""Tests for the reference document parsing flow."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select

from app.models.rkp import RefClause, RefDocument, RefSource
from app.services.ref_documents import compute_document_checksum
from flows.parse_segment import parse_reference_documents


@pytest.mark.asyncio
async def test_parse_reference_documents(async_session_factory, ref_storage_service) -> None:
    pdf_payload = (
        "Clause 1.1: Means of Escape\n"
        "Pages 1-2\n"
        "Every building shall provide unobstructed exits.\n\n"
        "Clause 2.0: Fire Resistance\n"
        "Page 3\n"
        "Structural elements must resist fire for two hours."
    ).encode("utf-8")
    html_payload = (
        "<html><body>"
        "<section data-clause=\"5.1\" data-pages=\"5-6\">"
        "<h2>Escape Routes</h2>"
        "<p>Routes to exits shall be clearly marked.</p>"
        "</section>"
        "</body></html>"
    ).encode("utf-8")

    async with async_session_factory() as session:
        await session.execute(RefClause.__table__.delete())
        await session.execute(RefDocument.__table__.delete())
        await session.execute(RefSource.__table__.delete())
        source_pdf = RefSource(
            jurisdiction="SG",
            authority="SCDF",
            topic="fire",
            doc_title="Fire Code",
            landing_url="https://example.com/fire.pdf",
            fetch_kind="pdf",
            is_active=True,
        )
        source_html = RefSource(
            jurisdiction="SG",
            authority="BCA",
            topic="accessibility",
            doc_title="Accessibility Code",
            landing_url="https://example.com/accessibility.html",
            fetch_kind="html",
            is_active=True,
        )
        session.add_all([source_pdf, source_html])
        await session.flush()

        stored_pdf = await ref_storage_service.write_document(
            source=source_pdf, payload=pdf_payload, extension="pdf"
        )
        stored_html = await ref_storage_service.write_document(
            source=source_html, payload=html_payload, extension="html"
        )

        document_pdf = RefDocument(
            source_id=source_pdf.id,
            storage_path=stored_pdf.storage_path,
            file_hash=compute_document_checksum(pdf_payload),
            http_etag='"pdf"',
            suspected_update=True,
        )
        document_html = RefDocument(
            source_id=source_html.id,
            storage_path=stored_html.storage_path,
            file_hash=compute_document_checksum(html_payload),
            http_etag='"html"',
            suspected_update=True,
        )
        session.add_all([document_pdf, document_html])
        await session.commit()
        pdf_id = document_pdf.id
        html_id = document_html.id

    summaries = await parse_reference_documents(
        async_session_factory, storage_service=ref_storage_service
    )

    assert {summary["document_id"] for summary in summaries} == {pdf_id, html_id}

    async with async_session_factory() as session:
        pdf_doc = await session.get(RefDocument, pdf_id)
        assert pdf_doc and pdf_doc.suspected_update is False
        pdf_clauses = (
            await session.execute(
                select(RefClause)
                .where(RefClause.document_id == pdf_id)
                .order_by(RefClause.id)
            )
        ).scalars().all()
        assert len(pdf_clauses) == 2
        assert pdf_clauses[0].clause_ref == "1.1"
        assert pdf_clauses[0].page_from == 1
        assert "unobstructed exits" in pdf_clauses[0].text_span

        html_doc = await session.get(RefDocument, html_id)
        assert html_doc and html_doc.suspected_update is False
        html_clauses = (
            await session.execute(select(RefClause).where(RefClause.document_id == html_id))
        ).scalars().all()
        assert len(html_clauses) == 1
        assert html_clauses[0].clause_ref == "5.1"
        assert html_clauses[0].section_heading == "Escape Routes"
        assert html_clauses[0].page_from == 5
        assert "Routes to exits" in html_clauses[0].text_span
