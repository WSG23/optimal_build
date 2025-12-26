"""Organization API endpoints for multi-tenancy.

Provides endpoints for:
- Organization CRUD operations
- Member management
- Invitation workflows
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.auth.service import get_current_user
from app.core.exceptions import AuthorizationError, NotFoundError
from app.models.organization import (
    Organization,
    OrganizationInvitation,
    OrganizationMember,
    OrganizationRole,
)
from app.models.projects import Project
from app.schemas.organization import (
    InvitationAccept,
    OrganizationCreate,
    OrganizationDetail,
    OrganizationInvitationCreate,
    OrganizationInvitationListResponse,
    OrganizationInvitationResponse,
    OrganizationMemberCreate,
    OrganizationMemberListResponse,
    OrganizationMemberResponse,
    OrganizationMemberUpdate,
    OrganizationResponse,
    OrganizationUpdate,
    SwitchOrganization,
)

if TYPE_CHECKING:
    from app.core.auth.service import TokenData

router = APIRouter(prefix="/organizations", tags=["organizations"])

# Invitation expiry duration
INVITATION_EXPIRY_DAYS = 7


# ============================================================================
# Helper Functions
# ============================================================================


async def get_organization_or_404(
    db: AsyncSession,
    organization_id: UUID,
) -> Organization:
    """Get an organization by ID or raise 404."""
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError("Organization", organization_id)
    return org


async def check_org_permission(
    db: AsyncSession,
    user_id: UUID,
    organization_id: UUID,
    required_roles: list[OrganizationRole] | None = None,
) -> OrganizationMember:
    """Check if user has permission within an organization.

    Args:
        db: Database session
        user_id: TokenData ID to check
        organization_id: Organization ID to check
        required_roles: List of allowed roles. If None, any active member is allowed.

    Returns:
        OrganizationMember object

    Raises:
        AuthorizationError: If user doesn't have required permission
    """
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_active == True,  # noqa: E712
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise AuthorizationError("Not a member of this organization")

    if required_roles and member.role not in required_roles:
        raise AuthorizationError(
            required_role=required_roles[0].value,
        )

    return member


# ============================================================================
# Organization CRUD
# ============================================================================


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
async def create_organization(
    data: OrganizationCreate,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Create a new organization.

    The creating user automatically becomes the owner of the organization.
    """
    # Check if slug is already taken
    existing = await db.execute(
        select(Organization).where(Organization.slug == data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization slug '{data.slug}' is already taken",
        )

    # Create organization
    org = Organization(
        id=uuid4(),
        name=data.name,
        slug=data.slug,
        uen_number=data.uen_number,
    )
    db.add(org)

    # Add creator as owner
    member = OrganizationMember(
        id=uuid4(),
        organization_id=org.id,
        user_id=current_user.id,
        role=OrganizationRole.OWNER,
    )
    db.add(member)

    await db.commit()
    await db.refresh(org)

    return org


@router.get(
    "",
    response_model=list[OrganizationResponse],
    summary="List organizations for current user",
)
async def list_organizations(
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Organization]:
    """List all organizations the current user is a member of."""
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.is_active == True,  # noqa: E712
            Organization.is_active == True,  # noqa: E712
        )
        .order_by(Organization.name)
    )
    return list(result.scalars().all())


