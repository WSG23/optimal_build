"""Application configuration."""

import json
import os
import secrets
from typing import Iterable, List

_DEFAULT_ALLOWED_ORIGINS = ("http://localhost:3000", "http://localhost:5173")


def _load_allowed_origins() -> List[str]:
    """Retrieve allowed CORS origins from the environment."""

    raw_origins = os.getenv("BACKEND_ALLOWED_ORIGINS")
    if not raw_origins:
        return list(_DEFAULT_ALLOWED_ORIGINS)

    origins: Iterable[str]
    try:
        parsed = json.loads(raw_origins)
    except json.JSONDecodeError:
        parsed = raw_origins

    if isinstance(parsed, str):
        origins = parsed.split(",")
    elif isinstance(parsed, (list, tuple, set)):
        origins = parsed
    else:
        return list(_DEFAULT_ALLOWED_ORIGINS)

    cleaned = [str(origin).strip() for origin in origins if str(origin).strip()]
    # Fall back to defaults if the environment variable produces no valid entries.
    if not cleaned:
        return list(_DEFAULT_ALLOWED_ORIGINS)

    # Preserve ordering while removing duplicates.
    return list(dict.fromkeys(cleaned))


class Settings:
    """Application settings."""
    
    PROJECT_NAME: str = "Building Compliance Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENVIRONMENT: str = "development"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "building_compliance"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: str = "postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    ALLOWED_ORIGINS: List[str] = _load_allowed_origins()
    
    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
