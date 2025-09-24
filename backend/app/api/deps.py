"""API dependencies shared across routers."""

from __future__ import annotations

from typing import Literal

from fastapi import Depends, Header, HTTPException, status

Role = Literal["viewer", "reviewer", "admin"]

_VIEWER_ROLES: set[str] = {"viewer", "reviewer", "admin"}
_REVIEWER_ROLES: set[str] = {"reviewer", "admin"}


async def get_request_role(x_role: str | None = Header(default=None)) -> Role:
    """Derive the caller role from the ``X-Role`` header."""

    role = (x_role or "viewer").strip().lower()
    if role not in _VIEWER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role supplied for entitlements access",
        )
    return role  # type: ignore[return-value]


async def require_viewer(role: Role = Depends(get_request_role)) -> Role:
    """Permit any viewer-equivalent role to access read-only endpoints."""

    return role


async def require_reviewer(role: Role = Depends(get_request_role)) -> Role:
    """Restrict mutations to reviewer or admin roles."""

    if role not in _REVIEWER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer or admin role required for mutation",
        )
    return role


__all__ = ["get_request_role", "require_viewer", "require_reviewer", "Role"]
