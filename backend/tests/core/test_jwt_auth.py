from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core import jwt_auth


def _token_payload() -> dict[str, str]:
    return {"email": "user@example.com", "username": "demo", "user_id": "123"}


def test_create_and_verify_access_token_round_trip():
    token = jwt_auth.create_access_token(_token_payload())
    data = jwt_auth.verify_token(token, token_type="access")
    assert data.email == "user@example.com"
    assert data.username == "demo"


def test_verify_token_rejects_mismatched_type():
    refresh = jwt_auth.create_refresh_token(_token_payload())
    with pytest.raises(HTTPException):
        jwt_auth.verify_token(refresh, token_type="access")


def test_verify_token_rejects_tampered_payload():
    with pytest.raises(HTTPException):
        jwt_auth.verify_token("invalid-token", token_type="access")


@pytest.mark.asyncio
async def test_get_optional_user_handles_credentials_and_missing():
    assert await jwt_auth.get_optional_user(None) is None
    token = jwt_auth.create_access_token(_token_payload())
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = await jwt_auth.get_optional_user(credentials)
    assert user.email == "user@example.com"


def test_create_tokens_returns_both_token_types():
    response = jwt_auth.create_tokens(
        {"email": "user@example.com", "username": "demo", "id": "42"}
    )
    assert response.token_type == "bearer"
    assert jwt_auth.verify_token(response.access_token).user_id == "42"