@router.get(
    "/{organization_id}",
    response_model=OrganizationDetail,
    summary="Get organization details",
)
async def get_organization(
    organization_id: UUID,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get detailed information about an organization."""
    await check_org_permission(db, current_user.id, organization_id)

    org = await get_organization_or_404(db, organization_id)

    # Get member count
    member_count_result = await db.execute(
        select(func.count(OrganizationMember.id)).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.is_active == True,  # noqa: E712
        )
    )
    member_count = member_count_result.scalar() or 0

    # Get project count
    project_count_result = await db.execute(
        select(func.count(Project.id)).where(
            Project.organization_id == organization_id,
        )
    )
    project_count = project_count_result.scalar() or 0

    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "plan": org.plan,
        "is_active": org.is_active,
        "is_verified": org.is_verified,
        "uen_number": org.uen_number,
        "created_at": org.created_at,
        "updated_at": org.updated_at,
        "settings": org.settings,
        "member_count": member_count,
        "project_count": project_count,
    }


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
)
async def update_organization(
    organization_id: UUID,
    data: OrganizationUpdate,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Update an organization. Requires owner or admin role."""
    await check_org_permission(
        db,
        current_user.id,
        organization_id,
        required_roles=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
    )

    org = await get_organization_or_404(db, organization_id)

    # Update fields
    if data.name is not None:
        org.name = data.name
    if data.settings is not None:
        org.settings = data.settings
    if data.uen_number is not None:
        org.uen_number = data.uen_number

    await db.commit()
    await db.refresh(org)

    return org


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete organization",
)
async def delete_organization(
    organization_id: UUID,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete an organization. Requires owner role."""
    await check_org_permission(
        db,
        current_user.id,
        organization_id,
        required_roles=[OrganizationRole.OWNER],
    )

    org = await get_organization_or_404(db, organization_id)
    org.is_active = False
    org.deleted_at = datetime.now(timezone.utc)

    await db.commit()


# ============================================================================
# Member Management
# ============================================================================


@router.get(
    "/{organization_id}/members",
    response_model=OrganizationMemberListResponse,
    summary="List organization members",
)
async def list_members(
    organization_id: UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all members of an organization."""
    await check_org_permission(db, current_user.id, organization_id)

    # Count total
    count_result = await db.execute(
        select(func.count(OrganizationMember.id)).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.is_active == True,  # noqa: E712
        )
    )
    total = count_result.scalar() or 0

    # Get paginated members
    offset = (page - 1) * page_size
    result = await db.execute(
        select(OrganizationMember)
        .where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.is_active == True,  # noqa: E712
        )
        .offset(offset)
        .limit(page_size)
    )
    members = list(result.scalars().all())

    # Enrich with user info
    items = []
    for member in members:
        user = await db.get(member.user.__class__, member.user_id)
        items.append(
            OrganizationMemberResponse(
                id=member.id,
                organization_id=member.organization_id,
                user_id=member.user_id,
                role=member.role,
                is_active=member.is_active,
                joined_at=member.joined_at,
                user_email=user.email if user else None,
                user_name=user.name if user and hasattr(user, "name") else None,
            )
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "/{organization_id}/members",
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a member to organization",
)
async def add_member(
    organization_id: UUID,
    data: OrganizationMemberCreate,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationMember:
    """Add a user as a member of the organization. Requires owner or admin role."""
    await check_org_permission(
        db,
        current_user.id,
        organization_id,
        required_roles=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
    )

    # Check if user is already a member
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == data.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="TokenData is already a member of this organization",
        )

    member = OrganizationMember(
        id=uuid4(),
        organization_id=organization_id,
        user_id=data.user_id,
        role=data.role,
    )
    db.add(member)

    await db.commit()
    await db.refresh(member)

    return member


