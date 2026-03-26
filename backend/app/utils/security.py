"""Password hashing helpers shared across user APIs."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

_bcrypt_module: Any = None

try:  # pragma: no cover - optional legacy verifier
    import bcrypt as _bcrypt
except ModuleNotFoundError:  # pragma: no cover - bcrypt is optional
    pass
else:  # pragma: no cover - imported only when bcrypt is installed
    _bcrypt_module = _bcrypt

PBKDF2_SCHEME = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 310_000
PBKDF2_SALT_BYTES = 16
LEGACY_SHA256_SCHEME = "sha256"
_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def hash_password(password: str) -> str:
    """Hash a password for storage using PBKDF2-HMAC-SHA256."""

    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"{PBKDF2_SCHEME}${PBKDF2_ITERATIONS}$" f"{salt.hex()}${digest.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against PBKDF2 and legacy hash formats."""

    if not hashed_password:
        return False

    if hashed_password.startswith(f"{PBKDF2_SCHEME}$"):
        return _verify_pbkdf2_password(plain_password, hashed_password)
    if hashed_password.startswith(f"{LEGACY_SHA256_SCHEME}$"):
        return _verify_legacy_sha256_password(plain_password, hashed_password)
    if hashed_password.startswith(_BCRYPT_PREFIXES):
        return _verify_legacy_bcrypt_password(plain_password, hashed_password)
    return False


def password_needs_rehash(hashed_password: str) -> bool:
    """Return ``True`` when a verified password should be upgraded in storage."""

    if not hashed_password:
        return False
    if hashed_password.startswith(f"{LEGACY_SHA256_SCHEME}$"):
        return True
    if hashed_password.startswith(_BCRYPT_PREFIXES):
        return True
    if not hashed_password.startswith(f"{PBKDF2_SCHEME}$"):
        return False
    iteration_count, salt_hex, digest_hex = _parse_pbkdf2_hash(hashed_password)
    if iteration_count is None or salt_hex is None or digest_hex is None:
        return False
    return iteration_count < PBKDF2_ITERATIONS


def _verify_pbkdf2_password(plain_password: str, hashed_password: str) -> bool:
    iteration_count, salt_hex, digest_hex = _parse_pbkdf2_hash(hashed_password)
    if iteration_count is None or salt_hex is None or digest_hex is None:
        return False
    salt = bytes.fromhex(salt_hex)
    expected_digest = bytes.fromhex(digest_hex)

    computed_digest = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        iteration_count,
    )
    return hmac.compare_digest(computed_digest, expected_digest)


def _verify_legacy_sha256_password(plain_password: str, hashed_password: str) -> bool:
    try:
        scheme, salt, digest = hashed_password.split("$", 2)
    except ValueError:
        return False
    if scheme != LEGACY_SHA256_SCHEME:
        return False
    computed = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
    return hmac.compare_digest(computed, digest)


def _verify_legacy_bcrypt_password(plain_password: str, hashed_password: str) -> bool:
    if _bcrypt_module is None:
        return False
    try:
        return bool(
            _bcrypt_module.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        )
    except ValueError:
        return False


def _parse_pbkdf2_hash(
    hashed_password: str,
) -> tuple[int | None, str | None, str | None]:
    try:
        scheme, iterations, salt_hex, digest_hex = hashed_password.split("$", 3)
    except ValueError:
        return None, None, None

    if scheme != PBKDF2_SCHEME:
        return None, None, None

    try:
        bytes.fromhex(salt_hex)
        bytes.fromhex(digest_hex)
        iteration_count = int(iterations)
    except ValueError:
        return None, None, None
    return iteration_count, salt_hex, digest_hex


__all__ = [
    "LEGACY_SHA256_SCHEME",
    "PBKDF2_ITERATIONS",
    "PBKDF2_SCHEME",
    "PBKDF2_SALT_BYTES",
    "hash_password",
    "password_needs_rehash",
    "verify_password",
]
