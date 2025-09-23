"""Utility helpers for optional HTML to PDF conversion."""

from __future__ import annotations

from typing import Optional


try:  # pragma: no cover - exercised only when dependency is available
    from weasyprint import HTML  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency missing
    HTML = None  # type: ignore

try:  # pragma: no cover - exercised only when dependency is available
    import pdfkit  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency missing
    pdfkit = None  # type: ignore


def html_to_pdf(html_content: str) -> Optional[bytes]:
    """Render HTML content to PDF when supported.

    Returns ``None`` when no renderer is available or an error occurs. Consumers
    can gracefully fall back to alternative formats.
    """

    if HTML is not None:
        try:
            document = HTML(string=html_content)
            return document.write_pdf()
        except Exception:  # pragma: no cover - defensive fallback
            pass

    if pdfkit is not None:
        try:
            return pdfkit.from_string(html_content, False)
        except Exception:  # pragma: no cover - defensive fallback
            pass

    return None


__all__ = ["html_to_pdf"]
