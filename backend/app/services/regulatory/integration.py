from __future__ import annotations

from typing import Any, Dict

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class CorenetIntegrationService:
    """Integration service for CORENET 2.0 submission workflows."""

    def __init__(self) -> None:
        self.submit_url = settings.CORENET_SUBMIT_URL
        self.status_url = settings.CORENET_STATUS_URL
        self.api_key = settings.CORENET_API_KEY
        self.api_key_header = settings.CORENET_API_KEY_HEADER
        try:
            self.client = httpx.AsyncClient(timeout=settings.CORENET_TIMEOUT_SECONDS)
        except RuntimeError:  # pragma: no cover - httpx stub unavailable
            logger.warning("httpx AsyncClient unavailable; CORENET disabled")
            self.client = None

    def _require_client(self) -> httpx.AsyncClient:
        if self.client is None:
            raise RuntimeError("CORENET HTTP client is unavailable")
        return self.client

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.api_key:
            headers[self.api_key_header] = self.api_key
        return headers

    @staticmethod
    def _normalize_status(payload: Dict[str, Any]) -> Dict[str, Any]:
        submission_no = (
            payload.get("submission_no")
            or payload.get("submissionNo")
            or payload.get("transaction_id")
        )
        status = payload.get("status") or payload.get("submission_status")
        last_updated = payload.get("last_updated") or payload.get("updated_at")
        agency_remarks = payload.get("agency_remarks") or payload.get("remarks")
        return {
            "submission_no": submission_no,
            "status": status,
            "last_updated": last_updated,
            "agency_remarks": agency_remarks,
            **payload,
        }

    async def submit_application(self, payload: Dict[str, Any]) -> str:
        """Submit an application to CORENET and return the submission reference."""
        if not self.submit_url:
            raise RuntimeError("CORENET submit endpoint not configured")
        client = self._require_client()

        response = await client.post(
            self.submit_url, json=payload, headers=self._headers()
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"CORENET submission failed with status {response.status_code}"
            )

        data = response.json()
        submission_no = (
            data.get("submission_no")
            or data.get("submissionNo")
            or data.get("transaction_id")
        )
        if not submission_no:
            raise RuntimeError("CORENET response missing submission reference")
        return str(submission_no)

    async def check_submission_status(self, submission_no: str) -> Dict[str, Any]:
        """Fetch submission status from CORENET for the given reference."""
        if not self.status_url:
            raise RuntimeError("CORENET status endpoint not configured")
        client = self._require_client()

        response = await client.get(
            self.status_url,
            params={"submission_no": submission_no},
            headers=self._headers(),
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"CORENET status request failed with status {response.status_code}"
            )

        payload = response.json()
        if isinstance(payload, dict):
            return self._normalize_status(payload)
        return {"submission_no": submission_no, "status": None, "raw": payload}
