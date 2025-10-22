"""User management API endpoints (CRUD operations)."""

import uuid
from datetime import datetime
from typing import List, Optional

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

from app.core.auth.jwt import TokenData, get_current_user
from app.utils.db import session_dependency
from app.utils.security import hash_password
from backend._compat.datetime import utcnow

# Database setup (shared with auth.py)
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

router = APIRouter(prefix="/users", tags=["User Management"])


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


class UserUpdate(BaseModel):
    """User update model."""

    full_name: Optional[str] = None
    company_name: Optional[str] = None
    password: Optional[str] = None


class UserListResponse(BaseModel):
    """Response for user list endpoint."""

    users: List[UserResponse]
    total: int


# User Management Endpoints
@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all users with pagination.

    Args:
        skip: Number of users to skip (for pagination)
        limit: Maximum number of users to return
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserListResponse with list of users and total count

    Note:
        This endpoint requires authentication. In production, add admin-only access control.
    """
    users = db.query(UserDB).offset(skip).limit(limit).all()
    total = db.query(UserDB).count()

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users], total=total
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user by ID.

    Args:
        user_id: User ID to retrieve
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserResponse with user details

    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(UserDB).filter(UserDB.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user details.

    Args:
        user_id: User ID to update
        user_update: Fields to update
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserResponse with updated user details

    Raises:
        HTTPException: 403 if trying to update another user (non-admin)
        HTTPException: 404 if user not found

    Note:
        Currently users can only update their own profile. Add admin role check
        to allow admins to update any user.
    """
    # Get user from database
    user = db.query(UserDB).filter(UserDB.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is updating their own profile
    if user.id != current_user.user_id:
        # TODO: Add admin role check here
        raise HTTPException(
            status_code=403, detail="You can only update your own profile"
        )

    # Update fields if provided
    if user_update.full_name is not None:
        user.full_name = user_update.full_name

    if user_update.company_name is not None:
        user.company_name = user_update.company_name

    if user_update.password is not None:
        user.hashed_password = hash_password(user_update.password)

    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete user (soft delete by setting is_active=False).

    Args:
        user_id: User ID to delete
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 403 if trying to delete another user (non-admin)
        HTTPException: 404 if user not found

    Note:
        This performs a soft delete (sets is_active=False). Add admin role check
        to allow admins to delete any user.
    """
    # Get user from database
    user = db.query(UserDB).filter(UserDB.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is deleting their own account
    if user.id != current_user.user_id:
        # TODO: Add admin role check here
        raise HTTPException(
            status_code=403, detail="You can only delete your own account"
        )

    # Soft delete (set is_active=False)
    user.is_active = False
    db.commit()

    return {"message": "User account deactivated successfully", "user_id": user_id}


@router.get("/test/health")
def test_endpoint():
    """Test endpoint to verify user management API is working."""
    return {
        "status": "ok",
        "message": "User Management API is working!",
        "endpoints": [
            "GET /api/v1/users - List all users (paginated)",
            "GET /api/v1/users/{user_id} - Get user by ID",
            "PATCH /api/v1/users/{user_id} - Update user profile",
            "DELETE /api/v1/users/{user_id} - Deactivate user account",
        ],
    }
