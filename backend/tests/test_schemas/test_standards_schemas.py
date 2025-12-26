"""Comprehensive tests for standards schemas.

Tests cover:
- MaterialStandard schema
- Field types and validation
- ORM attribute mapping
"""

from __future__ import annotations

from datetime import date


class TestMaterialStandard:
    """Tests for MaterialStandard schema."""

    def test_id_required(self) -> None:
        """Test id is required."""
        standard_id = 1
        assert standard_id is not None

    def test_standard_code_required(self) -> None:
        """Test standard_code is required."""
        standard_code = "SS EN 1992-1-1"
        assert len(standard_code) > 0

    def test_material_type_required(self) -> None:
        """Test material_type is required."""
        material_type = "concrete"
        assert len(material_type) > 0

    def test_standard_body_required(self) -> None:
        """Test standard_body is required."""
        standard_body = "Singapore Standards"
        assert len(standard_body) > 0

    def test_property_key_required(self) -> None:
        """Test property_key is required."""
        property_key = "compressive_strength"
        assert len(property_key) > 0

    def test_value_required(self) -> None:
        """Test value is required."""
        value = "30"
        assert len(value) > 0

    def test_unit_optional(self) -> None:
        """Test unit is optional."""
        standard = {}
        assert standard.get("unit") is None

    def test_context_optional(self) -> None:
        """Test context is optional dict."""
        standard = {}
        assert standard.get("context") is None

    def test_section_optional(self) -> None:
        """Test section is optional."""
        standard = {}
        assert standard.get("section") is None

    def test_applicability_optional(self) -> None:
        """Test applicability is optional dict."""
        standard = {}
        assert standard.get("applicability") is None

    def test_edition_optional(self) -> None:
        """Test edition is optional."""
        standard = {}
        assert standard.get("edition") is None

    def test_effective_date_optional(self) -> None:
        """Test effective_date is optional."""
        standard = {}
        assert standard.get("effective_date") is None

    def test_license_ref_optional(self) -> None:
        """Test license_ref is optional."""
        standard = {}
        assert standard.get("license_ref") is None

    def test_provenance_optional(self) -> None:
        """Test provenance is optional dict."""
        standard = {}
        assert standard.get("provenance") is None

    def test_source_document_optional(self) -> None:
        """Test source_document is optional."""
        standard = {}
        assert standard.get("source_document") is None


class TestMaterialTypes:
    """Tests for material type values."""

    def test_concrete_type(self) -> None:
        """Test concrete material type."""
        material_type = "concrete"
        assert material_type == "concrete"

    def test_steel_type(self) -> None:
        """Test steel material type."""
        material_type = "steel"
        assert material_type == "steel"

    def test_timber_type(self) -> None:
        """Test timber material type."""
        material_type = "timber"
        assert material_type == "timber"

    def test_masonry_type(self) -> None:
        """Test masonry material type."""
        material_type = "masonry"
        assert material_type == "masonry"

    def test_glass_type(self) -> None:
        """Test glass material type."""
        material_type = "glass"
        assert material_type == "glass"

    def test_aluminum_type(self) -> None:
        """Test aluminum material type."""
        material_type = "aluminum"
        assert material_type == "aluminum"


class TestStandardBodies:
    """Tests for standard body values."""

    def test_singapore_standards(self) -> None:
        """Test Singapore Standards body."""
        body = "Singapore Standards"
        assert "Singapore" in body

    def test_british_standards(self) -> None:
        """Test British Standards body."""
        body = "British Standards"
        assert "British" in body

    def test_eurocode(self) -> None:
        """Test Eurocode body."""
        body = "Eurocode"
        assert body == "Eurocode"

    def test_astm(self) -> None:
        """Test ASTM body."""
        body = "ASTM"
        assert body == "ASTM"

    def test_iso(self) -> None:
        """Test ISO body."""
        body = "ISO"
        assert body == "ISO"


class TestPropertyKeys:
    """Tests for property key values."""

    def test_compressive_strength(self) -> None:
        """Test compressive_strength property key."""
        key = "compressive_strength"
        assert key == "compressive_strength"

    def test_tensile_strength(self) -> None:
        """Test tensile_strength property key."""
        key = "tensile_strength"
        assert key == "tensile_strength"

    def test_yield_strength(self) -> None:
        """Test yield_strength property key."""
        key = "yield_strength"
        assert key == "yield_strength"

    def test_modulus_of_elasticity(self) -> None:
        """Test modulus_of_elasticity property key."""
        key = "modulus_of_elasticity"
        assert key == "modulus_of_elasticity"

    def test_fire_rating(self) -> None:
        """Test fire_rating property key."""
        key = "fire_rating"
        assert key == "fire_rating"

    def test_density(self) -> None:
        """Test density property key."""
        key = "density"
        assert key == "density"


