from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from app.schemas.team import InvitationCreate, InvitationRead, TeamMemberRead
from app.services.team.team_service import TeamService

router = APIRouter()


@router.get("/members", response_model=List[TeamMemberRead])
async def list_team_members(
    project_id: UUID,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> Any:
    """
    List all team members for a project.
    """
    members = await TeamService.get_team_members(db, project_id)
    return members


@router.post("/invite", response_model=InvitationRead)
async def invite_member(
    project_id: UUID,
    invitation_in: InvitationCreate,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_reviewer),
) -> Any:
    """
    Invite a new member (specialist/consultant) to the project.
    Only reviewers/admins can invite.
    """
    invitation = await TeamService.invite_member(
        db,
        project_id,
        invitation_in.email,
        invitation_in.role,
        inviter_id=identity.user_id,
    )
    return invitation


@router.post("/invitations/{token}/accept", response_model=TeamMemberRead)
async def accept_invitation(
    token: str,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.get_identity),
) -> Any:
    """
    Accept an invitation using a token.
    """
    if not identity.user_id:
        raise HTTPException(
            status_code=401, detail="Authentication required to accept invitation"
        )

    member = await TeamService.accept_invitation(db, token, identity.user_id)
    if not member:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")
    return member


@router.delete("/members/{user_id}", response_model=bool)
async def remove_member(
    project_id: UUID,
    user_id: UUID,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_reviewer),
) -> Any:
    """
    Remove a member from the project.
    """
    success = await TeamService.remove_member(db, project_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return True
