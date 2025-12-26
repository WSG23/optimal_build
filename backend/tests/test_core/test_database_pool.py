"""Tests for database connection pooling configuration."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch


class TestDatabasePoolSettings:
    """Tests for _get_pool_settings function."""

    def test_production_pool_settings(self) -> None:
        """Production environment uses larger pool with pre-ping."""
        mock_settings = MagicMock()
        mock_settings.ENVIRONMENT = "production"

        with patch("app.core.database.settings", mock_settings):
            from app.core.database import _get_pool_settings

            settings = _get_pool_settings()

            assert settings["pool_pre_ping"] is True
            assert settings["echo"] is False
            assert settings["pool_size"] == 10
            assert settings["max_overflow"] == 20
            assert settings["pool_recycle"] == 1800

    def test_development_pool_settings(self) -> None:
        """Development environment uses smaller pool with SQL logging."""
        mock_settings = MagicMock()
        mock_settings.ENVIRONMENT = "development"

        with patch("app.core.database.settings", mock_settings):
            from app.core.database import _get_pool_settings

            settings = _get_pool_settings()

            assert settings["pool_pre_ping"] is False
            assert settings["echo"] is True
            assert settings["pool_size"] == 5
            assert settings["max_overflow"] == 10

    def test_custom_pool_size_from_env(self) -> None:
        """Production pool size can be customized via environment."""
        mock_settings = MagicMock()
        mock_settings.ENVIRONMENT = "production"

        with (
            patch("app.core.database.settings", mock_settings),
            patch.dict(os.environ, {"DB_POOL_SIZE": "25"}),
        ):
            from app.core.database import _get_pool_settings

            settings = _get_pool_settings()
            assert settings["pool_size"] == 25

    def test_custom_max_overflow_from_env(self) -> None:
        """Production max overflow can be customized via environment."""
        mock_settings = MagicMock()
        mock_settings.ENVIRONMENT = "production"

        with (
            patch("app.core.database.settings", mock_settings),
            patch.dict(os.environ, {"DB_MAX_OVERFLOW": "50"}),
        ):
            from app.core.database import _get_pool_settings

            settings = _get_pool_settings()
            assert settings["max_overflow"] == 50

    def test_custom_pool_recycle_from_env(self) -> None:
        """Production pool recycle time can be customized via environment."""
        mock_settings = MagicMock()
        mock_settings.ENVIRONMENT = "production"

        with (
            patch("app.core.database.settings", mock_settings),
            patch.dict(os.environ, {"DB_POOL_RECYCLE": "900"}),
        ):
            from app.core.database import _get_pool_settings

            settings = _get_pool_settings()
            assert settings["pool_recycle"] == 900
