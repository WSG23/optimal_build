"""Secure user API with validation and password hashing."""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

try:  # pragma: no cover - optional dependency
    import email_validator  # type: ignore  # noqa: F401
    from pydantic import EmailStr  # type: ignore
except ImportError:  # pragma: no cover - fallback when validator missing
    EmailStr = str  # type: ignore

from app.core.jwt_auth import TokenData, TokenResponse, create_tokens, get_current_user
from app.schemas.user import UserSignupBase
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/secure-users", tags=["Secure Users"])

# Temporary in-memory storage (will replace with database)
users_db: Dict[str, dict] = {}


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


class LoginResponse(BaseModel):
    """Login response with JWT tokens."""

    message: str
    user: UserResponse
    tokens: TokenResponse


@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserSignup):
    """Register a new user with validation and password hashing."""

    # Check if email already exists
    if user_data.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username already exists
    if any(u["username"] == user_data.username for u in users_db.values()):
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user with hashed password
    user_id = f"user_{len(users_db) + 1}"
    user = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "company_name": user_data.company_name,
        "hashed_password": hash_password(user_data.password),  # Hash the password!
        "created_at": datetime.utcnow().isoformat(),
        "is_active": True,
    }

    users_db[user_data.email] = user

    # Return user without password
    return UserResponse(**{k: v for k, v in user.items() if k != "hashed_password"})


@router.post("/login", response_model=LoginResponse)
def login(credentials: UserLogin):
    """Login with email and password, returns JWT tokens."""

    # Check if user exists
    if credentials.email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = users_db[credentials.email]

    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create JWT tokens
    tokens = create_tokens(user)

    # Create response
    user_response = UserResponse(
        **{k: v for k, v in user.items() if k != "hashed_password"}
    )

    return LoginResponse(message="Login successful", user=user_response, tokens=tokens)


@router.get("/test")
def test():
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
def list_users():
    """List all users (for testing - remove in production!)."""
    safe_users = []
    for email, user in users_db.items():
        safe_user = {k: v for k, v in user.items() if k != "hashed_password"}
        safe_users.append(safe_user)

    return {"users": safe_users, "total": len(safe_users)}


@router.get("/me")
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user info from JWT token."""
    if current_user.email not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    user = users_db[current_user.email]
    return UserResponse(**{k: v for k, v in user.items() if k != "hashed_password"})
