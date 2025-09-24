"""Rendering helpers for optional PDF generation."""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - optional dependency
    from weasyprint import HTML  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - graceful fallback when unavailable
    HTML = None  # type: ignore


def render_html_to_pdf(html: str) -> Optional[bytes]:
    """Convert HTML markup into a PDF document if dependencies allow."""

    if HTML is None:
        return None
    try:  # pragma: no cover - exercised when dependency is installed
        document = HTML(string=html)
        return document.write_pdf()
    except Exception:  # pragma: no cover - fallback for rendering failures
        return None


__all__ = ["render_html_to_pdf"]
