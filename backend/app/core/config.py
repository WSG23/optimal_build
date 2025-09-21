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

    def __init__(self) -> None:
        self.PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Building Compliance Platform")
        self.VERSION: str = os.getenv("PROJECT_VERSION", "1.0.0")
        self.API_V1_STR: str = "/api/v1"
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

        # Database
        self.POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
        self.POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
        self.POSTGRES_DB: str = os.getenv("POSTGRES_DB", "building_compliance")
        self.POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
        default_db_uri = (
            "postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        self.SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", default_db_uri)

        # Object storage
        self.OBJECT_STORAGE_ENDPOINT: str = os.getenv("OBJECT_STORAGE_ENDPOINT", "http://localhost:9000")
        self.OBJECT_STORAGE_BUCKET: str = os.getenv("OBJECT_STORAGE_BUCKET", "documents")
        self.OBJECT_STORAGE_ACCESS_KEY: str = os.getenv("OBJECT_STORAGE_ACCESS_KEY", "minioadmin")
        self.OBJECT_STORAGE_SECRET_KEY: str = os.getenv("OBJECT_STORAGE_SECRET_KEY", "minioadmin")
        self.OBJECT_STORAGE_REGION: str = os.getenv("OBJECT_STORAGE_REGION", "us-east-1")
        use_ssl = os.getenv("OBJECT_STORAGE_USE_SSL", "false").lower() in {"1", "true", "yes"}
        self.OBJECT_STORAGE_USE_SSL: bool = use_ssl

        # Prefect
        self.PREFECT_API_URL: str = os.getenv("PREFECT_API_URL", "http://prefect:4200/api")
        self.PREFECT_API_KEY: str | None = os.getenv("PREFECT_API_KEY")

        # CORS
        self.ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
        self.ALLOWED_ORIGINS: List[str] = _load_allowed_origins()

        # Logging
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def object_storage_settings(self) -> dict:
        """Return object storage configuration dict."""

        return {
            "bucket": self.OBJECT_STORAGE_BUCKET,
            "endpoint_url": self.OBJECT_STORAGE_ENDPOINT,
            "access_key": self.OBJECT_STORAGE_ACCESS_KEY,
            "secret_key": self.OBJECT_STORAGE_SECRET_KEY,
            "region_name": self.OBJECT_STORAGE_REGION,
            "use_ssl": self.OBJECT_STORAGE_USE_SSL,
        }


settings = Settings()
