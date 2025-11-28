"""Developer workspace API - unified router combining domain modules.

This module re-exports the combined router from domain-focused modules:
- developers_gps: GPS logging, preview jobs
- developers_checklists: Checklist CRUD, template management
- developers_conditions: Condition assessments, PDF export

Original file: 2,509 lines → split into 4 files (~600 lines each)
"""

from fastapi import APIRouter

from app.api.v1.developers_gps import router as gps_router
from app.api.v1.developers_checklists import router as checklists_router
from app.api.v1.developers_conditions import router as conditions_router

# Re-export shared models for backward compatibility
from app.api.v1.developers_common import (
    DeveloperAssetOptimization,
    DeveloperBuildEnvelope,
    DeveloperCapitalStructureScenario,
    DeveloperCashFlowMilestone,
    DeveloperColorLegendEntry,
    DeveloperConstraintViolation,
    DeveloperDebtFacility,
    DeveloperEquityWaterfall,
    DeveloperEquityWaterfallTier,
    DeveloperExitAssumptions,
    DeveloperFinanceBlueprint,
    DeveloperFinancialSummary,
    DeveloperMassingLayer,
    DeveloperSensitivityBand,
    DeveloperVisualizationSummary,
    PreviewJobSchema,
)

# Re-export GPS-specific models
from app.api.v1.developers_gps import (
    DeveloperGPSLogRequest,
    DeveloperGPSLogResponse,
    PreviewJobRefreshRequest,
)

# Re-export checklist models
from app.api.v1.developers_checklists import (
    ChecklistItemResponse,
    ChecklistItemsResponse,
    ChecklistProgressResponse,
    ChecklistSummaryResponse,
    ChecklistTemplateBulkImportRequest,
    ChecklistTemplateBulkImportResponse,
    ChecklistTemplateBaseRequest,
    ChecklistTemplateCreateRequest,
    ChecklistTemplateResponse,
    ChecklistTemplateUpdateRequest,
    UpdateChecklistStatusRequest,
)

# Re-export condition models
from app.api.v1.developers_conditions import (
    ConditionAssessmentResponse,
    ConditionAssessmentUpsertRequest,
    ConditionInsightResponse,
    ConditionReportResponse,
    ConditionSystemRequest,
    ConditionSystemResponse,
    ScenarioComparisonEntryResponse,
)


# Create unified router
router = APIRouter()

# Include all domain routers (they already have prefix="/developers")
# We need to strip the prefix since they're being included at the same level
router.include_router(gps_router, prefix="", tags=["developers"])
router.include_router(checklists_router, prefix="", tags=["developers"])
router.include_router(conditions_router, prefix="", tags=["developers"])


__all__ = [
    "router",
    # Common models
    "DeveloperAssetOptimization",
    "DeveloperBuildEnvelope",
    "DeveloperCapitalStructureScenario",
    "DeveloperCashFlowMilestone",
    "DeveloperColorLegendEntry",
    "DeveloperConstraintViolation",
    "DeveloperDebtFacility",
    "DeveloperEquityWaterfall",
    "DeveloperEquityWaterfallTier",
    "DeveloperExitAssumptions",
    "DeveloperFinanceBlueprint",
    "DeveloperFinancialSummary",
    "DeveloperMassingLayer",
    "DeveloperSensitivityBand",
    "DeveloperVisualizationSummary",
    "PreviewJobSchema",
    # GPS models
    "DeveloperGPSLogRequest",
    "DeveloperGPSLogResponse",
    "PreviewJobRefreshRequest",
    # Checklist models
    "ChecklistItemResponse",
    "ChecklistItemsResponse",
    "ChecklistProgressResponse",
    "ChecklistSummaryResponse",
    "ChecklistTemplateBulkImportRequest",
    "ChecklistTemplateBulkImportResponse",
    "ChecklistTemplateBaseRequest",
    "ChecklistTemplateCreateRequest",
    "ChecklistTemplateResponse",
    "ChecklistTemplateUpdateRequest",
    "UpdateChecklistStatusRequest",
    # Condition models
    "ConditionAssessmentResponse",
    "ConditionAssessmentUpsertRequest",
    "ConditionInsightResponse",
    "ConditionReportResponse",
    "ConditionSystemRequest",
    "ConditionSystemResponse",
    "ScenarioComparisonEntryResponse",
]
