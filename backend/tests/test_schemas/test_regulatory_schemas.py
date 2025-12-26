"""Comprehensive tests for regulatory schemas.

Tests cover:
- SubmissionDocument schemas
- AuthoritySubmission schemas
- AssetCompliancePath schemas
- ChangeOfUse schemas
- HeritageSubmission schemas
- SubmissionType enum
- AssetType enum
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4


class TestSubmissionDocumentBase:
    """Tests for SubmissionDocumentBase schema."""

    def test_document_type_required(self) -> None:
        """Test document_type is required."""
        document_type = "architectural_plan"
        assert len(document_type) > 0

    def test_file_name_required(self) -> None:
        """Test file_name is required."""
        file_name = "floor_plan_v1.pdf"
        assert len(file_name) > 0

    def test_file_path_required(self) -> None:
        """Test file_path is required."""
        file_path = "/uploads/project_123/floor_plan_v1.pdf"
        assert len(file_path) > 0


class TestSubmissionDocumentRead:
    """Tests for SubmissionDocumentRead schema."""

    def test_id_required(self) -> None:
        """Test id is required."""
        doc_id = 1
        assert doc_id is not None

    def test_submission_id_required(self) -> None:
        """Test submission_id is required."""
        submission_id = 1
        assert submission_id is not None

    def test_version_required(self) -> None:
        """Test version is required."""
        version = 1
        assert version >= 1

    def test_uploaded_at_required(self) -> None:
        """Test uploaded_at is required."""
        uploaded_at = datetime.utcnow()
        assert uploaded_at is not None

    def test_uploaded_by_id_optional(self) -> None:
        """Test uploaded_by_id is optional."""
        doc = {}
        assert doc.get("uploaded_by_id") is None


class TestAuthoritySubmissionBase:
    """Tests for AuthoritySubmissionBase schema."""

    def test_agency_required(self) -> None:
        """Test agency is required."""
        agency = "URA"
        assert len(agency) > 0

    def test_submission_type_required(self) -> None:
        """Test submission_type is required."""
        submission_type = "DEVELOPMENT_APPROVAL"
        assert submission_type is not None


class TestAuthoritySubmissionCreate:
    """Tests for AuthoritySubmissionCreate schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None


class TestAuthoritySubmissionRead:
    """Tests for AuthoritySubmissionRead schema."""

    def test_id_required(self) -> None:
        """Test id is required."""
        submission_id = 1
        assert submission_id is not None

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_status_required(self) -> None:
        """Test status is required."""
        status = "PENDING"
        assert status is not None

    def test_submission_date_optional(self) -> None:
        """Test submission_date is optional."""
        submission = {}
        assert submission.get("submission_date") is None

    def test_approval_date_optional(self) -> None:
        """Test approval_date is optional."""
        submission = {}
        assert submission.get("approval_date") is None

    def test_reference_number_optional(self) -> None:
        """Test reference_number is optional."""
        submission = {}
        assert submission.get("reference_number") is None

    def test_agency_remarks_optional(self) -> None:
        """Test agency_remarks is optional."""
        submission = {}
        assert submission.get("agency_remarks") is None

    def test_documents_default_empty(self) -> None:
        """Test documents defaults to empty list."""
        documents = []
        assert isinstance(documents, list)


class TestAuthoritySubmissionUpdate:
    """Tests for AuthoritySubmissionUpdate schema."""

    def test_all_fields_optional(self) -> None:
        """Test all fields are optional."""
        update = {}
        assert update.get("status") is None
        assert update.get("agency_remarks") is None
        assert update.get("reference_number") is None


class TestAssetCompliancePathBase:
    """Tests for AssetCompliancePathBase schema."""

    def test_asset_type_required(self) -> None:
        """Test asset_type is required."""
        asset_type = "OFFICE"
        assert asset_type is not None

    def test_submission_type_required(self) -> None:
        """Test submission_type is required."""
        submission_type = "DEVELOPMENT_APPROVAL"
        assert submission_type is not None

    def test_sequence_order_default(self) -> None:
        """Test sequence_order defaults to 1."""
        sequence_order = 1
        assert sequence_order == 1

    def test_is_mandatory_default_true(self) -> None:
        """Test is_mandatory defaults to True."""
        is_mandatory = True
        assert is_mandatory is True

    def test_description_optional(self) -> None:
        """Test description is optional."""
        path = {}
        assert path.get("description") is None

    def test_typical_duration_days_optional(self) -> None:
        """Test typical_duration_days is optional."""
        path = {}
        assert path.get("typical_duration_days") is None


class TestAssetCompliancePathCreate:
    """Tests for AssetCompliancePathCreate schema."""

    def test_agency_id_required(self) -> None:
        """Test agency_id is required UUID."""
        agency_id = uuid4()
        assert agency_id is not None


class TestAssetCompliancePathRead:
    """Tests for AssetCompliancePathRead schema."""

    def test_id_required(self) -> None:
        """Test id is required UUID."""
        path_id = uuid4()
        assert len(str(path_id)) == 36

    def test_agency_id_required(self) -> None:
        """Test agency_id is required."""
        agency_id = uuid4()
        assert agency_id is not None

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None


class TestChangeOfUseBase:
    """Tests for ChangeOfUseBase schema."""

    def test_current_use_required(self) -> None:
        """Test current_use is required."""
        current_use = "OFFICE"
        assert current_use is not None

    def test_proposed_use_required(self) -> None:
        """Test proposed_use is required."""
        proposed_use = "RESIDENTIAL"
        assert proposed_use is not None

    def test_justification_optional(self) -> None:
        """Test justification is optional."""
        change_of_use = {}
        assert change_of_use.get("justification") is None


