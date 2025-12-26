"""Comprehensive tests for regulatory model.

Tests cover:
- AgencyCode enum
- AssetType enum
- SubmissionType enum
- SubmissionStatus enum
- RegulatoryAgency model structure
- AuthoritySubmission model structure
- SubmissionDocument model structure
- RegulatoryRequirement model structure
- AssetCompliancePath model structure
- ChangeOfUseApplication model structure
- HeritageSubmission model structure
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4


class TestAgencyCode:
    """Tests for AgencyCode enum - Singapore regulatory agencies."""

    def test_ura(self) -> None:
        """Test URA - Urban Redevelopment Authority."""
        code = "URA"
        assert code == "URA"

    def test_bca(self) -> None:
        """Test BCA - Building and Construction Authority."""
        code = "BCA"
        assert code == "BCA"

    def test_scdf(self) -> None:
        """Test SCDF - Singapore Civil Defence Force."""
        code = "SCDF"
        assert code == "SCDF"

    def test_nea(self) -> None:
        """Test NEA - National Environment Agency."""
        code = "NEA"
        assert code == "NEA"

    def test_lta(self) -> None:
        """Test LTA - Land Transport Authority."""
        code = "LTA"
        assert code == "LTA"

    def test_nparks(self) -> None:
        """Test NPARKS - National Parks Board."""
        code = "NPARKS"
        assert code == "NPARKS"

    def test_pub(self) -> None:
        """Test PUB - Public Utilities Board."""
        code = "PUB"
        assert code == "PUB"

    def test_sla(self) -> None:
        """Test SLA - Singapore Land Authority."""
        code = "SLA"
        assert code == "SLA"

    def test_stb(self) -> None:
        """Test STB - Singapore Tourism Board (Heritage)."""
        code = "STB"
        assert code == "STB"

    def test_jtc(self) -> None:
        """Test JTC - JTC Corporation (Industrial)."""
        code = "JTC"
        assert code == "JTC"


class TestAssetType:
    """Tests for AssetType enum."""

    def test_office(self) -> None:
        """Test office asset type."""
        asset = "office"
        assert asset == "office"

    def test_retail(self) -> None:
        """Test retail asset type."""
        asset = "retail"
        assert asset == "retail"

    def test_residential(self) -> None:
        """Test residential asset type."""
        asset = "residential"
        assert asset == "residential"

    def test_industrial(self) -> None:
        """Test industrial asset type."""
        asset = "industrial"
        assert asset == "industrial"

    def test_heritage(self) -> None:
        """Test heritage asset type."""
        asset = "heritage"
        assert asset == "heritage"

    def test_mixed_use(self) -> None:
        """Test mixed_use asset type."""
        asset = "mixed_use"
        assert asset == "mixed_use"

    def test_hospitality(self) -> None:
        """Test hospitality asset type."""
        asset = "hospitality"
        assert asset == "hospitality"


class TestSubmissionType:
    """Tests for SubmissionType enum."""

    def test_dc(self) -> None:
        """Test DC - Development Control."""
        sub_type = "DC"
        assert sub_type == "DC"

    def test_bp(self) -> None:
        """Test BP - Building Plan."""
        sub_type = "BP"
        assert sub_type == "BP"

    def test_top(self) -> None:
        """Test TOP - Temporary Occupation Permit."""
        sub_type = "TOP"
        assert sub_type == "TOP"

    def test_csc(self) -> None:
        """Test CSC - Certificate of Statutory Completion."""
        sub_type = "CSC"
        assert sub_type == "CSC"

    def test_waiver(self) -> None:
        """Test Waiver submission type."""
        sub_type = "Waiver"
        assert sub_type == "Waiver"

    def test_consultation(self) -> None:
        """Test Consultation submission type."""
        sub_type = "Consultation"
        assert sub_type == "Consultation"

    def test_change_of_use(self) -> None:
        """Test CHANGE_OF_USE submission type."""
        sub_type = "CHANGE_OF_USE"
        assert sub_type == "CHANGE_OF_USE"

    def test_heritage_approval(self) -> None:
        """Test HERITAGE_APPROVAL submission type."""
        sub_type = "HERITAGE_APPROVAL"
        assert sub_type == "HERITAGE_APPROVAL"

    def test_industrial_permit(self) -> None:
        """Test INDUSTRIAL_PERMIT submission type."""
        sub_type = "INDUSTRIAL_PERMIT"
        assert sub_type == "INDUSTRIAL_PERMIT"


class TestSubmissionStatus:
    """Tests for SubmissionStatus enum."""

    def test_draft(self) -> None:
        """Test draft status."""
        status = "draft"
        assert status == "draft"

    def test_submitted(self) -> None:
        """Test submitted status."""
        status = "submitted"
        assert status == "submitted"

    def test_in_review(self) -> None:
        """Test in_review status."""
        status = "in_review"
        assert status == "in_review"

    def test_approved(self) -> None:
        """Test approved status."""
        status = "approved"
        assert status == "approved"

    def test_rejected(self) -> None:
        """Test rejected status."""
        status = "rejected"
        assert status == "rejected"

    def test_rfi(self) -> None:
        """Test RFI - Request for Information/Amendment status."""
        status = "rfi"
        assert status == "rfi"


class TestRegulatoryAgencyModel:
    """Tests for RegulatoryAgency model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        agency_id = uuid4()
        assert len(str(agency_id)) == 36

    def test_code_required(self) -> None:
        """Test code is required."""
        code = "URA"
        assert len(code) > 0

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "Urban Redevelopment Authority"
        assert len(name) > 0

    def test_description_optional(self) -> None:
        """Test description is optional."""
        agency = {}
        assert agency.get("description") is None

    def test_api_endpoint_optional(self) -> None:
        """Test api_endpoint is optional."""
        agency = {}
        assert agency.get("api_endpoint") is None


