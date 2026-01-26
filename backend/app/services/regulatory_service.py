from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.regulatory import (
    AuthoritySubmission,
    RegulatoryAgency,
    SubmissionStatus,
)
from app.models.project import Project
from app.schemas.regulatory import AuthoritySubmissionCreate
from app.services.regulatory.integration import CorenetIntegrationService


class RegulatoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.corenet = CorenetIntegrationService()

    @staticmethod
    def _map_external_status(status: str | None) -> SubmissionStatus | None:
        if not status:
            return None
        normalised = status.lower()
        if "approve" in normalised:
            return SubmissionStatus.APPROVED
        if "reject" in normalised:
            return SubmissionStatus.REJECTED
        if (
            "rfi" in normalised
            or "clarification" in normalised
            or "amend" in normalised
        ):
            return SubmissionStatus.RFI
        if (
            "process" in normalised
            or "review" in normalised
            or "received" in normalised
        ):
            return SubmissionStatus.IN_REVIEW
        if "submit" in normalised:
            return SubmissionStatus.SUBMITTED
        return None

    async def create_submission(
        self,
        project_id: UUID,
        submission: AuthoritySubmissionCreate,
        submitted_by_id: Optional[UUID] = None,
    ) -> AuthoritySubmission:
        """
        Creates a new submission record and sends it to the external agency.
        """
        # 1. Validate Project
        result = await self.db.execute(select(Project).filter(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 2. Get or Create Agency (ensure agency exists in DB for FK)
        result = await self.db.execute(
            select(RegulatoryAgency).filter(RegulatoryAgency.code == submission.agency)
        )
        agency = result.scalar_one_or_none()

        if not agency:
            # Auto-create for dev simplicity if not found
            agency = RegulatoryAgency(
                code=submission.agency,
                name=f"{submission.agency} Authority",
                description="Auto-created agency",
            )
            self.db.add(agency)
            await self.db.flush()

        # 3. Create Draft Submission Record
        db_submission = AuthoritySubmission(
            project_id=project_id,
            agency_id=agency.id,
            submission_type=submission.submission_type,
            title=f"{submission.agency} Submission for {project.project_code}",
            status=SubmissionStatus.SUBMITTED,  # Jump to submitted for demo flow
            submitted_at=datetime.utcnow(),
            # submitted_by_id=submitted_by_id # User tracking if available
        )
        self.db.add(db_submission)
        await self.db.commit()
        await self.db.refresh(db_submission)

        # 4. Trigger External Submission
        submission_ref = await self.corenet.submit_application(
            {
                "agency": submission.agency,
                "submission_type": submission.submission_type,
                "project_ref": project.project_code,
                "payload": submission.model_dump(),
            }
        )

        # 5. Update Record with External Reference
        db_submission.submission_no = submission_ref
        await self.db.commit()
        await self.db.refresh(db_submission)

        return db_submission

    async def update_submission_status(
        self, submission_id: UUID
    ) -> AuthoritySubmission:
        """
        Polls the external service for status updates and persists changes.
        """
        submission = await self.db.get(AuthoritySubmission, submission_id)
        if not submission:
            raise ValueError("Submission not found")

        if not submission.submission_no or submission.status in [
            SubmissionStatus.APPROVED,
            SubmissionStatus.REJECTED,
        ]:
            return submission  # No Update needed

        status_update = await self.corenet.check_submission_status(
            submission.submission_no
        )

        external_status = status_update.get("status") or status_update.get(
            "submission_status"
        )
        mapped_status = status_update.get("mapped_status") or self._map_external_status(
            external_status
        )
        remarks = status_update.get("agency_remarks") or status_update.get("remarks")

        if mapped_status and mapped_status != submission.status:
            submission.status = mapped_status
            if mapped_status == SubmissionStatus.APPROVED:
                submission.approved_at = datetime.utcnow()

            if remarks:
                existing_desc = submission.description or ""
                submission.description = (
                    f"{existing_desc}\n\n[System Update]: {remarks}".strip()
                )

            await self.db.commit()
            await self.db.refresh(submission)

        return submission

    async def get_project_submissions(
        self, project_id: UUID
    ) -> List[AuthoritySubmission]:
        result = await self.db.execute(
            select(AuthoritySubmission)
            .where(AuthoritySubmission.project_id == project_id)
            .order_by(AuthoritySubmission.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_submission(
        self, submission_id: UUID
    ) -> Optional[AuthoritySubmission]:
        return await self.db.get(AuthoritySubmission, submission_id)
