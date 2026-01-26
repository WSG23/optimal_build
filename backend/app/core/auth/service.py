"""Unified authentication and authorization utilities.

All auth flows (token handling, user registration/login, and policy checks)
live here to avoid the previous split across multiple modules.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Iterable, Literal, Optional, Protocol

from backend._compat.datetime import UTC, utcnow
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import settings
from app.schemas.user import UserSignupBase
from app.services.account_lockout import AccountLockoutService, get_lockout_service
from app.utils.logging import get_logger, log_event
from app.utils.security import hash_password, verify_password

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Token models and helpers

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


# Pydantic BaseModel subclasses trigger mypy misc errors due to metaclass magic
class TokenData(BaseModel):  # type: ignore[misc]  # Pydantic metaclass
    """Token payload data."""

    email: str
    username: str
    user_id: str


class TokenResponse(BaseModel):  # type: ignore[misc]  # Pydantic metaclass
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def _secret_key() -> str:
    """Return the configured JWT secret key.

    The SECRET_KEY is validated at startup in config.py, so this should
    never fail in a properly configured environment.
    """
    if not settings.SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not configured. This should have been caught at startup."
        )
    return str(settings.SECRET_KEY)


def create_access_token(data: dict[str, Any]) -> str:
    """Create a JWT access token."""

    to_encode = data.copy()
    expire = utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, _secret_key(), algorithm="HS256")


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token."""

    to_encode = data.copy()
    expire = utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, _secret_key(), algorithm="HS256")


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Verify and decode a JWT token."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, _secret_key(), algorithms=["HS256"])
        if payload.get("type") != token_type:
            raise credentials_exception

        email = payload.get("email")
        username = payload.get("username")
        user_id = payload.get("user_id")

        if email is None or username is None or user_id is None:
            raise credentials_exception

        return TokenData(email=str(email), username=str(username), user_id=str(user_id))
    except JWTError as exc:  # pragma: no cover - passthrough
        raise credentials_exception from exc


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


# ---------------------------------------------------------------------------
# User storage


class UserORMBase(DeclarativeBase):  # type: ignore[misc]
    """Base class for ORM models in the auth module."""

    pass


