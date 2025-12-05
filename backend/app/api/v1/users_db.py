"""User API with real database support using SQLAlchemy."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sqlalchemy import Boolean, Column, DateTime, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

try:  # pragma: no cover - optional dependency
    import email_validator  # type: ignore  # noqa: F401
    from pydantic import EmailStr  # type: ignore
except ImportError:  # pragma: no cover - fallback when validator missing
    EmailStr = str  # type: ignore

from backend._compat.datetime import utcnow

from app.core.jwt_auth import TokenData, TokenResponse, create_tokens, get_current_user
from app.schemas.user import UserSignupBase
from app.utils.db import session_dependency
from app.utils.security import hash_password, verify_password

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

router = APIRouter(prefix="/users-db", tags=["Database Users"])


# Database Model
class UserDB(Base):
    __tablename__ = "users"

    id = Column(
        String, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:8]}"
    )
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    is_active = Column(Boolean, default=True)


# Create tables
Base.metadata.create_all(bind=engine)


# Dependency to get DB session
get_db = session_dependency(SessionLocal)


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

    # Check if email already exists
    if db.query(UserDB).filter(UserDB.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username already exists
    if db.query(UserDB).filter(UserDB.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create new user
    db_user = UserDB(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        company_name=user_data.company_name,
        hashed_password=hash_password(user_data.password),
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse.model_validate(db_user)


@router.post("/login", response_model=LoginResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)) -> LoginResponse:
    """Login with email and password, returns JWT tokens."""

    # Get user from database
    user = db.query(UserDB).filter(UserDB.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create JWT tokens
    user_dict = {"id": user.id, "email": user.email, "username": user.username}
    tokens = create_tokens(user_dict)

    # Create response
    user_response = UserResponse.model_validate(user)

    return LoginResponse(message="Login successful", user=user_response, tokens=tokens)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserResponse:
    """Get current user info from JWT token."""
    user = db.query(UserDB).filter(UserDB.email == current_user.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)


@router.get("/list")
def list_users(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """List all users (for testing - remove in production!)."""
    users = db.query(UserDB).all()
    return {
        "users": [UserResponse.model_validate(u) for u in users],
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
