"""Secrets management module for production environments.

Supports:
- AWS Secrets Manager
- HashiCorp Vault
- Environment variables (development fallback)
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


class SecretsBackend(ABC):
    """Abstract base class for secrets backends."""

    @abstractmethod
    async def get_secret(self, secret_name: str) -> dict[str, Any]:
        """Retrieve a secret by name.

        Args:
            secret_name: The name/path of the secret to retrieve.

        Returns:
            Dictionary containing the secret key-value pairs.
        """
        pass

    @abstractmethod
    async def get_secret_value(self, secret_name: str, key: str) -> str | None:
        """Retrieve a specific value from a secret.

        Args:
            secret_name: The name/path of the secret.
            key: The specific key within the secret.

        Returns:
            The secret value or None if not found.
        """
        pass


class AWSSecretsManager(SecretsBackend):
    """AWS Secrets Manager backend."""

    def __init__(self, region_name: str | None = None) -> None:
        self.region_name = region_name or os.getenv("AWS_REGION", "ap-southeast-1")
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy initialization of boto3 client."""
        if self._client is None:
            try:
                import boto3

                self._client = boto3.client(
                    "secretsmanager",
                    region_name=self.region_name,
                )
            except ImportError:
                raise RuntimeError(
                    "boto3 is required for AWS Secrets Manager. "
                    "Install with: pip install boto3"
                )
        return self._client

    async def get_secret(self, secret_name: str) -> dict[str, Any]:
        """Retrieve a secret from AWS Secrets Manager."""
        try:
            client = self._get_client()
            response = client.get_secret_value(SecretId=secret_name)
            secret_string = response.get("SecretString")
            if secret_string:
                return json.loads(secret_string)
            return {}
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise

    async def get_secret_value(self, secret_name: str, key: str) -> str | None:
        """Retrieve a specific value from an AWS secret."""
        secret = await self.get_secret(secret_name)
        return secret.get(key)


