"""Simple test API for users - learning exercise."""

from typing import Dict

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])

# Simple in-memory storage (will reset when server restarts)
fake_users_db: Dict[str, dict] = {}


class UserSignup(BaseModel):
    """What the user sends to register."""

    email: str
    username: str
    full_name: str
    password: str


class UserResponse(BaseModel):
    """What we send back (never send password!)."""

    email: str
    username: str
    full_name: str
    message: str


@router.get("/test")
def test_endpoint():
    """Super simple test to make sure API works."""
    return {"message": "Users API is working!", "status": "success"}


@router.post("/signup", response_model=UserResponse)
def signup(user: UserSignup):
    """Register a new user (fake - just stores in memory)."""

    # Check if user already exists
    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Store user (in real app, we'd hash the password!)
    fake_users_db[user.email] = {
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "password": user.password,  # Never do this in production!
    }

    return UserResponse(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        message="User registered successfully!",
    )


@router.get("/list")
def list_users():
    """List all registered users (for testing)."""
    # Remove passwords from response
    safe_users = []
    for _email, user_data in fake_users_db.items():
        safe_user = {k: v for k, v in user_data.items() if k != "password"}
        safe_users.append(safe_user)

    return {"users": safe_users, "total": len(safe_users)}
