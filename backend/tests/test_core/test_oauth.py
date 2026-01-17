"""Tests for the OAuth2/OIDC authentication module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.oauth import (
    OAuthClient,
    OAuthConfig,
    OAuthError,
    OAuthProvider,
    OAuthUser,
    get_oauth_client,
    get_oauth_config_from_env,
)


class TestOAuthConfig:
    """Tests for OAuthConfig initialization."""

    def test_azure_config_sets_defaults(self) -> None:
        """Test Azure AD config sets correct default URLs."""
        config = OAuthConfig(
            provider=OAuthProvider.AZURE,
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant",
        )

        assert "login.microsoftonline.com" in config.authorization_url
        assert config.tenant_id in config.authorization_url
        assert "graph.microsoft.com" in config.userinfo_url
        assert "openid" in config.scopes

    def test_google_config_sets_defaults(self) -> None:
        """Test Google config sets correct default URLs."""
        config = OAuthConfig(
            provider=OAuthProvider.GOOGLE,
            client_id="test-client-id",
            client_secret="test-secret",
        )

        assert "accounts.google.com" in config.authorization_url
        assert "googleapis.com" in config.userinfo_url
        assert "openid" in config.scopes

    def test_okta_config_sets_defaults(self) -> None:
        """Test Okta config sets correct default URLs."""
        config = OAuthConfig(
            provider=OAuthProvider.OKTA,
            client_id="test-client-id",
            client_secret="test-secret",
            domain="dev-123456.okta.com",
        )

        assert "dev-123456.okta.com" in config.authorization_url
        assert "dev-123456.okta.com" in config.userinfo_url

    def test_custom_urls_override_defaults(self) -> None:
        """Test custom URLs override provider defaults."""
        config = OAuthConfig(
            provider=OAuthProvider.GOOGLE,
            client_id="test-client-id",
            client_secret="test-secret",
            authorization_url="https://custom.auth.com/authorize",
            token_url="https://custom.auth.com/token",
        )

        assert config.authorization_url == "https://custom.auth.com/authorize"
        assert config.token_url == "https://custom.auth.com/token"


class TestOAuthClient:
    """Tests for OAuthClient."""

    @pytest.fixture
    def google_config(self) -> OAuthConfig:
        return OAuthConfig(
            provider=OAuthProvider.GOOGLE,
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8000/callback",
        )

    @pytest.fixture
    def client(self, google_config: OAuthConfig) -> OAuthClient:
        return OAuthClient(google_config)

    def test_get_authorization_url(self, client: OAuthClient) -> None:
        """Test generating authorization URL."""
        url = client.get_authorization_url(state="random-state", nonce="random-nonce")

        assert "accounts.google.com" in url
        assert "client_id=test-client-id" in url
        assert "state=random-state" in url
        assert "nonce=random-nonce" in url
        assert "redirect_uri=" in url
        assert "response_type=code" in url

    def test_get_authorization_url_includes_scopes(self, client: OAuthClient) -> None:
        """Test authorization URL includes scopes."""
        url = client.get_authorization_url(state="test-state")

        assert "scope=" in url
        assert "openid" in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, client: OAuthClient) -> None:
        """Test successful code exchange."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "id_token": "test-id-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600,
        }

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_get_client.return_value = mock_http

            result = await client.exchange_code("auth-code-123")

            assert result["access_token"] == "test-access-token"
            assert result["id_token"] == "test-id-token"
            mock_http.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_exchange_code_failure(self, client: OAuthClient) -> None:
        """Test code exchange failure."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid code"

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_get_client.return_value = mock_http

            with pytest.raises(OAuthError, match="Token exchange failed"):
                await client.exchange_code("invalid-code")

    @pytest.mark.asyncio
    async def test_get_user_info_google(self, client: OAuthClient) -> None:
        """Test fetching user info from Google."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sub": "12345",
            "email": "user@example.com",
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/photo.jpg",
        }

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value = mock_http

            user = await client.get_user_info("test-access-token")

            assert isinstance(user, OAuthUser)
            assert user.id == "12345"
            assert user.email == "user@example.com"
            assert user.name == "Test User"
            assert user.given_name == "Test"
            assert user.picture == "https://example.com/photo.jpg"

    @pytest.mark.asyncio
    async def test_get_user_info_failure(self, client: OAuthClient) -> None:
        """Test user info fetch failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value = mock_http

            with pytest.raises(OAuthError, match="User info request failed"):
                await client.get_user_info("invalid-token")

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: OAuthClient) -> None:
        """Test successful token refresh."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 3600,
        }

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_get_client.return_value = mock_http

            result = await client.refresh_token("refresh-token-123")

            assert result["access_token"] == "new-access-token"