class VaultSecretsBackend(SecretsBackend):
    """HashiCorp Vault secrets backend."""

    def __init__(
        self,
        addr: str | None = None,
        token: str | None = None,
        mount_point: str = "optimal-build",
    ) -> None:
        self.addr = addr or os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.mount_point = mount_point
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy initialization of hvac client."""
        if self._client is None:
            try:
                import hvac

                self._client = hvac.Client(url=self.addr, token=self.token)
                if not self._client.is_authenticated():
                    raise RuntimeError("Vault authentication failed")
            except ImportError:
                raise RuntimeError(
                    "hvac is required for Vault. Install with: pip install hvac"
                )
        return self._client

    async def get_secret(self, secret_name: str) -> dict[str, Any]:
        """Retrieve a secret from HashiCorp Vault."""
        try:
            client = self._get_client()
            response = client.secrets.kv.v2.read_secret_version(
                path=secret_name,
                mount_point=self.mount_point,
            )
            return response.get("data", {}).get("data", {})
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise

    async def get_secret_value(self, secret_name: str, key: str) -> str | None:
        """Retrieve a specific value from a Vault secret."""
        secret = await self.get_secret(secret_name)
        return secret.get(key)


class EnvironmentSecretsBackend(SecretsBackend):
    """Environment variables backend for development."""

    def __init__(self, prefix: str = "OPTIMAL_BUILD") -> None:
        self.prefix = prefix

    async def get_secret(self, secret_name: str) -> dict[str, Any]:
        """Retrieve secrets from environment variables.

        Looks for variables with pattern: PREFIX_SECRETNAME_KEY
        """
        secret_prefix = f"{self.prefix}_{secret_name.upper().replace('/', '_')}_"
        result = {}
        for key, value in os.environ.items():
            if key.startswith(secret_prefix):
                secret_key = key[len(secret_prefix) :].lower()
                result[secret_key] = value
        return result

    async def get_secret_value(self, secret_name: str, key: str) -> str | None:
        """Retrieve a specific value from environment variables."""
        env_key = f"{self.prefix}_{secret_name.upper().replace('/', '_')}_{key.upper()}"
        return os.getenv(env_key)


@lru_cache(maxsize=1)
def get_secrets_backend() -> SecretsBackend:
    """Factory function to get the configured secrets backend.

    Returns:
        Configured secrets backend based on SECRETS_MANAGER env var.
    """
    manager = os.getenv("SECRETS_MANAGER", "env").lower()

    if manager == "aws":
        return AWSSecretsManager()
    elif manager == "vault":
        return VaultSecretsBackend()
    else:
        return EnvironmentSecretsBackend()


async def get_database_credentials() -> dict[str, str]:
    """Retrieve database credentials from the secrets backend.

    Returns:
        Dictionary with keys: username, password, host, port, database
    """
    backend = get_secrets_backend()
    environment = os.getenv("ENVIRONMENT", "development")

    if isinstance(backend, EnvironmentSecretsBackend):
        # Fallback to direct environment variables for development
        return {
            "username": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "password"),
            "host": os.getenv("POSTGRES_SERVER", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "building_compliance"),
        }

    secret_name = f"{environment}/database"
    return await backend.get_secret(secret_name)


async def get_app_secrets() -> dict[str, str]:
    """Retrieve application secrets from the secrets backend.

    Returns:
        Dictionary with keys: secret_key, jwt_secret, etc.
    """
    backend = get_secrets_backend()
    environment = os.getenv("ENVIRONMENT", "development")

    if isinstance(backend, EnvironmentSecretsBackend):
        # Fallback to direct environment variables for development
        return {
            "secret_key": os.getenv("SECRET_KEY", "dev-only-change-in-production"),
            "listing_token_secret": os.getenv("LISTING_TOKEN_SECRET", ""),
        }

    secret_name = f"{environment}/app"
    return await backend.get_secret(secret_name)


async def get_s3_credentials() -> dict[str, str]:
    """Retrieve S3/MinIO credentials from the secrets backend.

    Returns:
        Dictionary with keys: access_key, secret_key, endpoint
    """
    backend = get_secrets_backend()
    environment = os.getenv("ENVIRONMENT", "development")

    if isinstance(backend, EnvironmentSecretsBackend):
        return {
            "access_key": os.getenv("S3_ACCESS_KEY", "minioadmin"),
            "secret_key": os.getenv("S3_SECRET_KEY", "minioadmin"),
            "endpoint": os.getenv("S3_ENDPOINT", "http://localhost:9000"),
        }

    secret_name = f"{environment}/s3"
    return await backend.get_secret(secret_name)


async def get_redis_credentials() -> dict[str, str]:
    """Retrieve Redis credentials from the secrets backend.

    Returns:
        Dictionary with keys: url, password (optional)
    """
    backend = get_secrets_backend()
    environment = os.getenv("ENVIRONMENT", "development")

    if isinstance(backend, EnvironmentSecretsBackend):
        return {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "password": os.getenv("REDIS_PASSWORD", ""),
        }

    secret_name = f"{environment}/redis"
    return await backend.get_secret(secret_name)


async def get_oauth_credentials(provider: str) -> dict[str, str]:
    """Retrieve OAuth provider credentials.

    Args:
        provider: OAuth provider name (e.g., 'google', 'azure', 'okta')

    Returns:
        Dictionary with keys: client_id, client_secret, etc.
    """
    backend = get_secrets_backend()
    environment = os.getenv("ENVIRONMENT", "development")

    if isinstance(backend, EnvironmentSecretsBackend):
        prefix = f"OAUTH_{provider.upper()}"
        return {
            "client_id": os.getenv(f"{prefix}_CLIENT_ID", ""),
            "client_secret": os.getenv(f"{prefix}_CLIENT_SECRET", ""),
            "tenant_id": os.getenv(f"{prefix}_TENANT_ID", ""),
        }

    secret_name = f"{environment}/oauth/{provider}"
    return await backend.get_secret(secret_name)


async def get_sentry_dsn() -> str | None:
    """Retrieve Sentry DSN for error tracking.

    Returns:
        Sentry DSN string or None if not configured.
    """
    backend = get_secrets_backend()
    environment = os.getenv("ENVIRONMENT", "development")

    if isinstance(backend, EnvironmentSecretsBackend):
        return os.getenv("SENTRY_DSN")

    secret_name = f"{environment}/monitoring"
    try:
        secrets = await backend.get_secret(secret_name)
        return secrets.get("sentry_dsn")
    except Exception:
        return None
