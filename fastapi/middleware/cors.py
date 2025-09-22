"""Stub implementation of ``fastapi.middleware.cors``."""

from __future__ import annotations

from typing import Iterable, Sequence


class CORSMiddleware:  # pragma: no cover - behaviour not exercised in tests
    """Placeholder maintaining compatibility with the real middleware API."""

    def __init__(
        self,
        app,
        *,
        allow_origins: Sequence[str] | Iterable[str] | None = None,
        allow_credentials: bool = False,
        allow_methods: Sequence[str] | Iterable[str] | None = None,
        allow_headers: Sequence[str] | Iterable[str] | None = None,
    ) -> None:
        self.app = app
        self.allow_origins = list(allow_origins or [])
        self.allow_credentials = allow_credentials
        self.allow_methods = list(allow_methods or [])
        self.allow_headers = list(allow_headers or [])


__all__ = ["CORSMiddleware"]
