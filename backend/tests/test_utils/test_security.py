"""Tests for password hashing and security utilities."""

from __future__ import annotations

import hashlib

import pytest


def test_hash_password_uses_pbkdf2_format():
    """New password hashes should use the PBKDF2 format."""
    from app.utils.security import hash_password

    password = "test_password_123"
    hashed = hash_password(password)

    assert hashed is not None
    assert len(hashed) > 0
    assert hashed != password
    scheme, iterations, salt, digest = hashed.split("$", 3)
    assert scheme == "pbkdf2_sha256"
    assert int(iterations) > 0
    assert len(salt) == 32
    assert len(digest) == 64


def test_verify_password_success():
    """Test password verification with correct password."""
    from app.utils.security import hash_password, verify_password

    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_failure():
    """Test password verification with incorrect password."""
    from app.utils.security import hash_password, verify_password

    password = "test_password_123"
    wrong_password = "wrong_password"
    hashed = hash_password(password)

    assert verify_password(wrong_password, hashed) is False


def test_hash_and_verify_different_passwords():
    """Test that different passwords produce different hashes."""
    from app.utils.security import hash_password, verify_password

    password1 = "password_one"
    password2 = "password_two"

    hash1 = hash_password(password1)
    hash2 = hash_password(password2)

    # Different passwords should have different hashes
    assert hash1 != hash2

    # Each password should only verify against its own hash
    assert verify_password(password1, hash1) is True
    assert verify_password(password2, hash2) is True
    assert verify_password(password1, hash2) is False
    assert verify_password(password2, hash1) is False


def test_hash_password_produces_unique_salts():
    """Test that hashing the same password twice produces different hashes (due to salt)."""
    from app.utils.security import hash_password

    password = "same_password"

    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Same password should produce different hashes due to random salt.
    from app.utils.security import verify_password

    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
    assert hash1 != hash2


def test_verify_password_supports_legacy_sha256_hashes():
    """Legacy sha256 hashes should continue to verify after the PBKDF2 migration."""
    from app.utils.security import verify_password

    salt = "1234abcd5678ef901234abcd5678ef90"
    digest = hashlib.sha256((salt + "password").encode("utf-8")).hexdigest()
    legacy_hash = f"sha256${salt}${digest}"

    assert verify_password("password", legacy_hash) is True
    assert verify_password("wrong-password", legacy_hash) is False


def test_password_needs_rehash_for_legacy_hashes():
    """Legacy password schemes should be upgraded after successful login."""
    from app.utils.security import password_needs_rehash

    salt = "1234abcd5678ef901234abcd5678ef90"
    digest = hashlib.sha256((salt + "password").encode("utf-8")).hexdigest()

    assert password_needs_rehash(f"sha256${salt}${digest}") is True
    assert (
        password_needs_rehash(
            "$2b$12$abcdefghijklmnopqrstuuH2xD4Q6t2zY9d1A1m8tK9L5g6q7r8s"
        )
        is True
    )


def test_password_needs_rehash_for_old_pbkdf2_iterations():
    """PBKDF2 hashes below the current work factor should be rotated."""
    from app.utils.security import hash_password, password_needs_rehash

    assert password_needs_rehash(hash_password("password")) is False
    assert (
        password_needs_rehash(hash_password("password").replace("310000", "1000", 1))
        is True
    )


def test_verify_password_invalid_format():
    """Malformed hashes should fail verification cleanly."""
    from app.utils.security import verify_password

    assert verify_password("password", "invalid_hash") is False
    assert verify_password("password", "sha256$only_two_parts") is False
    assert verify_password("password", "") is False


def test_verify_password_wrong_scheme():
    """Unknown schemes should be rejected."""
    from app.utils.security import verify_password

    wrong_scheme_hash = "md5$somesalt$somedigest"
    assert verify_password("password", wrong_scheme_hash) is False


def test_empty_password_handling():
    """Test that empty passwords can be hashed and verified."""
    from app.utils.security import hash_password, verify_password

    empty_password = ""
    hashed = hash_password(empty_password)

    assert verify_password(empty_password, hashed) is True
    assert verify_password("not_empty", hashed) is False


def test_unicode_password_handling():
    """Test that unicode passwords are handled correctly."""
    from app.utils.security import hash_password, verify_password

    unicode_password = "пароль123测试🔒"
    hashed = hash_password(unicode_password)

    assert verify_password(unicode_password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_very_long_password():
    """Test that very long passwords work correctly."""
    from app.utils.security import hash_password, verify_password

    long_password = "a" * 10000
    hashed = hash_password(long_password)

    assert verify_password(long_password, hashed) is True
    assert verify_password("a" * 9999, hashed) is False


@pytest.mark.parametrize(
    "password",
    [
        "simple",
        "with spaces",
        "with\nnewlines\n",
        "with\ttabs",
        "special!@#$%^&*()",
        "quotes'and\"double",
    ],
)
def test_various_password_formats(password):
    """Test various password formats."""
    from app.utils.security import hash_password, verify_password

    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
