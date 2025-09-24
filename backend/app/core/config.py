"""Application configuration."""

import json
import os
import secrets
from typing import Iterable, List
from urllib.parse import urlparse, urlunparse

_DEFAULT_ALLOWED_ORIGINS = ("http://localhost:3000", "http://localhost:5173")
_DEFAULT_ALLOWED_HOSTS = ("localhost", "127.0.0.1")


def _load_bool(name: str, default: bool) -> bool:
    """Return a boolean configuration flag from the environment."""

    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalised = raw_value.strip().lower()
    if normalised in {"1", "true", "yes", "on"}:
        return True
    if normalised in {"0", "false", "no", "off"}:
        return False
    return default


def _load_positive_float(name: str, default: float) -> float:
    """Return a positive floating point value from the environment."""

    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        candidate = float(raw_value)
    except (TypeError, ValueError):
        return default
    return candidate if candidate > 0 else default


def _load_fractional_float(name: str, default: float) -> float:
    """Return a fractional floating point value between 0 and 1."""

    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        candidate = float(raw_value)
    except (TypeError, ValueError):
        return default
    if 0 < candidate <= 1:
        return candidate
    return default


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


def _load_allowed_hosts() -> List[str]:
    """Retrieve allowed hosts from the environment."""

    raw_hosts = os.getenv("ALLOWED_HOSTS")
    if not raw_hosts:
        return list(_DEFAULT_ALLOWED_HOSTS)

    hosts = [host.strip() for host in raw_hosts.split(",") if host.strip()]
    if not hosts:
        return list(_DEFAULT_ALLOWED_HOSTS)

    return list(dict.fromkeys(hosts))


def _derive_redis_url(base_url: str, db: int) -> str:
    """Return ``base_url`` pointing at a specific Redis database index.

    If ``base_url`` looks like a standard redis/rediss URL, adjust the path so the
    caller receives an address for the requested database while preserving other
    components (authentication, host, query string, etc.). If the URL uses an
    unexpected scheme or structure, fall back to returning it unchanged so the
    caller can decide how to handle custom connection syntaxes.
    """

    parsed = urlparse(base_url)
    if parsed.scheme not in {"redis", "rediss"} or not parsed.netloc:
        return base_url

    return urlunparse(parsed._replace(path=f"/{db}"))


class Settings:
    """Application settings."""

    PROJECT_NAME: str
    VERSION: str
    API_V1_STR: str
    SECRET_KEY: str
    ENVIRONMENT: str

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str
    SQLALCHEMY_DATABASE_URI: str

    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    RQ_REDIS_URL: str

    ODA_LICENSE_KEY: str

    OVERLAY_QUEUE_LOW: str
    OVERLAY_QUEUE_DEFAULT: str
    OVERLAY_QUEUE_HIGH: str

    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    IMPORTS_BUCKET_NAME: str
    EXPORTS_BUCKET_NAME: str

    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str

    ALLOWED_HOSTS: List[str]
    ALLOWED_ORIGINS: List[str]

    LOG_LEVEL: str

    BUILDABLE_TYP_FLOOR_TO_FLOOR_M: float
    BUILDABLE_EFFICIENCY_RATIO: float
    BUILDABLE_USE_POSTGIS: bool

    def __init__(self) -> None:
        self.PROJECT_NAME = os.getenv("PROJECT_NAME", "Building Compliance Platform")
        self.VERSION = os.getenv("PROJECT_VERSION", "1.0.0")
        self.API_V1_STR = "/api/v1"
        self.SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

        self.POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "building_compliance")
        self.POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

        default_db_uri = (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        self.SQLALCHEMY_DATABASE_URI = os.getenv(
            "SQLALCHEMY_DATABASE_URI", default_db_uri
        )

        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_base = self.REDIS_URL or "redis://localhost:6379"
        default_celery_broker = _derive_redis_url(redis_base, 0)
        default_celery_backend = _derive_redis_url(redis_base, 1)
        default_rq_url = _derive_redis_url(redis_base, 2)

        self.CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", default_celery_broker)
        self.CELERY_RESULT_BACKEND = os.getenv(
            "CELERY_RESULT_BACKEND", default_celery_backend
        )
        self.RQ_REDIS_URL = os.getenv("RQ_REDIS_URL", default_rq_url)

        self.ODA_LICENSE_KEY = os.getenv("ODA_LICENSE_KEY", "")

        self.OVERLAY_QUEUE_LOW = os.getenv("OVERLAY_QUEUE_LOW", "overlay:low")
        self.OVERLAY_QUEUE_DEFAULT = os.getenv(
            "OVERLAY_QUEUE_DEFAULT", "overlay:default"
        )
        self.OVERLAY_QUEUE_HIGH = os.getenv("OVERLAY_QUEUE_HIGH", "overlay:high")

        self.S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
        self.S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
        self.S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
        self.IMPORTS_BUCKET_NAME = os.getenv("IMPORTS_BUCKET_NAME", "cad-imports")
        self.EXPORTS_BUCKET_NAME = os.getenv("EXPORTS_BUCKET_NAME", "cad-exports")

        self.FIRST_SUPERUSER = os.getenv(
            "FIRST_SUPERUSER", "admin@buildingcompliance.com"
        )
        self.FIRST_SUPERUSER_PASSWORD = os.getenv(
            "FIRST_SUPERUSER_PASSWORD", "changeme"
        )

        self.ALLOWED_HOSTS = _load_allowed_hosts()
        self.ALLOWED_ORIGINS = _load_allowed_origins()

        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

        self.BUILDABLE_TYP_FLOOR_TO_FLOOR_M = _load_positive_float(
            "BUILDABLE_TYP_FLOOR_TO_FLOOR_M", 4.0
        )
        self.BUILDABLE_EFFICIENCY_RATIO = _load_fractional_float(
            "BUILDABLE_EFFICIENCY_RATIO", 0.82
        )
        self.BUILDABLE_USE_POSTGIS = _load_bool("BUILDABLE_USE_POSTGIS", False)


settings = Settings()
