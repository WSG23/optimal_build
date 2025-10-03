"""Password hashing helpers shared across user APIs."""

from __future__ import annotations

import hashlib
import hmac
import secrets

try:  # pragma: no cover - prefer passlib when available
    from passlib.context import CryptContext
except ModuleNotFoundError:  # pragma: no cover - fallback implementation
    CryptContext = None  # type: ignore[assignment]


if CryptContext is not None:
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

    def hash_password(password: str) -> str:
        """Hash a password for storing using passlib."""

        return pwd_context.hash(password)

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash using passlib."""

        return pwd_context.verify(plain_password, hashed_password)

else:

    def hash_password(password: str) -> str:
        """Fallback password hashing using salted SHA256."""

        salt = secrets.token_hex(16)
        digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return f"sha256${salt}${digest}"

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Fallback verification matching the salted SHA256 format."""

        try:
            scheme, salt, digest = hashed_password.split("$", 2)
        except ValueError:
            return False
        if scheme != "sha256":
            return False
        computed = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
        return hmac.compare_digest(computed, digest)
