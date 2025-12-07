from typing import List, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.regulatory import (
    RegulatoryAgencyRead,
    SubmissionCreate,
    SubmissionRead,
    SubmissionStatusCheck,
)
from app.services.regulatory.service import RegulatoryService
from app.services.regulatory.integration import CorenetIntegrationService

router = APIRouter()


@router.get("/agencies", response_model=List[RegulatoryAgencyRead])
async def list_agencies(
    db: AsyncSession = Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> Any:
    """
    List all supported regulatory agencies (URA, BCA, etc.).
    """
    agencies = await RegulatoryService.get_all_agencies(db)
    return agencies


@router.get("/submissions", response_model=List[SubmissionRead])
async def list_submissions(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> Any:
    """
    List all submissions for a specific project.
    """
    # TODO: Verify user has access to project
    submissions = await RegulatoryService.get_project_submissions(db, project_id)
    return submissions


@router.post("/submissions", response_model=SubmissionRead)
async def create_submission(
    project_id: UUID,
    submission_in: SubmissionCreate,
    db: AsyncSession = Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_reviewer),
) -> Any:
    """
    Draft a new authority submission.
    """
    submission = await RegulatoryService.create_submission(
        db, project_id, submission_in
    )
    return submission


@router.post("/submissions/{submission_id}/submit", response_model=SubmissionRead)
async def submit_application(
    submission_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_reviewer),
) -> Any:
    """
    Submit a drafted application to the agency's (mock) portal.
    """
    submission = await RegulatoryService.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Simulate API call to CORENET
    submission_payload = {
        "id": str(submission.id),
        "type": submission.submission_type,
        "title": submission.title,
    }

    external_ref = await CorenetIntegrationService.submit_application(
        submission_payload
    )

    # Update local record
    submission = await RegulatoryService.submit_application(
        db, submission, external_ref
    )
    return submission


@router.get("/submissions/{submission_id}/status", response_model=SubmissionStatusCheck)
async def check_status(
    submission_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> Any:
    """
    Check the live status of a submission from the agency's (mock) portal.
    """
    submission = await RegulatoryService.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if not submission.submission_no:
        raise HTTPException(
            status_code=400, detail="Submission has not been submitted yet"
        )

    status_response = await CorenetIntegrationService.check_submission_status(
        submission.submission_no
    )
    return status_response