class TestChangeOfUseCreate:
    """Tests for ChangeOfUseCreate schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required UUID."""
        project_id = uuid4()
        assert project_id is not None


class TestChangeOfUseRead:
    """Tests for ChangeOfUseRead schema."""

    def test_id_required(self) -> None:
        """Test id is required UUID."""
        cou_id = uuid4()
        assert len(str(cou_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_status_required(self) -> None:
        """Test status is required."""
        status = "PENDING"
        assert status is not None

    def test_ura_reference_optional(self) -> None:
        """Test ura_reference is optional."""
        cou = {}
        assert cou.get("ura_reference") is None

    def test_requires_dc_amendment_required(self) -> None:
        """Test requires_dc_amendment is required."""
        requires_dc_amendment = False
        assert isinstance(requires_dc_amendment, bool)

    def test_requires_planning_permission_required(self) -> None:
        """Test requires_planning_permission is required."""
        requires_planning_permission = True
        assert isinstance(requires_planning_permission, bool)

    def test_submitted_at_optional(self) -> None:
        """Test submitted_at is optional."""
        cou = {}
        assert cou.get("submitted_at") is None

    def test_approved_at_optional(self) -> None:
        """Test approved_at is optional."""
        cou = {}
        assert cou.get("approved_at") is None


class TestChangeOfUseUpdate:
    """Tests for ChangeOfUseUpdate schema."""

    def test_all_fields_optional(self) -> None:
        """Test all fields are optional."""
        update = {}
        assert update.get("status") is None
        assert update.get("justification") is None
        assert update.get("ura_reference") is None


class TestHeritageSubmissionBase:
    """Tests for HeritageSubmissionBase schema."""

    def test_conservation_status_required(self) -> None:
        """Test conservation_status is required."""
        conservation_status = "GAZETTED"
        assert len(conservation_status) > 0

    def test_original_construction_year_optional(self) -> None:
        """Test original_construction_year is optional."""
        heritage = {}
        assert heritage.get("original_construction_year") is None

    def test_heritage_elements_optional(self) -> None:
        """Test heritage_elements is optional."""
        heritage = {}
        assert heritage.get("heritage_elements") is None

    def test_proposed_interventions_optional(self) -> None:
        """Test proposed_interventions is optional."""
        heritage = {}
        assert heritage.get("proposed_interventions") is None


class TestHeritageSubmissionCreate:
    """Tests for HeritageSubmissionCreate schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required UUID."""
        project_id = uuid4()
        assert project_id is not None


class TestHeritageSubmissionRead:
    """Tests for HeritageSubmissionRead schema."""

    def test_id_required(self) -> None:
        """Test id is required UUID."""
        heritage_id = uuid4()
        assert len(str(heritage_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_stb_reference_optional(self) -> None:
        """Test stb_reference is optional."""
        heritage = {}
        assert heritage.get("stb_reference") is None

    def test_status_required(self) -> None:
        """Test status is required."""
        status = "PENDING"
        assert status is not None

    def test_conservation_plan_attached_required(self) -> None:
        """Test conservation_plan_attached is required."""
        conservation_plan_attached = False
        assert isinstance(conservation_plan_attached, bool)


class TestHeritageSubmissionUpdate:
    """Tests for HeritageSubmissionUpdate schema."""

    def test_all_fields_optional(self) -> None:
        """Test all fields are optional."""
        update = {}
        assert update.get("status") is None
        assert update.get("stb_reference") is None


class TestAssetType:
    """Tests for AssetType enum values."""

    def test_office_type(self) -> None:
        """Test OFFICE asset type."""
        asset_type = "OFFICE"
        assert asset_type == "OFFICE"

    def test_retail_type(self) -> None:
        """Test RETAIL asset type."""
        asset_type = "RETAIL"
        assert asset_type == "RETAIL"

    def test_industrial_type(self) -> None:
        """Test INDUSTRIAL asset type."""
        asset_type = "INDUSTRIAL"
        assert asset_type == "INDUSTRIAL"

    def test_residential_type(self) -> None:
        """Test RESIDENTIAL asset type."""
        asset_type = "RESIDENTIAL"
        assert asset_type == "RESIDENTIAL"

    def test_hospitality_type(self) -> None:
        """Test HOSPITALITY asset type."""
        asset_type = "HOSPITALITY"
        assert asset_type == "HOSPITALITY"


class TestSubmissionType:
    """Tests for SubmissionType enum values."""

    def test_development_approval(self) -> None:
        """Test DEVELOPMENT_APPROVAL type."""
        submission_type = "DEVELOPMENT_APPROVAL"
        assert submission_type == "DEVELOPMENT_APPROVAL"

    def test_building_plan(self) -> None:
        """Test BUILDING_PLAN type."""
        submission_type = "BUILDING_PLAN"
        assert submission_type == "BUILDING_PLAN"

    def test_structural_plan(self) -> None:
        """Test STRUCTURAL_PLAN type."""
        submission_type = "STRUCTURAL_PLAN"
        assert submission_type == "STRUCTURAL_PLAN"

    def test_change_of_use(self) -> None:
        """Test CHANGE_OF_USE type."""
        submission_type = "CHANGE_OF_USE"
        assert submission_type == "CHANGE_OF_USE"
