from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.projects import Project
from app.models.regulatory import (
    AuthoritySubmission,
    RegulatoryAgency,
    SubmissionStatus,
)
from app.schemas.regulatory import AuthoritySubmissionCreate
from app.services import regulatory_service as regulatory_service_module
from app.services.regulatory_service import RegulatoryService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return RegulatoryService(mock_db)


@pytest.mark.asyncio
async def test_create_submission_success(service, mock_db):
    # Setup
    project_id = uuid4()
    submission_data = AuthoritySubmissionCreate(
        project_id=str(project_id),
        agency="URA",
        submission_type="DC",
        submission_mode="submission_prep",
    )

    # Mocks
    mock_project = Project(id=project_id, project_code="P123")
    mock_agency = RegulatoryAgency(id=uuid4(), code="URA")

    # Configure DB mock returns
    # The service uses:
    #   project = db.execute(select(Project)...).scalar_one_or_none()
    #   agency = db.execute(select(Agency)...).scalar_one_or_none()

    # Simplification: Mocking the scalar_one_or_none chaing is tricky with simple MagicMock
    # We will patch the db.execute return value structure
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.side_effect = [mock_project, mock_agency]
    mock_db.execute.return_value = mock_result

    # Mock Corenet
    service.corenet.submit_to_agency = AsyncMock(
        return_value={
            "success": True,
            "transaction_id": "ES2025-MOCK",
            "status": "submission_ready",
            "submission_mode": "submission_prep",
            "package_status": "submission_ready",
            "package_requirements": ["Qualified person sign-off"],
            "delivery_blockers": ["Live CORENET credentials are not configured"],
            "live_submission_available": False,
            "integration_status": {"provider": "corenet", "state": "mock"},
        }
    )
    service.corenet.capability = MagicMock(
        return_value=MagicMock(
            submission_mode_default="submission_prep",
            live_submission_available=False,
            package_status="submission_ready",
            package_requirements=("Qualified person sign-off",),
            delivery_blockers=("Live CORENET credentials are not configured",),
        )
    )
    append_event_mock = AsyncMock()
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(regulatory_service_module, "append_event", append_event_mock)

    # Execute
    try:
        result = await service.create_submission(project_id, submission_data)
    finally:
        monkeypatch.undo()

    # Assert
    assert result.submission_no == "ES2025-MOCK"
    assert result.status == SubmissionStatus.DRAFT
    assert result.agency_code == "URA"
    assert result.agency_name == mock_agency.name
    assert result.submission_mode == "submission_prep"
    assert result.package_status == "submission_ready"
    assert result.live_submission_available is False
    assert result.integration_status["provider"] == "corenet"
    assert result.integration_status["state"] == "mock"
    append_event_mock.assert_awaited_once()
    assert append_event_mock.await_args.kwargs["event_type"] == "submission_packaged"
    mock_db.add.assert_called()  # Should add submission
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_update_status(service, mock_db):
    # Setup
    submission_id = uuid4()
    project_id = uuid4()
    agency_code = "BCA"
    submission = AuthoritySubmission(
        id=submission_id,
        project_id=project_id,
        submission_no="REF-123",
        status=SubmissionStatus.SUBMITTED,
        agency=RegulatoryAgency(code=agency_code),
    )
    mock_db.get.return_value = submission

    # Mock Corenet
    service.corenet.check_status = AsyncMock(
        return_value={
            "mapped_status": SubmissionStatus.APPROVED,
            "remarks": "Approves per code.",
            "integration_status": {"provider": "corenet", "state": "mock"},
            "submission_mode": "submission_prep",
            "package_status": "submission_ready",
            "package_requirements": ["Qualified person sign-off"],
            "delivery_blockers": ["Live CORENET credentials are not configured"],
            "live_submission_available": False,
        }
    )
    service.corenet.capability = MagicMock(
        return_value=MagicMock(
            submission_mode_default="submission_prep",
            live_submission_available=False,
            package_status="submission_ready",
            package_requirements=("Qualified person sign-off",),
            delivery_blockers=("Live CORENET credentials are not configured",),
        )
    )
    append_event_mock = AsyncMock()
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(regulatory_service_module, "append_event", append_event_mock)

    # Execute
    try:
        result = await service.update_submission_status(submission_id)
    finally:
        monkeypatch.undo()

    # Assert
    assert result.status == SubmissionStatus.APPROVED
    assert result.approved_at is not None
    assert "Approves per code" in result.description
    assert result.agency_code == agency_code
    assert result.integration_status["provider"] == "corenet"
    assert result.integration_status["state"] == "mock"
    append_event_mock.assert_awaited_once()
    assert (
        append_event_mock.await_args.kwargs["event_type"] == "submission_status_changed"
    )
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_create_submission_rejects_live_submit_when_unavailable(service, mock_db):
    project_id = uuid4()
    submission_data = AuthoritySubmissionCreate(
        project_id=str(project_id),
        agency="URA",
        submission_type="DC",
        submission_mode="live_submit",
    )
    service.corenet.capability = MagicMock(
        return_value=MagicMock(
            submission_mode_default="submission_prep",
            live_submission_available=False,
            package_status="submission_ready",
            package_requirements=("Qualified person sign-off",),
            delivery_blockers=("Live CORENET credentials are not configured",),
        )
    )

    with pytest.raises(
        ValueError,
        match="Live CORENET submission is unavailable",
    ):
        await service.create_submission(project_id, submission_data)
