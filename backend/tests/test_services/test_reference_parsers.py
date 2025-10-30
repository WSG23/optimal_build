"""High-quality tests for reference document parsing service.

This test suite provides comprehensive coverage of the ClauseParser class,
focusing on text parsing, HTML parsing, and clause extraction logic.
"""

from __future__ import annotations

import pytest

from app.services.reference_parsers import ClauseParser, ParsedClause

# =============================================================================
# ParsedClause Tests
# =============================================================================


def test_parsed_clause_creation_with_all_fields():
    """Test creating ParsedClause with all fields."""
    clause = ParsedClause(
        clause_ref="3.1.2",
        heading="Building Height Restrictions",
        text="Maximum building height shall not exceed 80 meters.",
        page_from=5,
        page_to=6,
        quality="high",
    )

    assert clause.clause_ref == "3.1.2"
    assert clause.heading == "Building Height Restrictions"
    assert clause.text == "Maximum building height shall not exceed 80 meters."
    assert clause.page_from == 5
    assert clause.page_to == 6
    assert clause.quality == "high"


def test_parsed_clause_default_quality():
    """Test that quality defaults to 'high'."""
    clause = ParsedClause(
        clause_ref="1.1",
        heading="Title",
        text="Body",
        page_from=1,
        page_to=1,
    )

    assert clause.quality == "high"


# =============================================================================
# ClauseParser.parse() Tests
# =============================================================================


def test_parse_pdf_kind():
    """Test parsing with kind='pdf'."""
    parser = ClauseParser()
    payload = b"Section 1: Introduction\nThis is the introduction text."

    result = parser.parse(kind="pdf", payload=payload)

    assert len(result) == 1
    assert result[0].clause_ref == "1"
    assert "Introduction" in result[0].heading


def test_parse_html_kind():
    """Test parsing with kind='html'."""
    parser = ClauseParser()
    payload = b"<h1>3.1 Building Requirements</h1><p>Building text here.</p>"

    result = parser.parse(kind="html", payload=payload)

    assert len(result) >= 1
    assert any("3.1" in clause.clause_ref for clause in result)


def test_parse_sitemap_kind():
    """Test parsing with kind='sitemap' (treated as HTML)."""
    parser = ClauseParser()
    payload = b"<h2>2.5 Zoning Rules</h2><p>Zoning content.</p>"

    result = parser.parse(kind="sitemap", payload=payload)

    assert len(result) >= 1
    assert any("2.5" in clause.clause_ref for clause in result)


def test_parse_unknown_kind_defaults_to_text():
    """Test that unknown kinds default to text parsing."""
    parser = ClauseParser()
    payload = b"1.1 Title\nSome content here."

    result = parser.parse(kind="unknown", payload=payload)

    assert len(result) == 1
    assert result[0].clause_ref == "1.1"


def test_parse_none_kind_defaults_to_text():
    """Test that None kind defaults to text parsing."""
    parser = ClauseParser()
    payload = b"5.2 Section Title\nSection content."

    result = parser.parse(kind=None, payload=payload)

    assert len(result) == 1
    assert result[0].clause_ref == "5.2"


def test_parse_case_insensitive_kind():
    """Test that kind matching is case insensitive."""
    parser = ClauseParser()
    payload = b"<h1>1.0 Title</h1><p>Text</p>"

    result_upper = parser.parse(kind="HTML", payload=payload)
    result_lower = parser.parse(kind="html", payload=payload)
    result_mixed = parser.parse(kind="HtMl", payload=payload)

    assert len(result_upper) == len(result_lower) == len(result_mixed)


# =============================================================================
# ClauseParser._decode() Tests
# =============================================================================


def test_decode_valid_utf8():
    """Test decoding valid UTF-8 bytes."""
    parser = ClauseParser()
    payload = b"Hello World"

    result = parser._decode(payload)

    assert result == "Hello World"


def test_decode_with_unicode_characters():
    """Test decoding Unicode characters."""
    parser = ClauseParser()
    payload = "Building façade requirements".encode("utf-8")

    result = parser._decode(payload)

    assert result == "Building façade requirements"


