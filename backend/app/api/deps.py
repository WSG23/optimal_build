"""Shared API dependencies for RBAC enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set

from fastapi import Depends, Header, HTTPException, status


class Role(str, Enum):
    """Supported API roles."""

    VIEWER = "viewer"
    REVIEWER = "reviewer"
    ADMIN = "admin"


@dataclass
class RequestUser:
    """User context derived from request headers."""

    principal: Optional[str]
    roles: Set[Role]

    def has_any(self, allowed: Set[Role]) -> bool:
        return bool(self.roles.intersection(allowed))


def _parse_roles(raw: Optional[str]) -> Set[Role]:
    if not raw:
        return set()
    roles: Set[Role] = set()
    for entry in raw.split(","):
        value = entry.strip().lower()
        if not value:
            continue
        try:
            roles.add(Role(value))
        except ValueError:  # pragma: no cover - defensive for unknown roles
            continue
    return roles


async def get_current_user(
    x_user: Optional[str] = Header(default=None, alias="X-User"),
    x_user_roles: Optional[str] = Header(default=None, alias="X-User-Roles"),
) -> RequestUser:
    """Extract the caller identity and roles from headers."""

    return RequestUser(principal=x_user, roles=_parse_roles(x_user_roles))


def require_roles(*allowed: Role):
    """Dependency factory enforcing at least one allowed role."""

    allowed_set = set(allowed)

    async def _dependency(user: RequestUser = Depends(get_current_user)) -> RequestUser:
        if not user.has_any(allowed_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User lacks required role",
            )
        return user

    return _dependency


require_viewer = require_roles(Role.VIEWER, Role.REVIEWER, Role.ADMIN)
require_reviewer = require_roles(Role.REVIEWER, Role.ADMIN)
require_admin = require_roles(Role.ADMIN)


__all__ = [
    "Role",
    "RequestUser",
    "get_current_user",
    "require_admin",
    "require_reviewer",
    "require_roles",
    "require_viewer",
]
