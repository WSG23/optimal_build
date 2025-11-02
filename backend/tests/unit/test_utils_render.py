import importlib

import pytest

import app.utils.render as render


@pytest.fixture(autouse=True)
def reload_render_module() -> None:
    importlib.reload(render)


@pytest.mark.no_db
class TestRenderUtilities:
    def test_escape_pdf_text_escapes_special_characters(self) -> None:
        escaped = render._escape_pdf_text("Line (1) with \\slash")
        assert escaped == "Line \\(1\\) with \\\\slash"

    def test_strip_html_to_text_removes_markup_and_wraps(self) -> None:
        markup = """
            <h1>Title</h1>
            <p>Paragraph with <strong>formatting</strong> and a<br/>line break.</p>
            <script>ignored()</script>
        """
        text = render._strip_html_to_text(markup)
        assert "Title" in text
        assert "Paragraph with formatting" in text
        assert "line break." in text
        # ensure wrapped output does not contain HTML tags
        assert "<" not in text and ">" not in text

    def test_strip_html_to_text_returns_default_for_empty_content(self) -> None:
        text = render._strip_html_to_text("<style>body{display:none;}</style>")
        assert text == "Condition report"

    def test_fallback_html_to_pdf_embeds_text(self) -> None:
        pdf_bytes = render._fallback_html_to_pdf("<p>Hello World</p>")
        assert pdf_bytes.startswith(b"%PDF")
        assert b"Hello World" in pdf_bytes

    def test_render_html_to_pdf_uses_fallback_when_factory_missing(self) -> None:
        pdf_bytes = render.render_html_to_pdf("<p>Fallback</p>")
        assert pdf_bytes is not None
        assert pdf_bytes.startswith(b"%PDF")

    def test_render_html_to_pdf_uses_factory_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class DummyDocument:
            def __init__(self, *, string: str) -> None:
                self._string = string

            def write_pdf(self) -> bytes:
                return self._string.upper().encode("utf-8")

        monkeypatch.setattr(render, "_HTML_FACTORY", lambda **kwargs: DummyDocument(**kwargs))
        pdf_bytes = render.render_html_to_pdf("<p>factory</p>")
        assert pdf_bytes == b"<P>FACTORY</P>"

    def test_render_html_to_pdf_handles_factory_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def failing_factory(**_: str) -> object:
            raise RuntimeError("boom")

        monkeypatch.setattr(render, "_HTML_FACTORY", failing_factory)
        assert render.render_html_to_pdf("<p>boom</p>") is None
