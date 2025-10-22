"""Authentication API endpoints (login, signup, token refresh)."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

try:  # pragma: no cover - optional dependency
    import email_validator  # type: ignore  # noqa: F401

    from pydantic import EmailStr  # type: ignore
except ImportError:  # pragma: no cover - fallback when validator missing
    EmailStr = str  # type: ignore

from app.core.auth.jwt import (
    TokenData,
    TokenResponse,
    create_access_token,
    create_tokens,
    get_current_user,
    verify_token,
)
from app.schemas.user import UserSignupBase
from app.utils.db import session_dependency
from app.utils.security import hash_password, verify_password
from backend._compat.datetime import utcnow

# Database setup (shared with users.py)
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Database Model (shared schema)
class UserDB(Base):
    """User model for database persistence."""

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


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response with new access token."""

    access_token: str
    token_type: str = "bearer"


# Authentication Endpoints
@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """Register a new user with database persistence.

    Args:
        user_data: User registration data (email, username, password, etc.)
        db: Database session

    Returns:
        UserResponse with created user details (without password)

    Raises:
        HTTPException: 400 if email or username already exists
    """
    # Check if email already exists
    if db.query(UserDB).filter(UserDB.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username already exists
    if db.query(UserDB).filter(UserDB.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create new user with hashed password
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
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password, returns JWT tokens.

    Args:
        credentials: Email and password
        db: Database session

    Returns:
        LoginResponse with user details and JWT tokens (access + refresh)

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Get user from database
    user = db.query(UserDB).filter(UserDB.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify user is active
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is inactive")

    # Create JWT tokens
    user_dict = {"id": user.id, "email": user.email, "username": user.username}
    tokens = create_tokens(user_dict)

    # Create response
    user_response = UserResponse.model_validate(user)

    return LoginResponse(message="Login successful", user=user_response, tokens=tokens)


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using a valid refresh token.

    This endpoint allows clients to obtain a new access token without
    requiring the user to log in again, as long as their refresh token
    is still valid.

    Args:
        request: Contains the refresh token
        db: Database session

    Returns:
        RefreshTokenResponse with new access token

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    try:
        # Verify the refresh token
        token_data = verify_token(request.refresh_token, token_type="refresh")

        # Verify user still exists in database
        user = db.query(UserDB).filter(UserDB.email == token_data.email).first()

        if not user:
            raise HTTPException(status_code=401, detail="User no longer exists")

        # Verify user is still active
        if not user.is_active:
            raise HTTPException(status_code=401, detail="User account is inactive")

        # Create new access token with current user data
        new_access_token = create_access_token(
            {
                "email": user.email,
                "username": user.username,
                "user_id": user.id,
            }
        )

        return RefreshTokenResponse(access_token=new_access_token)

    except HTTPException:
        # Re-raise HTTP exceptions (from verify_token or our checks)
        raise
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=401, detail="Could not validate refresh token"
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current user info from JWT token.

    Args:
        current_user: Token data extracted from JWT
        db: Database session

    Returns:
        UserResponse with current user details

    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(UserDB).filter(UserDB.email == current_user.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)


@router.get("/test")
def test_endpoint():
    """Test endpoint to verify authentication API is working."""
    return {
        "status": "ok",
        "message": "Authentication API is working!",
        "endpoints": [
            "POST /api/v1/auth/signup - Register new user",
            "POST /api/v1/auth/login - Login and get tokens",
            "POST /api/v1/auth/refresh - Refresh access token",
            "GET /api/v1/auth/me - Get current user info",
        ],
    }
