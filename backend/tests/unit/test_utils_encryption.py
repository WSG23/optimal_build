import base64
import importlib

import pytest

import builtins

import app.utils.encryption as encryption


@pytest.fixture(autouse=True)
def reload_encryption_module() -> None:
    importlib.reload(encryption)


@pytest.mark.no_db
class TestTokenCipher:
    def test_encrypt_decrypt_roundtrip(self) -> None:
        cipher = encryption.TokenCipher("top-secret-key")
        token = cipher.encrypt("payload")
        assert isinstance(token, str)
        assert cipher.decrypt(token) == "payload"

    def test_encrypt_decrypt_with_none(self) -> None:
        cipher = encryption.TokenCipher("another-secret")
        assert cipher.encrypt(None) is None
        assert cipher.decrypt(None) is None

    def test_normalise_base64_key_is_preserved(self) -> None:
        raw_key = b"z" * 32
        encoded_key = base64.urlsafe_b64encode(raw_key).decode("ascii")

        normalised = encryption.TokenCipher._normalise_key(encoded_key)
        assert base64.urlsafe_b64decode(normalised) == raw_key

        cipher = encryption.TokenCipher(encoded_key)
        roundtrip = cipher.decrypt(cipher.encrypt("value"))
        assert roundtrip == "value"

    def test_normalise_arbitrary_secret_produces_fernet_key(self) -> None:
        normalised = encryption.TokenCipher._normalise_key("short")
        decoded = base64.urlsafe_b64decode(normalised)
        assert len(decoded) == 32

    def test_decrypt_invalid_token_raises_value_error(self) -> None:
        cipher = encryption.TokenCipher("invalid-token-secret")
        with pytest.raises(ValueError):
            cipher.decrypt("not-a-valid-token")

    def test_fallback_cipher_used_when_cryptography_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        original_import = builtins.__import__

        def fake_import(name: str, *args: object, **kwargs: object):
            if name.startswith("cryptography"):
                raise ModuleNotFoundError("cryptography unavailable")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        module = importlib.reload(encryption)
        try:
            cipher = module.TokenCipher("fallback-secret")
            token = cipher.encrypt("hello")
            assert cipher.decrypt(token) == "hello"
        finally:
            importlib.reload(encryption)
