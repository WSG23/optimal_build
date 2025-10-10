"""Shared user-facing schemas."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

try:  # pragma: no cover - optional email validation dependency
    import email_validator  # type: ignore  # noqa: F401

    from pydantic import EmailStr  # type: ignore
except ImportError:  # pragma: no cover - fallback when validator missing
    EmailStr = str  # type: ignore

from app.utils import validators as user_validators


class UserSignupBase(BaseModel):
    """Reusable user registration payload with validation."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return user_validators.validate_username(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return user_validators.validate_password(value)
