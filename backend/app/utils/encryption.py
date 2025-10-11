"""Helpers for symmetric encryption of sensitive values."""

from __future__ import annotations

import base64
import hashlib
from typing import Optional

try:
    from cryptography.fernet import Fernet as _Fernet
    from cryptography.fernet import InvalidToken as _InvalidToken

    Fernet = _Fernet
    InvalidToken = _InvalidToken
except ModuleNotFoundError:  # pragma: no cover - fallback for lightweight test envs

    class InvalidToken(Exception):  # type: ignore[no-redef]
        """Raised when decryption fails using the lightweight cipher stub."""

    class Fernet:  # type: ignore[no-redef]
        """Minimal stub that uses reversible base64 encoding in tests."""

        def __init__(self, key: bytes) -> None:
            self._key = key  # key retained for compatibility; unused

        def encrypt(self, value: bytes) -> bytes:
            return base64.urlsafe_b64encode(value)

        def decrypt(self, token: bytes) -> bytes:
            try:
                return base64.urlsafe_b64decode(token)
            except Exception as exc:  # pragma: no cover - defensive fallback
                raise InvalidToken(str(exc)) from exc


class TokenCipher:
    """Encrypt and decrypt short strings using Fernet."""

    def __init__(self, secret: str) -> None:
        self._fernet = Fernet(self._normalise_key(secret))

    def encrypt(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        token = self._fernet.encrypt(value.encode("utf-8"))
        return str(token.decode("utf-8"))

    def decrypt(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        try:
            plaintext = self._fernet.decrypt(value.encode("utf-8"))
        except InvalidToken as err:
            raise ValueError(
                "Failed to decrypt stored token; invalid cipher text"
            ) from err
        return str(plaintext.decode("utf-8"))

    @staticmethod
    def _normalise_key(secret: str) -> bytes:
        try:
            candidate = base64.urlsafe_b64decode(secret.encode("utf-8"))
            if len(candidate) == 32:
                return base64.urlsafe_b64encode(candidate)
        except Exception:
            pass
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)


__all__ = ["TokenCipher"]
