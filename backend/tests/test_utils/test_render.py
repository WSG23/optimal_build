"""Tests for PDF rendering utilities."""

from __future__ import annotations


from app.utils import render


def test_escape_pdf_text() -> None:
    """Test PDF text escaping."""
    # Test backslash escaping
    assert render._escape_pdf_text("test\\path") == "test\\\\path"

    # Test parentheses escaping
    assert render._escape_pdf_text("test (value)") == "test \\(value\\)"

    # Test combined escaping
    assert render._escape_pdf_text("c:\\folder\\(test)") == "c:\\\\folder\\\\\\(test\\)"

    # Test normal text
    assert render._escape_pdf_text("normal text") == "normal text"


def test_strip_html_to_text() -> None:
    """Test HTML to text conversion."""
    # Simple paragraph
    assert "Hello World" in render._strip_html_to_text("<p>Hello World</p>")

    # Remove script tags
    result = render._strip_html_to_text("<p>Text</p><script>alert('bad')</script>")
    assert "Text" in result
    assert "alert" not in result
    assert "script" not in result

    # Remove style tags
    result = render._strip_html_to_text("<p>Text</p><style>.class{}</style>")
    assert "Text" in result
    assert "class" not in result

    # Handle line breaks
    result = render._strip_html_to_text("<p>Line 1</p><br><p>Line 2</p>")
    assert "Line 1" in result
    assert "Line 2" in result

    # Handle lists
    result = render._strip_html_to_text("<ul><li>Item 1</li><li>Item 2</li></ul>")
    assert "Item 1" in result
    assert "Item 2" in result

    # Handle HTML entities
    result = render._strip_html_to_text("<p>&amp; &lt; &gt; &nbsp;</p>")
    assert "&" in result
    assert "<" in result
    assert ">" in result

    # Handle empty HTML
    assert render._strip_html_to_text("") == "Condition report"
    assert render._strip_html_to_text("   ") == "Condition report"
    assert render._strip_html_to_text("<p></p>") == "Condition report"

    # Test text wrapping
    long_text = "A" * 200  # Very long text
    result = render._strip_html_to_text(f"<p>{long_text}</p>")
    lines = result.split("\n")
    assert all(len(line) <= 90 for line in lines), "Lines should be wrapped at 90 chars"


def test_fallback_html_to_pdf_basic() -> None:
    """Test fallback PDF generation."""
    html = "<h1>Test Report</h1><p>This is a test document.</p>"
    pdf = render._fallback_html_to_pdf(html)

    assert pdf is not None
    assert pdf.startswith(b"%PDF-1.4"), "PDF should have correct header"
    assert b"%%EOF" in pdf, "PDF should have EOF marker"
    assert b"Test Report" in pdf or b"test" in pdf.lower(), "PDF should contain content"


def test_fallback_html_to_pdf_with_special_chars() -> None:
    """Test PDF generation with special characters."""
    html = "<p>Text with (parentheses) and \\backslash</p>"
    pdf = render._fallback_html_to_pdf(html)

    assert pdf is not None
    assert pdf.startswith(b"%PDF-1.4")
    # Special chars should be escaped in PDF
    assert b"\\(" in pdf or b"\\)" in pdf or b"\\\\" in pdf


def test_fallback_html_to_pdf_multiline() -> None:
    """Test PDF generation with multiple lines."""
    html = """
    <h1>Title</h1>
    <p>Paragraph 1</p>
    <p>Paragraph 2</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
    """
    pdf = render._fallback_html_to_pdf(html)

    assert pdf is not None
    assert pdf.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf


def test_fallback_html_to_pdf_empty() -> None:
    """Test PDF generation with empty/minimal HTML."""
    pdf = render._fallback_html_to_pdf("")
    assert pdf is not None
    assert pdf.startswith(b"%PDF-1.4")
    assert b"Condition report" in pdf  # Default fallback text

    pdf = render._fallback_html_to_pdf("<p></p>")
    assert pdf is not None
    assert b"Condition report" in pdf


def test_render_html_to_pdf_fallback() -> None:
    """Test main render function uses fallback when weasyprint unavailable."""
    # Since weasyprint is likely not installed, this should use fallback
    html = "<h1>Test</h1><p>Content</p>"
    pdf = render.render_html_to_pdf(html)

    assert pdf is not None
    assert pdf.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf


def test_render_html_to_pdf_complex_html() -> None:
    """Test rendering complex HTML structure."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Report</title>
        <style>
            body { font-family: Arial; }
            .hidden { display: none; }
        </style>
    </head>
    <body>
        <h1>Developer Conditions Report</h1>
        <div class="section">
            <h2>Conditions</h2>
            <ul>
                <li>Condition 1: Description here</li>
                <li>Condition 2: Another description</li>
            </ul>
        </div>
        <script>console.log('test');</script>
    </body>
    </html>
    """
    pdf = render.render_html_to_pdf(html)

    assert pdf is not None
    assert pdf.startswith(b"%PDF-1.4")
    # Script should be removed
    assert b"console.log" not in pdf


def test_html_factory_is_none_uses_fallback() -> None:
    """Test that when HTML factory is None, fallback is used."""
    # This is implicitly tested by other tests, but make it explicit
    original_factory = render._HTML_FACTORY
    try:
        render._HTML_FACTORY = None
        html = "<p>Test</p>"
        pdf = render.render_html_to_pdf(html)
        assert pdf is not None
        assert pdf.startswith(b"%PDF-1.4")
    finally:
        render._HTML_FACTORY = original_factory
