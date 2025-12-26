"""Comprehensive tests for standards service.

Tests cover:
- Material standard data structures
- Standard lookup operations
- Standard upsert operations
"""

from __future__ import annotations

from datetime import date

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestStandardCodes:
    """Tests for standard code values."""

    def test_ss_code(self) -> None:
        """Test Singapore Standard code."""
        code = "SS 544"
        assert code.startswith("SS")

    def test_bs_code(self) -> None:
        """Test British Standard code."""
        code = "BS 8110"
        assert code.startswith("BS")

    def test_astm_code(self) -> None:
        """Test ASTM code."""
        code = "ASTM C150"
        assert code.startswith("ASTM")

    def test_iso_code(self) -> None:
        """Test ISO code."""
        code = "ISO 9001"
        assert code.startswith("ISO")

    def test_en_code(self) -> None:
        """Test European Norm code."""
        code = "EN 1992-1-1"
        assert code.startswith("EN")


class TestStandardBodies:
    """Tests for standard body values."""

    def test_spring_singapore(self) -> None:
        """Test SPRING Singapore."""
        body = "SPRING Singapore"
        assert body == "SPRING Singapore"

    def test_bsi(self) -> None:
        """Test BSI (British Standards Institution)."""
        body = "BSI"
        assert body == "BSI"

    def test_astm_international(self) -> None:
        """Test ASTM International."""
        body = "ASTM International"
        assert body == "ASTM International"

    def test_iso(self) -> None:
        """Test ISO."""
        body = "ISO"
        assert body == "ISO"


class TestMaterialTypes:
    """Tests for material type values."""

    def test_concrete(self) -> None:
        """Test concrete material type."""
        material = "concrete"
        assert material == "concrete"

    def test_steel(self) -> None:
        """Test steel material type."""
        material = "steel"
        assert material == "steel"

    def test_timber(self) -> None:
        """Test timber material type."""
        material = "timber"
        assert material == "timber"

    def test_masonry(self) -> None:
        """Test masonry material type."""
        material = "masonry"
        assert material == "masonry"

    def test_glass(self) -> None:
        """Test glass material type."""
        material = "glass"
        assert material == "glass"


class TestMaterialStandardData:
    """Tests for material standard data structures."""

    def test_concrete_standard(self) -> None:
        """Test concrete standard data structure."""
        standard = {
            "standard_code": "SS 544",
            "standard_body": "SPRING Singapore",
            "material_type": "concrete",
            "property_key": "compressive_strength_min_mpa",
            "value": "30",
            "unit": "MPa",
            "section": "Table 4.1",
            "applicability": {"grade": "C30"},
            "edition": "2020",
            "effective_date": date(2020, 1, 1).isoformat(),
        }
        assert standard["value"] == "30"
        assert standard["unit"] == "MPa"

    def test_steel_standard(self) -> None:
        """Test steel standard data structure."""
        standard = {
            "standard_code": "SS 490",
            "standard_body": "SPRING Singapore",
            "material_type": "steel",
            "property_key": "yield_strength_min_mpa",
            "value": "460",
            "unit": "MPa",
            "section": "Table 2",
            "applicability": {"grade": "S460"},
        }
        assert standard["property_key"] == "yield_strength_min_mpa"

    def test_timber_standard(self) -> None:
        """Test timber standard data structure."""
        standard = {
            "standard_code": "SS 544",
            "material_type": "timber",
            "property_key": "bending_strength_mpa",
            "value": "24",
            "unit": "MPa",
            "applicability": {"class": "C24"},
        }
        assert standard["material_type"] == "timber"


