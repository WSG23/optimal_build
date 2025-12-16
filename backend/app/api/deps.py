"""API dependencies shared across routers."""

from __future__ import annotations

from typing import Literal, AsyncGenerator

from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session

Role = Literal["viewer", "developer", "reviewer", "admin"]

_VIEWER_ROLES: set[str] = {"viewer", "developer", "reviewer", "admin"}
_REVIEWER_ROLES: set[str] = {"reviewer", "admin"}


@dataclass(slots=True)
class RequestIdentity:
    """Represents caller role/identity extracted from headers."""

    role: Role
    user_id: str | None = None
    email: str | None = None

    @classmethod
    def from_headers(
        cls,
        x_role: str | None,
        x_user_id: str | None,
        x_user_email: str | None,
    ) -> "RequestIdentity":
        configured_default = settings.DEFAULT_ROLE.strip().lower()
        if configured_default not in _VIEWER_ROLES:
            configured_default = "viewer"
        role = (x_role or configured_default).strip().lower()
        if role not in _VIEWER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid role supplied",
            )
        user_id = (x_user_id or "").strip() or None
        email = (x_user_email or "").strip() or None
        return cls(role=role, user_id=user_id, email=email)  # type: ignore[arg-type]


async def get_identity(
    x_role: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_user_email: str | None = Header(default=None),
) -> RequestIdentity:
    """Resolve the caller identity from the provided headers."""

    return RequestIdentity.from_headers(x_role, x_user_id, x_user_email)


async def get_request_role(x_role: str | None = Header(default=None)) -> Role:
    """Derive the caller role from the X-Role header.

    DEPRECATED: Use get_identity() for Phase 2C privacy enforcement.
    Kept for backward compatibility with existing endpoints.
    """
    identity = await get_identity(x_role=x_role, x_user_id=None, x_user_email=None)
    return identity.role


async def require_viewer(
    identity: RequestIdentity = Depends(get_identity),
) -> RequestIdentity:
    """Permit any viewer-equivalent role to access read-only endpoints."""

    return identity


async def require_reviewer(
    identity: RequestIdentity = Depends(get_identity),
) -> RequestIdentity:
    """Restrict mutations to reviewer or admin roles."""

    if identity.role not in _REVIEWER_ROLES:
        if settings.ALLOW_VIEWER_MUTATIONS:
            return identity
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer or admin role required for mutation",
        )
    return identity


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async for session in get_session():
        yield session


__all__ = [
    "RequestIdentity",
    "Role",
    "get_identity",
    "get_request_role",
    "require_reviewer",
    "require_viewer",
    "get_db",
]
