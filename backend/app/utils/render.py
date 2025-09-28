"""Rendering helpers for optional PDF generation."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, cast


class _HTMLDocument(Protocol):
    """Minimal interface required from a rendered HTML document."""

    def write_pdf(self) -> bytes: ...


HTMLFactory = Callable[..., _HTMLDocument]


if TYPE_CHECKING:  # pragma: no cover - import only for typing
    pass


try:  # pragma: no cover - optional dependency
    _weasyprint_module = importlib.import_module("weasyprint")
except ModuleNotFoundError:  # pragma: no cover - graceful fallback when unavailable
    _HTML_FACTORY: HTMLFactory | None = None
else:
    _HTML_FACTORY = cast(HTMLFactory, _weasyprint_module.HTML)


def render_html_to_pdf(html: str) -> bytes | None:
    """Convert HTML markup into a PDF document if dependencies allow."""
    factory = _HTML_FACTORY
    if factory is None:
        return None
    try:  # pragma: no cover - exercised when dependency is installed
        document = factory(string=html)
        return document.write_pdf()
    except Exception:  # pragma: no cover - fallback for rendering failures
        return None


__all__ = ["render_html_to_pdf"]
