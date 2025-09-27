"""Type definitions for the SQLAlchemy stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["JSON", "TypeDecorator"]


@dataclass
class JSON:
    """Placeholder for :class:`sqlalchemy.types.JSON`."""

    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] | None = None


class TypeDecorator:
    """Very small subset of :class:`sqlalchemy.types.TypeDecorator`."""

    impl = None

    cache_ok = False

    def process_bind_param(
        self, value: Any, dialect: Any
    ) -> Any:  # noqa: D401 - default passthrough
        return value

    def process_result_value(
        self, value: Any, dialect: Any
    ) -> Any:  # noqa: D401 - default passthrough
        return value
