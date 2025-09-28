"""AI classification plugin configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass

from backend.yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
    dynamic_config,
)

__all__ = ["AIClassificationConfig"]


def _coerce_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


@dataclass(frozen=True, slots=True)
class AIClassificationConfig:
    """Resolved configuration for the AI classification plugin."""

    enabled: bool

    @classmethod
    def load(cls) -> "AIClassificationConfig":
        """Load the configuration from the dynamic configuration layer."""

        raw_value = dynamic_config.get("AI_CLASSIFICATION_ENABLED", True)
        return cls(enabled=_coerce_bool(raw_value, True))