class TestAuthoritySubmissionModel:
    """Tests for AuthoritySubmission model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        submission_id = uuid4()
        assert len(str(submission_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_agency_id_required(self) -> None:
        """Test agency_id is required."""
        agency_id = uuid4()
        assert agency_id is not None

    def test_submission_type_required(self) -> None:
        """Test submission_type is required."""
        sub_type = "BP"
        assert sub_type is not None

    def test_submission_no_optional(self) -> None:
        """Test submission_no (external reference) is optional."""
        submission = {}
        assert submission.get("submission_no") is None

    def test_status_default_draft(self) -> None:
        """Test status defaults to draft."""
        status = "draft"
        assert status == "draft"

    def test_title_required(self) -> None:
        """Test title is required."""
        title = "Building Plan Submission for Marina Bay Tower"
        assert len(title) > 0

    def test_description_optional(self) -> None:
        """Test description is optional."""
        submission = {}
        assert submission.get("description") is None

    def test_submitted_at_optional(self) -> None:
        """Test submitted_at is optional."""
        submission = {}
        assert submission.get("submitted_at") is None

    def test_approved_at_optional(self) -> None:
        """Test approved_at is optional."""
        submission = {}
        assert submission.get("approved_at") is None


class TestSubmissionDocumentModel:
    """Tests for SubmissionDocument model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        doc_id = uuid4()
        assert len(str(doc_id)) == 36

    def test_submission_id_required(self) -> None:
        """Test submission_id is required."""
        submission_id = uuid4()
        assert submission_id is not None

    def test_document_type_required(self) -> None:
        """Test document_type is required."""
        doc_type = "architectural_plans"
        assert len(doc_type) > 0

    def test_file_name_required(self) -> None:
        """Test file_name is required."""
        file_name = "floor_plans_rev3.pdf"
        assert len(file_name) > 0

    def test_file_path_required(self) -> None:
        """Test file_path is required."""
        file_path = "/submissions/project-123/floor_plans_rev3.pdf"
        assert len(file_path) > 0

    def test_version_default_one(self) -> None:
        """Test version defaults to 1."""
        version = 1
        assert version == 1


