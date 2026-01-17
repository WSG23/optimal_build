"""OAuth2/OIDC authentication module for enterprise SSO.

Supports:
- Azure AD (Microsoft Entra ID)
- Google Workspace
- Okta
- Generic OIDC providers
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""

    AZURE = "azure"
    GOOGLE = "google"
    OKTA = "okta"
    GENERIC = "generic"


@dataclass
class OAuthConfig:
    """OAuth provider configuration."""

    provider: OAuthProvider
    client_id: str
    client_secret: str
    tenant_id: str | None = None  # For Azure AD
    domain: str | None = None  # For Okta
    authorization_url: str | None = None
    token_url: str | None = None
    userinfo_url: str | None = None
    scopes: list[str] | None = None
    redirect_uri: str | None = None

    def __post_init__(self) -> None:
        """Set provider-specific URLs if not explicitly configured."""
        if self.provider == OAuthProvider.AZURE:
            base_url = f"https://login.microsoftonline.com/{self.tenant_id}"
            self.authorization_url = self.authorization_url or f"{base_url}/oauth2/v2.0/authorize"
            self.token_url = self.token_url or f"{base_url}/oauth2/v2.0/token"
            self.userinfo_url = self.userinfo_url or "https://graph.microsoft.com/v1.0/me"
            self.scopes = self.scopes or ["openid", "profile", "email", "User.Read"]

        elif self.provider == OAuthProvider.GOOGLE:
            self.authorization_url = self.authorization_url or "https://accounts.google.com/o/oauth2/v2/auth"
            self.token_url = self.token_url or "https://oauth2.googleapis.com/token"
            self.userinfo_url = self.userinfo_url or "https://www.googleapis.com/oauth2/v3/userinfo"
            self.scopes = self.scopes or ["openid", "profile", "email"]

        elif self.provider == OAuthProvider.OKTA:
            base_url = f"https://{self.domain}"
            self.authorization_url = self.authorization_url or f"{base_url}/oauth2/default/v1/authorize"
            self.token_url = self.token_url or f"{base_url}/oauth2/default/v1/token"
            self.userinfo_url = self.userinfo_url or f"{base_url}/oauth2/default/v1/userinfo"
            self.scopes = self.scopes or ["openid", "profile", "email"]


@dataclass
class OAuthUser:
    """User information from OAuth provider."""

    id: str
    email: str
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
    provider: OAuthProvider | None = None
    raw_data: dict[str, Any] | None = None


class OAuthClient:
    """OAuth2/OIDC client for enterprise authentication."""

    def __init__(self, config: OAuthConfig) -> None:
        self.config = config
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def get_authorization_url(self, state: str, nonce: str | None = None) -> str:
        """Generate the authorization URL for the OAuth flow.

        Args:
            state: Random state parameter for CSRF protection.
            nonce: Random nonce for ID token validation (OIDC).

        Returns:
            The authorization URL to redirect the user to.
        """
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes or ["openid", "profile", "email"]),
            "state": state,
        }

        if nonce:
            params["nonce"] = nonce

        # Provider-specific parameters
        if self.config.provider == OAuthProvider.AZURE:
            params["response_mode"] = "query"

        return f"{self.config.authorization_url}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from the OAuth callback.

        Returns:
            Token response containing access_token, id_token, etc.
        """
        client = await self._get_client()

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        response = await client.post(
            self.config.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            raise OAuthError(f"Token exchange failed: {response.status_code}")

        return response.json()

    async def get_user_info(self, access_token: str) -> OAuthUser:
        """Fetch user information from the OAuth provider.

        Args:
            access_token: OAuth access token.

        Returns:
            OAuthUser with user information.
        """
        client = await self._get_client()

        response = await client.get(
            self.config.userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code != 200:
            logger.error(f"User info request failed: {response.text}")
            raise OAuthError(f"User info request failed: {response.status_code}")

        data = response.json()
        return self._parse_user_info(data)

    def _parse_user_info(self, data: dict[str, Any]) -> OAuthUser:
        """Parse user info response based on provider.

        Args:
            data: Raw user info response from provider.

        Returns:
            Normalized OAuthUser object.
        """
        if self.config.provider == OAuthProvider.AZURE:
            return OAuthUser(
                id=data.get("id") or data.get("sub", ""),
                email=data.get("mail") or data.get("userPrincipalName", ""),
                name=data.get("displayName"),
                given_name=data.get("givenName"),
                family_name=data.get("surname"),
                provider=self.config.provider,
                raw_data=data,
            )

        elif self.config.provider == OAuthProvider.GOOGLE:
            return OAuthUser(
                id=data.get("sub", ""),
                email=data.get("email", ""),
                name=data.get("name"),
                given_name=data.get("given_name"),
                family_name=data.get("family_name"),
                picture=data.get("picture"),
                provider=self.config.provider,
                raw_data=data,
            )

        elif self.config.provider == OAuthProvider.OKTA:
            return OAuthUser(
                id=data.get("sub", ""),
                email=data.get("email", ""),
                name=data.get("name"),
                given_name=data.get("given_name"),
                family_name=data.get("family_name"),
                provider=self.config.provider,
                raw_data=data,
            )

        # Generic OIDC
        return OAuthUser(
            id=data.get("sub", ""),
            email=data.get("email", ""),
            name=data.get("name"),
            given_name=data.get("given_name"),
            family_name=data.get("family_name"),
            picture=data.get("picture"),
            provider=self.config.provider,
            raw_data=data,
        )

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an access token using a refresh token.

        Args:
            refresh_token: OAuth refresh token.

        Returns:
            New token response.
        """
        client = await self._get_client()

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        response = await client.post(
            self.config.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.text}")
            raise OAuthError(f"Token refresh failed: {response.status_code}")

        return response.json()


class OAuthError(Exception):
    """OAuth-related error."""

    pass


def get_oauth_config_from_env(provider: str) -> OAuthConfig | None:
    """Load OAuth configuration from environment variables.

    Args:
        provider: Provider name (azure, google, okta).

    Returns:
        OAuthConfig if configured, None otherwise.
    """
    provider_enum = OAuthProvider(provider.lower())
    prefix = f"OAUTH_{provider.upper()}"

    client_id = os.getenv(f"{prefix}_CLIENT_ID")
    client_secret = os.getenv(f"{prefix}_CLIENT_SECRET")

    if not client_id or not client_secret:
        return None

    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    redirect_uri = os.getenv(
        f"{prefix}_REDIRECT_URI",
        f"{base_url}/api/v1/auth/oauth/{provider}/callback",
    )

    config = OAuthConfig(
        provider=provider_enum,
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=os.getenv(f"{prefix}_TENANT_ID"),
        domain=os.getenv(f"{prefix}_DOMAIN"),
        redirect_uri=redirect_uri,
    )

    return config


# Global OAuth clients cache
_oauth_clients: dict[str, OAuthClient] = {}


def get_oauth_client(provider: str) -> OAuthClient | None:
    """Get or create an OAuth client for a provider.

    Args:
        provider: Provider name.

    Returns:
        OAuthClient if provider is configured, None otherwise.
    """
    if provider in _oauth_clients:
        return _oauth_clients[provider]

    config = get_oauth_config_from_env(provider)
    if config is None:
        return None

    client = OAuthClient(config)
    _oauth_clients[provider] = client
    return client


async def cleanup_oauth_clients() -> None:
    """Close all OAuth clients."""
    for client in _oauth_clients.values():
        await client.close()
    _oauth_clients.clear()
