"""AI Services Package - Phases 1-4 of AI Rollout Plan."""

from __future__ import annotations

from importlib import import_module
from typing import Final

_EXPORTS: Final[dict[str, str]] = {
    # Phase 1: Foundation
    "NaturalLanguageQueryService": ".natural_language_query",
    "DocumentExtractionService": ".document_extractor",
    "AnomalyDetectionService": ".anomaly_detector",
    "RAGKnowledgeBaseService": ".rag_knowledge_base",
    # Phase 2: Predictive
    "DealScoringService": ".deal_scoring",
    "ScenarioOptimizerService": ".scenario_optimizer",
    "MarketPredictorService": ".market_predictor",
    "CompliancePredictorService": ".compliance_predictor",
    # Phase 3: Automation
    "DueDiligenceService": ".due_diligence_generator",
    "AIReportGenerator": ".report_generator",
    "CommunicationDrafterService": ".communication_drafter",
    "WorkflowEngineService": ".workflow_engine",
    # Phase 4: Advanced
    "ConversationalAssistantService": ".conversational_assistant",
    "MultiModalAnalyzerService": ".multi_modal_analyzer",
    "PortfolioOptimizerService": ".portfolio_optimizer",
    "CompetitiveIntelligenceService": ".competitive_intelligence",
}


def __getattr__(name: str) -> object:
    """Lazy-load exported AI service classes on first access."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value


__all__ = list(_EXPORTS)
