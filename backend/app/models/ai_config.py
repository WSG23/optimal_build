"""AI Configuration models for configurable AI service parameters.

This module stores configurable parameters that were previously hardcoded
in AI service files, allowing them to be managed via API and customized
per organization/user.
"""

import uuid
from enum import Enum

from backend._compat.datetime import utcnow

from app.models.base import UUID, BaseModel
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship


class AIConfigCategory(str, Enum):
    """Categories of AI configuration."""

    DEAL_SCORING = "deal_scoring"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    COMPLIANCE_PREDICTION = "compliance_prediction"
    ANOMALY_DETECTION = "anomaly_detection"
    DUE_DILIGENCE = "due_diligence"


class AIConfig(BaseModel):
    """AI Configuration storage for service parameters.

    Stores configurable parameters like scoring weights, thresholds,
    allocation targets, and timeline estimates that were previously
    hardcoded in AI service modules.
    """

    __tablename__ = "ai_configs"
    __table_args__ = (
        UniqueConstraint(
            "category",
            "config_key",
            "organization_id",
            name="uq_ai_config_category_key_org",
        ),
        Index("ix_ai_configs_category", "category"),
        Index("ix_ai_configs_organization_id", "organization_id"),
    )

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Configuration identification
    category = Column(String(100), nullable=False)
    config_key = Column(String(200), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)

    # Configuration value (stored as JSON for flexibility)
    config_value = Column(JSON, nullable=False)

    # Value type hint for UI rendering
    value_type = Column(
        String(50), nullable=False, default="object"
    )  # number, string, object, array

    # Validation schema (optional JSON Schema)
    validation_schema = Column(JSON)

    # Scope: null = system default, organization_id = org-specific
    # Note: organization_id is a UUID stored without FK constraint since teams table
    # uses team_members pattern rather than a standalone teams table
    organization_id = Column(UUID(), nullable=True)

    # Active/inactive flag
    is_active = Column(Boolean, default=True, nullable=False)

    # Version tracking for audit
    version = Column(String(20), default="1.0.0", nullable=False)

    # Metadata
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    created_by = Column(UUID(), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(), ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<AIConfig {self.category}:{self.config_key}>"


class AIConfigAudit(BaseModel):
    """Audit log for AI configuration changes."""

    __tablename__ = "ai_config_audits"
    __table_args__ = (
        Index("ix_ai_config_audits_config_id", "config_id"),
        Index("ix_ai_config_audits_changed_at", "changed_at"),
    )

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(), ForeignKey("ai_configs.id"), nullable=False)

    # Change details
    previous_value = Column(JSON)
    new_value = Column(JSON)
    change_reason = Column(Text)

    # Who and when
    changed_by = Column(UUID(), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    config = relationship("AIConfig")
    user = relationship("User", foreign_keys=[changed_by])

    def __repr__(self) -> str:
        return f"<AIConfigAudit {self.config_id} at {self.changed_at}>"


# Default configuration values - used for seeding
DEFAULT_AI_CONFIGS = {
    AIConfigCategory.DEAL_SCORING: {
        "scoring_weights": {
            "display_name": "Deal Scoring Weights",
            "description": "Weights for different factors in deal scoring algorithm",
            "value_type": "object",
            "config_value": {
                "location_match": 0.15,
                "submarket_strength": 0.10,
                "tenure_adequacy": 0.10,
                "building_age": 0.05,
                "gpr_headroom": 0.08,
                "seller_motivation": 0.12,
                "competition_level": 0.08,
                "price_vs_market": 0.15,
                "historical_success_rate": 0.10,
                "similar_deal_outcomes": 0.07,
            },
        },
        "seller_motivation_categories": {
            "display_name": "Seller Motivation Categories",
            "description": "Classification of seller motivation types",
            "value_type": "object",
            "config_value": {
                "high": [
                    "estate_sale",
                    "distressed",
                    "divorce",
                    "urgent",
                    "relocation",
                ],
                "medium": ["portfolio_rebalance", "upgrade", "retirement"],
            },
        },
        "tenure_thresholds": {
            "display_name": "Tenure Year Thresholds",
            "description": "Year thresholds for tenure scoring",
            "value_type": "object",
            "config_value": {
                "strong": {"min_years": 70, "score": 0.7},
                "adequate": {"min_years": 50, "score": 0.3},
                "limited": {"min_years": 30, "score": -0.3},
                "short": {"min_years": 0, "score": -0.7},
            },
        },
        "price_deviation_thresholds": {
            "display_name": "Price Deviation Thresholds",
            "description": "Thresholds for price vs market scoring",
            "value_type": "object",
            "config_value": {
                "below_market": {"max_deviation": -10, "score": 0.6},
                "at_market": {"max_deviation": 5, "score": 0.2},
                "above_market": {"max_deviation": 15, "score": -0.3},
                "significantly_above": {"max_deviation": 100, "score": -0.6},
            },
        },
        "win_rate_thresholds": {
            "display_name": "Historical Win Rate Thresholds",
            "description": "Win rate thresholds for historical success scoring",
            "value_type": "object",
            "config_value": {
                "strong": {"min_rate": 0.7, "score": 0.7},
                "moderate": {"min_rate": 0.5, "score": 0.3},
                "weak": {"min_rate": 0.0, "score": -0.3},
            },
        },
        "gpr_headroom_thresholds": {
            "display_name": "GPR Headroom Thresholds",
            "description": "GPR headroom percentages for scoring",
            "value_type": "object",
            "config_value": {
                "significant": {"min_percent": 20, "score": 0.7},
                "some": {"min_percent": 10, "score": 0.3},
                "limited": {"min_percent": 0, "score": 0.0},
            },
        },
        "location_win_thresholds": {
            "display_name": "Location Win Count Thresholds",
            "description": "Win count thresholds for location matching",
            "value_type": "object",
            "config_value": {
                "experienced": {"min_wins": 5, "score": 0.8},
                "some_experience": {"min_wins": 2, "score": 0.4},
                "limited": {"min_wins": 0, "score": 0.0},
            },
        },
    },
    AIConfigCategory.PORTFOLIO_OPTIMIZATION: {
        "allocation_targets": {
            "display_name": "Portfolio Allocation Targets by Strategy",
            "description": "Target allocation percentages by optimization strategy",
            "value_type": "object",
            "config_value": {
                "maximize_returns": {
                    "office": 15.0,
                    "industrial": 35.0,
                    "retail": 10.0,
                    "residential": 15.0,
                    "mixed_use": 15.0,
                    "land": 10.0,
                },
                "minimize_risk": {
                    "office": 25.0,
                    "industrial": 20.0,
                    "retail": 10.0,
                    "residential": 30.0,
                    "mixed_use": 10.0,
                    "land": 5.0,
                },
                "balanced": {
                    "office": 20.0,
                    "industrial": 25.0,
                    "retail": 15.0,
                    "residential": 20.0,
                    "mixed_use": 10.0,
                    "land": 10.0,
                },
                "income_focused": {
                    "office": 30.0,
                    "industrial": 25.0,
                    "retail": 20.0,
                    "residential": 15.0,
                    "mixed_use": 5.0,
                    "land": 5.0,
                },
                "growth_focused": {
                    "office": 10.0,
                    "industrial": 30.0,
                    "retail": 10.0,
                    "residential": 20.0,
                    "mixed_use": 15.0,
                    "land": 15.0,
                },
            },
        },
        "allocation_variance_thresholds": {
            "display_name": "Allocation Variance Thresholds",
            "description": "Thresholds for determining rebalancing actions",
            "value_type": "object",
            "config_value": {
                "increase_threshold": 5.0,
                "decrease_threshold": 5.0,
            },
        },
        "default_metrics": {
            "display_name": "Default Portfolio Metrics",
            "description": "Default values for portfolio metrics when data unavailable",
            "value_type": "object",
            "config_value": {
                "weighted_yield": 0.045,
                "liquidity_score": 60,
                "portfolio_beta": 1.0,
            },
        },
    },
    AIConfigCategory.COMPLIANCE_PREDICTION: {
        "typical_timelines": {
            "display_name": "Typical Regulatory Timelines",
            "description": "Typical timelines in weeks by submission type",
            "value_type": "object",
            "config_value": {
                "development_control": {"min": 10, "max": 16, "typical": 12},
                "building_plan": {"min": 6, "max": 12, "typical": 8},
                "temporary_occupation_permit": {"min": 4, "max": 8, "typical": 6},
                "certificate_statutory_completion": {"min": 2, "max": 6, "typical": 4},
                "waiver": {"min": 8, "max": 20, "typical": 14},
                "consultation": {"min": 2, "max": 6, "typical": 4},
            },
        },
        "risk_triggers": {
            "display_name": "Risk Factor Triggers",
            "description": "Thresholds that trigger risk factors",
            "value_type": "object",
            "config_value": {
                "high_gpr_threshold": 4.0,
                "mrt_proximity_meters": 200,
                "building_age_structural_review": 30,
                "large_deal_value_threshold": 50000000,
            },
        },
    },
    AIConfigCategory.ANOMALY_DETECTION: {
        "alert_thresholds": {
            "display_name": "Alert Detection Thresholds",
            "description": "Thresholds for triggering various alerts",
            "value_type": "object",
            "config_value": {
                "assumption_deviation_percent": 15,
                "assumption_deviation_high_percent": 25,
                "pipeline_velocity_drop_percent": -20,
                "pipeline_velocity_drop_high_percent": -30,
                "pipeline_growth_percent": 50,
                "regulatory_delay_days": 60,
                "regulatory_delay_high_days": 90,
                "comparable_deviation_percent": 10,
            },
        },
        "check_intervals": {
            "display_name": "Alert Check Intervals",
            "description": "Check intervals in minutes for different alert types",
            "value_type": "object",
            "config_value": {
                "assumption_vs_market": 240,
                "pipeline_velocity": 1440,
                "regulatory_delay": 720,
                "comparable_transaction": 480,
                "cash_flow_deviation": 1440,
            },
        },
    },
    AIConfigCategory.DUE_DILIGENCE: {
        "dd_templates": {
            "display_name": "Due Diligence Templates",
            "description": "DD checklist templates by deal type",
            "value_type": "object",
            "config_value": {
                "buy_side": {
                    "legal": [
                        {
                            "name": "Title Search",
                            "description": "Verify clean title with no encumbrances",
                            "priority": "critical",
                            "auto_completable": True,
                            "source": "SLA",
                        },
                        {
                            "name": "Encumbrance Check",
                            "description": "Check for mortgages, charges, caveats",
                            "priority": "critical",
                            "auto_completable": True,
                            "source": "SLA",
                        },
                        {
                            "name": "Lease Review",
                            "description": "Review all tenancy agreements",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Legal Opinion",
                            "description": "Obtain legal opinion on title",
                            "priority": "critical",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Power of Attorney",
                            "description": "Verify seller's authority to sell",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Strata Title Status",
                            "description": "Verify strata subdivision if applicable",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "IRAS Tax Clearance",
                            "description": "Obtain property tax clearance",
                            "priority": "high",
                            "auto_completable": True,
                            "source": "IRAS",
                        },
                        {
                            "name": "Pending Litigation",
                            "description": "Check for any pending legal matters",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                    ],
                    "technical": [
                        {
                            "name": "Building Inspection",
                            "description": "Conduct physical building inspection",
                            "priority": "critical",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "M&E Assessment",
                            "description": "Assess mechanical and electrical systems",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Structural Survey",
                            "description": "Structural integrity assessment",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "As-Built Plans Review",
                            "description": "Review approved plans vs as-built",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Fire Safety Compliance",
                            "description": "Verify FSC and fire systems",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Lift Assessment",
                            "description": "Assess lift condition and compliance",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                    ],
                    "financial": [
                        {
                            "name": "Tenancy Schedule",
                            "description": "Verify rent roll and lease terms",
                            "priority": "critical",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Operating Expenses",
                            "description": "Analyze historical operating costs",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Service Charges",
                            "description": "Verify service charge budgets",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Arrears Analysis",
                            "description": "Check for tenant arrears",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Income Verification",
                            "description": "Verify historical income statements",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Capex History",
                            "description": "Review historical capital expenditure",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                    ],
                    "regulatory": [
                        {
                            "name": "Zoning Confirmation",
                            "description": "Confirm URA zoning and permitted use",
                            "priority": "critical",
                            "auto_completable": True,
                            "source": "URA",
                        },
                        {
                            "name": "Planning Approvals",
                            "description": "Review all planning approvals",
                            "priority": "high",
                            "auto_completable": True,
                            "source": "URA",
                        },
                        {
                            "name": "Outstanding Applications",
                            "description": "Check for pending applications",
                            "priority": "high",
                            "auto_completable": True,
                            "source": "URA",
                        },
                        {
                            "name": "GFA Compliance",
                            "description": "Verify approved vs built GFA",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "DC/BP Compliance",
                            "description": "Review DC and BP approvals",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "TOP/CSC Status",
                            "description": "Verify TOP and CSC status",
                            "priority": "high",
                            "auto_completable": True,
                            "source": "BCA",
                        },
                    ],
                    "environmental": [
                        {
                            "name": "Phase I ESA",
                            "description": "Environmental site assessment",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Contamination Check",
                            "description": "Check for soil/groundwater contamination",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Asbestos Survey",
                            "description": "Check for asbestos-containing materials",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Hazardous Materials",
                            "description": "Identify hazardous materials",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                    ],
                    "commercial": [
                        {
                            "name": "Market Comparable Analysis",
                            "description": "Analyze comparable transactions",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Tenant Credit Analysis",
                            "description": "Assess tenant creditworthiness",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Competition Assessment",
                            "description": "Analyze competing properties",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Vacancy Analysis",
                            "description": "Assess market vacancy trends",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                    ],
                },
                "lease": {
                    "legal": [
                        {
                            "name": "Landlord Title",
                            "description": "Verify landlord's title to property",
                            "priority": "high",
                            "auto_completable": True,
                            "source": "SLA",
                        },
                        {
                            "name": "Lease Template Review",
                            "description": "Review standard lease terms",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Negotiated Terms",
                            "description": "Document negotiated variations",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                    ],
                    "technical": [
                        {
                            "name": "Premises Inspection",
                            "description": "Inspect premises condition",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Fit-out Assessment",
                            "description": "Assess fit-out requirements",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "M&E Capacity",
                            "description": "Verify M&E capacity for intended use",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                    ],
                    "commercial": [
                        {
                            "name": "Rent Benchmark",
                            "description": "Compare rent to market rates",
                            "priority": "high",
                            "auto_completable": False,
                            "source": None,
                        },
                        {
                            "name": "Operating Cost Analysis",
                            "description": "Analyze service charges and costs",
                            "priority": "medium",
                            "auto_completable": False,
                            "source": None,
                        },
                    ],
                },
            },
        },
        "conditional_triggers": {
            "display_name": "Conditional DD Item Triggers",
            "description": "Triggers for adding conditional DD items",
            "value_type": "object",
            "config_value": {
                "old_building_years": 20,
                "large_deal_threshold": 50000000,
            },
        },
    },
}
