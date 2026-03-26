"""Minimal JWT codec for HS256 tokens.

The application only needs symmetric HMAC signing for internal auth tokens, so
keeping this implementation local avoids the deprecated python-jose dependency
and keeps startup predictable.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from backend._compat.datetime import UTC, utcnow

ALGORITHM = "HS256"


class JWTError(Exception):
    """Raised when a JWT cannot be decoded or verified."""


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except (ValueError, base64.binascii.Error) as exc:
        raise JWTError("Invalid token encoding") from exc


def _normalize_claim_value(value: Any) -> Any:
    if isinstance(value, datetime):
        normalized = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return int(normalized.astimezone(UTC).timestamp())
    if isinstance(value, Mapping):
        return {str(key): _normalize_claim_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize_claim_value(item) for item in value]
    return value


def encode(payload: Mapping[str, Any], key: str, algorithm: str = ALGORITHM) -> str:
    """Encode a JWT payload using HS256."""

    if algorithm != ALGORITHM:
        raise JWTError(f"Unsupported signing algorithm: {algorithm}")

    header = {"alg": ALGORITHM, "typ": "JWT"}
    body = _normalize_claim_value(dict(payload))
    signing_input = ".".join(
        (
            _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8")),
        )
    )
    signature = hmac.new(
        key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode(
    token: str,
    key: str,
    algorithms: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Decode and verify a JWT payload."""

    allowed_algorithms = list(algorithms or [ALGORITHM])
    if ALGORITHM not in allowed_algorithms:
        raise JWTError("Unsupported signing algorithm")

    try:
        header_segment, payload_segment, signature_segment = token.split(".", 2)
    except ValueError as exc:
        raise JWTError("Invalid token format") from exc

    expected_signature = hmac.new(
        key.encode("utf-8"),
        f"{header_segment}.{payload_segment}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    actual_signature = _b64url_decode(signature_segment)
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise JWTError("Signature verification failed")

    try:
        header = json.loads(_b64url_decode(header_segment))
        payload = json.loads(_b64url_decode(payload_segment))
    except json.JSONDecodeError as exc:
        raise JWTError("Invalid token payload") from exc

    if not isinstance(header, dict) or header.get("alg") != ALGORITHM:
        raise JWTError("Unsupported signing algorithm")
    if not isinstance(payload, dict):
        raise JWTError("Invalid token payload")

    exp = payload.get("exp")
    if exp is not None:
        try:
            exp_value = float(exp)
        except (TypeError, ValueError) as exc:
            raise JWTError("Invalid exp claim") from exc
        if utcnow().timestamp() >= exp_value:
            raise JWTError("Token has expired")

    return payload


class _JWTNamespace:
    @staticmethod
    def encode(payload: Mapping[str, Any], key: str, algorithm: str = ALGORITHM) -> str:
        return encode(payload, key, algorithm=algorithm)

    @staticmethod
    def decode(
        token: str,
        key: str,
        algorithms: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        return decode(token, key, algorithms=algorithms)


jwt = _JWTNamespace()

__all__ = ["ALGORITHM", "JWTError", "decode", "encode", "jwt"]