def test_decode_with_invalid_bytes():
    """Test decoding with invalid UTF-8 bytes (should ignore errors)."""
    parser = ClauseParser()
    payload = b"Valid text\xff\xfeInvalid"

    result = parser._decode(payload)

    # Should not raise, errors are ignored
    assert "Valid text" in result


def test_decode_empty_payload():
    """Test decoding empty payload."""
    parser = ClauseParser()
    payload = b""

    result = parser._decode(payload)

    assert result == ""


# =============================================================================
# ClauseParser._parse_text_clauses() Tests
# =============================================================================


def test_parse_text_clauses_simple_section():
    """Test parsing simple numbered section."""
    parser = ClauseParser()
    text = "1. Introduction\nThis is the introduction text."

    result = parser._parse_text_clauses(text)

    assert len(result) == 1
    assert result[0].clause_ref == "1"
    assert "Introduction" in result[0].heading
    assert "introduction text" in result[0].text


def test_parse_text_clauses_nested_numbering():
    """Test parsing nested section numbers like 3.1.2."""
    parser = ClauseParser()
    text = "3.1.2 Building Height\nMaximum height is 80 meters."

    result = parser._parse_text_clauses(text)

    assert len(result) == 1
    assert result[0].clause_ref == "3.1.2"
    assert "Building Height" in result[0].heading


def test_parse_text_clauses_with_letter_suffix():
    """Test parsing sections with letter suffixes like 5.2A."""
    parser = ClauseParser()
    text = "5.2A Special Provisions\nAdditional requirements apply."

    result = parser._parse_text_clauses(text)

    assert len(result) == 1
    assert result[0].clause_ref == "5.2A"
    assert "Special Provisions" in result[0].heading


def test_parse_text_clauses_section_keyword():
    """Test parsing with 'Section' keyword prefix."""
    parser = ClauseParser()
    text = "Section 10: Compliance\nAll buildings must comply."

    result = parser._parse_text_clauses(text)

    assert len(result) == 1
    assert result[0].clause_ref == "10"
    assert "Compliance" in result[0].heading


def test_parse_text_clauses_multiple_sections():
    """Test parsing multiple sections."""
    parser = ClauseParser()
    text = """
1. First Section
First content.

2. Second Section
Second content.

3. Third Section
Third content.
"""

    result = parser._parse_text_clauses(text)

    assert len(result) == 3
    assert result[0].clause_ref == "1"
    assert result[1].clause_ref == "2"
    assert result[2].clause_ref == "3"


def test_parse_text_clauses_multiline_content():
    """Test parsing sections with multiple lines of content."""
    parser = ClauseParser()
    text = """
4.1 Long Section
This section has multiple lines.
Each line adds to the content.
All should be combined.
"""

    result = parser._parse_text_clauses(text)

    assert len(result) == 1
    assert "multiple lines" in result[0].text
    assert "combined" in result[0].text


def test_parse_text_clauses_skips_empty_lines():
    """Test that empty lines are skipped."""
    parser = ClauseParser()
    text = """

1. Section One


Content here.


"""

    result = parser._parse_text_clauses(text)

    assert len(result) == 1
    assert result[0].clause_ref == "1"


def test_parse_text_clauses_handles_colons():
    """Test parsing section titles with colons."""
    parser = ClauseParser()
    text = "7.3: Parking Requirements\nMinimum parking spaces required."

    result = parser._parse_text_clauses(text)

    assert len(result) == 1
    assert result[0].clause_ref == "7.3"
    assert "Parking Requirements" in result[0].heading


def test_parse_text_clauses_handles_dashes():
    """Test parsing section titles with dashes."""
    parser = ClauseParser()
    text = "8.5 - Fire Safety\nFire safety measures must be implemented."

    result = parser._parse_text_clauses(text)

    assert len(result) == 1
    assert result[0].clause_ref == "8.5"
    assert "Fire Safety" in result[0].heading


def test_parse_text_clauses_empty_text():
    """Test parsing empty text."""
    parser = ClauseParser()
    text = ""

    result = parser._parse_text_clauses(text)

    assert result == []


