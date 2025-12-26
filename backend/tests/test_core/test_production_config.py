"""Tests for production configuration validation."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestProductionConfigValidation:
    """Tests for production environment validation in Settings."""

    def test_production_requires_allowed_origins(self) -> None:
        """Production startup fails without BACKEND_ALLOWED_ORIGINS."""
        env = {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "test-secret-key-for-testing",
            "SQLALCHEMY_DATABASE_URI": "postgresql+asyncpg://user:pass@host/db",
            # Missing BACKEND_ALLOWED_ORIGINS
        }

        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            with pytest.raises(RuntimeError) as exc_info:
                Settings(validate_production=True)

            assert "BACKEND_ALLOWED_ORIGINS" in str(exc_info.value)

    def test_production_requires_database_uri(self) -> None:
        """Production startup fails without SQLALCHEMY_DATABASE_URI."""
        env = {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "test-secret-key-for-testing",
            "BACKEND_ALLOWED_ORIGINS": "https://example.com",
            # Missing SQLALCHEMY_DATABASE_URI
        }

        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            with pytest.raises(RuntimeError) as exc_info:
                Settings(validate_production=True)

            assert "SQLALCHEMY_DATABASE_URI" in str(exc_info.value)

    def test_production_succeeds_with_required_vars(self) -> None:
        """Production startup succeeds when all required vars are present."""
        env = {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "test-secret-key-for-testing-production",
            "BACKEND_ALLOWED_ORIGINS": "https://example.com",
            "SQLALCHEMY_DATABASE_URI": "postgresql+asyncpg://user:pass@host/db",
        }

        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            # Should not raise
            settings = Settings(validate_production=True)
            assert settings.ENVIRONMENT == "production"

    def test_development_does_not_require_production_vars(self) -> None:
        """Development environment doesn't require production-only vars."""
        env = {
            "ENVIRONMENT": "development",
            "SECRET_KEY": "test-secret-key-for-testing",
            # No BACKEND_ALLOWED_ORIGINS or SQLALCHEMY_DATABASE_URI
        }

        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            # Should not raise
            settings = Settings(validate_production=True)
            assert settings.ENVIRONMENT == "development"

    def test_validation_skipped_in_tests(self) -> None:
        """Validation is skipped when pytest is detected."""
        env = {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "test-secret-key",
            # Missing required production vars
        }

        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            # Should not raise because validate_production defaults to False in tests
            settings = Settings()  # Uses default validate_production logic
            assert settings.ENVIRONMENT == "production"
