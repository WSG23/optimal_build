"""Comprehensive tests for users_secure API.

Tests cover:
- UserSignup model
- UserLogin model
- UserResponse model
- LoginResponse model
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.users_secure import (
    UserSignup,
    UserLogin,
    UserResponse,
    LoginResponse,
)
from app.core.auth import TokenResponse, AuthUser

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestUserSignup:
    """Tests for UserSignup model."""

    def test_valid_signup(self) -> None:
        """Test valid signup data."""
        signup = UserSignup(
            email="test@example.com",
            password="SecurePass123",
            username="testuser",
            full_name="Test User",
        )
        assert signup.email == "test@example.com"
        assert signup.username == "testuser"

    def test_full_name_validation(self) -> None:
        """Test full_name cannot be just whitespace."""
        raised = False
        try:
            UserSignup(
                email="test@example.com",
                password="SecurePass123",
                username="testuser",
                full_name="   ",
            )
        except ValidationError:
            raised = True
        assert raised, "Should raise for whitespace-only full_name"

    def test_full_name_trimmed(self) -> None:
        """Test full_name is trimmed."""
        signup = UserSignup(
            email="test@example.com",
            password="SecurePass123",
            username="testuser",
            full_name="  John Doe  ",
        )
        assert signup.full_name == "John Doe"

    def test_with_company_name(self) -> None:
        """Test signup with company name."""
        signup = UserSignup(
            email="business@example.com",
            password="SecurePass123",
            username="businessuser",
            full_name="Jane Smith",
            company_name="Acme Corp",
        )
        assert signup.company_name == "Acme Corp"


class TestUserLogin:
    """Tests for UserLogin model."""

    def test_valid_login(self) -> None:
        """Test valid login credentials."""
        login = UserLogin(
            email="test@example.com",
            password="SecurePass123",
        )
        assert login.email == "test@example.com"
        assert login.password == "SecurePass123"


class TestUserResponse:
    """Tests for UserResponse model."""

    def test_from_auth_user(self) -> None:
        """Test creating response from AuthUser."""
        from datetime import datetime

        auth_user = AuthUser(
            id="user-123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_pw",
            company_name="Test Corp",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            is_active=True,
        )

        response = UserResponse.from_auth_user(auth_user)
        assert response.id == "user-123"
        assert response.email == "test@example.com"
        assert response.full_name == "Test User"
        assert response.is_active is True

    def test_response_fields(self) -> None:
        """Test response fields."""
        response = UserResponse(
            id="user-456",
            email="developer@example.com",
            username="developer",
            full_name="Developer User",
            company_name="Dev Inc",
            created_at="2024-01-15T09:30:00",
            is_active=True,
        )
        assert response.id == "user-456"
        assert response.company_name == "Dev Inc"

    def test_nullable_company(self) -> None:
        """Test nullable company_name."""
        response = UserResponse(
            id="user-789",
            email="individual@example.com",
            username="individual",
            full_name="Solo Developer",
            company_name=None,
            created_at="2024-02-01T08:00:00",
            is_active=True,
        )
        assert response.company_name is None


class TestLoginResponse:
    """Tests for LoginResponse model."""

    def test_login_response(self) -> None:
        """Test login response structure."""
        user = UserResponse(
            id="user-123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            company_name=None,
            created_at="2024-01-01T00:00:00",
            is_active=True,
        )
        tokens = TokenResponse(
            access_token="eyJ...",
            refresh_token="refresh...",
            token_type="bearer",
        )

        response = LoginResponse(
            message="Login successful",
            user=user,
            tokens=tokens,
        )
        assert response.message == "Login successful"
        assert response.user.email == "test@example.com"
        assert response.tokens.token_type == "bearer"


class TestUserSecureScenarios:
    """Tests for user security use case scenarios."""

    def test_registration_workflow(self) -> None:
        """Test user registration workflow."""
        # User fills signup form
        signup = UserSignup(
            email="newuser@example.com",
            password="MySecure123Pass",
            username="newuser",
            full_name="New User",
            company_name="New Corp",
        )

        # Verify data is captured
        assert signup.email == "newuser@example.com"
        assert signup.full_name == "New User"

        # Simulate response after registration
        response = UserResponse(
            id="new-user-id",
            email=signup.email,
            username=signup.username,
            full_name=signup.full_name,
            company_name=signup.company_name,
            created_at="2024-03-01T12:00:00",
            is_active=True,
        )
        assert response.is_active is True

    def test_login_workflow(self) -> None:
        """Test user login workflow."""
        # User submits login form
        login = UserLogin(
            email="existing@example.com",
            password="ExistingPass123",
        )

        # Simulate successful login response
        user = UserResponse(
            id="existing-user-id",
            email=login.email,
            username="existinguser",
            full_name="Existing User",
            company_name=None,
            created_at="2024-01-01T00:00:00",
            is_active=True,
        )
        tokens = TokenResponse(
            access_token="jwt.access.token",
            refresh_token="jwt.refresh.token",
            token_type="bearer",
        )
        response = LoginResponse(
            message="Login successful",
            user=user,
            tokens=tokens,
        )

        assert response.user.email == login.email
        assert response.tokens.access_token is not None

    def test_inactive_user(self) -> None:
        """Test inactive user response."""
        response = UserResponse(
            id="inactive-user",
            email="inactive@example.com",
            username="inactiveuser",
            full_name="Inactive User",
            company_name=None,
            created_at="2024-01-01T00:00:00",
            is_active=False,
        )
        assert response.is_active is False

    def test_corporate_user(self) -> None:
        """Test corporate user with company details."""
        signup = UserSignup(
            email="executive@corporation.com",
            password="Corporate123Pass",
            username="executive",
            full_name="Corporate Executive",
            company_name="Global Corporation Ltd",
        )

        response = UserResponse(
            id="corp-user-id",
            email=signup.email,
            username=signup.username,
            full_name=signup.full_name,
            company_name=signup.company_name,
            created_at="2024-02-15T09:00:00",
            is_active=True,
        )

        assert response.company_name == "Global Corporation Ltd"

    def test_password_not_in_response(self) -> None:
        """Test password is not included in response."""
        response = UserResponse(
            id="user-123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            company_name=None,
            created_at="2024-01-01T00:00:00",
            is_active=True,
        )

        # Verify password field doesn't exist in response
        data = response.model_dump()
        assert "password" not in data
        assert "hashed_password" not in data

    def test_multiple_users(self) -> None:
        """Test handling multiple users."""
        users = [
            UserResponse(
                id=f"user-{i}",
                email=f"user{i}@example.com",
                username=f"user{i}",
                full_name=f"User {i}",
                company_name=f"Company {i}" if i % 2 == 0 else None,
                created_at="2024-01-01T00:00:00",
                is_active=True,
            )
            for i in range(5)
        ]

        assert len(users) == 5
        assert users[0].company_name == "Company 0"
        assert users[1].company_name is None
