"""JWT Authentication utilities (compat wrapper).

The full implementation lives in ``app.core.auth.service`` to keep auth logic
centralised. Existing imports continue to work by re-exporting those helpers.
"""

import os

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
from app.core.config import settings

# Re-export constants for backward compatibility with tests
ALGORITHM = "HS256"
SECRET_KEY = settings.SECRET_KEY or os.getenv(
    "SECRET_KEY",
    "fallback-secret-key-for-development-only-do-not-use-in-production",
)

__all__ = [
    "ALGORITHM",
    "SECRET_KEY",
    "TokenData",
    "TokenResponse",
    "create_access_token",
    "create_refresh_token",
    "create_tokens",
    "get_current_user",
    "get_optional_user",
    "verify_token",
]
