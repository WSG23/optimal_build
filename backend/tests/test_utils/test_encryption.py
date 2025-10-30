"""Tests for encryption utilities."""

from __future__ import annotations

import base64

import pytest

from app.utils.encryption import TokenCipher


def test_token_cipher_encrypts_and_decrypts_string():
    """Test basic encryption and decryption roundtrip."""
    cipher = TokenCipher("test-secret-key")
    original = "sensitive data"

    encrypted = cipher.encrypt(original)
    assert encrypted is not None
    assert encrypted != original

    decrypted = cipher.decrypt(encrypted)
    assert decrypted == original


def test_token_cipher_handles_none_values():
    """Test that None values are handled correctly."""
    cipher = TokenCipher("test-secret")

    encrypted_none = cipher.encrypt(None)
    assert encrypted_none is None

    decrypted_none = cipher.decrypt(None)
    assert decrypted_none is None


def test_token_cipher_encrypts_different_values_differently():
    """Test that different plaintexts produce different ciphertexts."""
    cipher = TokenCipher("secret")

    encrypted1 = cipher.encrypt("value1")
    encrypted2 = cipher.encrypt("value2")

    assert encrypted1 != encrypted2


def test_token_cipher_decrypts_with_same_key():
    """Test that encryption/decryption works with the same key."""
    secret = "shared-secret"
    cipher1 = TokenCipher(secret)
    cipher2 = TokenCipher(secret)

    original = "confidential"
    encrypted = cipher1.encrypt(original)
    decrypted = cipher2.decrypt(encrypted)

    assert decrypted == original


def test_token_cipher_decrypt_invalid_token_raises_error():
    """Test that decrypting invalid data raises ValueError."""
    cipher = TokenCipher("secret")

    with pytest.raises(ValueError, match="Failed to decrypt"):
        cipher.decrypt("invalid-base64-!@#$%")


def test_token_cipher_normalizes_key_from_secret():
    """Test that secrets are normalized to valid Fernet keys."""
    # Any string should work as a secret
    cipher1 = TokenCipher("short")
    cipher2 = TokenCipher("a very long secret phrase that exceeds normal key length")

    # Both should work
    value = "test data"
    encrypted1 = cipher1.encrypt(value)
    encrypted2 = cipher2.encrypt(value)

    assert cipher1.decrypt(encrypted1) == value
    assert cipher2.decrypt(encrypted2) == value


def test_token_cipher_with_base64_encoded_key():
    """Test cipher with a pre-encoded base64 key."""
    # Generate a proper 32-byte key and encode it
    key_bytes = b"0" * 32
    base64_key = base64.urlsafe_b64encode(key_bytes).decode("utf-8")

    cipher = TokenCipher(base64_key)
    original = "test value"

    encrypted = cipher.encrypt(original)
    decrypted = cipher.decrypt(encrypted)

    assert decrypted == original


def test_token_cipher_handles_unicode_strings():
    """Test encryption/decryption of unicode strings."""
    cipher = TokenCipher("secret")

    unicode_text = "Hello 世界 🌍"
    encrypted = cipher.encrypt(unicode_text)
    decrypted = cipher.decrypt(encrypted)

    assert decrypted == unicode_text


def test_token_cipher_handles_empty_string():
    """Test encryption/decryption of empty strings."""
    cipher = TokenCipher("secret")

    encrypted = cipher.encrypt("")
    assert encrypted is not None

    decrypted = cipher.decrypt(encrypted)
    assert decrypted == ""


def test_token_cipher_same_value_encrypted_multiple_times():
    """Test that encrypting the same value multiple times may produce different ciphertexts."""
    cipher = TokenCipher("secret")
    value = "repeated value"

    # Note: Fernet includes a timestamp, so repeated encryptions may differ
    # But decryption should still work
    encrypted1 = cipher.encrypt(value)
    encrypted2 = cipher.encrypt(value)

    assert cipher.decrypt(encrypted1) == value
    assert cipher.decrypt(encrypted2) == value
