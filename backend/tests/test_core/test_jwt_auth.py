"""Tests for JWT authentication utilities."""

from datetime import timedelta

import pytest
from backend._compat.datetime import utcnow
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.jwt_auth import (
    ALGORITHM,
    SECRET_KEY,
    TokenData,
    TokenResponse,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_optional_user,
    verify_token,
)


class TestTokenModels:
    """Tests for token data models."""

    def test_token_data_creation(self):
        """Test creating a TokenData instance."""
        token_data = TokenData(
            email="test@example.com",
            username="testuser",
            user_id="user-123",
        )

        assert token_data.email == "test@example.com"
        assert token_data.username == "testuser"
        assert token_data.user_id == "user-123"

    def test_token_response_creation(self):
        """Test creating a TokenResponse instance."""
        response = TokenResponse(
            access_token="access-token-123",
            refresh_token="refresh-token-456",
        )

        assert response.access_token == "access-token-123"
        assert response.refresh_token == "refresh-token-456"
        assert response.token_type == "bearer"

    def test_token_response_custom_token_type(self):
        """Test TokenResponse with custom token type."""
        response = TokenResponse(
            access_token="token",
            refresh_token="refresh",
            token_type="custom",
        )

        assert response.token_type == "custom"


class TestCreateTokens:
    """Tests for token creation functions."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "user_id": "user-123",
        }

        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify token contents
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["email"] == "test@example.com"
        assert payload["username"] == "testuser"
        assert payload["user_id"] == "user-123"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "user_id": "user-123",
        }

        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify token contents
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["email"] == "test@example.com"
        assert payload["username"] == "testuser"
        assert payload["user_id"] == "user-123"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_access_token_has_correct_expiration(self):
        """Test that access token expires after expected time."""
        data = {"email": "test@example.com", "username": "test", "user_id": "123"}

        before = utcnow()
        token = create_access_token(data)
        after = utcnow()

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = payload["exp"]

        # Should expire approximately 30 minutes from now
        expected_min = before + timedelta(minutes=29)
        expected_max = after + timedelta(minutes=31)

        assert expected_min.timestamp() <= exp_time <= expected_max.timestamp()

    def test_refresh_token_has_correct_expiration(self):
        """Test that refresh token expires after expected time."""
        data = {"email": "test@example.com", "username": "test", "user_id": "123"}

        before = utcnow()
        token = create_refresh_token(data)
        after = utcnow()

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = payload["exp"]

        # Should expire approximately 7 days from now
        expected_min = before + timedelta(days=6, hours=23)
        expected_max = after + timedelta(days=7, hours=1)

        assert expected_min.timestamp() <= exp_time <= expected_max.timestamp()

    def test_token_does_not_mutate_original_data(self):
        """Test that creating a token doesn't mutate the input data."""
        original_data = {
            "email": "test@example.com",
            "username": "testuser",
            "user_id": "user-123",
        }
        data_copy = original_data.copy()

        create_access_token(original_data)

        assert original_data == data_copy
        assert "exp" not in original_data
        assert "type" not in original_data


class TestVerifyToken:
    """Tests for token verification."""

    def test_verify_valid_access_token(self):
        """Test verifying a valid access token."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "user_id": "user-123",
        }
        token = create_access_token(data)

        token_data = verify_token(token, token_type="access")

        assert token_data.email == "test@example.com"
        assert token_data.username == "testuser"
        assert token_data.user_id == "user-123"

    def test_verify_valid_refresh_token(self):
        """Test verifying a valid refresh token."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "user_id": "user-123",
        }
        token = create_refresh_token(data)

        token_data = verify_token(token, token_type="refresh")

        assert token_data.email == "test@example.com"
        assert token_data.username == "testuser"
        assert token_data.user_id == "user-123"

    def test_verify_token_wrong_type_raises_error(self):
        """Test that using access token as refresh token fails."""
        data = {"email": "test@example.com", "username": "test", "user_id": "123"}
        token = create_access_token(data)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, token_type="refresh")

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_verify_token_invalid_signature_raises_error(self):
        """Test that invalid token signature raises error."""
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_verify_token_missing_email_raises_error(self):
        """Test that token without email raises error."""
        data = {"username": "testuser", "user_id": "user-123"}
        # Manually create token without email
        to_encode = data.copy()
        to_encode.update({"exp": utcnow() + timedelta(minutes=30), "type": "access"})
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401

    def test_verify_token_missing_username_raises_error(self):
        """Test that token without username raises error."""
        data = {"email": "test@example.com", "user_id": "user-123"}
        to_encode = data.copy()
        to_encode.update({"exp": utcnow() + timedelta(minutes=30), "type": "access"})
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401

    def test_verify_token_missing_user_id_raises_error(self):
        """Test that token without user_id raises error."""
        data = {"email": "test@example.com", "username": "testuser"}
        to_encode = data.copy()
        to_encode.update({"exp": utcnow() + timedelta(minutes=30), "type": "access"})
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401

    def test_verify_expired_token_raises_error(self):
        """Test that expired token raises error."""
        data = {"email": "test@example.com", "username": "test", "user_id": "123"}
        # Create token that expired 1 hour ago
        to_encode = data.copy()
        to_encode.update({"exp": utcnow() - timedelta(hours=1), "type": "access"})
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    async def test_get_current_user_with_valid_token(self):
        """Test getting current user with valid token."""
        data = {"email": "test@example.com", "username": "test", "user_id": "123"}
        token = create_access_token(data)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        user = await get_current_user(credentials)

        assert user.email == "test@example.com"
        assert user.username == "test"
        assert user.user_id == "123"

    async def test_get_current_user_with_invalid_token(self):
        """Test getting current user with invalid token raises error."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid-token"
        )

        with pytest.raises(HTTPException):
            await get_current_user(credentials)


@pytest.mark.asyncio
class TestGetOptionalUser:
    """Tests for get_optional_user dependency."""

    async def test_get_optional_user_with_valid_token(self):
        """Test getting optional user with valid token."""
        data = {"email": "test@example.com", "username": "test", "user_id": "123"}
        token = create_access_token(data)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        user = await get_optional_user(credentials)

        assert user is not None
        assert user.email == "test@example.com"
        assert user.username == "test"
        assert user.user_id == "123"

    async def test_get_optional_user_without_credentials(self):
        """Test getting optional user without credentials returns None."""
        user = await get_optional_user(None)

        assert user is None

    async def test_get_optional_user_with_invalid_token(self):
        """Test getting optional user with invalid token raises error."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid-token"
        )

        with pytest.raises(HTTPException):
            await get_optional_user(credentials)


class TestSecretKeyConfiguration:
    """Tests for SECRET_KEY configuration."""

    def test_secret_key_from_environment(self):
        """Test that SECRET_KEY is read from environment."""
        # SECRET_KEY should be set or have a fallback
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0

    def test_secret_key_used_for_signing(self):
        """Test that SECRET_KEY is actually used for token signing."""
        data = {"email": "test@example.com", "username": "test", "user_id": "123"}
        token = create_access_token(data)

        # Should be able to decode with the same secret
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["email"] == "test@example.com"

        # Should NOT be decodable with a different secret
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret-key", algorithms=[ALGORITHM])
