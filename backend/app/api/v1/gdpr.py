"""GDPR Compliance API endpoints.

Provides endpoints for:
- Data export (right to data portability)
- Account deletion (right to be forgotten)
- Consent management
- Data access requests
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth.service import get_current_user
from app.core.exceptions import NotFoundError
from app.utils.logging import get_logger, log_event

if TYPE_CHECKING:
    from app.core.auth.service import TokenData


logger = get_logger(__name__)
router = APIRouter(prefix="/gdpr", tags=["gdpr"])


# ============================================================================
# Consent Types and Models
# ============================================================================


class ConsentType(str, Enum):
    """Types of user consent."""

    MARKETING_EMAIL = "marketing_email"
    MARKETING_SMS = "marketing_sms"
    ANALYTICS = "analytics"
    THIRD_PARTY_SHARING = "third_party_sharing"
    PERSONALIZATION = "personalization"
    COOKIES_ESSENTIAL = "cookies_essential"
    COOKIES_ANALYTICS = "cookies_analytics"
    COOKIES_MARKETING = "cookies_marketing"


class ConsentRecord(BaseModel):
    """Record of user consent."""

    consent_type: ConsentType
    granted: bool
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = None


class ConsentUpdateRequest(BaseModel):
    """Request to update consent preferences."""

    consents: list[ConsentRecord] = Field(..., description="List of consent updates")


class ConsentResponse(BaseModel):
    """Current consent status."""

    user_id: str
    consents: list[ConsentRecord]
    updated_at: datetime


# ============================================================================
# Data Export Models
# ============================================================================


class DataExportStatus(str, Enum):
    """Status of a data export request."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class DataExportRequest(BaseModel):
    """Request for data export."""

    include_projects: bool = Field(True, description="Include project data")
    include_properties: bool = Field(True, description="Include property data")
    include_documents: bool = Field(True, description="Include document metadata")
    include_activity_logs: bool = Field(True, description="Include activity history")
    format: str = Field("json", description="Export format (json or csv)")


class DataExportResponse(BaseModel):
    """Response for data export request."""

    export_id: str
    status: DataExportStatus
    requested_at: datetime
    estimated_completion: Optional[datetime] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None


# ============================================================================
# Account Deletion Models
# ============================================================================


class DeletionRequestStatus(str, Enum):
    """Status of account deletion request."""

    PENDING = "pending"  # Waiting for confirmation
    CONFIRMED = "confirmed"  # User confirmed
    PROCESSING = "processing"  # Being processed
    COMPLETED = "completed"  # Account deleted
    CANCELLED = "cancelled"  # User cancelled


class DeletionRequest(BaseModel):
    """Request for account deletion."""

    confirmation: str = Field(
        ...,
        description="Must be 'DELETE MY ACCOUNT' to confirm",
    )
    reason: Optional[str] = Field(
        None, max_length=500, description="Optional reason for leaving"
    )


class DeletionResponse(BaseModel):
    """Response for deletion request."""

    request_id: str
    status: DeletionRequestStatus
    requested_at: datetime
    grace_period_ends: Optional[datetime] = None
    message: str


# ============================================================================
# Data Access Request Models
# ============================================================================


class DataAccessRequest(BaseModel):
    """Request to access personal data (DSAR)."""

    request_type: str = Field(
        "full_report",
        description="Type of access request: 'full_report', 'specific_data'",
    )
    specific_categories: Optional[list[str]] = Field(
        None,
        description="Specific data categories if request_type is 'specific_data'",
    )


class DataAccessResponse(BaseModel):
    """Response for data access request."""

    request_id: str
    status: str
    requested_at: datetime
    estimated_response: datetime
    message: str


# ============================================================================
# In-Memory Storage (Replace with database in production)
# ============================================================================

# These would be stored in the database in production
_consent_store: dict[str, list[ConsentRecord]] = {}
_export_requests: dict[str, DataExportResponse] = {}
_deletion_requests: dict[str, DeletionResponse] = {}


# ============================================================================
# Consent Management Endpoints
# ============================================================================


@router.get(
    "/consent",
    response_model=ConsentResponse,
    summary="Get current consent preferences",
)
async def get_consent(
    current_user: "TokenData" = Depends(get_current_user),
) -> ConsentResponse:
    """Get current user's consent preferences."""
    user_consents = _consent_store.get(current_user.user_id, [])

    return ConsentResponse(
        user_id=current_user.user_id,
        consents=user_consents,
        updated_at=datetime.now(timezone.utc),
    )


