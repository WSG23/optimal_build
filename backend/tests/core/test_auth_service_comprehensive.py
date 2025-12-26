"""Comprehensive tests for auth service (JWT tokens, login, registration, policy).

This module provides extensive coverage for:
- JWT token creation and verification
- User registration flows
- Login with lockout integration
- Authorization policy checks
- Edge cases and error handling
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from app.core.auth.service import (
    AuthResult,
    AuthService,
    AuthUser,
    InMemoryAuthRepository,
    PolicyContext,
    SignoffSnapshot,
    TokenData,
    TokenResponse,
    WorkspaceRole,
    can_export_permit_ready,
    can_invite_architect,
    create_access_token,
    create_refresh_token,
    create_tokens,
    requires_signoff,
    verify_token,
    watermark_forced,
    watermark_text,
)
from app.core.config import settings
from app.schemas.user import UserSignupBase
from app.services.account_lockout import (
    AccountLockoutService,
    LockoutConfig,
    get_lockout_service,
    reset_lockout_service,
)
from backend._compat.datetime import UTC


@pytest.fixture
def signup_payload() -> UserSignupBase:
    return UserSignupBase(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        password="SecurePass123!",
        company_name="Test Company",
    )


@pytest.fixture
def fresh_lockout_service() -> AccountLockoutService:
    reset_lockout_service()
    return get_lockout_service()


@pytest.fixture
def repo() -> InMemoryAuthRepository:
    return InMemoryAuthRepository()


@pytest.fixture
def auth_service(fresh_lockout_service: AccountLockoutService) -> AuthService:
    return AuthService(lockout_service=fresh_lockout_service)


@pytest.fixture
def approved_signoff() -> SignoffSnapshot:
    return SignoffSnapshot(
        project_id=1,
        overlay_version="v1.0",
        status="approved",
        architect_user_id=42,
        signed_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def pending_signoff() -> SignoffSnapshot:
    return SignoffSnapshot(
        project_id=1,
        overlay_version="v1.0",
        status="pending",
        architect_user_id=None,
        signed_at=None,
    )


class TestAccessTokenCreation:
    def test_create_access_token_contains_email(self) -> None:
        data = {"email": "test@example.com", "username": "testuser", "user_id": "123"}
        token = create_access_token(data)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert decoded["email"] == "test@example.com"

    def test_create_access_token_contains_type(self) -> None:
        data = {"email": "test@example.com", "username": "testuser", "user_id": "123"}
        token = create_access_token(data)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert decoded["type"] == "access"

    def test_create_access_token_has_expiration(self) -> None:
        data = {"email": "test@example.com", "username": "testuser", "user_id": "123"}
        token = create_access_token(data)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert "exp" in decoded
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=UTC)
        now = datetime.now(UTC)
        time_diff = exp_time - now
        assert timedelta(minutes=25) < time_diff < timedelta(minutes=35)


class TestRefreshTokenCreation:
    def test_create_refresh_token_has_type_refresh(self) -> None:
        data = {"email": "test@example.com", "username": "testuser", "user_id": "123"}
        token = create_refresh_token(data)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert decoded["type"] == "refresh"

    def test_create_refresh_token_has_longer_expiration(self) -> None:
        data = {"email": "test@example.com", "username": "testuser", "user_id": "123"}
        token = create_refresh_token(data)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=UTC)
        now = datetime.now(UTC)
        time_diff = exp_time - now
        assert timedelta(days=6) < time_diff < timedelta(days=8)


class TestTokenVerification:
    def test_verify_valid_access_token(self) -> None:
        data = {"email": "test@example.com", "username": "testuser", "user_id": "123"}
        token = create_access_token(data)
        result = verify_token(token, token_type="access")
        assert isinstance(result, TokenData)
        assert result.email == "test@example.com"

    def test_verify_access_token_with_refresh_type_fails(self) -> None:
        data = {"email": "test@example.com", "username": "testuser", "user_id": "123"}
        token = create_access_token(data)
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, token_type="refresh")
        assert exc_info.value.status_code == 401

    def test_verify_invalid_token_fails(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here", token_type="access")
        assert exc_info.value.status_code == 401

    def test_verify_token_missing_email_fails(self) -> None:
        token = jwt.encode(
            {"username": "testuser", "user_id": "123", "type": "access"},
            settings.SECRET_KEY,
            algorithm="HS256",
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, token_type="access")
        assert exc_info.value.status_code == 401

    def test_verify_expired_token_fails(self) -> None:
        expired_payload = {
            "email": "test@example.com",
            "username": "testuser",
            "user_id": "123",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, token_type="access")
        assert exc_info.value.status_code == 401


class TestCreateTokens:
    def test_create_tokens_returns_both_tokens(self) -> None:
        user_data = {
            "id": "user_123",
            "email": "test@example.com",
            "username": "testuser",
        }
        result = create_tokens(user_data)
        assert isinstance(result, TokenResponse)
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"


class TestUserRegistration:
    def test_register_user_success(
        self,
        auth_service: AuthService,
        repo: InMemoryAuthRepository,
        signup_payload: UserSignupBase,
    ) -> None:
        user = auth_service.register_user(signup_payload, repo=repo)
        assert isinstance(user, AuthUser)
        assert user.email == signup_payload.email
        assert user.is_active is True

    def test_register_user_password_is_hashed(
        self,
        auth_service: AuthService,
        repo: InMemoryAuthRepository,
        signup_payload: UserSignupBase,
    ) -> None:
        user = auth_service.register_user(signup_payload, repo=repo)
        assert user.hashed_password != signup_payload.password

    def test_register_duplicate_email_fails(
        self,
        auth_service: AuthService,
        repo: InMemoryAuthRepository,
        signup_payload: UserSignupBase,
    ) -> None:
        auth_service.register_user(signup_payload, repo=repo)
        duplicate_payload = UserSignupBase(
            email=signup_payload.email,
            username="different_username",
            full_name="Different User",
            password="AnotherPass123!",
            company_name=None,
        )
        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(duplicate_payload, repo=repo)
        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail

    def test_register_duplicate_username_fails(
        self,
        auth_service: AuthService,
        repo: InMemoryAuthRepository,
        signup_payload: UserSignupBase,
    ) -> None:
        auth_service.register_user(signup_payload, repo=repo)
        duplicate_payload = UserSignupBase(
            email="different@example.com",
            username=signup_payload.username,
            full_name="Different User",
            password="AnotherPass123!",
            company_name=None,
        )
        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(duplicate_payload, repo=repo)
        assert exc_info.value.status_code == 400
        assert "Username already taken" in exc_info.value.detail


class TestLogin:
    def test_login_success(
        self,
        auth_service: AuthService,
        repo: InMemoryAuthRepository,
        signup_payload: UserSignupBase,
    ) -> None:
        user = auth_service.register_user(signup_payload, repo=repo)
        result = auth_service.login(
            email=user.email, password=signup_payload.password, repo=repo
        )
        assert isinstance(result, AuthResult)
        assert result.user.email == user.email
        assert result.tokens.access_token

    def test_login_wrong_password_fails(
        self,
        auth_service: AuthService,
        repo: InMemoryAuthRepository,
        signup_payload: UserSignupBase,
    ) -> None:
        user = auth_service.register_user(signup_payload, repo=repo)
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(
                email=user.email, password="WrongPassword123!", repo=repo
            )
        assert exc_info.value.status_code == 401

    def test_login_nonexistent_user_fails(
        self, auth_service: AuthService, repo: InMemoryAuthRepository
    ) -> None:
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(
                email="nonexistent@example.com", password="AnyPassword123!", repo=repo
            )
        assert exc_info.value.status_code == 401


class TestLoginLockout:
    def test_lockout_after_max_attempts(
        self, repo: InMemoryAuthRepository, signup_payload: UserSignupBase
    ) -> None:
        reset_lockout_service(
            LockoutConfig(
                max_attempts=3, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        auth_service = AuthService(lockout_service=get_lockout_service())
        user = auth_service.register_user(signup_payload, repo=repo)

        for _ in range(2):
            with pytest.raises(HTTPException) as exc_info:
                auth_service.login(email=user.email, password="wrong", repo=repo)
            assert exc_info.value.status_code == 401

        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(email=user.email, password="wrong", repo=repo)
        assert exc_info.value.status_code == 429
        assert "Account locked" in exc_info.value.detail

    def test_locked_account_rejects_valid_password(
        self, repo: InMemoryAuthRepository, signup_payload: UserSignupBase
    ) -> None:
        reset_lockout_service(
            LockoutConfig(
                max_attempts=2, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        auth_service = AuthService(lockout_service=get_lockout_service())
        user = auth_service.register_user(signup_payload, repo=repo)

        for _ in range(2):
            try:
                auth_service.login(email=user.email, password="wrong", repo=repo)
            except HTTPException:
                pass

        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(
                email=user.email, password=signup_payload.password, repo=repo
            )
        assert exc_info.value.status_code == 429


class TestAuthUser:
    def test_auth_user_public_dict_excludes_password(self) -> None:
        user = AuthUser(
            id="user_123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            company_name="Test Co",
            hashed_password="$2b$12$hashed...",
            created_at=datetime.now(UTC),
            is_active=True,
        )
        public = user.public_dict
        assert "hashed_password" not in public
        assert public["email"] == "test@example.com"


class TestInMemoryAuthRepository:
    def test_get_by_email_returns_none_when_empty(
        self, repo: InMemoryAuthRepository
    ) -> None:
        result = repo.get_by_email("any@example.com")
        assert result is None

    def test_create_and_retrieve_by_email(self, repo: InMemoryAuthRepository) -> None:
        payload = UserSignupBase(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="SecurePass123!",
            company_name=None,
        )
        created = repo.create_user(payload, hashed_password="hashed")
        retrieved = repo.get_by_email("test@example.com")
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_users_returns_all(self, repo: InMemoryAuthRepository) -> None:
        for i in range(3):
            payload = UserSignupBase(
                email=f"user{i}@example.com",
                username=f"user{i}",
                full_name=f"User {i}",
                password="SecurePass123!",
                company_name=None,
            )
            repo.create_user(payload, hashed_password="hashed")
        users = list(repo.list_users())
        assert len(users) == 3


class TestSignoffSnapshot:
    def test_approved_signoff_is_approved(
        self, approved_signoff: SignoffSnapshot
    ) -> None:
        assert approved_signoff.is_approved() is True

    def test_pending_signoff_is_not_approved(
        self, pending_signoff: SignoffSnapshot
    ) -> None:
        assert pending_signoff.is_approved() is False


class TestPolicyContext:
    def test_has_approved_signoff_with_approved(
        self, approved_signoff: SignoffSnapshot
    ) -> None:
        context = PolicyContext(role=WorkspaceRole.DEVELOPER, signoff=approved_signoff)
        assert context.has_approved_signoff is True

    def test_has_approved_signoff_with_none(self) -> None:
        context = PolicyContext(role=WorkspaceRole.DEVELOPER, signoff=None)
        assert context.has_approved_signoff is False


class TestRequiresSignoff:
    def test_developer_requires_signoff(
        self, approved_signoff: SignoffSnapshot
    ) -> None:
        context = PolicyContext(role=WorkspaceRole.DEVELOPER, signoff=approved_signoff)
        assert requires_signoff(context) is True

    def test_architect_does_not_require_signoff(
        self, approved_signoff: SignoffSnapshot
    ) -> None:
        context = PolicyContext(role=WorkspaceRole.ARCHITECT, signoff=approved_signoff)
        assert requires_signoff(context) is False


class TestCanExportPermitReady:
    def test_agency_cannot_export(self, approved_signoff: SignoffSnapshot) -> None:
        context = PolicyContext(role=WorkspaceRole.AGENCY, signoff=approved_signoff)
        assert can_export_permit_ready(context) is False

    def test_developer_can_export_with_approved_signoff(
        self, approved_signoff: SignoffSnapshot
    ) -> None:
        context = PolicyContext(role=WorkspaceRole.DEVELOPER, signoff=approved_signoff)
        assert can_export_permit_ready(context) is True

    def test_developer_cannot_export_without_signoff(self) -> None:
        context = PolicyContext(role=WorkspaceRole.DEVELOPER, signoff=None)
        assert can_export_permit_ready(context) is False


class TestCanInviteArchitect:
    def test_developer_can_invite(self, approved_signoff: SignoffSnapshot) -> None:
        context = PolicyContext(role=WorkspaceRole.DEVELOPER, signoff=approved_signoff)
        assert can_invite_architect(context) is True

    def test_agency_cannot_invite(self) -> None:
        context = PolicyContext(role=WorkspaceRole.AGENCY, signoff=None)
        assert can_invite_architect(context) is False


class TestWatermarkPolicies:
    def test_agency_always_has_watermark(
        self, approved_signoff: SignoffSnapshot
    ) -> None:
        context = PolicyContext(role=WorkspaceRole.AGENCY, signoff=approved_signoff)
        assert watermark_forced(context) is True
        assert watermark_text(context) != ""

    def test_approved_signoff_no_watermark_for_developer(
        self, approved_signoff: SignoffSnapshot
    ) -> None:
        context = PolicyContext(role=WorkspaceRole.DEVELOPER, signoff=approved_signoff)
        assert watermark_forced(context) is False
        assert watermark_text(context) == ""
