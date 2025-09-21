"""Schema exports."""

from __future__ import annotations

__all__: list[str] = []

try:  # pragma: no cover - optional dependency
    from .costs import CostIndex  # noqa: F401

    __all__.append("CostIndex")
except ModuleNotFoundError:  # pragma: no cover - costs schema unavailable
    CostIndex = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from .overlay import (  # noqa: F401
        OverlayDecisionPayload,
        OverlayDecisionRecord,
        OverlaySuggestion,
    )

    __all__.extend(
        ["OverlaySuggestion", "OverlayDecisionPayload", "OverlayDecisionRecord"]
    )
except ModuleNotFoundError:  # pragma: no cover - overlay schema unavailable
    OverlaySuggestion = OverlayDecisionPayload = OverlayDecisionRecord = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from .standards import MaterialStandard  # noqa: F401

    __all__.append("MaterialStandard")
except ModuleNotFoundError:  # pragma: no cover - standards schema unavailable
    MaterialStandard = None  # type: ignore[assignment]

__all__ = __all__
