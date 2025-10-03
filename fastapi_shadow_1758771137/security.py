"""Minimal security primitives for the FastAPI shadow implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class HTTPAuthorizationCredentials:
    """Simple container for HTTP Authorization header values."""

    scheme: str
    credentials: str


class HTTPBearer:
    """Stub dependency that extracts a bearer token from request headers."""

    def __init__(self, *, auto_error: bool = True) -> None:
        self.auto_error = auto_error

    async def __call__(self, request) -> Optional[HTTPAuthorizationCredentials]:  # type: ignore[override]
        authorization = None
        headers = getattr(request, "headers", {})
        if isinstance(headers, dict):
            authorization = headers.get("authorization") or headers.get("Authorization")
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
            return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        if self.auto_error:
            raise PermissionError("Missing or invalid Authorization header")
        return None


__all__ = ["HTTPBearer", "HTTPAuthorizationCredentials"]
