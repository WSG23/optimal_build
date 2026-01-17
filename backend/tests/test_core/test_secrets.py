"""Tests for the secrets management module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from app.core.secrets import (
    AWSSecretsManager,
    EnvironmentSecretsBackend,
    VaultSecretsBackend,
    get_app_secrets,
    get_database_credentials,
    get_oauth_credentials,
    get_secrets_backend,
    get_sentry_dsn,
)


class TestEnvironmentSecretsBackend:
    """Tests for environment variable secrets backend."""

    @pytest.fixture
    def backend(self) -> EnvironmentSecretsBackend:
        return EnvironmentSecretsBackend(prefix="TEST")

    @pytest.mark.asyncio
    async def test_get_secret_from_env(
        self, backend: EnvironmentSecretsBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test retrieving secrets from environment variables."""
        monkeypatch.setenv("TEST_DATABASE_HOST", "localhost")
        monkeypatch.setenv("TEST_DATABASE_PORT", "5432")

        result = await backend.get_secret("database")

        assert result["host"] == "localhost"
        assert result["port"] == "5432"

    @pytest.mark.asyncio
    async def test_get_secret_empty_when_not_set(
        self, backend: EnvironmentSecretsBackend
    ) -> None:
        """Test returns empty dict when no matching env vars."""
        result = await backend.get_secret("nonexistent")
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_secret_value(
        self, backend: EnvironmentSecretsBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test retrieving a specific secret value."""
        monkeypatch.setenv("TEST_APP_SECRET_KEY", "my-secret-key")

        result = await backend.get_secret_value("app", "secret_key")

        assert result == "my-secret-key"


class TestAWSSecretsManager:
    """Tests for AWS Secrets Manager backend."""

    @pytest.fixture
    def mock_boto3_client(self) -> MagicMock:
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(
                {
                    "username": "admin",
                    "password": "super-secret",
                }
            )
        }
        return mock_client

    @pytest.mark.asyncio
    async def test_get_secret(self, mock_boto3_client: MagicMock) -> None:
        """Test retrieving secrets from AWS Secrets Manager."""
        backend = AWSSecretsManager(region_name="us-east-1")
        backend._client = mock_boto3_client

        result = await backend.get_secret("production/database")

        assert result["username"] == "admin"
        assert result["password"] == "super-secret"


class TestVaultSecretsBackend:
    """Tests for HashiCorp Vault backend."""

    @pytest.fixture
    def mock_hvac_client(self) -> MagicMock:
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"username": "vault-user", "password": "vault-secret"}}
        }
        return mock_client

    @pytest.mark.asyncio
    async def test_get_secret(self, mock_hvac_client: MagicMock) -> None:
        """Test retrieving secrets from Vault."""
        backend = VaultSecretsBackend(
            addr="https://vault.example.com",
            token="test-token",
            mount_point="optimal-build",
        )
        backend._client = mock_hvac_client

        result = await backend.get_secret("production/database")

        assert result["username"] == "vault-user"


class TestGetSecretsBackend:
    """Tests for the secrets backend factory function."""

    def test_returns_env_backend_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SECRETS_MANAGER", raising=False)
        get_secrets_backend.cache_clear()

        backend = get_secrets_backend()

        assert isinstance(backend, EnvironmentSecretsBackend)

    def test_returns_aws_backend(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SECRETS_MANAGER", "aws")
        get_secrets_backend.cache_clear()

        backend = get_secrets_backend()

        assert isinstance(backend, AWSSecretsManager)


class TestCredentialFunctions:
    """Tests for credential retrieval convenience functions."""

    @pytest.mark.asyncio
    async def test_get_database_credentials_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SECRETS_MANAGER", "env")
        monkeypatch.setenv("POSTGRES_USER", "testuser")
        monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
        monkeypatch.setenv("POSTGRES_SERVER", "testhost")
        get_secrets_backend.cache_clear()

        creds = await get_database_credentials()

        assert creds["username"] == "testuser"
        assert creds["host"] == "testhost"

    @pytest.mark.asyncio
    async def test_get_app_secrets_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SECRETS_MANAGER", "env")
        monkeypatch.setenv("SECRET_KEY", "my-secret-key")
        get_secrets_backend.cache_clear()

        secrets = await get_app_secrets()

        assert secrets["secret_key"] == "my-secret-key"

    @pytest.mark.asyncio
    async def test_get_oauth_credentials_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SECRETS_MANAGER", "env")
        monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "google-client-id")
        get_secrets_backend.cache_clear()

        creds = await get_oauth_credentials("google")

        assert creds["client_id"] == "google-client-id"

    @pytest.mark.asyncio
    async def test_get_sentry_dsn_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SECRETS_MANAGER", "env")
        monkeypatch.setenv("SENTRY_DSN", "https://key@sentry.io/123")
        get_secrets_backend.cache_clear()

        dsn = await get_sentry_dsn()

        assert dsn == "https://key@sentry.io/123"
