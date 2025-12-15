import random
import string
from typing import Dict, Any
from datetime import datetime
import asyncio


class CorenetIntegrationService:
    """
    Mock service to simulate interaction with Singapore's CORENET 2.0 API.
    Since we don't have real credentials, this service simulates:
    1. Submission acknowledgement (generating a transaction ID)
    2. Status checking (randomly advancing status for demo purposes)
    """

    @staticmethod
    async def submit_application(payload: Dict[str, Any]) -> str:
        """
        Simulate submitting an application to CORENET.
        Returns a mock Transaction ID (e.g., "ES20251207-12345")
        """
        # Simulate network latency
        await asyncio.sleep(1)

        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = "".join(random.choices(string.digits, k=5))
        return f"ES{timestamp}-{random_suffix}"

    @staticmethod
    async def check_submission_status(submission_no: str) -> Dict[str, Any]:
        """
        Simulate checking status from CORENET.
        Returns a dict with 'status' and 'last_updated'.
        """
        # Mock logic: deterministically return status based on the submission number suffix
        # This allows for consistent manual testing scenarios:
        # Ends in 0-2: Processing/Pending
        # Ends in 3: Pending Amendment (RFI)
        # Ends in 4-8: Approved
        # Ends in 9: Rejected

        try:
            # Extract last digit from the numeric part
            numeric_part = submission_no.split("-")[1]
            trigger_val = int(numeric_part[-1])
        except (IndexError, ValueError):
            trigger_val = 0

        if trigger_val <= 2:
            status = "Processing"
        elif trigger_val == 3:
            status = "Pending Amendment"
        elif trigger_val <= 8:
            status = "Approved"
        else:
            status = "Rejected"

        return {
            "submission_no": submission_no,
            "status": status,
            "last_updated": datetime.now().isoformat(),
            "agency_remarks": "Mock CORENET response. Triggered by ID suffix.",
        }