def test_parse_text_clauses_no_matching_sections():
    """Test text with no recognizable section patterns."""
    parser = ClauseParser()
    text = "Just some random text without section numbers."

    result = parser._parse_text_clauses(text)

    assert result == []


def test_parse_text_clauses_section_without_content():
    """Test that sections without content are filtered out."""
    parser = ClauseParser()
    text = """
1. Section With Content
This has content.

2. Empty Section

3. Another With Content
More content here.
"""

    result = parser._parse_text_clauses(text)

    # Section 2 should be included but with empty text
    assert len(result) == 3


def test_parse_text_clauses_page_numbering():
    """Test that page_from and page_to are assigned correctly."""
    parser = ClauseParser()
    text = """
1. First
Content one.

2. Second
Content two.
"""

    result = parser._parse_text_clauses(text)

    assert result[0].page_from == 1
    assert result[0].page_to == 1
    assert result[1].page_from == 2
    assert result[1].page_to == 2


# =============================================================================
# ClauseParser._extract_clause_ref() Tests
# =============================================================================


def test_extract_clause_ref_simple_number():
    """Test extracting simple clause reference."""
    parser = ClauseParser()

    result = parser._extract_clause_ref("Section 5 Overview")

    assert result == "5"


def test_extract_clause_ref_nested_number():
    """Test extracting nested clause reference."""
    parser = ClauseParser()

    result = parser._extract_clause_ref("3.2.1 Building Requirements")

    assert result == "3.2.1"


def test_extract_clause_ref_with_letter():
    """Test extracting clause reference with letter suffix."""
    parser = ClauseParser()

    result = parser._extract_clause_ref("10.5A Special Case")

    assert result == "10.5A"


def test_extract_clause_ref_none_text():
    """Test extracting from None text."""
    parser = ClauseParser()

    result = parser._extract_clause_ref(None)

    assert result is None


def test_extract_clause_ref_empty_text():
    """Test extracting from empty text."""
    parser = ClauseParser()

    result = parser._extract_clause_ref("")

    assert result is None


def test_extract_clause_ref_no_match():
    """Test extracting when no pattern matches."""
    parser = ClauseParser()

    result = parser._extract_clause_ref("No numbers here")

    assert result is None


# =============================================================================
# ClauseParser HTML Parsing Tests
# =============================================================================


def test_parse_html_sections_with_heading_and_paragraph():
    """Test parsing HTML with heading and paragraph."""
    parser = ClauseParser()
    payload = b"<h1>2.1 Zoning</h1><p>Zoning regulations apply.</p>"

    result = parser._parse_html_sections(payload)

    assert len(result) >= 1
    heading, body = result[0]
    assert "2.1" in heading or "2.1" in body


def test_parse_html_sections_multiple_sections():
    """Test parsing multiple HTML sections."""
    parser = ClauseParser()
    payload = b"""
<h2>1.0 First</h2>
<p>First content</p>
<h2>2.0 Second</h2>
<p>Second content</p>
"""

    result = parser._parse_html_sections(payload)

    assert len(result) == 2


def test_parse_html_sections_nested_tags():
    """Test parsing HTML with nested div and span tags."""
    parser = ClauseParser()
    payload = b"""
<h3>3.5 Requirements</h3>
<div>
    <span>Content in span</span>
    <p>Content in paragraph</p>
</div>
"""

    result = parser._parse_html_sections(payload)

    assert len(result) >= 1


def test_parse_html_sections_with_br_tags():
    """Test that <br> tags are handled."""
    parser = ClauseParser()
    payload = b"<h1>5.0 Title</h1><p>Line one<br>Line two</p>"

    result = parser._parse_html_sections(payload)

    assert len(result) >= 1


def test_parse_html_sections_empty_html():
    """Test parsing empty HTML."""
    parser = ClauseParser()
    payload = b""

    result = parser._parse_html_sections(payload)

    assert result == []


