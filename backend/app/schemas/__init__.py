"""Schema package exports.

The package stays import-light so importing a single schema module does not pull
the entire Pydantic graph into startup or route registration.
"""

from __future__ import annotations

from functools import lru_cache
import sys
from types import ModuleType
from typing import Final

from app.schemas._typing import typed_import_module


def _counterpart(name: str) -> str | None:
    if name.startswith("backend."):
        return name.removeprefix("backend.")
    if name.startswith("app."):
        return f"backend.{name}"
    return None


def _register_alias(module_name: str, module: ModuleType) -> None:
    alias = _counterpart(module_name)
    if alias and alias not in sys.modules:
        sys.modules[alias] = module


_SCHEMA_MODULES: Final[tuple[str, ...]] = (
    "ai",
    "ai_config",
    "buildable",
    "compliance",
    "costs",
    "deals",
    "engineering",
    "entitlements",
    "feasibility",
    "finance",
    "imports",
    "market",
    "notification",
    "overlay",
    "performance",
    "property",
    "regulatory",
    "rulesets",
    "standards",
    "team",
    "user",
    "workflow",
)

_EXPORTS: Final[dict[str, str]] = {
    "AgentPerformanceSnapshotResponse": "performance",
    "BenchmarkResponse": "performance",
    "CashflowInputs": "finance",
    "CommissionAdjustmentCreate": "deals",
    "CommissionAdjustmentResponse": "deals",
    "CommissionCreate": "deals",
    "CommissionResponse": "deals",
    "CommissionStatusChangeRequest": "deals",
    "ComplianceCheckRequest": "compliance",
    "ComplianceCheckResponse": "compliance",
    "CostEscalationInput": "finance",
    "CostIndex": "costs",
    "CostIndexProvenance": "finance",
    "CostIndexSnapshot": "finance",
    "DealCreate": "deals",
    "DealSchema": "deals",
    "DealStageChangeRequest": "deals",
    "DealStageEventSchema": "deals",
    "DealUpdate": "deals",
    "DealWithTimelineSchema": "deals",
    "DetectedFloor": "imports",
    "DscrEntrySchema": "finance",
    "DscrInputs": "finance",
    "EntApprovalTypeCreate": "entitlements",
    "EntApprovalTypeSchema": "entitlements",
    "EntApprovalTypeUpdate": "entitlements",
    "EntAuthorityCreate": "entitlements",
    "EntAuthoritySchema": "entitlements",
    "EntAuthorityUpdate": "entitlements",
    "EntEngagementCollection": "entitlements",
    "EntEngagementCreate": "entitlements",
    "EntEngagementSchema": "entitlements",
    "EntEngagementUpdate": "entitlements",
    "EntLegalInstrumentCollection": "entitlements",
    "EntLegalInstrumentCreate": "entitlements",
    "EntLegalInstrumentSchema": "entitlements",
    "EntLegalInstrumentUpdate": "entitlements",
    "EntRoadmapCollection": "entitlements",
    "EntRoadmapItemCreate": "entitlements",
    "EntRoadmapItemSchema": "entitlements",
    "EntRoadmapItemUpdate": "entitlements",
    "EntStudyCollection": "entitlements",
    "EntStudyCreate": "entitlements",
    "EntStudySchema": "entitlements",
    "EntStudyUpdate": "entitlements",
    "FinanceFeasibilityRequest": "finance",
    "FinanceFeasibilityResponse": "finance",
    "FinanceResultSchema": "finance",
    "FinanceScenarioInput": "finance",
    "ImportResult": "imports",
    "MarketPeriod": "market",
    "MarketReportPayload": "market",
    "MarketReportResponse": "market",
    "MaterialStandard": "standards",
    "OverlayDecisionPayload": "overlay",
    "OverlayDecisionRecord": "overlay",
    "OverlaySuggestion": "overlay",
    "PaginatedCollection": "entitlements",
    "ParseStatusResponse": "imports",
    "PropertyComplianceSummary": "property",
    "RuleEvaluationResult": "rulesets",
    "RulePackSchema": "rulesets",
    "RulePackSummary": "rulesets",
    "RulesetEvaluationSummary": "rulesets",
    "RulesetListResponse": "rulesets",
    "RulesetValidationRequest": "rulesets",
    "RulesetValidationResponse": "rulesets",
    "SingaporePropertySchema": "property",
    "SnapshotRequest": "performance",
    "ViolationDetail": "rulesets",
    "ViolationFact": "rulesets",
}


def _load_submodule(module_name: str) -> ModuleType:
    module = typed_import_module(f"{__name__}.{module_name}")
    globals()[module_name] = module
    _register_alias(f"{__name__}.{module_name}", module)
    return module


@lru_cache(maxsize=1)
def load_schema_modules() -> None:
    for module_name in _SCHEMA_MODULES:
        _load_submodule(module_name)


def __getattr__(name: str) -> ModuleType | object:
    if name in _SCHEMA_MODULES:
        return _load_submodule(name)
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    module = _load_submodule(module_name)
    value: object = getattr(module, name)
    globals()[name] = value
    return value


_ALIAS = _counterpart(__name__)
if _ALIAS and _ALIAS in sys.modules:
    _existing: ModuleType = sys.modules[_ALIAS]
    globals().update(_existing.__dict__)
    sys.modules[__name__] = _existing
else:
    _register_alias(__name__, sys.modules[__name__])
    __all__ = ["load_schema_modules", *_SCHEMA_MODULES, *sorted(_EXPORTS)]
