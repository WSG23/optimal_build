"""Multi-jurisdiction financing structures.

Provides jurisdiction-specific financing parameters and constraints:
- Singapore: LTV limits, ABSD (Additional Buyer's Stamp Duty)
- New Zealand: LVR (Loan-to-Value Ratio), CCCFA compliance
- USA (Seattle): DSCR requirements, Fannie/Freddie conforming limits
- Canada (Toronto): CMHC insurance, B-20 stress testing
- Hong Kong: IO-heavy structures, high LTV developer loans
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


class JurisdictionCode(str, Enum):
    """Supported jurisdiction codes for financing."""

    SG = "SG"  # Singapore
    NZ = "NZ"  # New Zealand
    SEA = "SEA"  # Seattle, Washington, USA
    TOR = "TOR"  # Toronto, Ontario, Canada
    HK = "HK"  # Hong Kong


class PropertyType(str, Enum):
    """Property types affecting financing terms."""

    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    DEVELOPMENT = "development"


class BorrowerType(str, Enum):
    """Borrower classification affecting financing terms."""

    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    DEVELOPER = "developer"
    REIT = "reit"
    FOREIGN = "foreign"


@dataclass
class FinancingConstraints:
    """Jurisdiction-specific financing constraints."""

    max_ltv: Decimal  # Maximum Loan-to-Value ratio
    max_ltc: Decimal  # Maximum Loan-to-Cost ratio
    min_dscr: Decimal  # Minimum Debt Service Coverage Ratio
    min_equity_pct: Decimal  # Minimum equity contribution
    stress_test_rate: Optional[Decimal] = None  # Rate buffer for stress testing
    max_amortization_years: int = 30
    interest_only_allowed: bool = True
    max_io_period_months: int = 36
    notes: List[str] = field(default_factory=list)


@dataclass
class StampDutyRates:
    """Stamp duty / transfer tax rates by property type."""

    base_rate_pct: Decimal
    additional_rate_pct: Decimal = Decimal("0")  # For foreign/second property
    absd_rate_pct: Decimal = Decimal("0")  # Singapore ABSD
    notes: List[str] = field(default_factory=list)


@dataclass
class JurisdictionFinancingProfile:
    """Complete financing profile for a jurisdiction."""

    jurisdiction: JurisdictionCode
    currency: str
    base_rate_name: str  # e.g., "SORA", "OCR", "SOFR", "CORRA", "HIBOR"
    typical_spread_bps: int  # Typical margin over base rate
    constraints: Dict[PropertyType, FinancingConstraints]
    stamp_duty: Dict[PropertyType, StampDutyRates]
    regulatory_notes: List[str] = field(default_factory=list)


# Singapore Financing Profile
SG_CONSTRAINTS = {
    PropertyType.RESIDENTIAL: FinancingConstraints(
        max_ltv=Decimal("0.75"),  # 75% for first property
        max_ltc=Decimal("0.80"),
        min_dscr=Decimal("1.25"),
        min_equity_pct=Decimal("0.25"),
        stress_test_rate=Decimal("0.035"),  # 3.5% stress test buffer
        max_amortization_years=35,
        interest_only_allowed=False,
        notes=[
            "MAS TDSR limits total debt servicing to 55% of income",
            "Lower LTV (55%) for second and subsequent properties",
            "Foreigners face 60% ABSD on residential",
        ],
    ),
    PropertyType.COMMERCIAL: FinancingConstraints(
        max_ltv=Decimal("0.80"),
        max_ltc=Decimal("0.80"),
        min_dscr=Decimal("1.30"),
        min_equity_pct=Decimal("0.20"),
        max_amortization_years=25,
        interest_only_allowed=True,
        max_io_period_months=24,
        notes=["No ABSD for commercial properties", "Interest-only typically 2 years"],
    ),
    PropertyType.DEVELOPMENT: FinancingConstraints(
        max_ltv=Decimal("0.70"),
        max_ltc=Decimal("0.65"),
        min_dscr=Decimal("1.35"),
        min_equity_pct=Decimal("0.35"),
        max_amortization_years=5,  # Construction period
        interest_only_allowed=True,
        max_io_period_months=60,
        notes=[
            "Development loans typically 60-65% LTC",
            "Draw-down structure based on construction milestones",
        ],
    ),
}

SG_STAMP_DUTY = {
    PropertyType.RESIDENTIAL: StampDutyRates(
        base_rate_pct=Decimal("4.0"),  # BSD up to 4%
        absd_rate_pct=Decimal("20.0"),  # 20% for PR second property
        notes=[
            "BSD: 1% (first $180k), 2% (next $180k), 3% (next $640k), 4% (remainder)",
            "ABSD: Citizens 20% (2nd+), PR 30% (2nd+), Foreigners 60%",
        ],
    ),
    PropertyType.COMMERCIAL: StampDutyRates(
        base_rate_pct=Decimal("3.0"),
        notes=["BSD only, no ABSD for commercial"],
    ),
}

SG_PROFILE = JurisdictionFinancingProfile(
    jurisdiction=JurisdictionCode.SG,
    currency="SGD",
    base_rate_name="SORA",
    typical_spread_bps=150,  # SORA + 1.50%
    constraints=SG_CONSTRAINTS,
    stamp_duty=SG_STAMP_DUTY,
    regulatory_notes=[
        "MAS regulates lending via TDSR and LTV limits",
        "Property cooling measures reviewed quarterly",
        "QC/ABSD regime affects foreign buyers",
    ],
)


# New Zealand Financing Profile
NZ_CONSTRAINTS = {
    PropertyType.RESIDENTIAL: FinancingConstraints(
        max_ltv=Decimal("0.80"),  # 80% LVR for owner-occupiers
        max_ltc=Decimal("0.80"),
        min_dscr=Decimal("1.20"),
        min_equity_pct=Decimal("0.20"),
        stress_test_rate=Decimal("0.035"),  # CCCFA stress test
        max_amortization_years=30,
        interest_only_allowed=True,
        max_io_period_months=60,
        notes=[
            "RBNZ LVR restrictions: 80% for owner-occupied, 65% for investors",
            "CCCFA requires affordability assessment at stressed rates",
            "Interest-only limited for investment properties",
        ],
    ),
    PropertyType.COMMERCIAL: FinancingConstraints(
        max_ltv=Decimal("0.70"),
        max_ltc=Decimal("0.70"),
        min_dscr=Decimal("1.40"),
        min_equity_pct=Decimal("0.30"),
        max_amortization_years=20,
        interest_only_allowed=True,
        max_io_period_months=36,
        notes=["Commercial lending more conservative post-COVID"],
    ),
    PropertyType.DEVELOPMENT: FinancingConstraints(
        max_ltv=Decimal("0.65"),
        max_ltc=Decimal("0.60"),
        min_dscr=Decimal("1.50"),
        min_equity_pct=Decimal("0.40"),
        max_amortization_years=3,
        interest_only_allowed=True,
        max_io_period_months=36,
        notes=["Development finance typically requires 40%+ equity"],
    ),
}

NZ_STAMP_DUTY = {
    PropertyType.RESIDENTIAL: StampDutyRates(
        base_rate_pct=Decimal("0"),  # No stamp duty in NZ
        notes=["No stamp duty/transfer tax in New Zealand"],
    ),
}

NZ_PROFILE = JurisdictionFinancingProfile(
    jurisdiction=JurisdictionCode.NZ,
    currency="NZD",
    base_rate_name="OCR",
    typical_spread_bps=250,  # OCR + 2.50% for floating
    constraints=NZ_CONSTRAINTS,
    stamp_duty=NZ_STAMP_DUTY,
    regulatory_notes=[
        "RBNZ LVR restrictions apply to all mortgage lending",
        "CCCFA (Credit Contracts and Consumer Finance Act) compliance required",
        "Overseas Investment Act restricts foreign residential purchases",
    ],
)


# Seattle/USA Financing Profile
SEA_CONSTRAINTS = {
    PropertyType.RESIDENTIAL: FinancingConstraints(
        max_ltv=Decimal("0.80"),  # Conforming limit
        max_ltc=Decimal("0.80"),
        min_dscr=Decimal("1.00"),  # Personal guarantee often used
        min_equity_pct=Decimal("0.20"),
        max_amortization_years=30,
        interest_only_allowed=True,
        max_io_period_months=120,  # 10-year IO common
        notes=[
            "Conforming loan limits apply ($766,550 in King County 2024)",
            "Jumbo loans require higher down payments",
            "DSCR loans available for investors",
        ],
    ),
    PropertyType.COMMERCIAL: FinancingConstraints(
        max_ltv=Decimal("0.75"),
        max_ltc=Decimal("0.75"),
        min_dscr=Decimal("1.25"),
        min_equity_pct=Decimal("0.25"),
        max_amortization_years=25,
        interest_only_allowed=True,
        max_io_period_months=60,
        notes=["SBA 504 loans available for owner-occupied"],
    ),
    PropertyType.DEVELOPMENT: FinancingConstraints(
        max_ltv=Decimal("0.65"),
        max_ltc=Decimal("0.65"),
        min_dscr=Decimal("1.20"),
        min_equity_pct=Decimal("0.35"),
        max_amortization_years=3,
        interest_only_allowed=True,
        max_io_period_months=36,
        notes=[
            "Construction-to-perm loans common",
            "Recourse typically required during construction",
        ],
    ),
}

SEA_STAMP_DUTY = {
    PropertyType.RESIDENTIAL: StampDutyRates(
        base_rate_pct=Decimal("1.78"),  # WA REET
        notes=[
            "Washington Real Estate Excise Tax (REET) 1.78% base",
            "Additional 0.25% for properties > $500k",
        ],
    ),
}

SEA_PROFILE = JurisdictionFinancingProfile(
    jurisdiction=JurisdictionCode.SEA,
    currency="USD",
    base_rate_name="SOFR",
    typical_spread_bps=200,  # SOFR + 2.00%
    constraints=SEA_CONSTRAINTS,
    stamp_duty=SEA_STAMP_DUTY,
    regulatory_notes=[
        "Fannie Mae/Freddie Mac guidelines for conforming loans",
        "DSCR investor loans becoming popular",
        "No prepayment penalties on residential owner-occupied",
    ],
)


# Toronto/Canada Financing Profile
TOR_CONSTRAINTS = {
    PropertyType.RESIDENTIAL: FinancingConstraints(
        max_ltv=Decimal("0.80"),  # 80% with CMHC insurance
        max_ltc=Decimal("0.80"),
        min_dscr=Decimal("1.00"),
        min_equity_pct=Decimal("0.20"),
        stress_test_rate=Decimal(
            "0.02"
        ),  # B-20 stress test (higher of contract+2% or 5.25%)
        max_amortization_years=30,  # 25 for insured
        interest_only_allowed=False,  # Not for insured mortgages
        notes=[
            "CMHC insurance required for LTV > 80%",
            "B-20 stress test at contract rate + 2%",
            "Max 25-year amortization for insured mortgages",
        ],
    ),
    PropertyType.COMMERCIAL: FinancingConstraints(
        max_ltv=Decimal("0.75"),
        max_ltc=Decimal("0.75"),
        min_dscr=Decimal("1.30"),
        min_equity_pct=Decimal("0.25"),
        max_amortization_years=25,
        interest_only_allowed=True,
        max_io_period_months=24,
        notes=["CMHC MLI Select for affordable housing"],
    ),
    PropertyType.DEVELOPMENT: FinancingConstraints(
        max_ltv=Decimal("0.65"),
        max_ltc=Decimal("0.65"),
        min_dscr=Decimal("1.25"),
        min_equity_pct=Decimal("0.35"),
        max_amortization_years=3,
        interest_only_allowed=True,
        max_io_period_months=36,
        notes=["Construction financing typically 60-65% LTC"],
    ),
}

TOR_STAMP_DUTY = {
    PropertyType.RESIDENTIAL: StampDutyRates(
        base_rate_pct=Decimal("2.5"),  # Ontario LTT
        additional_rate_pct=Decimal("2.0"),  # Toronto Municipal LTT
        notes=[
            "Ontario Land Transfer Tax: marginal rates up to 2.5%",
            "Toronto Municipal LTT: additional 2% (marginal)",
            "Foreign buyer ban for residential (temporary)",
        ],
    ),
}

TOR_PROFILE = JurisdictionFinancingProfile(
    jurisdiction=JurisdictionCode.TOR,
    currency="CAD",
    base_rate_name="CORRA",
    typical_spread_bps=175,  # Prime - 0.25% to Prime + 0.50%
    constraints=TOR_CONSTRAINTS,
    stamp_duty=TOR_STAMP_DUTY,
    regulatory_notes=[
        "OSFI B-20 mortgage underwriting guidelines",
        "CMHC mortgage insurance for high-ratio mortgages",
        "Foreign buyer prohibition (extended to 2027)",
    ],
)


# Hong Kong Financing Profile
HK_CONSTRAINTS = {
    PropertyType.RESIDENTIAL: FinancingConstraints(
        max_ltv=Decimal("0.90"),  # Up to 90% with HKMC insurance
        max_ltc=Decimal("0.90"),
        min_dscr=Decimal("1.00"),
        min_equity_pct=Decimal("0.10"),
        stress_test_rate=Decimal("0.03"),  # 3% stress test
        max_amortization_years=30,
        interest_only_allowed=True,  # Common in HK
        max_io_period_months=36,
        notes=[
            "HKMA LTV limits: 90% (< HK$10M), 80% (HK$10-15M), 70% (> HK$15M)",
            "Mortgage insurance required for LTV > 60%",
            "H+/P- floating rates common",
        ],
    ),
    PropertyType.COMMERCIAL: FinancingConstraints(
        max_ltv=Decimal("0.50"),  # Conservative commercial LTV
        max_ltc=Decimal("0.50"),
        min_dscr=Decimal("1.50"),
        min_equity_pct=Decimal("0.50"),
        max_amortization_years=15,
        interest_only_allowed=True,
        max_io_period_months=60,  # IO-heavy structures common
        notes=[
            "Commercial LTV caps at 40-50%",
            "HIBOR-based floating rates prevalent",
        ],
    ),
    PropertyType.DEVELOPMENT: FinancingConstraints(
        max_ltv=Decimal("0.60"),
        max_ltc=Decimal("0.55"),
        min_dscr=Decimal("1.40"),
        min_equity_pct=Decimal("0.45"),
        max_amortization_years=5,
        interest_only_allowed=True,
        max_io_period_months=60,
        notes=[
            "Developer loans typically IO during construction",
            "Presale proceeds often required as condition",
        ],
    ),
}

HK_STAMP_DUTY = {
    PropertyType.RESIDENTIAL: StampDutyRates(
        base_rate_pct=Decimal("4.25"),  # AVD
        additional_rate_pct=Decimal("15.0"),  # BSD for non-permanent residents
        notes=[
            "Ad Valorem Stamp Duty (AVD) up to 4.25%",
            "Buyer's Stamp Duty (BSD) 15% for non-permanent residents",
            "Special Stamp Duty (SSD) for resales within 36 months",
        ],
    ),
}

HK_PROFILE = JurisdictionFinancingProfile(
    jurisdiction=JurisdictionCode.HK,
    currency="HKD",
    base_rate_name="HIBOR",
    typical_spread_bps=130,  # H+1.30% common
    constraints=HK_CONSTRAINTS,
    stamp_duty=HK_STAMP_DUTY,
    regulatory_notes=[
        "HKMA prudential measures on mortgage lending",
        "HKMC mortgage insurance program",
        "Property cooling measures reviewed by Financial Secretary",
    ],
)


# Registry of all jurisdiction profiles
JURISDICTION_PROFILES: Dict[JurisdictionCode, JurisdictionFinancingProfile] = {
    JurisdictionCode.SG: SG_PROFILE,
    JurisdictionCode.NZ: NZ_PROFILE,
    JurisdictionCode.SEA: SEA_PROFILE,
    JurisdictionCode.TOR: TOR_PROFILE,
    JurisdictionCode.HK: HK_PROFILE,
}


class JurisdictionFinancingService:
    """Service for applying jurisdiction-specific financing rules."""

    def __init__(self) -> None:
        self._profiles = JURISDICTION_PROFILES

    def get_profile(
        self, jurisdiction: JurisdictionCode | str
    ) -> JurisdictionFinancingProfile:
        """Get the financing profile for a jurisdiction."""
        if isinstance(jurisdiction, str):
            jurisdiction = JurisdictionCode(jurisdiction.upper())
        profile = self._profiles.get(jurisdiction)
        if not profile:
            raise ValueError(f"Unknown jurisdiction: {jurisdiction}")
        return profile

    def get_constraints(
        self,
        jurisdiction: JurisdictionCode | str,
        property_type: PropertyType | str = PropertyType.RESIDENTIAL,
    ) -> FinancingConstraints:
        """Get financing constraints for a jurisdiction and property type."""
        profile = self.get_profile(jurisdiction)
        if isinstance(property_type, str):
            property_type = PropertyType(property_type.lower())

        constraints = profile.constraints.get(property_type)
        if not constraints:
            # Fall back to residential constraints
            constraints = profile.constraints.get(PropertyType.RESIDENTIAL)
            if not constraints:
                raise ValueError(
                    f"No constraints for {property_type} in {jurisdiction}"
                )
        return constraints

    def calculate_stamp_duty(
        self,
        jurisdiction: JurisdictionCode | str,
        property_value: Decimal,
        property_type: PropertyType | str = PropertyType.RESIDENTIAL,
        is_foreign_buyer: bool = False,
    ) -> Dict[str, Any]:
        """Calculate stamp duty / transfer taxes."""
        profile = self.get_profile(jurisdiction)
        if isinstance(property_type, str):
            property_type = PropertyType(property_type.lower())

        rates = profile.stamp_duty.get(property_type)
        if not rates:
            rates = profile.stamp_duty.get(PropertyType.RESIDENTIAL)

        if not rates:
            return {
                "base_duty": Decimal("0"),
                "additional_duty": Decimal("0"),
                "total_duty": Decimal("0"),
                "effective_rate_pct": Decimal("0"),
                "notes": [],
            }

        base_duty = property_value * (rates.base_rate_pct / Decimal("100"))
        additional_duty = Decimal("0")

        if is_foreign_buyer:
            additional_duty = property_value * (
                (rates.additional_rate_pct + rates.absd_rate_pct) / Decimal("100")
            )

        total_duty = base_duty + additional_duty
        effective_rate = (total_duty / property_value * Decimal("100")).quantize(
            Decimal("0.01")
        )

        return {
            "base_duty": base_duty.quantize(Decimal("0.01")),
            "additional_duty": additional_duty.quantize(Decimal("0.01")),
            "total_duty": total_duty.quantize(Decimal("0.01")),
            "effective_rate_pct": effective_rate,
            "notes": list(rates.notes),
            "currency": profile.currency,
        }

    def validate_financing_structure(
        self,
        jurisdiction: JurisdictionCode | str,
        property_type: PropertyType | str,
        property_value: Decimal,
        loan_amount: Decimal,
        noi: Decimal,
        debt_service: Decimal,
    ) -> Dict[str, Any]:
        """Validate a financing structure against jurisdiction rules."""
        constraints = self.get_constraints(jurisdiction, property_type)

        ltv = loan_amount / property_value if property_value else Decimal("0")
        dscr = noi / debt_service if debt_service else Decimal("999")
        equity_pct = Decimal("1") - ltv

        violations = []
        warnings = []

        if ltv > constraints.max_ltv:
            violations.append(
                f"LTV {ltv:.1%} exceeds maximum {constraints.max_ltv:.1%}"
            )

        if dscr < constraints.min_dscr:
            violations.append(
                f"DSCR {dscr:.2f} below minimum {constraints.min_dscr:.2f}"
            )

        if equity_pct < constraints.min_equity_pct:
            violations.append(
                f"Equity {equity_pct:.1%} below minimum {constraints.min_equity_pct:.1%}"
            )

        # Add jurisdiction-specific notes as warnings
        for note in constraints.notes:
            warnings.append(note)

        return {
            "is_compliant": len(violations) == 0,
            "ltv": ltv.quantize(Decimal("0.0001")),
            "dscr": dscr.quantize(Decimal("0.01")),
            "equity_pct": equity_pct.quantize(Decimal("0.0001")),
            "violations": violations,
            "warnings": warnings,
            "constraints": {
                "max_ltv": constraints.max_ltv,
                "min_dscr": constraints.min_dscr,
                "min_equity_pct": constraints.min_equity_pct,
                "max_amortization_years": constraints.max_amortization_years,
                "interest_only_allowed": constraints.interest_only_allowed,
            },
        }

    def get_typical_rate(
        self,
        jurisdiction: JurisdictionCode | str,
        base_rate: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Get typical financing rate for a jurisdiction."""
        profile = self.get_profile(jurisdiction)
        spread_decimal = Decimal(profile.typical_spread_bps) / Decimal("10000")

        # Use provided base rate or estimate typical current rate
        if base_rate is None:
            # Rough current rate estimates as of 2024
            typical_base_rates = {
                JurisdictionCode.SG: Decimal("0.0350"),  # SORA ~3.50%
                JurisdictionCode.NZ: Decimal("0.0525"),  # OCR ~5.25%
                JurisdictionCode.SEA: Decimal("0.0500"),  # SOFR ~5.00%
                JurisdictionCode.TOR: Decimal("0.0475"),  # CORRA ~4.75%
                JurisdictionCode.HK: Decimal("0.0475"),  # HIBOR ~4.75%
            }
            jur_code = (
                JurisdictionCode(jurisdiction.upper())
                if isinstance(jurisdiction, str)
                else jurisdiction
            )
            base_rate = typical_base_rates.get(jur_code, Decimal("0.05"))

        all_in_rate = base_rate + spread_decimal

        return {
            "base_rate_name": profile.base_rate_name,
            "base_rate": base_rate,
            "spread_bps": profile.typical_spread_bps,
            "all_in_rate": all_in_rate,
            "currency": profile.currency,
        }


# Singleton instance
_financing_service: Optional[JurisdictionFinancingService] = None


def get_jurisdiction_financing_service() -> JurisdictionFinancingService:
    """Get the jurisdiction financing service singleton."""
    global _financing_service
    if _financing_service is None:
        _financing_service = JurisdictionFinancingService()
    return _financing_service


__all__ = [
    "JurisdictionCode",
    "PropertyType",
    "BorrowerType",
    "FinancingConstraints",
    "StampDutyRates",
    "JurisdictionFinancingProfile",
    "JurisdictionFinancingService",
    "get_jurisdiction_financing_service",
    "JURISDICTION_PROFILES",
]
