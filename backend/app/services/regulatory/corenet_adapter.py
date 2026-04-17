"""CORENET adapter boundary used by the regulatory service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.schemas.external_sources import ExternalSourceMetadata
from app.services.mock_corenet import MockCorenetService


@dataclass(frozen=True)
class CorenetCapability:
    """Advertised capabilities for the configured CORENET integration."""

    submission_mode_default: str
    live_submission_available: bool
    package_status: str
    package_requirements: tuple[str, ...]
    delivery_blockers: tuple[str, ...]


class CorenetAdapter(Protocol):
    """Adapter contract for submission-prep and live CORENET integrations."""

    def source_metadata(self) -> ExternalSourceMetadata: ...

    def capability(self) -> CorenetCapability: ...

    async def submit_to_agency(
        self,
        agency_code: str,
        submission_type: str,
        project_ref: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]: ...

    async def check_status(
        self, agency_code: str, reference_no: str
    ) -> dict[str, Any]: ...


class SubmissionPrepCorenetAdapter:
    """Submission-prep adapter that makes the mock integration explicit."""

    def __init__(self, delegate: MockCorenetService | None = None) -> None:
        self.delegate = delegate or MockCorenetService()

    def source_metadata(self) -> ExternalSourceMetadata:
        metadata = self.delegate.source_metadata()
        reason = metadata.reason or "CORENET submission-prep mode"
        return metadata.model_copy(
            update={
                "reason": f"{reason}; live submission credentials unavailable, package preparation only"
            }
        )

    def capability(self) -> CorenetCapability:
        return CorenetCapability(
            submission_mode_default="submission_prep",
            live_submission_available=False,
            package_status="submission_ready",
            package_requirements=(
                "Qualified person sign-off",
                "Agency-specific drawing package",
                "Supporting calculation sheets",
                "Applicant and consultant metadata",
            ),
            delivery_blockers=(
                "Live CORENET credentials are not configured",
                "Qualified-person workflow must complete outside this environment",
            ),
        )

    async def submit_to_agency(
        self,
        agency_code: str,
        submission_type: str,
        project_ref: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        response = await self.delegate.submit_to_agency(
            agency_code=agency_code,
            submission_type=submission_type,
            project_ref=project_ref,
            payload=payload,
        )
        capability = self.capability()
        response.update(
            {
                "submission_mode": capability.submission_mode_default,
                "package_status": capability.package_status,
                "package_requirements": list(capability.package_requirements),
                "delivery_blockers": list(capability.delivery_blockers),
                "live_submission_available": capability.live_submission_available,
                "status": capability.package_status,
                "message": (
                    f"Submission-ready package prepared for {agency_code}. "
                    "No live government submission was attempted."
                ),
            }
        )
        return response

    async def check_status(self, agency_code: str, reference_no: str) -> dict[str, Any]:
        response = await self.delegate.check_status(agency_code, reference_no)
        capability = self.capability()
        response.update(
            {
                "submission_mode": capability.submission_mode_default,
                "package_status": capability.package_status,
                "package_requirements": list(capability.package_requirements),
                "delivery_blockers": list(capability.delivery_blockers),
                "live_submission_available": capability.live_submission_available,
            }
        )
        return response


def get_corenet_adapter() -> CorenetAdapter:
    """Return the default CORENET adapter for this deployment."""

    return SubmissionPrepCorenetAdapter()


__all__ = [
    "CorenetAdapter",
    "CorenetCapability",
    "SubmissionPrepCorenetAdapter",
    "get_corenet_adapter",
]
