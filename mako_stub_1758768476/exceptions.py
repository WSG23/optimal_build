"""Provide minimal Mako exception interfaces used by Alembic."""

from __future__ import annotations


class TemplateError(RuntimeError):
    """Fallback template error type."""


class TemplateLookupException(TemplateError):
    """Raised when a template cannot be located."""


class _PlaceholderTemplate:
    """Simple object returning a helpful message when rendered."""

    def render(self, **_kwargs: object) -> str:  # pragma: no cover - trivial
        return "Mako templates are not available in this offline environment."


def text_error_template() -> _PlaceholderTemplate:
    """Return a placeholder error template used by Alembic."""

    return _PlaceholderTemplate()
