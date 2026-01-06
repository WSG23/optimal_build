"""AI Services Package - Phases 1-4 of AI Rollout Plan."""

from app.services.ai.natural_language_query import NaturalLanguageQueryService
from app.services.ai.document_extractor import DocumentExtractionService
from app.services.ai.anomaly_detector import AnomalyDetectionService
from app.services.ai.rag_knowledge_base import RAGKnowledgeBaseService
from app.services.ai.deal_scoring import DealScoringService
from app.services.ai.scenario_optimizer import ScenarioOptimizerService
from app.services.ai.market_predictor import MarketPredictorService
from app.services.ai.compliance_predictor import CompliancePredictorService
from app.services.ai.due_diligence_generator import DueDiligenceService
from app.services.ai.report_generator import AIReportGenerator
from app.services.ai.communication_drafter import CommunicationDrafterService
from app.services.ai.workflow_engine import WorkflowEngineService
from app.services.ai.conversational_assistant import ConversationalAssistantService
from app.services.ai.multi_modal_analyzer import MultiModalAnalyzerService
from app.services.ai.portfolio_optimizer import PortfolioOptimizerService
from app.services.ai.competitive_intelligence import CompetitiveIntelligenceService

__all__ = [
    # Phase 1: Foundation
    "NaturalLanguageQueryService",
    "DocumentExtractionService",
    "AnomalyDetectionService",
    "RAGKnowledgeBaseService",
    # Phase 2: Predictive
    "DealScoringService",
    "ScenarioOptimizerService",
    "MarketPredictorService",
    "CompliancePredictorService",
    # Phase 3: Automation
    "DueDiligenceService",
    "AIReportGenerator",
    "CommunicationDrafterService",
    "WorkflowEngineService",
    # Phase 4: Advanced
    "ConversationalAssistantService",
    "MultiModalAnalyzerService",
    "PortfolioOptimizerService",
    "CompetitiveIntelligenceService",
]
