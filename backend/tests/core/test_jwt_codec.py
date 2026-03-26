from __future__ import annotations

from datetime import timedelta

import pytest
from backend._compat.datetime import utcnow

from app.core.jwt_codec import JWTError, jwt


def test_jwt_codec_round_trips_payload_and_expiry() -> None:
    payload = {
        "sub": "user-123",
        "exp": utcnow() + timedelta(minutes=5),
        "roles": ["viewer"],
    }

    token = jwt.encode(payload, "secret-key")
    decoded = jwt.decode(token, "secret-key", algorithms=["HS256"])

    assert decoded["sub"] == "user-123"
    assert decoded["roles"] == ["viewer"]
    assert decoded["exp"] > utcnow().timestamp()


def test_jwt_codec_rejects_invalid_signature() -> None:
    token = jwt.encode({"sub": "user-123"}, "secret-key")

    with pytest.raises(JWTError):
        jwt.decode(token, "wrong-secret", algorithms=["HS256"])


def test_jwt_codec_rejects_expired_tokens() -> None:
    token = jwt.encode(
        {"sub": "user-123", "exp": utcnow() - timedelta(minutes=5)},
        "secret-key",
    )

    with pytest.raises(JWTError):
        jwt.decode(token, "secret-key", algorithms=["HS256"])
