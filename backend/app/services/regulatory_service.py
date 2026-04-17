from datetime import datetime
import inspect
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.audit.ledger import append_event
from app.models.regulatory import (
    AuthoritySubmission,
    RegulatoryAgency,
    SubmissionStatus,
)
from app.models.projects import Project
from app.services.deals.utils import audit_key_from_value
from app.schemas.regulatory import AuthoritySubmissionCreate
from app.services.regulatory.corenet_adapter import (
    CorenetAdapter,
    get_corenet_adapter,
)


class RegulatoryService:
    def __init__(self, db: AsyncSession, corenet: CorenetAdapter | None = None):
        self.db = db
        self.corenet = corenet or get_corenet_adapter()

    async def _load_agency(self, agency_id: UUID | None) -> RegulatoryAgency | None:
        if agency_id is None:
            return None
        return await self._maybe_await(self.db.get(RegulatoryAgency, agency_id))

    async def _stamp_submission_metadata(
        self,
        submission: AuthoritySubmission,
        *,
        agency: RegulatoryAgency | None = None,
    ) -> None:
        resolved_agency = agency or await self._load_agency(
            getattr(submission, "agency_id", None)
        )
        capability = self.corenet.capability()
        submission.integration_status = self.corenet.source_metadata().model_dump(
            mode="json"
        )
        submission.agency_code = resolved_agency.code if resolved_agency else None
        submission.agency_name = resolved_agency.name if resolved_agency else None
        submission.submission_mode = capability.submission_mode_default
        submission.package_status = capability.package_status
        submission.package_requirements = list(capability.package_requirements)
        submission.delivery_blockers = list(capability.delivery_blockers)
        submission.live_submission_available = capability.live_submission_available

    async def _append_submission_audit(
        self,
        *,
        project_id: UUID,
        event_type: str,
        submission: AuthoritySubmission,
        agency: RegulatoryAgency | None,
    ) -> None:
        audit_project_id = audit_key_from_value(project_id)
        if audit_project_id is None:
            return
        await append_event(
            self.db,
            project_id=audit_project_id,
            event_type=event_type,
            context={
                "agency": (
                    agency.code if agency else getattr(submission, "agency_code", None)
                ),
                "agency_name": (
                    agency.name if agency else getattr(submission, "agency_name", None)
                ),
                "submission_id": str(submission.id),
                "submission_no": submission.submission_no,
                "submission_type": str(submission.submission_type),
                "submission_mode": getattr(submission, "submission_mode", None),
                "package_status": getattr(submission, "package_status", None),
                "status": str(submission.status),
            },
        )
        await self._maybe_await(self.db.commit())

    @staticmethod
    async def _maybe_await(value):
        if inspect.isawaitable(value):
            return await value
        return value

    async def create_submission(
        self,
        project_id: UUID,
        submission: AuthoritySubmissionCreate,
        submitted_by_id: Optional[UUID] = None,
    ) -> AuthoritySubmission:
        """
        Creates a submission record and routes it through the configured CORENET adapter.
        """
        capability = self.corenet.capability()
        if (
            submission.submission_mode == "live_submit"
            and not capability.live_submission_available
        ):
            raise ValueError(
                "Live CORENET submission is unavailable; create a submission-ready package instead"
            )

        # 1. Validate Project
        result = await self._maybe_await(
            self.db.execute(select(Project).filter(Project.id == project_id))
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 2. Get or Create Agency (ensure agency exists in DB for FK)
        result = await self._maybe_await(
            self.db.execute(
                select(RegulatoryAgency).filter(
                    RegulatoryAgency.code == submission.agency
                )
            )
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
            await self._maybe_await(self.db.flush())

        # 3. Create Draft Submission Record
        db_submission = AuthoritySubmission(
            project_id=project_id,
            agency_id=agency.id,
            submission_type=submission.submission_type,
            title=f"{submission.agency} Submission for {project.project_code}",
            status=(
                SubmissionStatus.SUBMITTED
                if submission.submission_mode == "live_submit"
                else SubmissionStatus.DRAFT
            ),
            submitted_at=(
                datetime.utcnow()
                if submission.submission_mode == "live_submit"
                else None
            ),
            # submitted_by_id=submitted_by_id # User tracking if available
        )
        self.db.add(db_submission)
        await self._maybe_await(self.db.commit())
        await self._maybe_await(self.db.refresh(db_submission))

        # 4. Trigger External Submission (Mock)
        external_response = await self.corenet.submit_to_agency(
            agency_code=submission.agency,
            submission_type=submission.submission_type,
            project_ref=project.project_code,
            payload=submission.model_dump(),
        )

        # 5. Update Record with External Reference
        if external_response.get("success"):
            db_submission.submission_no = external_response.get("transaction_id")
            if submission.submission_mode == "live_submit":
                db_submission.submitted_at = datetime.utcnow()
            await self._maybe_await(self.db.commit())
            await self._maybe_await(self.db.refresh(db_submission))
        if submission.submission_mode != "live_submit":
            package_status = external_response.get("package_status")
            if package_status:
                existing_desc = db_submission.description or ""
                db_submission.description = (
                    f"{existing_desc}\n\n[Submission Package]: {package_status}".strip()
                )
                await self._maybe_await(self.db.commit())
                await self._maybe_await(self.db.refresh(db_submission))
        db_submission.integration_status = external_response.get("integration_status")
        db_submission.agency_code = agency.code
        db_submission.agency_name = agency.name
        db_submission.submission_mode = external_response.get(
            "submission_mode", capability.submission_mode_default
        )
        db_submission.package_status = external_response.get(
            "package_status", capability.package_status
        )
        db_submission.package_requirements = external_response.get(
            "package_requirements", list(capability.package_requirements)
        )
        db_submission.delivery_blockers = external_response.get(
            "delivery_blockers", list(capability.delivery_blockers)
        )
        db_submission.live_submission_available = external_response.get(
            "live_submission_available", capability.live_submission_available
        )
        await self._append_submission_audit(
            project_id=project_id,
            event_type=(
                "submission_submitted"
                if submission.submission_mode == "live_submit"
                else "submission_packaged"
            ),
            submission=db_submission,
            agency=agency,
        )

        return db_submission

    async def update_submission_status(
        self, submission_id: UUID
    ) -> AuthoritySubmission:
        """
        Polls the mock external service for status updates and persists changes.
        """
        submission = await self._maybe_await(
            self.db.get(AuthoritySubmission, submission_id)
        )
        if not submission:
            raise ValueError("Submission not found")

        capability = self.corenet.capability()

        if submission.status == SubmissionStatus.DRAFT:
            await self._stamp_submission_metadata(submission)
            return submission

        if not submission.submission_no or submission.status in [
            SubmissionStatus.APPROVED,
            SubmissionStatus.REJECTED,
        ]:
            return submission  # No Update needed

        # Fetch agency separately to avoid lazy loading issues in async context
        agency_code = None
        submission_agency = getattr(submission, "agency", None)
        if submission_agency is not None:
            agency_code = getattr(submission_agency, "code", None)
        if agency_code is None and getattr(submission, "agency_id", None) is not None:
            agency = await self._maybe_await(
                self.db.get(RegulatoryAgency, submission.agency_id)
            )
            agency_code = agency.code if agency else None
        if agency_code is None:
            agency_code = "URA"

        # Poll Mock Service
        status_update = await self.corenet.check_status(
            agency_code, submission.submission_no
        )

        mapped_status = status_update.get("mapped_status")
        remarks = status_update.get("remarks")

        if mapped_status and mapped_status != submission.status:
            submission.status = mapped_status
            if mapped_status == SubmissionStatus.APPROVED:
                submission.approved_at = datetime.utcnow()

            if remarks:
                existing_desc = submission.description or ""
                submission.description = (
                    f"{existing_desc}\n\n[System Update]: {remarks}".strip()
                )

            await self._maybe_await(self.db.commit())
            await self._maybe_await(self.db.refresh(submission))

        submission.integration_status = status_update.get("integration_status")
        agency = None
        if agency_code and getattr(submission, "agency_id", None) is not None:
            agency = await self._load_agency(submission.agency_id)
        submission.agency_code = agency.code if agency else agency_code
        submission.agency_name = agency.name if agency else None
        submission.submission_mode = status_update.get(
            "submission_mode", capability.submission_mode_default
        )
        submission.package_status = status_update.get(
            "package_status", capability.package_status
        )
        submission.package_requirements = status_update.get(
            "package_requirements", list(capability.package_requirements)
        )
        submission.delivery_blockers = status_update.get(
            "delivery_blockers", list(capability.delivery_blockers)
        )
        submission.live_submission_available = status_update.get(
            "live_submission_available", capability.live_submission_available
        )
        await self._append_submission_audit(
            project_id=submission.project_id,
            event_type="submission_status_changed",
            submission=submission,
            agency=agency,
        )
        return submission

    async def get_project_submissions(
        self, project_id: UUID
    ) -> List[AuthoritySubmission]:
        result = await self._maybe_await(
            self.db.execute(
                select(AuthoritySubmission)
                .where(AuthoritySubmission.project_id == project_id)
                .order_by(AuthoritySubmission.created_at.desc())
            )
        )
        submissions = list(result.scalars().all())
        for submission in submissions:
            await self._stamp_submission_metadata(submission)
        return submissions

    async def get_submission(
        self, submission_id: UUID
    ) -> Optional[AuthoritySubmission]:
        submission = await self._maybe_await(
            self.db.get(AuthoritySubmission, submission_id)
        )
        if submission is not None:
            await self._stamp_submission_metadata(submission)
        return submission
