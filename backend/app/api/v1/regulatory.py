"""Phase 2F: Singapore Regulatory Navigation API endpoints."""

import random
from datetime import datetime, timezone
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.regulatory import (
    AssetCompliancePath,
    AssetType,
    ChangeOfUseApplication,
    HeritageSubmission,
    RegulatoryAgency,
    SubmissionStatus,
)
from app.schemas.regulatory import (
    AssetCompliancePathRead,
    AuthoritySubmissionCreate,
    AuthoritySubmissionRead,
    ChangeOfUseCreate,
    ChangeOfUseRead,
    ChangeOfUseUpdate,
    HeritageSubmissionCreate,
    HeritageSubmissionRead,
    HeritageSubmissionUpdate,
)
from app.services.regulatory_service import RegulatoryService

router = APIRouter(prefix="/regulatory", tags=["regulatory"])


class AgencyRead(BaseModel):
    """Schema for reading regulatory agency info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None = None


# ============================================================================
# Core Regulatory Endpoints
# ============================================================================


@router.get("/agencies", response_model=List[AgencyRead])
async def list_agencies(
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    List all Singapore regulatory agencies (URA, BCA, SCDF, STB, JTC, etc.).
    """
    result = await db.execute(select(RegulatoryAgency))
    agencies = result.scalars().all()
    return agencies


@router.post("/submit", response_model=AuthoritySubmissionRead)
async def create_submission(
    submission: AuthoritySubmissionCreate,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Submit a regulatory application to a Singapore authority (Mock CORENET).
    """
    service = RegulatoryService(db)
    try:
        result = await service.create_submission(
            project_id=(
                UUID(str(submission.project_id))
                if isinstance(submission.project_id, int)
                else submission.project_id
            ),
            submission=submission,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get(
    "/project/{project_id}/submissions", response_model=List[AuthoritySubmissionRead]
)
async def list_project_submissions(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    List all regulatory submissions for a given project.
    """
    service = RegulatoryService(db)
    return service.get_project_submissions(project_id)


@router.get("/{submission_id}/status", response_model=AuthoritySubmissionRead)
async def get_submission_status(
    submission_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get the latest status of a submission. Triggers a poll to the external agency.
    """
    service = RegulatoryService(db)
    try:
        submission = await service.update_submission_status(submission_id)
        return submission
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        ) from None


# ============================================================================
# Asset-Specific Compliance Paths
# ============================================================================


@router.get(
    "/compliance-paths/{asset_type}", response_model=List[AssetCompliancePathRead]
)
async def get_compliance_path_for_asset(
    asset_type: AssetType,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get the regulatory compliance path for a specific asset type.

    Returns ordered list of required submissions (URA, BCA, SCDF, etc.)
    based on the property type (office, retail, residential, industrial, heritage).
    """
    result = await db.execute(
        select(AssetCompliancePath)
        .where(AssetCompliancePath.asset_type == asset_type)
        .order_by(AssetCompliancePath.sequence_order)
    )
    paths = result.scalars().all()
    return paths


@router.get("/compliance-paths", response_model=List[AssetCompliancePathRead])
async def list_all_compliance_paths(
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    List all asset-specific compliance paths.
    """
    result = await db.execute(
        select(AssetCompliancePath).order_by(
            AssetCompliancePath.asset_type, AssetCompliancePath.sequence_order
        )
    )
    paths = result.scalars().all()
    return paths


# ============================================================================
# Change of Use Navigation
# ============================================================================


@router.post("/change-of-use", response_model=ChangeOfUseRead)
async def create_change_of_use_application(
    data: ChangeOfUseCreate,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Create a change of use application for adaptive reuse projects.

    Automatically determines if DC amendment or planning permission is required.
    """
    requires_dc = data.current_use != data.proposed_use
    requires_planning = data.proposed_use in [
        AssetType.RESIDENTIAL,
        AssetType.HOSPITALITY,
    ]

    application = ChangeOfUseApplication(
        project_id=data.project_id,
        current_use=data.current_use,
        proposed_use=data.proposed_use,
        justification=data.justification,
        requires_dc_amendment=requires_dc,
        requires_planning_permission=requires_planning,
        status=SubmissionStatus.DRAFT,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/change-of-use/project/{project_id}", response_model=List[ChangeOfUseRead])
async def list_change_of_use_applications(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    List all change of use applications for a project.
    """
    result = await db.execute(
        select(ChangeOfUseApplication)
        .where(ChangeOfUseApplication.project_id == project_id)
        .order_by(ChangeOfUseApplication.created_at.desc())
    )
    applications = result.scalars().all()
    return applications


@router.patch("/change-of-use/{application_id}", response_model=ChangeOfUseRead)
async def update_change_of_use_application(
    application_id: UUID,
    data: ChangeOfUseUpdate,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Update a change of use application.
    """
    result = await db.execute(
        select(ChangeOfUseApplication).where(
            ChangeOfUseApplication.id == application_id
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change of use application not found",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(application, field, value)

    await db.commit()
    await db.refresh(application)
    return application


# ============================================================================
# Heritage Authority Management (STB)
# ============================================================================


@router.post("/heritage", response_model=HeritageSubmissionRead)
async def create_heritage_submission(
    data: HeritageSubmissionCreate,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Create a heritage submission for STB coordination.

    Used for conservation projects requiring heritage authority approval.
    """
    submission = HeritageSubmission(
        project_id=data.project_id,
        conservation_status=data.conservation_status,
        original_construction_year=data.original_construction_year,
        heritage_elements=data.heritage_elements,
        proposed_interventions=data.proposed_interventions,
        status=SubmissionStatus.DRAFT,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


@router.get(
    "/heritage/project/{project_id}", response_model=List[HeritageSubmissionRead]
)
async def list_heritage_submissions(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    List all heritage submissions for a project.
    """
    result = await db.execute(
        select(HeritageSubmission)
        .where(HeritageSubmission.project_id == project_id)
        .order_by(HeritageSubmission.created_at.desc())
    )
    submissions = result.scalars().all()
    return submissions


@router.get("/heritage/{submission_id}", response_model=HeritageSubmissionRead)
async def get_heritage_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get a specific heritage submission.
    """
    result = await db.execute(
        select(HeritageSubmission).where(HeritageSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heritage submission not found",
        )
    return submission


@router.patch("/heritage/{submission_id}", response_model=HeritageSubmissionRead)
async def update_heritage_submission(
    submission_id: UUID,
    data: HeritageSubmissionUpdate,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Update a heritage submission.
    """
    result = await db.execute(
        select(HeritageSubmission).where(HeritageSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heritage submission not found",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(submission, field, value)

    await db.commit()
    await db.refresh(submission)
    return submission


@router.post("/heritage/{submission_id}/submit", response_model=HeritageSubmissionRead)
async def submit_to_stb(
    submission_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Submit a heritage application to STB (Singapore Tourism Board).

    Generates STB reference number and changes status to SUBMITTED.
    """
    result = await db.execute(
        select(HeritageSubmission).where(HeritageSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heritage submission not found",
        )

    if submission.status != SubmissionStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft submissions can be submitted",
        )

    # Generate STB reference number
    date_str = datetime.now().strftime("%y%m%d")
    rand = random.randint(1000, 9999)
    submission.stb_reference = f"STB-{date_str}-{rand}"
    submission.status = SubmissionStatus.SUBMITTED
    submission.submitted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(submission)
    return submission
