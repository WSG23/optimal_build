"""Model package exports."""

from __future__ import annotations

__all__: list[str] = []

try:  # pragma: no cover - SQLAlchemy is optional in some environments
    from .base import Base  # noqa: F401

    __all__.append("Base")
except ModuleNotFoundError:  # pragma: no cover - expose a stub when SQLAlchemy is absent
    class Base:  # type: ignore[override]
        """Fallback base class when SQLAlchemy is not installed."""

    __all__.append("Base")

try:  # pragma: no cover - optional models requiring SQLAlchemy
    from . import overlay, rkp  # noqa: F401  pylint: disable=unused-import
except ModuleNotFoundError:  # pragma: no cover - skip optional models
    overlay = rkp = None  # type: ignore[assignment]

from . import rulesets  # noqa: F401  pylint: disable=unused-import

__all__.append("rulesets")
