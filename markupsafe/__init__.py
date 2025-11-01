"""Minimal MarkupSafe compatibility layer for tests."""

from __future__ import annotations

import html
from typing import Any

__all__ = ["Markup", "escape", "soft_str"]


class Markup(str):
    """Simple ``Markup`` implementation compatible with MarkupSafe."""

    def __new__(cls, base: Any = "", *args: Any, **kwargs: Any) -> "Markup":
        return super().__new__(cls, str(base))

    def __html__(self) -> str:
        return str(self)


def escape(value: Any) -> Markup:
    """Escape HTML-sensitive characters."""

    return Markup(html.escape(str(value)))


def soft_str(value: Any) -> Markup:
    """Return a ``Markup`` string without additional escaping."""

    return Markup(value)

