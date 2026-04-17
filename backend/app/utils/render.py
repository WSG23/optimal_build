"""Rendering helpers for optional PDF generation."""

from __future__ import annotations

import html
import importlib
import re
import textwrap
from collections.abc import Callable
from io import BytesIO
from typing import TYPE_CHECKING, Protocol, cast


class _HTMLDocument(Protocol):
    """Minimal interface required from a rendered HTML document."""

    def write_pdf(self) -> bytes: ...


HTMLFactory = Callable[..., _HTMLDocument]


if TYPE_CHECKING:  # pragma: no cover - import only for typing
    pass


try:  # pragma: no cover - optional dependency
    _weasyprint_module = importlib.import_module("weasyprint")
except (
    ModuleNotFoundError,
    OSError,
):  # pragma: no cover - graceful fallback when unavailable
    _HTML_FACTORY: HTMLFactory | None = None
else:
    _HTML_FACTORY = cast(HTMLFactory, _weasyprint_module.HTML)

_PDF_HEADER = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"


def _escape_pdf_text(value: str) -> str:
    """Escape text for inclusion in a PDF string literal."""
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _strip_html_to_text(markup: str) -> str:
    """Convert simple HTML into wrapped plain text for fallback PDFs."""
    sanitized = re.sub(r"(?is)<(style|script)[^>]*>.*?</\1>", " ", markup)
    # Normalize tags that imply line breaks before stripping the rest.
    normalized = re.sub(r"(?i)</?(br|p|li|h[1-6])[^>]*>", "\n", sanitized)
    # Remove all other tags and collapse whitespace.
    plain = re.sub(r"<[^>]+>", " ", normalized)
    plain = html.unescape(plain)
    plain = plain.replace("\xa0", " ").replace("·", "-")
    plain = re.sub(r"[ \t\r\f\v]+", " ", plain)
    lines = [line.strip() for line in plain.split("\n")]
    text = "\n".join(line for line in lines if line)
    if not text:
        return "Condition report"
    wrapped_lines = []
    for block in text.split("\n"):
        wrapped_lines.extend(textwrap.wrap(block, width=90) or [""])
    return "\n".join(wrapped_lines)


def _fallback_html_to_pdf(markup: str) -> bytes | None:
    """Create a minimal PDF document without external dependencies."""
    text = _strip_html_to_text(markup)
    lines = text.split("\n")

    content_lines = ["BT", "/F1 12 Tf", "72 756 Td"]
    for index, line in enumerate(lines):
        escaped = _escape_pdf_text(line)
        if index != 0:
            content_lines.append("0 -16 Td")
        content_lines.append(f"({escaped}) Tj")
    content_lines.append("ET")

    content_bytes = "\n".join(content_lines).encode("latin-1", "replace")
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        (
            f"<< /Length {len(content_bytes)} >>\nstream\n".encode("ascii")
            + content_bytes
            + b"\nendstream"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    buffer = BytesIO()
    buffer.write(_PDF_HEADER)
    xref_entries = [b"0000000000 65535 f "]

    for index, payload in enumerate(objects, start=1):
        offset = buffer.tell()
        xref_entries.append(f"{offset:010} 00000 n ".encode("ascii"))
        buffer.write(f"{index} 0 obj\n".encode("ascii"))
        buffer.write(payload)
        if not payload.endswith(b"\n"):
            buffer.write(b"\n")
        buffer.write(b"endobj\n")

    xref_offset = buffer.tell()
    buffer.write(b"xref\n")
    buffer.write(f"0 {len(objects) + 1}\n".encode("ascii"))
    for entry in xref_entries:
        buffer.write(entry + b"\n")
    buffer.write(b"trailer\n")
    buffer.write(b"<<\n")
    buffer.write(f"/Size {len(objects) + 1}\n".encode("ascii"))
    buffer.write(b"/Root 1 0 R\n")
    buffer.write(b">>\n")
    buffer.write(b"startxref\n")
    buffer.write(f"{xref_offset}\n".encode("ascii"))
    buffer.write(b"%%EOF\n")
    return buffer.getvalue()


def render_html_to_pdf(html: str) -> bytes | None:
    """Convert HTML markup into a PDF document if dependencies allow."""
    factory = _HTML_FACTORY
    if factory is None:
        return _fallback_html_to_pdf(html)
    try:  # pragma: no cover - exercised when dependency is installed
        document = factory(string=html)
        return document.write_pdf()
    except Exception:  # pragma: no cover - fallback for rendering failures
        return None


__all__ = ["render_html_to_pdf"]
