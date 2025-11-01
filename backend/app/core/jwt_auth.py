"""JWT Authentication utilities."""

import base64
import hashlib
import hmac
import json
import os
from datetime import timedelta
from typing import Any, Optional

from backend._compat.datetime import utcnow
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:  # pragma: no cover - optional dependency
    from jose import JWTError, jwt
except ModuleNotFoundError:  # pragma: no cover - lightweight fallback

    class JWTError(Exception):
        """Fallback JWT error used when python-jose is unavailable."""

    class _SimpleJWTModule:
        """Minimal JWT-compatible codec for test environments."""

        def encode(self, payload: dict[str, Any], key: str, algorithm: str = "HS256") -> str:
            message = json.dumps(payload, default=str, separators=(",", ":")).encode()
            signature = hmac.new(key.encode(), message, hashlib.sha256).digest()
            token = ".".join(
                _urlsafe_b64encode(part)
                for part in (message, signature, algorithm.encode())
            )
            return token

        def decode(
            self, token: str, key: str, algorithms: Optional[list[str]] = None
        ) -> dict[str, Any]:
            try:
                message_b64, signature_b64, algorithm_b64 = token.split(".")
                algorithm = _urlsafe_b64decode(algorithm_b64).decode()
                if algorithms is not None and algorithm not in algorithms:
                    raise ValueError("algorithm not allowed")

                message = _urlsafe_b64decode(message_b64)
                signature = _urlsafe_b64decode(signature_b64)
                expected = hmac.new(key.encode(), message, hashlib.sha256).digest()
                if not hmac.compare_digest(expected, signature):
                    raise ValueError("signature mismatch")

                return json.loads(message)
            except Exception as exc:  # pragma: no cover - defensive
                raise JWTError(str(exc)) from exc

    def _urlsafe_b64encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode().rstrip("=")

    def _urlsafe_b64decode(data: str) -> bytes:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)

    jwt = _SimpleJWTModule()  # type: ignore[assignment]

from pydantic import BaseModel

# Configuration - read SECRET_KEY from environment variable
SECRET_KEY = os.getenv(
    "SECRET_KEY", "fallback-secret-key-for-development-only-do-not-use-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Security scheme
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token payload data."""

    email: str
    username: str
    user_id: str


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def create_access_token(data: dict[str, Any]) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Verify and decode a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check token type
        if payload.get("type") != token_type:
            raise credentials_exception

        email: str = payload.get("email")
        username: str = payload.get("username")
        user_id: str = payload.get("user_id")

        if email is None or username is None or user_id is None:
            raise credentials_exception

        return TokenData(email=email, username=username, user_id=user_id)
    except JWTError as e:
        raise credentials_exception from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """Get current user from JWT token."""
    token = credentials.credentials
    return verify_token(token, token_type="access")


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[TokenData]:
    """Return authenticated user if a bearer token is provided, otherwise ``None``."""

    if credentials is None:
        return None
    return verify_token(credentials.credentials, token_type="access")


def create_tokens(user_data: dict[str, Any]) -> TokenResponse:
    """Create both access and refresh tokens."""
    token_data = {
        "email": user_data["email"],
        "username": user_data["username"],
        "user_id": user_data["id"],
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
