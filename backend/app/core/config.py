"""Application configuration."""

import secrets
from typing import List, Optional


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
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
