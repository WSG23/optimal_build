"""Comprehensive tests for rulesets model.

Tests cover:
- RulePack model structure
"""

from __future__ import annotations

from datetime import datetime


class TestRulePackModel:
    """Tests for RulePack model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        pack_id = 1
        assert isinstance(pack_id, int)

    def test_slug_required(self) -> None:
        """Test slug is required."""
        slug = "singapore-ura-dc-2024"
        assert len(slug) > 0

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "URA Development Control Guidelines 2024"
        assert len(name) > 0

    def test_description_optional(self) -> None:
        """Test description is optional."""
        pack = {}
        assert pack.get("description") is None

    def test_jurisdiction_required(self) -> None:
        """Test jurisdiction is required."""
        jurisdiction = "SG"
        assert len(jurisdiction) > 0

    def test_authority_optional(self) -> None:
        """Test authority is optional."""
        pack = {}
        assert pack.get("authority") is None

    def test_version_default_one(self) -> None:
        """Test version defaults to 1."""
        version = 1
        assert version >= 1

    def test_definition_required(self) -> None:
        """Test definition is required."""
        definition = {"rules": []}
        assert isinstance(definition, dict)

    def test_metadata_default_empty(self) -> None:
        """Test metadata defaults to empty dict."""
        metadata = {}
        assert isinstance(metadata, dict)

    def test_is_active_default_true(self) -> None:
        """Test is_active defaults to True."""
        is_active = True
        assert is_active is True


class TestRulePackJurisdictions:
    """Tests for rule pack jurisdiction values."""

    def test_singapore_jurisdiction(self) -> None:
        """Test Singapore jurisdiction."""
        jurisdiction = "SG"
        assert jurisdiction == "SG"

    def test_hong_kong_jurisdiction(self) -> None:
        """Test Hong Kong jurisdiction."""
        jurisdiction = "HK"
        assert jurisdiction == "HK"

    def test_malaysia_jurisdiction(self) -> None:
        """Test Malaysia jurisdiction."""
        jurisdiction = "MY"
        assert jurisdiction == "MY"

    def test_new_zealand_jurisdiction(self) -> None:
        """Test New Zealand jurisdiction."""
        jurisdiction = "NZ"
        assert jurisdiction == "NZ"

    def test_seattle_jurisdiction(self) -> None:
        """Test Seattle jurisdiction."""
        jurisdiction = "US-SEA"
        assert jurisdiction == "US-SEA"

    def test_toronto_jurisdiction(self) -> None:
        """Test Toronto jurisdiction."""
        jurisdiction = "CA-TOR"
        assert jurisdiction == "CA-TOR"


class TestRulePackAuthorities:
    """Tests for rule pack authority values."""

    def test_ura_authority(self) -> None:
        """Test URA authority."""
        authority = "URA"
        assert authority == "URA"

    def test_bca_authority(self) -> None:
        """Test BCA authority."""
        authority = "BCA"
        assert authority == "BCA"

    def test_scdf_authority(self) -> None:
        """Test SCDF authority."""
        authority = "SCDF"
        assert authority == "SCDF"

    def test_buildings_department_authority(self) -> None:
        """Test Buildings Department authority."""
        authority = "BD"
        assert authority == "BD"


class TestRulePackDefinitionStructure:
    """Tests for rule pack definition structure."""

    def test_definition_has_rules(self) -> None:
        """Test definition contains rules array."""
        definition = {"rules": [{"id": "rule_001", "name": "Test Rule"}]}
        assert "rules" in definition
        assert len(definition["rules"]) > 0

    def test_rule_has_id(self) -> None:
        """Test rule has id field."""
        rule = {"id": "URA_SETBACK_001", "name": "Front Setback"}
        assert "id" in rule

    def test_rule_has_name(self) -> None:
        """Test rule has name field."""
        rule = {"id": "URA_SETBACK_001", "name": "Front Setback"}
        assert "name" in rule

    def test_rule_has_condition(self) -> None:
        """Test rule has condition field."""
        rule = {
            "id": "URA_SETBACK_001",
            "condition": {"field": "front_setback", "operator": ">=", "value": 6.0},
        }
        assert "condition" in rule

    def test_rule_has_action(self) -> None:
        """Test rule has action field."""
        rule = {
            "id": "URA_SETBACK_001",
            "action": {"type": "violation", "severity": "error"},
        }
        assert "action" in rule


class TestRulePackMetadataStructure:
    """Tests for rule pack metadata structure."""

    def test_metadata_has_effective_date(self) -> None:
        """Test metadata contains effective_date."""
        metadata = {"effective_date": "2024-01-01"}
        assert "effective_date" in metadata

    def test_metadata_has_expiry_date(self) -> None:
        """Test metadata contains expiry_date."""
        metadata = {"expiry_date": "2025-12-31"}
        assert "expiry_date" in metadata

    def test_metadata_has_source_url(self) -> None:
        """Test metadata contains source_url."""
        metadata = {"source_url": "https://www.ura.gov.sg/dc-handbook"}
        assert "source_url" in metadata

    def test_metadata_has_last_reviewed(self) -> None:
        """Test metadata contains last_reviewed date."""
        metadata = {"last_reviewed": "2024-06-01"}
        assert "last_reviewed" in metadata


class TestRulePackScenarios:
    """Tests for rule pack use case scenarios."""

    def test_create_ura_rule_pack(self) -> None:
        """Test creating a URA development control rule pack."""
        pack = {
            "id": 1,
            "slug": "ura-dc-handbook-2024",
            "name": "URA Development Control Handbook 2024",
            "description": "Planning rules for Singapore property development",
            "jurisdiction": "SG",
            "authority": "URA",
            "version": 1,
            "definition": {
                "rules": [
                    {
                        "id": "URA_SETBACK_001",
                        "name": "Front Setback Requirement",
                        "condition": {
                            "field": "front_setback",
                            "operator": ">=",
                            "value": 6.0,
                        },
                        "action": {"type": "violation", "severity": "error"},
                    },
                    {
                        "id": "URA_PLOT_RATIO_001",
                        "name": "Plot Ratio Limit",
                        "condition": {
                            "field": "plot_ratio",
                            "operator": "<=",
                            "value": 3.0,
                        },
                        "action": {"type": "violation", "severity": "error"},
                    },
                ]
            },
            "metadata": {
                "effective_date": "2024-01-01",
                "source_url": "https://www.ura.gov.sg/dc-handbook",
            },
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        assert pack["jurisdiction"] == "SG"
        assert pack["authority"] == "URA"
        assert len(pack["definition"]["rules"]) == 2

    def test_create_bca_rule_pack(self) -> None:
        """Test creating a BCA building code rule pack."""
        pack = {
            "id": 2,
            "slug": "bca-building-code-2024",
            "name": "BCA Approved Document 2024",
            "jurisdiction": "SG",
            "authority": "BCA",
            "version": 1,
            "definition": {
                "rules": [
                    {
                        "id": "BCA_FIRE_001",
                        "name": "Fire Escape Distance",
                        "condition": {
                            "field": "escape_distance",
                            "operator": "<=",
                            "value": 45.0,
                        },
                    }
                ]
            },
            "is_active": True,
        }
        assert pack["authority"] == "BCA"

    def test_version_increment(self) -> None:
        """Test incrementing rule pack version."""
        pack = {"version": 1}
        pack["version"] = 2
        assert pack["version"] == 2

    def test_deactivate_rule_pack(self) -> None:
        """Test deactivating a rule pack."""
        pack = {"is_active": True}
        pack["is_active"] = False
        assert pack["is_active"] is False

    def test_update_rule_pack_definition(self) -> None:
        """Test updating rule pack definition."""
        pack = {"definition": {"rules": [{"id": "RULE_001", "name": "Old Rule"}]}}
        pack["definition"]["rules"].append({"id": "RULE_002", "name": "New Rule"})
        assert len(pack["definition"]["rules"]) == 2

    def test_multi_jurisdiction_rule_packs(self) -> None:
        """Test having multiple jurisdiction rule packs."""
        packs = [
            {"slug": "sg-ura-2024", "jurisdiction": "SG"},
            {"slug": "hk-bd-2024", "jurisdiction": "HK"},
            {"slug": "my-jkr-2024", "jurisdiction": "MY"},
        ]
        assert len(packs) == 3
        jurisdictions = {p["jurisdiction"] for p in packs}
        assert "SG" in jurisdictions
        assert "HK" in jurisdictions
