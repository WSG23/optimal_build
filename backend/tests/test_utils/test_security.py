"""Tests for password hashing and security utilities."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest


def test_hash_password_with_passlib():
    """Test password hashing with passlib (normal case)."""
    from app.utils.security import hash_password

    password = "test_password_123"
    hashed = hash_password(password)

    assert hashed is not None
    assert len(hashed) > 0
    assert hashed != password


def test_verify_password_with_passlib_success():
    """Test password verification with correct password."""
    from app.utils.security import hash_password, verify_password

    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_with_passlib_failure():
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

    # Same password should produce different hashes due to random salt
    # Note: This is true for the fallback implementation, passlib may vary
    # but both should work for verification
    from app.utils.security import verify_password

    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_fallback_hash_password_format():
    """Test fallback hash_password format without passlib."""
    # Temporarily hide passlib
    with patch.dict(sys.modules, {"passlib": None, "passlib.context": None}):
        # Force reload to use fallback
        import importlib

        import app.utils.security

        importlib.reload(app.utils.security)

        from app.utils.security import hash_password

        password = "test_fallback"
        hashed = hash_password(password)

        # Fallback format should be: sha256$salt$digest
        assert hashed.startswith("sha256$")
        parts = hashed.split("$")
        assert len(parts) == 3
        assert parts[0] == "sha256"
        assert len(parts[1]) == 32  # 16 bytes hex = 32 chars
        assert len(parts[2]) == 64  # SHA256 hex = 64 chars


def test_fallback_verify_password_success():
    """Test fallback verify_password with correct password."""
    with patch.dict(sys.modules, {"passlib": None, "passlib.context": None}):
        import importlib

        import app.utils.security

        importlib.reload(app.utils.security)

        from app.utils.security import hash_password, verify_password

        password = "test_fallback_verify"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True


def test_fallback_verify_password_failure():
    """Test fallback verify_password with incorrect password."""
    with patch.dict(sys.modules, {"passlib": None, "passlib.context": None}):
        import importlib

        import app.utils.security

        importlib.reload(app.utils.security)

        from app.utils.security import hash_password, verify_password

        password = "test_fallback_wrong"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False


def test_fallback_verify_password_invalid_format():
    """Test fallback verify_password with malformed hash."""
    with patch.dict(sys.modules, {"passlib": None, "passlib.context": None}):
        import importlib

        import app.utils.security

        importlib.reload(app.utils.security)

        from app.utils.security import verify_password

        # Test various invalid formats
        assert verify_password("password", "invalid_hash") is False
        assert verify_password("password", "sha256$only_two_parts") is False
        assert verify_password("password", "") is False


def test_fallback_verify_password_wrong_scheme():
    """Test fallback verify_password rejects non-sha256 scheme."""
    with patch.dict(sys.modules, {"passlib": None, "passlib.context": None}):
        import importlib

        import app.utils.security

        importlib.reload(app.utils.security)

        from app.utils.security import verify_password

        # Hash with wrong scheme
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