class TestOAuthUserParsing:
    """Tests for parsing user info from different providers."""

    def test_parse_azure_user(self) -> None:
        """Test parsing Azure AD user info."""
        config = OAuthConfig(
            provider=OAuthProvider.AZURE,
            client_id="test",
            client_secret="test",
            tenant_id="test-tenant",
        )
        client = OAuthClient(config)

        data = {
            "id": "azure-user-id",
            "mail": "user@company.com",
            "displayName": "Azure User",
            "givenName": "Azure",
            "surname": "User",
        }

        user = client._parse_user_info(data)

        assert user.id == "azure-user-id"
        assert user.email == "user@company.com"
        assert user.name == "Azure User"
        assert user.provider == OAuthProvider.AZURE

    def test_parse_okta_user(self) -> None:
        """Test parsing Okta user info."""
        config = OAuthConfig(
            provider=OAuthProvider.OKTA,
            client_id="test",
            client_secret="test",
            domain="dev.okta.com",
        )
        client = OAuthClient(config)

        data = {
            "sub": "okta-user-id",
            "email": "user@okta.com",
            "name": "Okta User",
        }

        user = client._parse_user_info(data)

        assert user.id == "okta-user-id"
        assert user.email == "user@okta.com"
        assert user.provider == OAuthProvider.OKTA


class TestOAuthConfigFromEnv:
    """Tests for loading OAuth config from environment."""

    def test_returns_none_when_not_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test returns None when credentials not set."""
        monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_SECRET", raising=False)

        config = get_oauth_config_from_env("google")

        assert config is None

    def test_loads_google_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading Google OAuth config from env."""
        monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "google-client-id")
        monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "google-client-secret")
        monkeypatch.setenv("BASE_URL", "https://app.example.com")

        config = get_oauth_config_from_env("google")

        assert config is not None
        assert config.provider == OAuthProvider.GOOGLE
        assert config.client_id == "google-client-id"
        assert "app.example.com" in config.redirect_uri

    def test_loads_azure_config_with_tenant(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading Azure OAuth config with tenant ID."""
        monkeypatch.setenv("OAUTH_AZURE_CLIENT_ID", "azure-client-id")
        monkeypatch.setenv("OAUTH_AZURE_CLIENT_SECRET", "azure-client-secret")
        monkeypatch.setenv("OAUTH_AZURE_TENANT_ID", "azure-tenant-id")

        config = get_oauth_config_from_env("azure")

        assert config is not None
        assert config.provider == OAuthProvider.AZURE
        assert config.tenant_id == "azure-tenant-id"


class TestGetOAuthClient:
    """Tests for OAuth client factory."""

    def test_returns_none_when_not_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test returns None when provider not configured."""
        monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)

        client = get_oauth_client("google")

        assert client is None

    def test_returns_client_when_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test returns client when provider is configured."""
        monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "test-id")
        monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "test-secret")

        # Clear cache
        from app.core.oauth import _oauth_clients

        _oauth_clients.clear()

        client = get_oauth_client("google")

        assert client is not None
        assert isinstance(client, OAuthClient)

    def test_caches_client_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test client instances are cached."""
        monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "test-id")
        monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "test-secret")

        from app.core.oauth import _oauth_clients

        _oauth_clients.clear()

        client1 = get_oauth_client("google")
        client2 = get_oauth_client("google")

        assert client1 is client2
