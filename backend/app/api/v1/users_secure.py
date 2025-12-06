"""Secure user API with validation and password hashing."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

try:  # pragma: no cover - optional dependency
    import email_validator  # type: ignore  # noqa: F401
    from pydantic import EmailStr  # type: ignore
except ImportError:  # pragma: no cover - fallback when validator missing
    EmailStr = str  # type: ignore

from app.core.auth import (
    AuthService,
    AuthUser,
    InMemoryAuthRepository,
    TokenData,
    TokenResponse,
    get_current_user,
)
from app.schemas.user import UserSignupBase
from app.services.account_lockout import get_lockout_service

router = APIRouter(prefix="/secure-users", tags=["Secure Users"])

auth_service = AuthService(lockout_service=get_lockout_service())
memory_repo = InMemoryAuthRepository()


class UserSignup(UserSignupBase):
    """User registration with validation."""

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Full name cannot be just whitespace."""
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()


class UserLogin(BaseModel):
    """User login credentials."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Safe user response without password."""

    id: str
    email: str
    username: str
    full_name: str
    company_name: Optional[str]
    created_at: str
    is_active: bool

    @classmethod
    def from_auth_user(cls, user: AuthUser) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            company_name=user.company_name,
            created_at=user.created_at.isoformat(),
            is_active=user.is_active,
        )


class LoginResponse(BaseModel):
    """Login response with JWT tokens."""

    message: str
    user: UserResponse
    tokens: TokenResponse


@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserSignup) -> UserResponse:
    """Register a new user with validation and password hashing."""

    user = auth_service.register_user(user_data, repo=memory_repo)
    return UserResponse.from_auth_user(user)


@router.post("/login", response_model=LoginResponse)
def login(credentials: UserLogin) -> LoginResponse:
    """Login with email and password, returns JWT tokens."""

    lockout_service = get_lockout_service()
    result = auth_service.login(
        email=credentials.email,
        password=credentials.password,
        repo=memory_repo,
        lockout_service=lockout_service,
    )
    return LoginResponse(
        message="Login successful",
        user=UserResponse.from_auth_user(result.user),
        tokens=result.tokens,
    )


@router.get("/test")
def test() -> Dict[str, Any]:
    """Test endpoint to verify API is working."""
    return {
        "status": "ok",
        "message": "Secure Users API is working!",
        "features": [
            "Email validation",
            "Password requirements (8+ chars, uppercase, lowercase, number)",
            "Password hashing with bcrypt",
            "Username validation",
            "Login endpoint",
        ],
    }


@router.get("/list")
def list_users() -> Dict[str, Any]:
    """List all users (for testing - remove in production!)."""
    safe_users = [
        UserResponse.from_auth_user(user) for user in memory_repo.list_users()
    ]
    return {"users": safe_users, "total": len(safe_users)}


@router.get("/me")
async def get_me(current_user: TokenData = Depends(get_current_user)) -> UserResponse:
    """Get current user info from JWT token."""

    user = auth_service.ensure_user_exists(current_user.email, repo=memory_repo)
    return UserResponse.from_auth_user(user)
