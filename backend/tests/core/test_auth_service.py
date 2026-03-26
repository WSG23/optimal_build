import hashlib

import pytest
from fastapi import HTTPException

from app.core.auth.service import AuthService, InMemoryAuthRepository
from app.schemas.user import UserSignupBase
from app.services.account_lockout import (
    LockoutConfig,
    get_lockout_service,
    reset_lockout_service,
)
from app.utils.security import hash_password


def _signup_payload(
    email: str = "user@example.com", username: str = "user"
) -> UserSignupBase:
    return UserSignupBase(
        email=email,
        username=username,
        full_name="Test User",
        password="Str0ngPass!",
        company_name=None,
    )


def test_register_and_login_success() -> None:
    reset_lockout_service()
    repo = InMemoryAuthRepository()
    service = AuthService(lockout_service=get_lockout_service())

    user = service.register_user(_signup_payload(), repo=repo)
    result = service.login(email=user.email, password="Str0ngPass!", repo=repo)

    assert result.user.email == user.email
    assert result.tokens.access_token
    assert result.tokens.refresh_token


def test_register_duplicate_email_raises() -> None:
    reset_lockout_service()
    repo = InMemoryAuthRepository()
    service = AuthService(lockout_service=get_lockout_service())

    service.register_user(_signup_payload(), repo=repo)
    try:
        service.register_user(_signup_payload(), repo=repo)
    except HTTPException as exc:
        assert exc.status_code == 400
    else:  # pragma: no cover - fail fast if no exception
        pytest.fail("Expected duplicate email to raise HTTPException")


def test_lockout_enforced_after_failed_attempts() -> None:
    reset_lockout_service(
        LockoutConfig(
            max_attempts=2, lockout_duration_seconds=30, attempt_window_seconds=60
        )
    )
    repo = InMemoryAuthRepository()
    service = AuthService(lockout_service=get_lockout_service())
    user = service.register_user(_signup_payload(), repo=repo)

    try:
        service.login(email=user.email, password="wrong-pass", repo=repo)
    except HTTPException as exc:
        assert exc.status_code == 401

    try:
        service.login(email=user.email, password="wrong-pass", repo=repo)
    except HTTPException as exc:
        assert exc.status_code == 429
    else:  # pragma: no cover - fail if no lockout
        pytest.fail("Expected account to be locked after repeated failures")


def test_login_rehashes_legacy_password_hashes() -> None:
    reset_lockout_service()
    repo = InMemoryAuthRepository()
    service = AuthService(lockout_service=get_lockout_service())
    salt = "legacy-salt"
    user = repo.create_user(
        _signup_payload(),
        hashed_password="sha256$"
        f"{salt}$"
        f"{hashlib.sha256((salt + 'Str0ngPass!').encode('utf-8')).hexdigest()}",
    )

    result = service.login(email=user.email, password="Str0ngPass!", repo=repo)

    assert result.user.hashed_password.startswith("pbkdf2_sha256$")
    assert repo.get_by_email(user.email) == result.user
    assert repo.get_by_email(user.email).hashed_password != user.hashed_password


def test_login_rehashes_low_iteration_pbkdf2_hashes() -> None:
    reset_lockout_service()
    repo = InMemoryAuthRepository()
    service = AuthService(lockout_service=get_lockout_service())
    _, _, salt_hex, _ = hash_password("Str0ngPass!").split("$", 3)
    legacy_pbkdf2 = (
        "pbkdf2_sha256$1000$"
        + salt_hex
        + "$"
        + hashlib.pbkdf2_hmac(
            "sha256",
            b"Str0ngPass!",
            bytes.fromhex(salt_hex),
            1000,
        ).hex()
    )

    user = repo.create_user(_signup_payload(), hashed_password=legacy_pbkdf2)
    result = service.login(email=user.email, password="Str0ngPass!", repo=repo)

    assert result.user.hashed_password.startswith("pbkdf2_sha256$310000$")
    assert result.user.hashed_password != legacy_pbkdf2
