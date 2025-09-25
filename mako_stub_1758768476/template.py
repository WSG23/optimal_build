"""Minimal stub of :mod:`mako.template` for Alembic."""

from __future__ import annotations

class Template:
    """Placeholder template object returning a descriptive message."""

    def __init__(self, *args: object, **kwargs: object) -> None:  # pragma: no cover - trivial
        self.args = args
        self.kwargs = kwargs

    def render(self, **_kwargs: object) -> str:  # pragma: no cover - trivial
        return "Mako templates are not available in this offline environment."