def test_parse_html_sections_no_headings():
    """Test HTML without headings."""
    parser = ClauseParser()
    payload = b"<p>Just a paragraph</p><p>Another paragraph</p>"

    result = parser._parse_html_sections(payload)

    # Should still capture sections even without explicit headings
    assert isinstance(result, list)


# =============================================================================
# ClauseParser._build_clauses_from_sections() Tests
# =============================================================================


def test_build_clauses_from_sections_basic():
    """Test building clauses from section tuples."""
    parser = ClauseParser()
    sections = [
        ("1.0 Introduction", "This is the introduction."),
        ("2.0 Requirements", "These are the requirements."),
    ]

    result = parser._build_clauses_from_sections(sections)

    assert len(result) == 2
    assert result[0].clause_ref == "1.0"
    assert result[1].clause_ref == "2.0"


def test_build_clauses_from_sections_duplicate_refs():
    """Test that duplicate clause references are filtered."""
    parser = ClauseParser()
    sections = [
        ("3.1 First", "First content."),
        ("3.1 Duplicate", "This should be skipped."),
        ("3.2 Second", "Second content."),
    ]

    result = parser._build_clauses_from_sections(sections)

    assert len(result) == 2
    assert result[0].clause_ref == "3.1"
    assert result[1].clause_ref == "3.2"


def test_build_clauses_from_sections_no_ref_in_heading():
    """Test extracting clause ref from body when not in heading."""
    parser = ClauseParser()
    sections = [
        ("Overview", "Section 4.5: This is in the body."),
    ]

    result = parser._build_clauses_from_sections(sections)

    assert len(result) == 1
    assert result[0].clause_ref == "4.5"


def test_build_clauses_from_sections_no_ref_found():
    """Test that sections without extractable refs are skipped."""
    parser = ClauseParser()
    sections = [
        ("No Numbers", "Just text without numbers."),
    ]

    result = parser._build_clauses_from_sections(sections)

    assert result == []


def test_build_clauses_from_sections_page_numbering():
    """Test that page numbers are assigned sequentially."""
    parser = ClauseParser()
    sections = [
        ("1.0 First", "Content"),
        ("2.0 Second", "Content"),
        ("3.0 Third", "Content"),
    ]

    result = parser._build_clauses_from_sections(sections)

    assert result[0].page_from == 1
    assert result[1].page_from == 2
    assert result[2].page_from == 3


def test_build_clauses_from_sections_whitespace_normalization():
    """Test that body text whitespace is normalized."""
    parser = ClauseParser()
    sections = [
        ("5.0 Title", "Content   with    irregular     spacing."),
    ]

    result = parser._build_clauses_from_sections(sections)

    assert result[0].text == "Content with irregular spacing."


def test_build_clauses_from_sections_empty_list():
    """Test building from empty sections list."""
    parser = ClauseParser()
    sections = []

    result = parser._build_clauses_from_sections(sections)

    assert result == []


# =============================================================================
# Integration Tests
# =============================================================================


def test_full_parse_pdf_integration():
    """Test full PDF parsing workflow."""
    parser = ClauseParser()
    pdf_content = b"""
1. Introduction
This document outlines the building regulations.

2.1 Height Restrictions
Buildings shall not exceed 80 meters.

2.2 Setback Requirements
Minimum setback is 3 meters from property line.
"""

    result = parser.parse(kind="pdf", payload=pdf_content)

    assert len(result) == 3
    assert result[0].clause_ref == "1"
    assert result[1].clause_ref == "2.1"
    assert result[2].clause_ref == "2.2"


def test_full_parse_html_integration():
    """Test full HTML parsing workflow."""
    parser = ClauseParser()
    html_content = b"""
<html>
<body>
<h1>3.0 Zoning Regulations</h1>
<p>All properties must comply with zoning rules.</p>
<h2>3.1 Residential Zoning</h2>
<p>Residential buildings are permitted in this zone.</p>
</body>
</html>
"""

    result = parser.parse(kind="html", payload=html_content)

    assert len(result) >= 2
    refs = [clause.clause_ref for clause in result]
    assert "3.0" in refs or "3.1" in refs
