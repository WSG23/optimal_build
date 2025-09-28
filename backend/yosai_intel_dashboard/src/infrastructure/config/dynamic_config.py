"""Lightweight dynamic configuration loader for the Yosai dashboard."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from threading import RLock
from typing import Any, Iterator

__all__ = ["ConfigProvider", "DynamicConfig", "dynamic_config"]

ConfigProvider = Callable[[], Mapping[str, Any]]


class DynamicConfig:
    """Aggregate configuration from multiple providers at runtime."""

    def __init__(self) -> None:
        self._providers: list[ConfigProvider] = []
        self._overrides: dict[str, Any] = {}
        self._lock = RLock()

    def register_provider(self, provider: ConfigProvider, *, prepend: bool = False) -> None:
        """Register ``provider`` so its values participate in the merged config."""

        with self._lock:
            if prepend:
                self._providers.insert(0, provider)
            else:
                self._providers.append(provider)

    def as_dict(self) -> dict[str, Any]:
        """Return the merged configuration from providers and overrides."""

        with self._lock:
            merged: dict[str, Any] = {}
            for provider in self._providers:
                try:
                    values = provider()
                except Exception:  # pragma: no cover - defensive
                    continue
                for key, value in values.items():
                    if value is None:
                        merged.pop(key, None)
                    else:
                        merged[key] = value
            merged.update(self._overrides)
            return dict(merged)

    def get(self, key: str, default: Any | None = None) -> Any | None:
        """Return the value associated with ``key`` from the merged configuration."""

        return self.as_dict().get(key, default)

    @contextmanager
    def override(self, mapping: Mapping[str, Any] | None = None, **values: Any) -> Iterator[None]:
        """Temporarily inject overrides into the configuration."""

        updates = dict(mapping or {})
        updates.update(values)

        with self._lock:
            previous: dict[str, Any | _Missing] = {}
            for key, value in updates.items():
                previous[key] = self._overrides.get(key, _MISSING)
                self._overrides[key] = value
        try:
            yield
        finally:
            with self._lock:
                for key, old_value in previous.items():
                    if old_value is _MISSING:
                        self._overrides.pop(key, None)
                    else:
                        self._overrides[key] = old_value


class _Missing:
    pass


_MISSING = _Missing()


def _environment_provider() -> Mapping[str, str]:
    """Expose ``os.environ`` as a configuration provider."""

    return dict(os.environ)


dynamic_config = DynamicConfig()
dynamic_config.register_provider(_environment_provider)
