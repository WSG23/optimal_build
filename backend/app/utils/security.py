"""Password hashing helpers shared across user APIs."""

from __future__ import annotations

import hashlib
import hmac
import secrets

try:  # pragma: no cover - prefer passlib when available
    from passlib.context import CryptContext

    _HAS_PASSLIB = True
except ModuleNotFoundError:  # pragma: no cover - fallback implementation
    _HAS_PASSLIB = False


if _HAS_PASSLIB:
    # Use bcrypt as primary scheme (more secure than sha256_crypt)
    # Keep sha256_crypt as deprecated for backward compatibility with existing hashes
    pwd_context = CryptContext(
        schemes=["bcrypt", "sha256_crypt"],
        default="bcrypt",
        deprecated=["sha256_crypt"],
    )

    def hash_password(password: str) -> str:
        """Hash a password for storing using passlib."""
        result: str = pwd_context.hash(password)
        return result

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash using passlib."""
        result: bool = pwd_context.verify(plain_password, hashed_password)
        return result

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
