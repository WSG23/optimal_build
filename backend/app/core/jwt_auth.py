"""JWT Authentication utilities (compat wrapper).

The full implementation lives in ``app.core.auth.service`` to keep auth logic
centralised. Existing imports continue to work by re-exporting those helpers.
"""

from app.core.auth.service import (  # noqa: F401
    TokenData,
    TokenResponse,
    create_access_token,
    create_refresh_token,
    create_tokens,
    get_current_user,
    get_optional_user,
    verify_token,
)

__all__ = [
    "TokenData",
    "TokenResponse",
    "create_access_token",
    "create_refresh_token",
    "create_tokens",
    "get_current_user",
    "get_optional_user",
    "verify_token",
]
