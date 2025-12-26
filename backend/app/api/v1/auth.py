"""Authentication API endpoints.

Provides endpoints for:
- Login/Logout
- Token refresh
- Session management
- Password reset (stubbed)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field

from app.core.auth.service import (
    AuthResult,
    AuthService,
    InMemoryAuthRepository,
    TokenResponse,
    create_tokens,
    get_current_user,
    security,
    verify_token,
)
from app.core.session import SessionInfo, get_session_manager
from app.schemas.user import UserSignupBase
from app.utils.client_ip import get_client_ip

if TYPE_CHECKING:
    from app.core.auth.service import TokenData


router = APIRouter(prefix="/auth", tags=["auth"])

# Use in-memory repository for now (can be swapped for database-backed)
_auth_repo = InMemoryAuthRepository()
_auth_service = AuthService()


# ============================================================================
# Request/Response Models
# ============================================================================


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")


class LogoutResponse(BaseModel):
    """Logout response schema."""

    message: str = "Successfully logged out"


class RefreshRequest(BaseModel):
    """Token refresh request schema."""

    refresh_token: str = Field(..., description="Refresh token")


class SessionListResponse(BaseModel):
    """List of active sessions."""

    sessions: list[SessionInfo]
    total: int


class RevokeSessionRequest(BaseModel):
    """Request to revoke a specific session."""

    session_id: str = Field(..., description="Session ID to revoke")


class LogoutAllResponse(BaseModel):
    """Response for logout from all devices."""

    message: str
    sessions_terminated: int


# ============================================================================
# Authentication Endpoints
# ============================================================================


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(user_data: UserSignupBase) -> dict:
    """Register a new user account."""
    user = _auth_service.register_user(user_data, _auth_repo)
    return {
        "message": "User registered successfully",
        "user": user.public_dict,
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get access tokens",
)
async def login(
    credentials: LoginRequest,
    request: Request,
    user_agent: str = Header(None),
) -> TokenResponse:
    """Authenticate user and return JWT tokens.

    Also creates a session record for multi-device tracking.
    """
    result: AuthResult = _auth_service.login(
        email=credentials.email,
        password=credentials.password,
        repo=_auth_repo,
    )

    # Create session for tracking
    session_manager = get_session_manager()
    session_id = str(uuid4())
    client_ip = get_client_ip(
        request, lambda r: r.client.host if r.client else "unknown"
    )

    session_manager.create_session(
        session_id=session_id,
        user_id=result.user.id,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    return result.tokens


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout current session",
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> LogoutResponse:
    """Logout by blacklisting the current access token.

    The token will be invalid for its remaining lifetime.
    """
    token = credentials.credentials
    session_manager = get_session_manager()
    session_manager.logout(token)

    return LogoutResponse()


@router.post(
    "/logout/all",
    response_model=LogoutAllResponse,
    summary="Logout from all devices",
)
async def logout_all(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: "TokenData" = Depends(get_current_user),
) -> LogoutAllResponse:
    """Logout from all devices by revoking all sessions.

    This invalidates the current token and terminates all active sessions.
    """
    token = credentials.credentials
    session_manager = get_session_manager()
    count = session_manager.logout_all_devices(current_user.user_id, token)

    return LogoutAllResponse(
        message="Successfully logged out from all devices",
        sessions_terminated=count,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(request: RefreshRequest) -> TokenResponse:
    """Get new access and refresh tokens using a valid refresh token."""
    try:
        token_data = verify_token(request.refresh_token, token_type="refresh")
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from e

    # Check if token is blacklisted
    session_manager = get_session_manager()
    if session_manager.is_token_revoked(request.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    # Issue new tokens
    new_tokens = create_tokens(
        {
            "email": token_data.email,
            "username": token_data.username,
            "id": token_data.user_id,
        }
    )

    return new_tokens


# ============================================================================
# Session Management Endpoints
# ============================================================================


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="List active sessions",
)
async def list_sessions(
    current_user: "TokenData" = Depends(get_current_user),
) -> SessionListResponse:
    """Get all active sessions for the current user.

    Useful for seeing what devices/browsers are logged in.
    """
    session_manager = get_session_manager()
    sessions = session_manager.get_active_sessions(current_user.user_id)

    return SessionListResponse(
        sessions=sessions,
        total=len(sessions),
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a specific session",
)
async def revoke_session(
    session_id: str,
    current_user: "TokenData" = Depends(get_current_user),
) -> None:
    """Revoke a specific session by its ID.

    Use this to log out a specific device without affecting other sessions.
    """
    session_manager = get_session_manager()

    # Verify session belongs to user
    sessions = session_manager.get_active_sessions(current_user.user_id)
    if not any(s.session_id == session_id for s in sessions):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session_manager.revoke_session(session_id)


# ============================================================================
# Account Security Endpoints (Stubs)
# ============================================================================


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr


class PasswordResetResponse(BaseModel):
    """Password reset response schema."""

    message: str = "If the email exists, a reset link has been sent"


@router.post(
    "/password/reset",
    response_model=PasswordResetResponse,
    summary="Request password reset",
)
async def request_password_reset(
    request: PasswordResetRequest,
) -> PasswordResetResponse:
    """Request a password reset email.

    Note: This is a stub. Email sending is not implemented.
    """
    # TODO: Implement email sending
    # For security, always return the same response regardless of email existence
    return PasswordResetResponse()


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


@router.post(
    "/password/change",
    response_model=dict,
    summary="Change password",
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: "TokenData" = Depends(get_current_user),
) -> dict:
    """Change the current user's password.

    Note: This is a stub. Password update is not implemented.
    """
    # TODO: Implement password change
    return {"message": "Password changed successfully"}