class UserRecord(UserORMBase):
    """SQLAlchemy user record used by the unified auth service."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex}")
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    is_active = Column(Boolean, default=True)


@dataclass(slots=True)
class AuthUser:
    """Internal representation of a user participating in auth flows."""

    id: str
    email: str
    username: str
    full_name: str
    company_name: str | None
    hashed_password: str
    created_at: datetime
    is_active: bool = True

    @property
    def public_dict(self) -> dict[str, Any]:
        """Return a dictionary safe for API responses."""

        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "company_name": self.company_name,
            "created_at": self.created_at,
            "is_active": self.is_active,
        }


class AuthRepository(Protocol):
    """Persistence contract for auth operations."""

    def get_by_email(self, email: str) -> AuthUser | None: ...

    def get_by_username(self, username: str) -> AuthUser | None: ...

    def create_user(
        self, payload: UserSignupBase, hashed_password: str
    ) -> AuthUser: ...

    def list_users(self) -> Iterable[AuthUser]: ...


class InMemoryAuthRepository(AuthRepository):
    """Lightweight in-memory repository for tests and dev sandboxes."""

    def __init__(self) -> None:
        self._users: dict[str, AuthUser] = {}

    def get_by_email(self, email: str) -> AuthUser | None:
        return self._users.get(email)

    def get_by_username(self, username: str) -> AuthUser | None:
        return next((u for u in self._users.values() if u.username == username), None)

    def create_user(self, payload: UserSignupBase, hashed_password: str) -> AuthUser:
        identifier = f"user_{len(self._users) + 1}"
        user = AuthUser(
            id=identifier,
            email=payload.email,
            username=payload.username,
            full_name=payload.full_name,
            company_name=payload.company_name,
            hashed_password=hashed_password,
            created_at=utcnow(),
            is_active=True,
        )
        self._users[payload.email] = user
        return user

    def list_users(self) -> Iterable[AuthUser]:
        return list(self._users.values())


class SqlAlchemyAuthRepository(AuthRepository):
    """Repository backed by SQLAlchemy sessions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> AuthUser | None:
        record = (
            self.session.query(UserRecord).filter(UserRecord.email == email).first()
        )
        return self._to_user(record)

    def get_by_username(self, username: str) -> AuthUser | None:
        record = (
            self.session.query(UserRecord)
            .filter(UserRecord.username == username)
            .first()
        )
        return self._to_user(record)

    def create_user(self, payload: UserSignupBase, hashed_password: str) -> AuthUser:
        record = UserRecord(
            email=payload.email,
            username=payload.username,
            full_name=payload.full_name,
            company_name=payload.company_name,
            hashed_password=hashed_password,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        # record is guaranteed to exist after refresh, use non-None overload
        return self._to_user_required(record)

    def list_users(self) -> Iterable[AuthUser]:
        records = self.session.query(UserRecord).all()
        return [self._to_user_required(record) for record in records if record]

    @staticmethod
    def _to_user(record: UserRecord | None) -> AuthUser | None:
        if record is None:
            return None
        return SqlAlchemyAuthRepository._to_user_required(record)

    @staticmethod
    def _to_user_required(record: UserRecord) -> AuthUser:
        return AuthUser(
            id=str(record.id),
            email=str(record.email),
            username=str(record.username),
            full_name=str(record.full_name),
            company_name=str(record.company_name) if record.company_name else None,
            hashed_password=str(record.hashed_password),
            created_at=record.created_at,
            is_active=bool(record.is_active),
        )


# ---------------------------------------------------------------------------
# Auth service orchestration


@dataclass(slots=True)
class AuthResult:
    """Return value for a successful authentication attempt."""

    user: AuthUser
    tokens: TokenResponse


class AuthService:
    """High-level orchestration for authentication flows."""

    def __init__(self, lockout_service: AccountLockoutService | None = None) -> None:
        self.lockout_service = lockout_service or get_lockout_service()

    def register_user(
        self, user_data: UserSignupBase, repo: AuthRepository
    ) -> AuthUser:
        """Create a new user after uniqueness validation."""

        if repo.get_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        if repo.get_by_username(user_data.username):
            raise HTTPException(status_code=400, detail="Username already taken")

        hashed = hash_password(user_data.password)
        user = repo.create_user(user_data, hashed_password=hashed)
        log_event(logger, "auth_user_registered", email=user.email)
        return user

    def login(
        self,
        *,
        email: str,
        password: str,
        repo: AuthRepository,
        lockout_service: AccountLockoutService | None = None,
    ) -> AuthResult:
        """Authenticate a user and issue JWT tokens."""

        lockout = lockout_service or self.lockout_service
        if lockout.is_locked(email):
            remaining = lockout.get_lockout_remaining_seconds(email)
            raise HTTPException(
                status_code=429,
                detail=f"Account temporarily locked due to too many failed attempts. Try again in {remaining} seconds.",
            )

        user = repo.get_by_email(email)
        if user is None:
            lockout.record_failed_attempt(email)
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(password, user.hashed_password):
            is_locked = lockout.record_failed_attempt(email)
            if is_locked:
                remaining = lockout.get_lockout_remaining_seconds(email)
                raise HTTPException(
                    status_code=429,
                    detail=f"Account locked due to too many failed attempts. Try again in {remaining} seconds.",
                )
            raise HTTPException(status_code=401, detail="Invalid email or password")

        lockout.record_successful_login(email)
        tokens = create_tokens(user.public_dict)
        return AuthResult(user=user, tokens=tokens)

    @staticmethod
    def ensure_user_exists(email: str, repo: AuthRepository) -> AuthUser:
        """Resolve a user from storage or raise a 404."""

        user = repo.get_by_email(email)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user


# ---------------------------------------------------------------------------
# Authorization policy (formerly app.core.auth.policy)


class WorkspaceRole(str, Enum):
    """Workspace roles supported by policy checks."""

    AGENCY = "agency"
    DEVELOPER = "developer"
    ARCHITECT = "architect"


SignoffStatus = Literal["pending", "approved", "rejected"]


@dataclass(frozen=True)
class SignoffSnapshot:
    project_id: int
    overlay_version: str
    status: SignoffStatus
    architect_user_id: int | None
    signed_at: datetime | None

    def is_approved(self) -> bool:
        return self.status == "approved"


@dataclass(frozen=True)
class PolicyContext:
    role: WorkspaceRole
    signoff: SignoffSnapshot | None = None

    @property
    def has_approved_signoff(self) -> bool:
        if not self.signoff:
            return False
        return self.signoff.is_approved()


_WATERMARK_TEXT = "Marketing Feasibility Only – Not for Permit or Construction."


def requires_signoff(context: PolicyContext) -> bool:
    if context.role == WorkspaceRole.DEVELOPER:
        return True
    if context.role == WorkspaceRole.AGENCY:
        return True
    return False


def can_export_permit_ready(context: PolicyContext) -> bool:
    if context.role == WorkspaceRole.AGENCY:
        return False
    if context.role == WorkspaceRole.DEVELOPER:
        return context.has_approved_signoff
    if context.role == WorkspaceRole.ARCHITECT:
        return context.has_approved_signoff
    return False


def can_invite_architect(context: PolicyContext) -> bool:
    return context.role == WorkspaceRole.DEVELOPER


def watermark_forced(context: PolicyContext) -> bool:
    if context.role == WorkspaceRole.AGENCY:
        return True
    if not context.has_approved_signoff:
        return True
    return False


def watermark_text(context: PolicyContext) -> str:
    if watermark_forced(context):
        return _WATERMARK_TEXT
    return ""


__all__ = [
    "AuthResult",
    "AuthService",
    "AuthUser",
    "AuthRepository",
    "InMemoryAuthRepository",
    "SqlAlchemyAuthRepository",
    "TokenData",
    "TokenResponse",
    "create_tokens",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",
    "get_optional_user",
    "UserRecord",
    "UserORMBase",
    "WorkspaceRole",
    "PolicyContext",
    "SignoffSnapshot",
    "SignoffStatus",
    "requires_signoff",
    "can_export_permit_ready",
    "can_invite_architect",
    "watermark_forced",
    "watermark_text",
]