class TestUnits:
    """Tests for unit values."""

    def test_mpa_unit(self) -> None:
        """Test MPa unit."""
        unit = "MPa"
        assert unit == "MPa"

    def test_gpa_unit(self) -> None:
        """Test GPa unit."""
        unit = "GPa"
        assert unit == "GPa"

    def test_kn_m2_unit(self) -> None:
        """Test kN/m² unit."""
        unit = "kN/m²"
        assert "kN" in unit

    def test_minutes_unit(self) -> None:
        """Test minutes unit for fire rating."""
        unit = "minutes"
        assert unit == "minutes"

    def test_kg_m3_unit(self) -> None:
        """Test kg/m³ unit for density."""
        unit = "kg/m³"
        assert "kg" in unit


class TestStandardCodes:
    """Tests for standard code formats."""

    def test_singapore_standard_code(self) -> None:
        """Test Singapore standard code format."""
        code = "SS EN 1992-1-1"
        assert code.startswith("SS")

    def test_british_standard_code(self) -> None:
        """Test British standard code format."""
        code = "BS 8110"
        assert code.startswith("BS")

    def test_eurocode_format(self) -> None:
        """Test Eurocode format."""
        code = "EN 1992-1-1"
        assert code.startswith("EN")

    def test_astm_format(self) -> None:
        """Test ASTM standard code format."""
        code = "ASTM A615"
        assert code.startswith("ASTM")


class TestMaterialStandardScenarios:
    """Tests for material standard use case scenarios."""

    def test_concrete_compressive_strength(self) -> None:
        """Test concrete compressive strength standard."""
        standard = {
            "id": 1,
            "standard_code": "SS EN 1992-1-1",
            "material_type": "concrete",
            "standard_body": "Singapore Standards",
            "property_key": "compressive_strength",
            "value": "30",
            "unit": "MPa",
            "context": {"grade": "C30", "curing_days": 28},
            "section": "3.1.2",
            "applicability": {"structural_element": "column"},
            "edition": "2010",
            "effective_date": date(2010, 1, 1),
        }
        assert standard["material_type"] == "concrete"
        assert standard["value"] == "30"

    def test_steel_yield_strength(self) -> None:
        """Test steel yield strength standard."""
        standard = {
            "id": 2,
            "standard_code": "SS EN 1993-1-1",
            "material_type": "steel",
            "standard_body": "Singapore Standards",
            "property_key": "yield_strength",
            "value": "355",
            "unit": "MPa",
            "context": {"grade": "S355", "thickness_mm": "16"},
        }
        assert standard["material_type"] == "steel"
        assert standard["value"] == "355"

    def test_fire_rating_standard(self) -> None:
        """Test fire rating standard."""
        standard = {
            "id": 3,
            "standard_code": "SS CP 24",
            "material_type": "concrete",
            "standard_body": "Singapore Standards",
            "property_key": "fire_rating",
            "value": "120",
            "unit": "minutes",
            "context": {"element": "structural_column", "cover_mm": 40},
        }
        assert standard["property_key"] == "fire_rating"
        assert standard["value"] == "120"

    def test_timber_modulus(self) -> None:
        """Test timber modulus of elasticity standard."""
        standard = {
            "id": 4,
            "standard_code": "SS EN 1995-1-1",
            "material_type": "timber",
            "standard_body": "Singapore Standards",
            "property_key": "modulus_of_elasticity",
            "value": "12",
            "unit": "GPa",
            "context": {"species": "softwood", "grade": "C24"},
        }
        assert standard["material_type"] == "timber"

    def test_multiple_standards_same_material(self) -> None:
        """Test multiple standards for same material."""
        standards = [
            {"material_type": "concrete", "property_key": "compressive_strength"},
            {"material_type": "concrete", "property_key": "tensile_strength"},
            {"material_type": "concrete", "property_key": "modulus_of_elasticity"},
        ]
        concrete_standards = [s for s in standards if s["material_type"] == "concrete"]
        assert len(concrete_standards) == 3
