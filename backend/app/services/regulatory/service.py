from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.regulatory import (
    RegulatoryAgency,
    AuthoritySubmission,
    SubmissionStatus,
    AgencyCode,
)
from app.schemas.regulatory import SubmissionCreate, SubmissionUpdate


class RegulatoryService:
    @staticmethod
    async def get_all_agencies(db: AsyncSession) -> List[RegulatoryAgency]:
        result = await db.execute(select(RegulatoryAgency))
        return list(result.scalars().all())

    @staticmethod
    async def get_agency_by_code(
        db: AsyncSession, code: AgencyCode
    ) -> Optional[RegulatoryAgency]:
        result = await db.execute(
            select(RegulatoryAgency).where(RegulatoryAgency.code == code)
        )
        return result.scalars().first()

    @staticmethod
    async def get_project_submissions(
        db: AsyncSession, project_id: UUID
    ) -> List[AuthoritySubmission]:
        result = await db.execute(
            select(AuthoritySubmission)
            .where(AuthoritySubmission.project_id == project_id)
            .order_by(AuthoritySubmission.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_submission(
        db: AsyncSession, project_id: UUID, submission_in: SubmissionCreate
    ) -> AuthoritySubmission:
        # Determine Agency based on submission type logic or explicit selection
        # For now, we assume the frontend passes the agency_id

        submission = AuthoritySubmission(
            project_id=project_id,
            agency_id=submission_in.agency_id,
            submission_type=submission_in.submission_type,
            title=submission_in.title,
            description=submission_in.description,
            status=SubmissionStatus.DRAFT,
        )

        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def get_submission(
        db: AsyncSession, submission_id: UUID
    ) -> Optional[AuthoritySubmission]:
        result = await db.execute(
            select(AuthoritySubmission).where(AuthoritySubmission.id == submission_id)
        )
        return result.scalars().first()

    @staticmethod
    async def update_submission(
        db: AsyncSession, submission: AuthoritySubmission, update_in: SubmissionUpdate
    ) -> AuthoritySubmission:
        for field, value in update_in.dict(exclude_unset=True).items():
            setattr(submission, field, value)

        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def submit_application(
        db: AsyncSession, submission: AuthoritySubmission, external_ref_no: str
    ) -> AuthoritySubmission:
        submission.status = SubmissionStatus.SUBMITTED
        submission.submission_no = external_ref_no
        submission.submitted_at = submission.updated_at  # Set to now on update

        await db.commit()
        await db.refresh(submission)
        return submission
