"""PostgreSQL dialect placeholders for the SQLAlchemy stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["JSONB"]


@dataclass
class JSONB:
    """Placeholder representing the PostgreSQL JSONB column type."""

    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] | None = None
