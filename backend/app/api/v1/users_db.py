"""User API with real database support using SQLAlchemy."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

if TYPE_CHECKING:
    from pydantic import EmailStr as _EmailStr

    EmailStr = _EmailStr
else:
    try:  # pragma: no cover - optional dependency
        import email_validator  # noqa: F401

        from pydantic import EmailStr
    except ImportError:  # pragma: no cover - fallback when validator missing
        EmailStr = str  # type: ignore[misc]

from app.core.auth import (
    AuthService,
    AuthUser,
    SqlAlchemyAuthRepository,
    TokenData,
    TokenResponse,
    UserORMBase,
    get_current_user,
)
from app.schemas.user import UserSignupBase
from app.services.account_lockout import get_lockout_service
from app.utils.db import session_dependency

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure the shared user table exists
UserORMBase.metadata.create_all(bind=engine)

router = APIRouter(prefix="/users-db", tags=["Database Users"])

# Dependency to get DB session
get_db = session_dependency(SessionLocal)
auth_service = AuthService(lockout_service=get_lockout_service())


# Pydantic models
class UserSignup(UserSignupBase):
    """User registration with validation."""

    pass


class UserResponse(BaseModel):
    """Safe user response without password."""

    id: str
    email: str
    username: str
    full_name: str
    company_name: Optional[str]
    created_at: datetime
    is_active: bool

    @classmethod
    def from_auth_user(cls, user: AuthUser) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            company_name=user.company_name,
            created_at=user.created_at,
            is_active=user.is_active,
        )

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """User login credentials."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with JWT tokens."""

    message: str
    user: UserResponse
    tokens: TokenResponse


# API Endpoints
@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserSignup, db: Session = Depends(get_db)) -> UserResponse:
    """Register a new user with database persistence."""

    repo = SqlAlchemyAuthRepository(db)
    user = auth_service.register_user(user_data, repo=repo)
    return UserResponse.from_auth_user(user)


@router.post("/login", response_model=LoginResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)) -> LoginResponse:
    """Login with email and password, returns JWT tokens."""

    repo = SqlAlchemyAuthRepository(db)
    result = auth_service.login(
        email=credentials.email,
        password=credentials.password,
        repo=repo,
    )
    return LoginResponse(
        message="Login successful",
        user=UserResponse.from_auth_user(result.user),
        tokens=result.tokens,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserResponse:
    """Get current user info from JWT token."""

    repo = SqlAlchemyAuthRepository(db)
    user = auth_service.ensure_user_exists(current_user.email, repo=repo)
    return UserResponse.from_auth_user(user)


@router.get("/list")
def list_users(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """List all users (for testing - remove in production!)."""

    repo = SqlAlchemyAuthRepository(db)
    users = [UserResponse.from_auth_user(u) for u in repo.list_users()]
    return {
        "users": users,
        "total": len(users),
    }


@router.get("/test")
def test_endpoint() -> Dict[str, Any]:
    """Test endpoint to verify API is working."""
    return {
        "status": "ok",
        "message": "Database Users API is working!",
        "features": [
            "SQLite database persistence",
            "Email validation",
            "Password hashing",
            "JWT authentication",
            "User registration and login",
        ],
    }