@router.put(
    "/consent",
    response_model=ConsentResponse,
    summary="Update consent preferences",
)
async def update_consent(
    request: ConsentUpdateRequest,
    current_user: "TokenData" = Depends(get_current_user),
) -> ConsentResponse:
    """Update user's consent preferences.

    Each consent change is recorded with timestamp for audit purposes.
    """
    now = datetime.now(timezone.utc)

    # Update consent records
    for consent in request.consents:
        if consent.granted:
            consent.granted_at = now
            consent.revoked_at = None
        else:
            consent.revoked_at = now

    _consent_store[current_user.user_id] = request.consents

    log_event(
        logger,
        "consent_updated",
        user_id=current_user.user_id,
        consents_count=len(request.consents),
    )

    return ConsentResponse(
        user_id=current_user.user_id,
        consents=request.consents,
        updated_at=now,
    )


@router.post(
    "/consent/withdraw-all",
    response_model=dict,
    summary="Withdraw all marketing consents",
)
async def withdraw_all_marketing_consent(
    current_user: "TokenData" = Depends(get_current_user),
) -> dict:
    """Withdraw all marketing and non-essential consents.

    Essential consents (cookies_essential) are not affected.
    """
    now = datetime.now(timezone.utc)
    marketing_types = [
        ConsentType.MARKETING_EMAIL,
        ConsentType.MARKETING_SMS,
        ConsentType.THIRD_PARTY_SHARING,
        ConsentType.COOKIES_MARKETING,
        ConsentType.COOKIES_ANALYTICS,
    ]

    existing = _consent_store.get(current_user.user_id, [])
    updated = []

    for consent in existing:
        if consent.consent_type in marketing_types:
            consent.granted = False
            consent.revoked_at = now
        updated.append(consent)

    _consent_store[current_user.user_id] = updated

    log_event(
        logger,
        "consent_all_marketing_withdrawn",
        user_id=current_user.user_id,
    )

    return {
        "message": "All marketing consents have been withdrawn",
        "updated_at": now.isoformat(),
    }


# ============================================================================
# Data Export Endpoints
# ============================================================================


@router.post(
    "/export",
    response_model=DataExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request data export",
)
async def request_data_export(
    request: DataExportRequest,
    background_tasks: BackgroundTasks,
    current_user: "TokenData" = Depends(get_current_user),
) -> DataExportResponse:
    """Request an export of all personal data.

    The export is processed asynchronously. You will receive a download
    link when the export is complete (within 30 days per GDPR requirements).
    """
    export_id = str(uuid4())
    now = datetime.now(timezone.utc)

    response = DataExportResponse(
        export_id=export_id,
        status=DataExportStatus.PENDING,
        requested_at=now,
        estimated_completion=now,  # Immediate in this stub
    )

    _export_requests[export_id] = response

    # In production, this would queue a background job
    log_event(
        logger,
        "data_export_requested",
        user_id=current_user.user_id,
        export_id=export_id,
        format=request.format,
    )

    return response


@router.get(
    "/export/{export_id}",
    response_model=DataExportResponse,
    summary="Check export status",
)
async def get_export_status(
    export_id: str,
    current_user: "TokenData" = Depends(get_current_user),
) -> DataExportResponse:
    """Check the status of a data export request."""
    export = _export_requests.get(export_id)

    if not export:
        raise NotFoundError("Export", export_id)

    return export


@router.get(
    "/export/{export_id}/download",
    summary="Download exported data",
)
async def download_export(
    export_id: str,
    current_user: "TokenData" = Depends(get_current_user),
) -> dict:
    """Download the exported data.

    Note: This is a stub. In production, this would return the actual file.
    """
    export = _export_requests.get(export_id)

    if not export:
        raise NotFoundError("Export", export_id)

    if export.status != DataExportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Export is not yet complete",
        )

    # In production, this would return a file download
    return {
        "message": "Export download stub",
        "export_id": export_id,
        "note": "In production, this returns the actual data file",
    }


# ============================================================================
# Account Deletion Endpoints
# ============================================================================


