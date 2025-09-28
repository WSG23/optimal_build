"""Type definitions for the SQLAlchemy stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Exported symbols must remain simple runtime placeholders so that the stubbed
# SQLAlchemy package continues to behave like the production dependency in
# integration tests.  The typing information added below mirrors the minimal
# protocol that our code relies on without introducing heavy dependencies on
# the real SQLAlchemy runtime.

__all__ = ["JSON", "TypeDecorator"]


@dataclass
class JSON:
    """Placeholder for :class:`sqlalchemy.types.JSON`."""

    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] | None = None


class TypeDecorator:
    """Very small subset of :class:`sqlalchemy.types.TypeDecorator`."""

    impl: object | None = None

    cache_ok = False

    def load_dialect_impl(self, dialect: object) -> object:  # pragma: no cover - stub
        """Return a dialect-specific type object.

        The real SQLAlchemy implementation returns a ``TypeEngine`` instance.  The
        stub keeps the return type intentionally broad so downstream code can
        provide precise overrides while retaining strict typing in mypy.
        """

        return dialect

    def process_bind_param(
        self, value: Any, dialect: Any
    ) -> Any:  # noqa: D401 - default passthrough
        return value

    def process_result_value(
        self, value: Any, dialect: Any
    ) -> Any:  # noqa: D401 - default passthrough
        return value
