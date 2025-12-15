import logging
import asyncio
import random
from datetime import datetime
from typing import Dict, Any
from app.models.regulatory import AgencyCode, SubmissionStatus

logger = logging.getLogger(__name__)


class MockCorenetService:
    """
    Simulates interaction with Singapore's CORENET (Construction and Real Estate Network)
    and individual agency APIs (URA, BCA, etc.) which are not yet publicly accessible.
    """

    def __init__(self):
        self.mock_delay_ms = 500  # Simulate network latency

    async def submit_to_agency(
        self,
        agency_code: str,
        submission_type: str,
        project_ref: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Simulates POST /submission to an agency.
        Returns a transaction ID and initial status.
        """
        await asyncio.sleep(self.mock_delay_ms / 1000)

        logger.info(
            f"Mocking submission to {agency_code} ({submission_type}) for project {project_ref}"
        )

        # Generate a realistic-looking agency reference number
        ref_no = self._generate_ref_no(agency_code, submission_type)

        return {
            "success": True,
            "transaction_id": ref_no,
            "status": "received",  # External system status
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Submission received by {agency_code}. Reference: {ref_no}",
        }

    async def check_status(self, agency_code: str, reference_no: str) -> Dict[str, Any]:
        """
        Simulates GET /status/{reference_no}.
        Randomly progresses the status to simulate a real workflow.
        """
        await asyncio.sleep(self.mock_delay_ms / 1000)

        # Randomly determine status based on some "hash" of the ref number to be deterministic-ish
        # or just random for demo purposes.
        # For demo, we want to see it move from Pending -> Processing -> Approved

        # Simple simulation:
        # New -> Processing (80%)
        # Processing -> Approved (60%), RFI (20%), Rejected (10%), Still Processing (10%)

        status_options = [
            ("processing", "Application is being reviewed by a rigorous officer."),
            (
                "approved",
                "Application satisfies all requirements. Written Permission granted.",
            ),
            ("rfi", "Pending clarification on Gross Floor Area calculations."),
            ("rejected", "Non-compliant with Master Plan 2024 height controls."),
        ]

        # Deterministic override for testing specific scenarios if ref_no ends with certain digit
        if reference_no.endswith("00"):
            s, m = "approved", "Auto-approved for demo."
        elif reference_no.endswith("99"):
            s, m = "rejected", "Rejected for demo purposes."
        else:
            s, m = random.choice(status_options)

        return {
            "reference_no": reference_no,
            "agency_code": agency_code,
            "external_status": s,
            "mapped_status": self._map_external_status(s),
            "remarks": m,
            "last_updated": datetime.utcnow().isoformat(),
        }

    def _generate_ref_no(self, agency: str, type_code: str) -> str:
        date_str = datetime.now().strftime("%y%m%d")
        rand = random.randint(1000, 9999)
        if agency == AgencyCode.URA:
            return f"ES{date_str}-{rand}K"
        elif agency == AgencyCode.BCA:
            return f"A{date_str}-{rand}-BP"
        else:
            return f"{agency}-{date_str}-{rand}"

    def _map_external_status(self, external_status: str) -> str:
        """Maps agency-specific status strings to our internal enum."""
        external_status = external_status.lower()
        if "approved" in external_status:
            return SubmissionStatus.APPROVED
        if "rejected" in external_status:
            return SubmissionStatus.REJECTED
        if "rfi" in external_status or "clarification" in external_status:
            return SubmissionStatus.RFI
        if "processing" in external_status or "received" in external_status:
            return SubmissionStatus.IN_REVIEW
        return SubmissionStatus.SUBMITTED