@router.post(
    "/delete-account",
    response_model=DeletionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request account deletion",
)
async def request_account_deletion(
    request: DeletionRequest,
    current_user: "TokenData" = Depends(get_current_user),
) -> DeletionResponse:
    """Request deletion of your account and all personal data.

    A 30-day grace period applies during which you can cancel the request.
    After the grace period, all data will be permanently deleted.
    """
    if request.confirmation != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please type 'DELETE MY ACCOUNT' to confirm deletion",
        )

    request_id = str(uuid4())
    now = datetime.now(timezone.utc)
    from datetime import timedelta

    grace_end = now + timedelta(days=30)

    response = DeletionResponse(
        request_id=request_id,
        status=DeletionRequestStatus.CONFIRMED,
        requested_at=now,
        grace_period_ends=grace_end,
        message=(
            f"Your account deletion request has been confirmed. "
            f"Your data will be permanently deleted on {grace_end.strftime('%Y-%m-%d')}. "
            f"You can cancel this request before then."
        ),
    )

    _deletion_requests[request_id] = response

    log_event(
        logger,
        "account_deletion_requested",
        user_id=current_user.user_id,
        request_id=request_id,
        reason=request.reason,
    )

    return response


@router.delete(
    "/delete-account/{request_id}",
    response_model=dict,
    summary="Cancel account deletion",
)
async def cancel_account_deletion(
    request_id: str,
    current_user: "TokenData" = Depends(get_current_user),
) -> dict:
    """Cancel a pending account deletion request.

    Only possible during the 30-day grace period.
    """
    deletion = _deletion_requests.get(request_id)

    if not deletion:
        raise NotFoundError("Deletion request", request_id)

    if deletion.status != DeletionRequestStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel: deletion is not in grace period",
        )

    deletion.status = DeletionRequestStatus.CANCELLED

    log_event(
        logger,
        "account_deletion_cancelled",
        user_id=current_user.user_id,
        request_id=request_id,
    )

    return {
        "message": "Account deletion request has been cancelled",
        "request_id": request_id,
    }


# ============================================================================
# Data Access Request Endpoints
# ============================================================================


@router.post(
    "/access-request",
    response_model=DataAccessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit data access request",
)
async def submit_access_request(
    request: DataAccessRequest,
    current_user: "TokenData" = Depends(get_current_user),
) -> DataAccessResponse:
    """Submit a Data Subject Access Request (DSAR).

    Per GDPR, we will respond within 30 days with details of all
    personal data we hold about you.
    """
    request_id = str(uuid4())
    now = datetime.now(timezone.utc)
    from datetime import timedelta

    response_deadline = now + timedelta(days=30)

    log_event(
        logger,
        "data_access_request_submitted",
        user_id=current_user.user_id,
        request_id=request_id,
        request_type=request.request_type,
    )

    return DataAccessResponse(
        request_id=request_id,
        status="received",
        requested_at=now,
        estimated_response=response_deadline,
        message=(
            f"Your data access request has been received. "
            f"You will receive a response by {response_deadline.strftime('%Y-%m-%d')} "
            f"as required by GDPR Article 15."
        ),
    )


# ============================================================================
# Privacy Dashboard
# ============================================================================


@router.get(
    "/privacy-dashboard",
    response_model=dict,
    summary="Get privacy dashboard data",
)
async def get_privacy_dashboard(
    current_user: "TokenData" = Depends(get_current_user),
) -> dict:
    """Get a comprehensive view of privacy-related data.

    Includes consent status, pending requests, and data categories.
    """
    consents = _consent_store.get(current_user.user_id, [])
    pending_exports = [
        e
        for e in _export_requests.values()
        if e.status in [DataExportStatus.PENDING, DataExportStatus.PROCESSING]
    ]
    pending_deletions = [
        d
        for d in _deletion_requests.values()
        if d.status == DeletionRequestStatus.CONFIRMED
    ]

    return {
        "user_id": current_user.user_id,
        "consents": {
            "total": len(consents),
            "granted": sum(1 for c in consents if c.granted),
            "revoked": sum(1 for c in consents if not c.granted),
            "details": consents,
        },
        "data_categories": [
            "Profile information",
            "Contact details",
            "Project data",
            "Property assessments",
            "Financial analyses",
            "Activity logs",
            "Authentication data",
        ],
        "pending_requests": {
            "exports": len(pending_exports),
            "deletions": len(pending_deletions),
        },
        "your_rights": {
            "access": "Request a copy of your data (Article 15)",
            "rectification": "Correct inaccurate data (Article 16)",
            "erasure": "Delete your data (Article 17)",
            "restriction": "Restrict processing (Article 18)",
            "portability": "Export your data (Article 20)",
            "objection": "Object to processing (Article 21)",
        },
        "data_retention": {
            "active_data": "Retained while account is active",
            "deleted_accounts": "30-day grace period, then permanent deletion",
            "backups": "Retained for 90 days for disaster recovery",
            "audit_logs": "Retained for 7 years for compliance",
        },
    }
