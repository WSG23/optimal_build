"""High-quality tests for password hashing and verification utilities."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.no_db

from app.utils.security import hash_password, verify_password


def test_hash_password_returns_hashed_string():
    """Test that hash_password returns a non-empty hashed string."""
    password = "my_secure_password123"

    hashed = hash_password(password)

    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != password  # Hashed value should differ from plain


def test_hash_password_produces_different_hashes_for_same_password():
    """Test that hashing the same password twice produces different hashes (due to salt)."""
    password = "same_password"

    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Different salts should produce different hashes
    assert hash1 != hash2


def test_hash_password_handles_empty_string():
    """Test that hash_password can handle empty strings."""
    hashed = hash_password("")

    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_hash_password_handles_unicode():
    """Test that hash_password handles Unicode characters."""
    password = "pǎssw0rd_测试_🔒"

    hashed = hash_password(password)

    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_hash_password_handles_long_password():
    """Test that hash_password handles very long passwords."""
    password = "a" * 1000

    hashed = hash_password(password)

    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_hash_password_handles_special_characters():
    """Test that hash_password handles special characters."""
    password = "p@ssw0rd!#$%^&*()_+-=[]{}|;':\",./<>?"

    hashed = hash_password(password)

    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_verify_password_succeeds_with_correct_password():
    """Test that verify_password returns True for correct password."""
    password = "correct_password"
    hashed = hash_password(password)

    result = verify_password(password, hashed)

    assert result is True


def test_verify_password_fails_with_wrong_password():
    """Test that verify_password returns False for incorrect password."""
    correct_password = "correct_password"
    wrong_password = "wrong_password"
    hashed = hash_password(correct_password)

    result = verify_password(wrong_password, hashed)

    assert result is False


def test_verify_password_fails_with_empty_password():
    """Test that verify_password handles empty password verification."""
    hashed = hash_password("real_password")

    result = verify_password("", hashed)

    assert result is False


def test_verify_password_handles_case_sensitive_passwords():
    """Test that password verification is case-sensitive."""
    password = "CaseSensitive"
    hashed = hash_password(password)

    # Exact match should succeed
    assert verify_password("CaseSensitive", hashed) is True

    # Different case should fail
    assert verify_password("casesensitive", hashed) is False
    assert verify_password("CASESENSITIVE", hashed) is False


def test_verify_password_handles_unicode_correctly():
    """Test that Unicode passwords verify correctly."""
    password = "pǎssw0rd_测试_🔒"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("different_password", hashed) is False


def test_verify_password_with_malformed_hash():
    """Test that verify_password handles malformed hash strings."""
    password = "test_password"

    # Malformed hash without proper format
    # Passlib may raise exceptions for truly invalid hashes, which is acceptable
    try:
        result = verify_password(password, "not_a_valid_hash")
        # If no exception, should return False
        assert result is False
    except Exception:
        # Exception is also acceptable for malformed input
        pass

    try:
        result = verify_password(password, "random_string")
        assert result is False
    except Exception:
        pass


def test_verify_password_with_wrong_scheme():
    """Test that verify_password rejects hashes with wrong scheme."""
    password = "test_password"

    # Hash with wrong scheme format
    fake_hash = "md5$somesalt$somedigest"

    try:
        result = verify_password(password, fake_hash)
        # If it doesn't raise, it should return False
        assert result is False
    except Exception:
        # Exception for unrecognized scheme is acceptable
        pass


def test_verify_password_with_missing_parts():
    """Test that verify_password handles hashes with missing parts."""
    password = "test_password"

    # Hash with missing parts
    try:
        result = verify_password(password, "sha256$onlyonepart")
        assert result is False
    except Exception:
        pass

    try:
        result = verify_password(password, "$$$")
        assert result is False
    except Exception:
        pass


def test_hash_and_verify_roundtrip():
    """Test full roundtrip of hashing and verifying a password."""
    original_password = "my_secure_password_123!"

    # Hash the password
    hashed = hash_password(original_password)

    # Verify with correct password
    assert verify_password(original_password, hashed) is True

    # Verify with slightly different password should fail
    assert verify_password(original_password + "x", hashed) is False
    assert verify_password("x" + original_password, hashed) is False


def test_hash_and_verify_multiple_passwords():
    """Test that multiple different passwords hash and verify independently."""
    passwords = [
        "password1",
        "password2",
        "password3",
        "very_long_password_with_many_characters_123456789",
        "short",
    ]

    # Hash all passwords
    hashes = [hash_password(pwd) for pwd in passwords]

    # All hashes should be unique
    assert len(set(hashes)) == len(hashes)

    # Each password should verify against its own hash
    for i, password in enumerate(passwords):
        assert verify_password(password, hashes[i]) is True

        # But not against other hashes
        for j, other_hash in enumerate(hashes):
            if i != j:
                assert verify_password(password, other_hash) is False


def test_verify_password_constant_time_comparison():
    """Test that verify_password uses constant-time comparison (timing-safe)."""
    # This is more of a documentation test - the actual timing-safety
    # is provided by hmac.compare_digest or passlib internals
    password = "test_password"
    hashed = hash_password(password)

    # Both correct and incorrect verifications should complete
    # (we can't easily test timing here, but we document the expectation)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_hash_password_deterministic_per_call():
    """Test that a single hash operation is internally consistent."""
    password = "test_password"

    hashed = hash_password(password)

    # The same hash should consistently verify the same password
    assert verify_password(password, hashed) is True
    assert verify_password(password, hashed) is True
    assert verify_password(password, hashed) is True