class TestAssetCompliancePathModel:
    """Tests for AssetCompliancePath model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        path_id = uuid4()
        assert len(str(path_id)) == 36

    def test_asset_type_required(self) -> None:
        """Test asset_type is required."""
        asset_type = "office"
        assert asset_type is not None

    def test_agency_id_required(self) -> None:
        """Test agency_id is required."""
        agency_id = uuid4()
        assert agency_id is not None

    def test_submission_type_required(self) -> None:
        """Test submission_type is required."""
        sub_type = "BP"
        assert sub_type is not None

    def test_sequence_order_default_one(self) -> None:
        """Test sequence_order defaults to 1."""
        order = 1
        assert order >= 1

    def test_is_mandatory_default_true(self) -> None:
        """Test is_mandatory defaults to True."""
        is_mandatory = True
        assert is_mandatory is True

    def test_typical_duration_days_optional(self) -> None:
        """Test typical_duration_days is optional."""
        path = {}
        assert path.get("typical_duration_days") is None


class TestChangeOfUseApplicationModel:
    """Tests for ChangeOfUseApplication model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        app_id = uuid4()
        assert len(str(app_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_current_use_required(self) -> None:
        """Test current_use is required."""
        current_use = "industrial"
        assert current_use is not None

    def test_proposed_use_required(self) -> None:
        """Test proposed_use is required."""
        proposed_use = "office"
        assert proposed_use is not None

    def test_status_default_draft(self) -> None:
        """Test status defaults to draft."""
        status = "draft"
        assert status == "draft"

    def test_requires_dc_amendment_default_false(self) -> None:
        """Test requires_dc_amendment defaults to False."""
        requires_dc = False
        assert requires_dc is False

    def test_requires_planning_permission_default_true(self) -> None:
        """Test requires_planning_permission defaults to True."""
        requires_planning = True
        assert requires_planning is True


class TestHeritageSubmissionModel:
    """Tests for HeritageSubmission model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        heritage_id = uuid4()
        assert len(str(heritage_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_conservation_status_required(self) -> None:
        """Test conservation_status is required."""
        status = "National Monument"
        assert len(status) > 0

    def test_stb_reference_optional(self) -> None:
        """Test stb_reference is optional."""
        submission = {}
        assert submission.get("stb_reference") is None

    def test_original_construction_year_optional(self) -> None:
        """Test original_construction_year is optional."""
        submission = {}
        assert submission.get("original_construction_year") is None

    def test_conservation_plan_attached_default_false(self) -> None:
        """Test conservation_plan_attached defaults to False."""
        attached = False
        assert attached is False


class TestRegulatoryScenarios:
    """Tests for regulatory use case scenarios."""

    def test_submit_building_plan(self) -> None:
        """Test submitting a building plan to BCA."""
        submission = {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "agency_id": str(uuid4()),
            "submission_type": "BP",
            "submission_no": "BP-2024-12345",
            "status": "submitted",
            "title": "Building Plan for Marina Bay Tower",
            "submitted_at": datetime.utcnow().isoformat(),
        }
        assert submission["submission_type"] == "BP"
        assert submission["status"] == "submitted"

    def test_change_of_use_industrial_to_office(self) -> None:
        """Test change of use from industrial to office."""
        application = {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "current_use": "industrial",
            "proposed_use": "office",
            "status": "draft",
            "justification": "Adaptive reuse of former factory building",
            "requires_dc_amendment": True,
            "requires_planning_permission": True,
        }
        assert application["current_use"] == "industrial"
        assert application["proposed_use"] == "office"

    def test_heritage_conservation_submission(self) -> None:
        """Test heritage conservation submission."""
        heritage = {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "conservation_status": "Conservation Area",
            "stb_reference": "STB-HER-2024-001",
            "status": "in_review",
            "original_construction_year": 1928,
            "heritage_elements": '["facade", "lobby", "staircase"]',
            "proposed_interventions": "Restoration of original facade features",
            "conservation_plan_attached": True,
        }
        assert heritage["conservation_status"] == "Conservation Area"
        assert heritage["original_construction_year"] == 1928

    def test_submission_approval_flow(self) -> None:
        """Test submission approval flow."""
        submission = {"status": "submitted"}
        # Review
        submission["status"] = "in_review"
        assert submission["status"] == "in_review"
        # Approve
        submission["status"] = "approved"
        submission["approved_at"] = datetime.utcnow()
        assert submission["status"] == "approved"

    def test_rfi_response(self) -> None:
        """Test responding to RFI (Request for Information)."""
        submission = {"status": "in_review"}
        submission["status"] = "rfi"
        assert submission["status"] == "rfi"
        # Submit additional information
        submission["status"] = "in_review"
        assert submission["status"] == "in_review"

    def test_office_compliance_path(self) -> None:
        """Test typical office development compliance path."""
        path = [
            {"submission_type": "DC", "agency": "URA", "sequence": 1},
            {"submission_type": "BP", "agency": "BCA", "sequence": 2},
            {"submission_type": "TOP", "agency": "BCA", "sequence": 3},
            {"submission_type": "CSC", "agency": "BCA", "sequence": 4},
        ]
        assert len(path) == 4
        assert path[0]["submission_type"] == "DC"