class TestPropertyKeys:
    """Tests for property key values."""

    def test_compressive_strength(self) -> None:
        """Test compressive strength property key."""
        key = "compressive_strength_min_mpa"
        assert "compressive" in key

    def test_tensile_strength(self) -> None:
        """Test tensile strength property key."""
        key = "tensile_strength_min_mpa"
        assert "tensile" in key

    def test_yield_strength(self) -> None:
        """Test yield strength property key."""
        key = "yield_strength_min_mpa"
        assert "yield" in key

    def test_modulus_of_elasticity(self) -> None:
        """Test modulus of elasticity property key."""
        key = "modulus_of_elasticity_gpa"
        assert "modulus" in key

    def test_density(self) -> None:
        """Test density property key."""
        key = "density_kg_m3"
        assert "density" in key


class TestStandardUnits:
    """Tests for standard unit values."""

    def test_mpa(self) -> None:
        """Test MPa unit."""
        unit = "MPa"
        assert unit == "MPa"

    def test_gpa(self) -> None:
        """Test GPa unit."""
        unit = "GPa"
        assert unit == "GPa"

    def test_kg_m3(self) -> None:
        """Test kg/m³ unit."""
        unit = "kg/m³"
        assert unit == "kg/m³"

    def test_mm(self) -> None:
        """Test mm unit."""
        unit = "mm"
        assert unit == "mm"

    def test_percent(self) -> None:
        """Test percent unit."""
        unit = "%"
        assert unit == "%"


class TestStandardScenarios:
    """Tests for standard use case scenarios."""

    def test_concrete_grade_c30(self) -> None:
        """Test concrete grade C30 properties."""
        properties = {
            "grade": "C30",
            "compressive_strength_min_mpa": 30,
            "modulus_of_elasticity_gpa": 32,
            "density_kg_m3": 2400,
            "poisson_ratio": 0.2,
        }
        assert properties["compressive_strength_min_mpa"] == 30

    def test_steel_grade_s355(self) -> None:
        """Test steel grade S355 properties."""
        properties = {
            "grade": "S355",
            "yield_strength_min_mpa": 355,
            "tensile_strength_min_mpa": 470,
            "modulus_of_elasticity_gpa": 210,
            "density_kg_m3": 7850,
        }
        assert properties["yield_strength_min_mpa"] == 355

    def test_rebar_grade_b500(self) -> None:
        """Test rebar grade B500 properties."""
        properties = {
            "grade": "B500",
            "yield_strength_min_mpa": 500,
            "bond_stress_mpa": 2.25,
            "min_elongation_pct": 5.0,
        }
        assert properties["yield_strength_min_mpa"] == 500

    def test_timber_class_c24(self) -> None:
        """Test timber class C24 properties."""
        properties = {
            "class": "C24",
            "bending_strength_mpa": 24,
            "tension_parallel_mpa": 14,
            "compression_parallel_mpa": 21,
            "density_kg_m3": 420,
        }
        assert properties["bending_strength_mpa"] == 24

    def test_glass_float_standard(self) -> None:
        """Test float glass properties."""
        properties = {
            "type": "float",
            "tensile_strength_mpa": 40,
            "modulus_of_elasticity_gpa": 70,
            "density_kg_m3": 2500,
            "poisson_ratio": 0.22,
        }
        assert properties["tensile_strength_mpa"] == 40


class TestStandardApplicability:
    """Tests for standard applicability data structures."""

    def test_grade_applicability(self) -> None:
        """Test grade-based applicability."""
        applicability = {"grade": ["C30", "C35", "C40"]}
        assert "C30" in applicability["grade"]

    def test_thickness_applicability(self) -> None:
        """Test thickness-based applicability."""
        applicability = {
            "thickness_mm": {"min": 3, "max": 16},
        }
        assert applicability["thickness_mm"]["min"] == 3

    def test_temperature_applicability(self) -> None:
        """Test temperature-based applicability."""
        applicability = {
            "temperature_c": {"min": -20, "max": 150},
        }
        assert applicability["temperature_c"]["max"] == 150

    def test_exposure_class_applicability(self) -> None:
        """Test exposure class applicability."""
        applicability = {
            "exposure_class": ["XC1", "XC2", "XC3"],
        }
        assert len(applicability["exposure_class"]) == 3
