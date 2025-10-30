"""Unit tests for the reference clause parsers."""

from __future__ import annotations

from app.services.reference_parsers import ClauseParser


def test_parse_text_clauses_extracts_sequential_sections() -> None:
    parser = ClauseParser()
    payload = b"""
    Section 1.1 General provisions
    This clause covers the basic definitions.

    1.2  Scope and Application
    Details about the permitted usage.
    Additional qualifiers appear here.

    2  Applicability
    Short note.
    """

    clauses = parser.parse("pdf", payload)

    assert [clause.clause_ref for clause in clauses] == ["1.1", "1.2", "2"]
    assert clauses[0].heading == "General provisions"
    assert clauses[0].text == "This clause covers the basic definitions."
    assert clauses[0].page_from == 1 and clauses[0].page_to == 1
    # Heading falls back to the reference when the title is omitted.
    assert clauses[-1].heading == "Applicability"
    assert "Additional qualifiers" in clauses[1].text


def test_parse_unknown_kind_falls_back_to_text_path() -> None:
    parser = ClauseParser()
    clauses = parser.parse(
        "docx",
        b"""
        3.4 - Mixed Use Controls
        Clause text.
        """,
    )

    assert len(clauses) == 1
    assert clauses[0].clause_ref == "3.4"
    assert clauses[0].heading == "Mixed Use Controls"


def test_parse_html_sections_extracts_unique_clauses() -> None:
    parser = ClauseParser()
    html = b"""
    <html>
      <body>
        <h2>1.1 General</h2>
        <p>The primary guidance.</p>
        <h2>1.2 Height Limits</h2>
        <p>Maximum height 36&nbsp;m.</p>
        <h3>1.2 Height Limits</h3>
        <p>Duplicate section that should be ignored.</p>
        <h2>Design Standards</h2>
        <p>Clause 2.4 applies with overlays.<br/>Additional lines.</p>
      </body>
    </html>
    """

    clauses = parser.parse("html", html)

    assert [clause.clause_ref for clause in clauses] == ["1.1", "1.2", "2.4"]
    assert clauses[0].heading == "1.1 General"
    assert clauses[0].text == "The primary guidance."
    assert clauses[1].heading == "1.2 Height Limits"
    assert clauses[1].text == "Maximum height 36 m."
    # The final clause reference is derived from the body content.
    assert "overlays." in clauses[-1].text
    assert clauses[-1].heading == "Design Standards"


def test_html_parser_ignores_sections_without_clause_reference() -> None:
    parser = ClauseParser()
    html = b"""
    <h2>Introduction</h2>
    <p>This section has no clause identifier.</p>
    <h2>Section 4.1 Heritage</h2>
    <p>Heritage controls apply.</p>
    """

    clauses = parser.parse("sitemap", html)

    assert len(clauses) == 1
    assert clauses[0].clause_ref == "4.1"
    assert clauses[0].text == "Heritage controls apply."
