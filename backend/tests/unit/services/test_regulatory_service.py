import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models.regulatory import (
    AuthoritySubmission,
    RegulatoryAgency,
    SubmissionStatus,
)
from app.models.projects import Project
from app.services.regulatory_service import RegulatoryService
from app.schemas.regulatory import AuthoritySubmissionCreate


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
        project_id=str(project_id), agency="URA", submission_type="DC"
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
            "status": "received",
        }
    )

    # Execute
    result = await service.create_submission(project_id, submission_data)

    # Assert
    assert result.submission_no == "ES2025-MOCK"
    assert result.status == SubmissionStatus.SUBMITTED
    mock_db.add.assert_called()  # Should add submission
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_update_status(service, mock_db):
    # Setup
    submission_id = uuid4()
    agency_code = "BCA"
    submission = AuthoritySubmission(
        id=submission_id,
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
        }
    )

    # Execute
    result = await service.update_submission_status(submission_id)

    # Assert
    assert result.status == SubmissionStatus.APPROVED
    assert result.approved_at is not None
    assert "Approves per code" in result.description
    mock_db.commit.assert_called()
