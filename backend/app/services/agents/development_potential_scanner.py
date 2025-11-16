"""Development Potential Scanner for analyzing property development opportunities."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from backend._compat.datetime import utcnow
from pydantic import BaseModel

from app.models.property import DevelopmentAnalysis, Property, PropertyType, TenureType
from app.services.agents.ura_integration import URAIntegrationService
from app.services.buildable import BuildableInput, BuildableService
from app.services.finance.calculator import FinanceCalculator
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DevelopmentScenario(BaseModel):
    """A development scenario for a property."""

    scenario_type: str
    description: str
    gfa_potential: float
    use_mix: Dict[str, float]  # e.g., {"office": 0.6, "retail": 0.4}
    market_comparable_psf: Optional[float] = None  # Market pricing only
    estimated_cost: Optional[float] = None
    estimated_revenue: Optional[float] = None
    projected_roi: Optional[float] = None
    timeline_months: Optional[int] = None
    indicative_timeline: str  # General timeline, not construction schedule
    constraints: List[str]
    opportunities: List[str]


class RawLandAnalysis(BaseModel):
    """Analysis results for raw land development."""

    gfa_potential: float
    optimal_use_mix: Dict[str, float]
    development_scenarios: List[DevelopmentScenario]
    site_constraints: List[str]
    development_opportunities: List[str]
    market_value_indication: Optional[float] = None  # Based on comparables only


class ExistingBuildingAnalysis(BaseModel):
    """Analysis results for existing building redevelopment."""

    current_gfa: float
    redevelopment_gfa_potential: float
    renovation_potential: Dict[str, Any]
    adaptive_reuse_options: List[Dict[str, Any]]
    asset_enhancement_opportunities: List[str]
    market_rent_potential: Optional[float] = None  # Market rent only
    comparable_values_psf: Optional[float] = None  # Market comparables only


class HistoricalPropertyAnalysis(BaseModel):
    """Analysis results for historical/conservation properties."""

    heritage_value: str
    conservation_requirements: List[str]
    facade_preservation_needed: bool
    allowable_modifications: List[str]
    adaptive_reuse_potential: List[Dict[str, Any]]
    grant_opportunities: List[str]
    special_considerations: List[str]


class DevelopmentPotentialScanner:
    """Service for scanning and analyzing property development potential."""

    def __init__(
        self,
        buildable_service: BuildableService,
        finance_calculator: FinanceCalculator,
        ura_service: URAIntegrationService,
    ):
        self.buildable = buildable_service
        self.finance = finance_calculator
        self.ura = ura_service

    async def analyze_property(
        self,
        property_data: Property,
        property_type: str,
        session: AsyncSession,
        save_analysis: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze development potential based on property type.

        Args:
            property_data: Property information
            property_type: Type of analysis (raw_land, existing_building, historical_property)
            session: Database session
            save_analysis: Whether to save analysis results to database

        Returns:
            Development analysis results
        """
        try:
            if property_type == "raw_land":
                analysis = await self._analyze_raw_land(property_data, session)
            elif property_type == "existing_building":
                analysis = await self._analyze_existing_building(property_data, session)
            elif property_type == "historical_property":
                analysis = await self._analyze_historical_property(
                    property_data, session
                )
            else:
                raise ValueError(f"Unknown property type for analysis: {property_type}")

            # Save analysis to database if requested
            if save_analysis:
                await self._save_analysis(
                    property_data.id, property_type, analysis, session
                )

            return analysis.dict()

        except Exception as e:
            logger.error(f"Error analyzing property {property_data.id}: {str(e)}")
            raise

    async def _analyze_raw_land(
        self, property_data: Property, session: AsyncSession
    ) -> RawLandAnalysis:
        """Analyze raw land development potential."""

        # Get zoning information
        zoning_info = await self.ura.get_zoning_info(property_data.address)

        # Calculate GFA potential using BuildableService
        buildable_input = BuildableInput(
            land_area=float(property_data.land_area_sqm or 0),
            zone_code=property_data.zoning_code or zoning_info.zone_code,
            plot_ratio=float(property_data.plot_ratio or zoning_info.plot_ratio),
        )

        buildable_result = await self.buildable.calculate_parameters(buildable_input)
        gfa_potential = buildable_result.gfa_total

        # Determine optimal use mix based on zoning
        optimal_use_mix = self._determine_optimal_use_mix(
            zoning_info, property_data.location
        )

        # Generate development scenarios
        scenarios = await self._generate_development_scenarios(
            property_data, gfa_potential, optimal_use_mix, zoning_info
        )

        # Identify site constraints
        site_constraints = self._identify_site_constraints(property_data, zoning_info)

        # Identify development opportunities
        opportunities = await self._identify_opportunities(
            property_data, zoning_info, optimal_use_mix
        )

        # Estimate land value
        land_value = await self._estimate_land_value(
            property_data, gfa_potential, optimal_use_mix
        )

        return RawLandAnalysis(
            gfa_potential=gfa_potential,
            optimal_use_mix=optimal_use_mix,
            development_scenarios=scenarios,
            site_constraints=site_constraints,
            development_opportunities=opportunities,
            estimated_land_value=land_value,
        )

    async def _analyze_existing_building(
        self, property_data: Property, session: AsyncSession
    ) -> ExistingBuildingAnalysis:
        """Analyze existing building redevelopment/renovation potential."""

        current_gfa = float(property_data.gross_floor_area_sqm or 0)

        # Get zoning for redevelopment potential
        zoning_info = await self.ura.get_zoning_info(property_data.address)

        # Calculate redevelopment GFA potential
        buildable_input = BuildableInput(
            land_area=float(property_data.land_area_sqm or 0),
            zone_code=property_data.zoning_code or zoning_info.zone_code,
            plot_ratio=float(property_data.plot_ratio or zoning_info.plot_ratio),
        )

        buildable_result = await self.buildable.calculate_parameters(buildable_input)
        redevelopment_gfa = buildable_result.gfa_total

        # Analyze renovation potential
        renovation_potential = await self._analyze_renovation_potential(
            property_data, current_gfa
        )

        # Identify adaptive reuse options
        adaptive_reuse = self._identify_adaptive_reuse_options(
            property_data, zoning_info
        )

        # Asset enhancement opportunities
        aei_opportunities = self._identify_aei_opportunities(property_data)

        # Cost and value estimates
        redevelopment_cost = await self._estimate_redevelopment_cost(
            property_data, redevelopment_gfa
        )

        value_uplift = await self._calculate_value_uplift(
            property_data, renovation_potential, redevelopment_gfa
        )

        return ExistingBuildingAnalysis(
            current_gfa=current_gfa,
            redevelopment_gfa_potential=redevelopment_gfa,
            renovation_potential=renovation_potential,
            adaptive_reuse_options=adaptive_reuse,
            asset_enhancement_opportunities=aei_opportunities,
            estimated_redevelopment_cost=redevelopment_cost,
            projected_value_uplift=value_uplift,
        )

    async def _analyze_historical_property(
        self, property_data: Property, session: AsyncSession
    ) -> HistoricalPropertyAnalysis:
        """Analyze historical/conservation property development potential."""

        # Determine heritage value and constraints
        heritage_value = self._assess_heritage_value(property_data)

        # Conservation requirements
        conservation_reqs = self._get_conservation_requirements(property_data)

        # Check facade preservation needs
        facade_preservation = property_data.conservation_status in [
            "conserved",
            "monument",
            "heritage",
        ]

        # Allowable modifications
        allowable_mods = self._get_allowable_modifications(
            property_data, conservation_reqs
        )

        # Adaptive reuse potential for heritage buildings
        adaptive_reuse = self._get_heritage_adaptive_reuse_options(property_data)

        # Grant opportunities
        grants = self._identify_heritage_grants(property_data)

        # Special considerations
        special_considerations = self._get_heritage_special_considerations(
            property_data
        )

        return HistoricalPropertyAnalysis(
            heritage_value=heritage_value,
            conservation_requirements=conservation_reqs,
            facade_preservation_needed=facade_preservation,
            allowable_modifications=allowable_mods,
            adaptive_reuse_potential=adaptive_reuse,
            grant_opportunities=grants,
            special_considerations=special_considerations,
        )

    def _determine_optimal_use_mix(
        self, zoning_info: Any, location: Any
    ) -> Dict[str, float]:
        """Determine optimal use mix based on zoning and market conditions."""

        # Default use mixes based on zoning
        use_mix_templates = {
            "Commercial": {"office": 0.7, "retail": 0.3},
            "Business": {"office": 0.5, "light_industrial": 0.3, "retail": 0.2},
            "Mixed Use": {"residential": 0.6, "retail": 0.2, "office": 0.2},
            "Residential": {"residential": 0.9, "retail": 0.1},
        }

        # Get base template
        base_mix = use_mix_templates.get(zoning_info.zone_description, {"mixed": 1.0})

        # TODO: Adjust based on market conditions and location factors

        return base_mix

    async def _generate_development_scenarios(
        self,
        property_data: Property,
        gfa_potential: float,
        optimal_use_mix: Dict[str, float],
        zoning_info: Any,
    ) -> List[DevelopmentScenario]:
        """Generate multiple development scenarios."""

        scenarios = []

        # Scenario 1: Optimal mix development
        optimal_cost = gfa_potential * 3500  # $3500 per sqm construction cost
        optimal_revenue = gfa_potential * 8000  # $8000 per sqm sales price
        optimal_roi = ((optimal_revenue - optimal_cost) / optimal_cost) * 100

        scenarios.append(
            DevelopmentScenario(
                scenario_type="optimal_mix",
                description="Development following recommended use mix",
                gfa_potential=gfa_potential,
                use_mix=optimal_use_mix,
                estimated_cost=optimal_cost,
                estimated_revenue=optimal_revenue,
                projected_roi=optimal_roi,
                timeline_months=36,
                indicative_timeline="36 months (concept to completion)",
                constraints=["Market dependent", "Financing required"],
                opportunities=["Strong location", "Growing demand"],
            )
        )

        # Scenario 2: Single use development
        if len(optimal_use_mix) > 1:
            # Take the dominant use
            dominant_use = max(optimal_use_mix.items(), key=lambda x: x[1])
            single_use_mix = {dominant_use[0]: 1.0}

            single_cost = gfa_potential * 3000  # Lower cost for single use
            single_revenue = gfa_potential * 7500
            single_roi = ((single_revenue - single_cost) / single_cost) * 100

            scenarios.append(
                DevelopmentScenario(
                    scenario_type="single_use",
                    description=f"Single use development - {dominant_use[0]}",
                    gfa_potential=gfa_potential,
                    use_mix=single_use_mix,
                    estimated_cost=single_cost,
                    estimated_revenue=single_revenue,
                    projected_roi=single_roi,
                    timeline_months=30,
                    indicative_timeline="30 months (streamlined delivery)",
                    constraints=["Less flexibility", "Market concentration risk"],
                    opportunities=["Simpler execution", "Clear target market"],
                )
            )

        # Scenario 3: Phased development
        if gfa_potential > 50000:  # Only for large sites
            phase1_gfa = gfa_potential * 0.4
            phase1_cost = phase1_gfa * 3200
            phase1_revenue = phase1_gfa * 7800

            scenarios.append(
                DevelopmentScenario(
                    scenario_type="phased",
                    description="Phased development approach",
                    gfa_potential=phase1_gfa,
                    use_mix=optimal_use_mix,
                    estimated_cost=phase1_cost,
                    estimated_revenue=phase1_revenue,
                    projected_roi=((phase1_revenue - phase1_cost) / phase1_cost) * 100,
                    timeline_months=24,
                    indicative_timeline="24 months for initial phase",
                    constraints=["Requires master planning", "Longer overall timeline"],
                    opportunities=[
                        "Risk mitigation",
                        "Market flexibility",
                        "Cash flow management",
                    ],
                )
            )

        return scenarios

    def _identify_site_constraints(
        self, property_data: Property, zoning_info: Any
    ) -> List[str]:
        """Identify site development constraints."""

        constraints = []

        # Height restrictions
        if zoning_info.building_height_limit:
            constraints.append(f"Height limit: {zoning_info.building_height_limit}m")

        # Conservation status
        if property_data.is_conservation:
            constraints.append("Conservation requirements apply")

        # Site coverage
        if zoning_info.site_coverage:
            constraints.append(f"Maximum site coverage: {zoning_info.site_coverage}%")

        # Special conditions
        if zoning_info.special_conditions:
            constraints.append(zoning_info.special_conditions)

        # Tenure limitations
        if property_data.tenure_type != TenureType.FREEHOLD:
            constraints.append(f"Leasehold tenure: {property_data.tenure_type}")

        return constraints

    async def _save_analysis(
        self,
        property_id: UUID,
        analysis_type: str,
        analysis_result: Any,
        session: AsyncSession,
    ) -> None:
        """Save analysis results to database."""

        # Prepare a lightweight financial summary for storage
        financial_summary = None
        recommended_scenario = None
        if (
            hasattr(analysis_result, "development_scenarios")
            and analysis_result.development_scenarios
        ):
            optimal = analysis_result.development_scenarios[0]
            recommended_scenario = optimal.scenario_type
            financial_summary = {
                "estimated_development_cost": optimal.estimated_cost,
                "estimated_revenue": optimal.estimated_revenue,
                "projected_roi_percentage": optimal.projected_roi,
                "timeline_months": optimal.timeline_months,
                "indicative_timeline": optimal.indicative_timeline,
            }

        analysis_record = {
            "property_id": property_id,
            "analysis_type": analysis_type,
            "analysis_date": utcnow(),
            "gfa_potential_sqm": getattr(analysis_result, "gfa_potential", None),
            "optimal_use_mix": getattr(analysis_result, "optimal_use_mix", None),
            "site_constraints": {
                "constraints": getattr(analysis_result, "site_constraints", [])
            },
            "development_opportunities": {
                "opportunities": getattr(
                    analysis_result, "development_opportunities", []
                )
            },
            "development_scenarios": [
                s.dict() for s in getattr(analysis_result, "development_scenarios", [])
            ],
            "value_add_potential": financial_summary,
            "recommended_scenario": recommended_scenario,
            "confidence_level": Decimal("0.75"),  # Default confidence
        }

        stmt = insert(DevelopmentAnalysis).values(**analysis_record)
        await session.execute(stmt)
        await session.commit()

        logger.info(f"Saved development analysis for property {property_id}")

    # Additional helper methods for specific analysis types

    async def _identify_opportunities(
        self, property_data: Property, zoning_info: Any, use_mix: Dict[str, float]
    ) -> List[str]:
        """Identify development opportunities."""
        opportunities = []

        # Location advantages
        if property_data.district and "CBD" in property_data.district:
            opportunities.append("Prime CBD location")

        # Zoning advantages
        if zoning_info.plot_ratio >= 10:
            opportunities.append("High density development allowed")

        # Mixed use potential
        if len(use_mix) > 1:
            opportunities.append("Mixed-use development potential")

        # TODO: Add market-based opportunities

        return opportunities

    async def _estimate_land_value(
        self, property_data: Property, gfa_potential: float, use_mix: Dict[str, float]
    ) -> float:
        """Estimate land value based on development potential."""
        # Simplified land value calculation
        # In production, this would use market comparables

        base_psf_values = {
            "office": 2500,
            "retail": 3000,
            "residential": 2000,
            "industrial": 800,
            "mixed": 2200,
        }

        # Calculate weighted average PSF
        weighted_psf = sum(
            base_psf_values.get(use, 2000) * proportion
            for use, proportion in use_mix.items()
        )

        # Apply location factor
        location_factor = 1.5 if "CBD" in (property_data.district or "") else 1.0

        # Land value = GFA potential * PSF value * residual factor
        land_value = gfa_potential * weighted_psf * location_factor * 0.3

        return land_value

    async def _analyze_renovation_potential(
        self, property_data: Property, current_gfa: float
    ) -> Dict[str, Any]:
        """Analyze renovation and upgrading potential."""

        building_age = None
        if property_data.year_built:
            building_age = datetime.now().year - property_data.year_built

        renovation_potential = {
            "facade_upgrade": {
                "feasible": building_age and building_age > 15,
                "estimated_cost_psm": 500,
                "value_uplift_percentage": 5,
            },
            "mep_upgrade": {  # Mechanical, Electrical, Plumbing
                "feasible": building_age and building_age > 20,
                "estimated_cost_psm": 800,
                "value_uplift_percentage": 10,
            },
            "space_reconfiguration": {
                "feasible": True,
                "estimated_cost_psm": 1200,
                "value_uplift_percentage": 15,
            },
            "green_certification": {
                "feasible": True,
                "estimated_cost_psm": 300,
                "value_uplift_percentage": 8,
                "additional_benefits": ["Lower operating costs", "Tenant attraction"],
            },
            "technology_upgrade": {
                "feasible": True,
                "estimated_cost_psm": 400,
                "value_uplift_percentage": 12,
                "features": [
                    "Smart building systems",
                    "IoT integration",
                    "Touchless access",
                ],
            },
        }

        # Calculate total potential
        total_cost = sum(
            option["estimated_cost_psm"] * current_gfa
            for option in renovation_potential.values()
            if option.get("feasible", False)
        )

        total_uplift = sum(
            option["value_uplift_percentage"]
            for option in renovation_potential.values()
            if option.get("feasible", False)
        )

        renovation_potential["summary"] = {
            "total_estimated_cost": total_cost,
            "total_value_uplift_percentage": min(total_uplift, 40),  # Cap at 40%
            "recommended_approach": (
                "Phased renovation" if total_cost > 10000000 else "Single phase"
            ),
        }

        return renovation_potential

    def _identify_adaptive_reuse_options(
        self, property_data: Property, zoning_info: Any
    ) -> List[Dict[str, Any]]:
        """Identify adaptive reuse possibilities."""

        current_type = property_data.property_type
        allowed_uses = zoning_info.use_groups if zoning_info else []

        reuse_options = []

        # Office to Residential conversion
        if current_type == PropertyType.OFFICE and "Residential" in allowed_uses:
            reuse_options.append(
                {
                    "conversion_type": "Office to Residential",
                    "feasibility": (
                        "High"
                        if property_data.year_built and property_data.year_built < 2000
                        else "Medium"
                    ),
                    "key_considerations": [
                        "Floor plate suitability",
                        "Natural ventilation requirements",
                        "Plumbing modifications",
                    ],
                    "estimated_timeline_months": 18,
                    "market_demand": "High",
                }
            )

        # Industrial to Creative Space
        if current_type == PropertyType.INDUSTRIAL:
            reuse_options.append(
                {
                    "conversion_type": "Industrial to Creative/Tech Space",
                    "feasibility": "High",
                    "key_considerations": [
                        "High ceiling advantage",
                        "Open floor plates",
                        "Parking requirements",
                    ],
                    "estimated_timeline_months": 12,
                    "market_demand": "Medium",
                }
            )

        # Retail to Mixed Use
        if current_type == PropertyType.RETAIL and "Mixed" in str(allowed_uses):
            reuse_options.append(
                {
                    "conversion_type": "Retail to Mixed-Use",
                    "feasibility": "Medium",
                    "key_considerations": [
                        "Upper floor conversion potential",
                        "Separate access requirements",
                        "Service requirements",
                    ],
                    "estimated_timeline_months": 24,
                    "market_demand": "High",
                }
            )

        # Hotel to Service Apartment/Co-living
        if current_type == PropertyType.HOTEL:
            reuse_options.append(
                {
                    "conversion_type": "Hotel to Service Apartments",
                    "feasibility": "High",
                    "key_considerations": [
                        "Existing room layouts advantageous",
                        "Kitchen additions needed",
                        "Regulatory compliance",
                    ],
                    "estimated_timeline_months": 9,
                    "market_demand": "High",
                }
            )

        return reuse_options

    def _identify_aei_opportunities(self, property_data: Property) -> List[str]:
        """Identify Asset Enhancement Initiative opportunities."""

        opportunities = []

        # Building age based opportunities
        if property_data.year_built:
            building_age = datetime.now().year - property_data.year_built

            if building_age > 10:
                opportunities.append("Facade refresh and modernization")
            if building_age > 15:
                opportunities.append("Lobby and common area upgrade")
            if building_age > 20:
                opportunities.append("Full MEP systems replacement")

        # Type-specific opportunities
        if property_data.property_type == PropertyType.OFFICE:
            opportunities.extend(
                [
                    "Convert to flexible workspace",
                    "Add wellness amenities",
                    "Implement touchless technologies",
                ]
            )
        elif property_data.property_type == PropertyType.RETAIL:
            opportunities.extend(
                [
                    "Add F&B components",
                    "Create experiential retail spaces",
                    "Integrate online-offline retail",
                ]
            )
        elif property_data.property_type == PropertyType.INDUSTRIAL:
            opportunities.extend(
                [
                    "Add ramp-up logistics facilities",
                    "Increase floor loading capacity",
                    "Install solar panels on roof",
                ]
            )

        # Universal opportunities
        opportunities.extend(
            [
                "Achieve green building certification",
                "Implement smart building technologies",
                "Improve accessibility features",
            ]
        )

        return opportunities

    async def _estimate_redevelopment_cost(
        self, property_data: Property, new_gfa: float
    ) -> float:
        """Estimate redevelopment cost."""

        # Base construction costs per sqm by type
        base_costs = {
            PropertyType.OFFICE: 3500,
            PropertyType.RETAIL: 4000,
            PropertyType.RESIDENTIAL: 3000,
            PropertyType.INDUSTRIAL: 2000,
            PropertyType.HOTEL: 4500,
            PropertyType.MIXED_USE: 3800,
        }

        base_cost_psm = base_costs.get(property_data.property_type, 3500)

        # Demolition cost if existing building
        demolition_cost = 0
        if property_data.gross_floor_area_sqm:
            demolition_cost = float(property_data.gross_floor_area_sqm) * 150

        # Construction cost
        construction_cost = new_gfa * base_cost_psm

        # Additional costs (professional fees, financing, contingency)
        additional_costs = construction_cost * 0.25

        total_cost = demolition_cost + construction_cost + additional_costs

        return total_cost

    async def _calculate_value_uplift(
        self,
        property_data: Property,
        renovation_potential: Dict[str, Any],
        redevelopment_gfa: float,
    ) -> float:
        """Calculate potential value uplift from renovation or redevelopment."""

        # Estimate current value (simplified)
        current_value = float(property_data.gross_floor_area_sqm or 0) * 5000

        # Renovation uplift
        renovation_uplift_pct = renovation_potential.get("summary", {}).get(
            "total_value_uplift_percentage", 0
        )
        renovation_value = current_value * (1 + renovation_uplift_pct / 100)

        # Redevelopment value
        redevelopment_value = redevelopment_gfa * 8000  # Simplified new building value

        # Return the better option
        return max(
            renovation_value - current_value, redevelopment_value - current_value
        )

    def _assess_heritage_value(self, property_data: Property) -> str:
        """Assess heritage value of property."""

        if property_data.conservation_status == "monument":
            return "National Monument - Highest protection"
        elif property_data.conservation_status == "conserved":
            return "Conserved Building - Protected facade and key features"
        elif property_data.year_built and property_data.year_built < 1950:
            return "Historic Building - Potential heritage value"
        elif property_data.architect and "SIT" in property_data.architect:
            return "Architectural Significance - Singapore Improvement Trust era"
        else:
            return "Standard Building - No special heritage value"

    def _get_conservation_requirements(self, property_data: Property) -> List[str]:
        """Get conservation requirements for heritage properties."""

        requirements = []

        if property_data.is_conservation:
            requirements.extend(
                [
                    "Maintain original facade",
                    "Preserve key architectural features",
                    "Use appropriate materials for restoration",
                    "Submit plans to URA Conservation team",
                    "Engage qualified conservation architect",
                ]
            )

            if property_data.conservation_status == "monument":
                requirements.extend(
                    [
                        "No structural alterations allowed",
                        "Interior features must be preserved",
                        "Regular maintenance inspections required",
                    ]
                )

        return requirements

    def _get_allowable_modifications(
        self, property_data: Property, conservation_requirements: List[str]
    ) -> List[str]:
        """Determine allowable modifications for heritage properties."""

        if not property_data.is_conservation:
            return ["All modifications allowed subject to planning approval"]

        allowable = []

        if property_data.conservation_status != "monument":
            allowable.extend(
                [
                    "Internal reconfiguration (non-structural)",
                    "Rear additions (subject to guidelines)",
                    "Roof additions (setback required)",
                    "Basement excavation (with precautions)",
                    "Modern services integration",
                ]
            )
        else:
            allowable.extend(
                [
                    "Reversible installations only",
                    "Sensitive lighting additions",
                    "Conservation-grade repairs",
                    "Interpretive displays",
                ]
            )

        return allowable

    def _get_heritage_adaptive_reuse_options(
        self, property_data: Property
    ) -> List[Dict[str, Any]]:
        """Get adaptive reuse options specific to heritage buildings."""

        options = []

        # Boutique hotel conversion
        options.append(
            {
                "use": "Boutique Heritage Hotel",
                "suitability": (
                    "High"
                    if property_data.floors_above_ground
                    and property_data.floors_above_ground >= 3
                    else "Medium"
                ),
                "key_features": [
                    "Preserve historic character",
                    "Limited room count maintains exclusivity",
                    "Heritage tourism appeal",
                ],
                "challenges": ["Modern services integration", "Fire safety compliance"],
                "precedents": ["Raffles Hotel", "Fullerton Hotel"],
            }
        )

        # Cultural/Arts space
        options.append(
            {
                "use": "Cultural/Arts Center",
                "suitability": "High",
                "key_features": [
                    "Public accessibility",
                    "Grant funding available",
                    "Community value",
                ],
                "challenges": ["Revenue generation", "Ongoing maintenance"],
                "precedents": ["National Gallery", "Arts House"],
            }
        )

        # F&B destination
        options.append(
            {
                "use": "Heritage F&B Destination",
                "suitability": "High",
                "key_features": [
                    "Character adds to dining experience",
                    "Multiple concepts possible",
                    "Tourist attraction",
                ],
                "challenges": ["Kitchen exhaust requirements", "Service access"],
                "precedents": ["CHIJMES", "Alkaff Mansion"],
            }
        )

        # Creative offices
        options.append(
            {
                "use": "Heritage Creative Offices",
                "suitability": "Medium",
                "key_features": [
                    "Unique workspace environment",
                    "Appeals to creative industries",
                    "Premium rental potential",
                ],
                "challenges": ["Modern IT infrastructure", "Subdivision limitations"],
                "precedents": ["The Working Capitol", "The Great Madras"],
            }
        )

        return options

    def _identify_heritage_grants(self, property_data: Property) -> List[str]:
        """Identify available heritage conservation grants."""

        grants = []

        if property_data.is_conservation:
            grants.extend(
                [
                    "URA Architectural Heritage Award (up to $1M)",
                    "National Heritage Board Conservation Grant",
                    "Business Improvement Fund (for heritage businesses)",
                    "STB Experience Step-Up Fund (for tourism uses)",
                ]
            )

            if property_data.conservation_status == "monument":
                grants.append("National Monument Maintenance Grant (annual)")

        # Property type specific grants
        if property_data.property_type in [PropertyType.RETAIL, PropertyType.MIXED_USE]:
            grants.append("Enterprise Singapore Capability Development Grant")

        return grants

    def _get_heritage_special_considerations(
        self, property_data: Property
    ) -> List[str]:
        """Get special considerations for heritage property development."""

        considerations = [
            "Extended approval timeline (6-12 months)",
            "Specialist consultants required",
            "Higher construction costs (20-40% premium)",
            "Limited contractor pool with conservation experience",
            "Potential archaeological requirements",
            "Public and stakeholder consultation may be required",
        ]

        if property_data.conservation_status == "monument":
            considerations.extend(
                [
                    "National Heritage Board approval required",
                    "Interpretive program development needed",
                    "Public access requirements",
                ]
            )

        return considerations
