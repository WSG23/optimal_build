"""User API with real database support using SQLAlchemy."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from passlib.context import CryptContext
from datetime import datetime
import re
from app.core.jwt_auth import create_tokens, TokenResponse, get_current_user, TokenData
import uuid

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

router = APIRouter(prefix="/users-db", tags=["Database Users"])


# Database Model
class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:8]}")
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


# Create tables
Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models
class UserSignup(BaseModel):
    """User registration with validation."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Username must be alphanumeric with underscores only."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Password must have at least 1 uppercase, 1 lowercase, 1 number."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v


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


# Helper functions
def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# API Endpoints
@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
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
        hashed_password=hash_password(user_data.password)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse.model_validate(db_user)


@router.post("/login", response_model=LoginResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password, returns JWT tokens."""

    # Get user from database
    user = db.query(UserDB).filter(UserDB.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create JWT tokens
    user_dict = {
        "id": user.id,
        "email": user.email,
        "username": user.username
    }
    tokens = create_tokens(user_dict)

    # Create response
    user_response = UserResponse.model_validate(user)

    return LoginResponse(
        message="Login successful",
        user=user_response,
        tokens=tokens
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user info from JWT token."""
    user = db.query(UserDB).filter(UserDB.email == current_user.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)


@router.get("/list")
def list_users(db: Session = Depends(get_db)):
    """List all users (for testing - remove in production!)."""
    users = db.query(UserDB).all()
    return {
        "users": [UserResponse.model_validate(u) for u in users],
        "total": len(users)
    }


@router.get("/test")
def test_endpoint():
    """Test endpoint to verify API is working."""
    return {
        "status": "ok",
        "message": "Database Users API is working!",
        "features": [
            "SQLite database persistence",
            "Email validation",
            "Password hashing",
            "JWT authentication",
            "User registration and login"
        ]
    }