@router.patch(
    "/{organization_id}/members/{member_id}",
    response_model=OrganizationMemberResponse,
    summary="Update member role",
)
async def update_member(
    organization_id: UUID,
    member_id: UUID,
    data: OrganizationMemberUpdate,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationMember:
    """Update a member's role. Requires owner or admin role."""
    requester_membership = await check_org_permission(
        db,
        current_user.id,
        organization_id,
        required_roles=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
    )

    # Get member to update
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == organization_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundError("Member", member_id)

    # Only owners can change owner roles
    if member.role == OrganizationRole.OWNER or data.role == OrganizationRole.OWNER:
        if requester_membership.role != OrganizationRole.OWNER:
            raise AuthorizationError(required_role=OrganizationRole.OWNER.value)

    member.role = data.role
    await db.commit()
    await db.refresh(member)

    return member


@router.delete(
    "/{organization_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member from organization",
)
async def remove_member(
    organization_id: UUID,
    member_id: UUID,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a member from the organization. Requires owner or admin role."""
    requester_membership = await check_org_permission(
        db,
        current_user.id,
        organization_id,
        required_roles=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
    )

    # Get member to remove
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == organization_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundError("Member", member_id)

    # Owners cannot be removed by admins
    if member.role == OrganizationRole.OWNER:
        if requester_membership.role != OrganizationRole.OWNER:
            raise AuthorizationError(required_role=OrganizationRole.OWNER.value)

    # Soft delete
    member.is_active = False
    await db.commit()


# ============================================================================
# Invitations
# ============================================================================


@router.get(
    "/{organization_id}/invitations",
    response_model=OrganizationInvitationListResponse,
    summary="List organization invitations",
)
async def list_invitations(
    organization_id: UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List pending invitations for an organization."""
    await check_org_permission(
        db,
        current_user.id,
        organization_id,
        required_roles=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
    )

    # Count total
    count_result = await db.execute(
        select(func.count(OrganizationInvitation.id)).where(
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.status == "pending",
        )
    )
    total = count_result.scalar() or 0

    # Get paginated invitations
    offset = (page - 1) * page_size
    result = await db.execute(
        select(OrganizationInvitation)
        .where(
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.status == "pending",
        )
        .offset(offset)
        .limit(page_size)
    )
    invitations = list(result.scalars().all())

    return {
        "items": [
            OrganizationInvitationResponse(
                id=inv.id,
                organization_id=inv.organization_id,
                email=inv.email,
                role=inv.role,
                status=inv.status,
                created_at=inv.created_at,
                expires_at=inv.expires_at,
                accepted_at=inv.accepted_at,
            )
            for inv in invitations
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "/{organization_id}/invitations",
    response_model=OrganizationInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invitation",
)
async def create_invitation(
    organization_id: UUID,
    data: OrganizationInvitationCreate,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationInvitation:
    """Create an invitation to join the organization."""
    await check_org_permission(
        db,
        current_user.id,
        organization_id,
        required_roles=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
    )

    # Check if invitation already exists
    existing = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.email == data.email,
            OrganizationInvitation.status == "pending",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An invitation already exists for this email",
        )

    invitation = OrganizationInvitation(
        id=uuid4(),
        organization_id=organization_id,
        email=data.email,
        role=data.role,
        token=secrets.token_urlsafe(32),
        invited_by=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=INVITATION_EXPIRY_DAYS),
    )
    db.add(invitation)

    await db.commit()
    await db.refresh(invitation)

    # TODO: Send invitation email

    return invitation


@router.delete(
    "/{organization_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke invitation",
)
async def revoke_invitation(
    organization_id: UUID,
    invitation_id: UUID,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke a pending invitation."""
    await check_org_permission(
        db,
        current_user.id,
        organization_id,
        required_roles=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
    )

    result = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.status == "pending",
        )
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise NotFoundError("Invitation", invitation_id)

    invitation.status = "revoked"
    await db.commit()


@router.post(
    "/invitations/accept",
    response_model=OrganizationMemberResponse,
    summary="Accept invitation",
)
async def accept_invitation(
    data: InvitationAccept,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationMember:
    """Accept an invitation to join an organization."""
    # Find invitation by token
    result = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.token == data.token,
            OrganizationInvitation.status == "pending",
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invitation token",
        )

    # Check if expired
    if invitation.expires_at < datetime.now(timezone.utc):
        invitation.status = "expired"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invitation has expired",
        )

    # Check email matches (optional - can be made stricter)
    if invitation.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to a different email address",
        )

    # Check if already a member
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == invitation.organization_id,
            OrganizationMember.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already a member of this organization",
        )

    # Create membership
    member = OrganizationMember(
        id=uuid4(),
        organization_id=invitation.organization_id,
        user_id=current_user.id,
        role=invitation.role,
    )
    db.add(member)

    # Update invitation
    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(member)

    return member


# ============================================================================
# Switch Organization
# ============================================================================


@router.post(
    "/switch",
    response_model=OrganizationResponse,
    summary="Switch active organization",
)
async def switch_organization(
    data: SwitchOrganization,
    current_user: "TokenData" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Switch the user's active organization context.

    Updates the user's primary_organization_id.
    """
    await check_org_permission(db, current_user.id, data.organization_id)

    org = await get_organization_or_404(db, data.organization_id)

    # Update user's primary organization
    current_user.primary_organization_id = org.id
    await db.commit()

    return org
