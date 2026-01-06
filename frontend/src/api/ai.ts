/**
 * AI Services API client for frontend integration.
 *
 * This module provides typed access to the 16 AI services exposed through the backend.
 */

import { buildSimpleUrl } from './utils'

const buildUrl = buildSimpleUrl

// ============================================================================
// Common Types
// ============================================================================

export interface AIHealthStatus {
  status: string
  services: Record<string, boolean>
}

// ============================================================================
// Natural Language Query Types
// ============================================================================

export interface NLQueryRequest {
  query: string
  user_id?: string
}

export interface NLQueryResponse {
  query: string
  intent: string
  entities: Record<string, unknown>
  structured_query: Record<string, unknown> | null
  confidence: number
  suggested_action: string | null
}

// ============================================================================
// Knowledge Base Types
// ============================================================================

export type SearchMode = 'semantic' | 'keyword' | 'hybrid'
export type KnowledgeSourceType =
  | 'property'
  | 'deal'
  | 'transaction'
  | 'regulatory'
  | 'document'
  | 'market_report'
  | 'news'
  | 'internal_note'

export interface KnowledgeSearchRequest {
  query: string
  mode?: SearchMode
  source_types?: KnowledgeSourceType[]
  limit?: number
  generate_answer?: boolean
}

export interface SearchResultItem {
  chunk_id: string
  source_type: string
  source_id: string
  content: string
  relevance_score: number
  metadata: Record<string, unknown>
}

export interface KnowledgeSearchResponse {
  query: string
  results: SearchResultItem[]
  total_chunks_searched: number
  search_time_ms: number
  generated_answer: string | null
}

export interface IngestionResponse {
  success: boolean
  chunks_created: number
  source_type: string
  source_id: string
  error: string | null
}

// ============================================================================
// Deal Scoring Types
// ============================================================================

export interface FactorScore {
  factor: string
  score: number
  weight: number
  weighted_score: number
  rationale: string
}

export interface DealScoreResponse {
  deal_id: string
  overall_score: number
  grade: string
  factor_scores: FactorScore[]
  recommendation: string
  confidence: number
  scored_at: string
}

// ============================================================================
// Scenario Optimizer Types
// ============================================================================

export type FinancingType = 'conventional' | 'construction' | 'bridge' | 'mezzanine'

export interface ScenarioOptimizeRequest {
  project_id: string
  financing_types?: FinancingType[]
  target_irr?: number
  max_leverage?: number
}

export interface FinancingScenario {
  id: string
  financing_type: string
  loan_amount: number
  ltv_ratio: number
  interest_rate: number
  debt_service_coverage: number
  projected_irr: number
  projected_equity_multiple: number
  total_interest_cost: number
  recommendation_score: number
}

export interface ScenarioOptimizeResponse {
  project_id: string
  scenarios: FinancingScenario[]
  recommended_scenario_id: string | null
  analysis_summary: string
}

// ============================================================================
// Market Predictor Types
// ============================================================================

export type PredictionType = 'rental' | 'capital_value' | 'supply' | 'demand'

export interface MarketPredictionRequest {
  property_id?: string
  district?: string
  property_type?: string
  prediction_types?: PredictionType[]
  forecast_months?: number
}

export interface PredictionItem {
  prediction_type: string
  current_value: number | null
  predicted_value: number | null
  change_percentage: number | null
  confidence: number
  factors: string[]
}

export interface MarketPredictionResponse {
  predictions: PredictionItem[]
  forecast_months: number
  generated_at: string
  summary: string
}

// ============================================================================
// Due Diligence Types
// ============================================================================

export interface DDItem {
  id: string
  category: string
  name: string
  description: string
  priority: string
  status: string
  requires_external: boolean
  external_source: string | null
  assigned_to: string | null
  due_date: string | null
  notes: string | null
}

export interface DDRecommendation {
  title: string
  description: string
  priority: string
  action_items: string[]
}

export interface DDChecklistResponse {
  id: string
  deal_id: string
  deal_title: string
  items: DDItem[]
  recommendations: DDRecommendation[]
  completion_percentage: number
  estimated_days_to_complete: number
}

// ============================================================================
// Report Generator Types
// ============================================================================

export interface ReportSection {
  title: string
  content: string
  order: number
}

export interface ReportResponse {
  id: string
  report_type: string
  title: string
  subtitle: string | null
  generated_at: string
  sections: ReportSection[]
  executive_summary: string | null
  recommendations: string[]
  generation_time_ms: number
}

// ============================================================================
// Communication Drafter Types
// ============================================================================

export type CommunicationType = 'email' | 'letter' | 'sms' | 'proposal' | 'memo'
export type CommunicationTone = 'formal' | 'professional' | 'friendly' | 'urgent'
export type CommunicationPurpose =
  | 'introduction'
  | 'follow_up'
  | 'offer'
  | 'counter_offer'
  | 'negotiation'
  | 'closing'
  | 'thank_you'
  | 'update'
  | 'request'
  | 'rejection'

export interface DraftCommunicationRequest {
  communication_type: CommunicationType
  purpose: CommunicationPurpose
  tone?: CommunicationTone
  recipient_name?: string
  recipient_company?: string
  recipient_role?: string
  deal_id?: string
  property_id?: string
  key_points?: string[]
  additional_context?: string
  include_alternatives?: boolean
}

export interface CommunicationDraftResponse {
  id: string
  communication_type: string
  purpose: string
  tone: string
  subject: string | null
  body: string
  alternatives: string[]
  generation_time_ms: number
}

// ============================================================================
// Conversational Assistant Types
// ============================================================================

export interface ChatMessageRequest {
  message: string
  conversation_id?: string
  user_id?: string
}

export interface ChatMessageResponse {
  conversation_id: string
  message: string
  suggestions: string[]
  actions_taken: Record<string, unknown>[]
  context_updates: Record<string, unknown>
}

export interface ConversationSummary {
  conversation_id: string
  user_id: string
  message_count: number
  created_at: string
  last_message_at: string
}

// ============================================================================
// Portfolio Optimizer Types
// ============================================================================

export type OptimizationStrategy =
  | 'maximize_returns'
  | 'minimize_risk'
  | 'balanced'
  | 'income_focused'
  | 'growth_focused'
export type RiskProfile = 'conservative' | 'moderate' | 'aggressive'

export interface PortfolioOptimizeRequest {
  user_id: string
  strategy?: OptimizationStrategy
  risk_profile?: RiskProfile
  max_concentration?: number
  min_liquidity?: number
}

export interface AssetAllocation {
  asset_type: string
  current_value: number
  current_percentage: number
  recommended_percentage: number
  variance: number
  action: string
}

export interface RebalancingRecommendation {
  asset_id: string
  asset_name: string
  asset_type: string
  current_allocation: number
  recommended_action: string
  target_allocation: number
  rationale: string
  priority: string
}

export interface PortfolioMetrics {
  total_value: number
  total_assets: number
  weighted_yield: number
  portfolio_beta: number
  diversification_score: number
  concentration_risk: string
  liquidity_score: number
}

export interface PortfolioOptimizeResponse {
  id: string
  user_id: string
  strategy: string
  risk_profile: string
  metrics: PortfolioMetrics
  current_allocation: AssetAllocation[]
  recommendations: RebalancingRecommendation[]
  target_allocation: Record<string, number>
  expected_improvement: Record<string, number>
  analysis_summary: string
}

// ============================================================================
// Image Analysis Types
// ============================================================================

export type ImageType =
  | 'floor_plan'
  | 'site_photo'
  | 'aerial_view'
  | 'building_facade'
  | 'interior'
  | 'document'
  | 'map'
export type AnalysisType =
  | 'space_analysis'
  | 'condition_assessment'
  | 'layout_extraction'
  | 'text_extraction'

export interface ImageAnalysisRequest {
  image_base64?: string
  image_url?: string
  image_type: ImageType
  analysis_types?: AnalysisType[]
  property_id?: string
}

export interface SpaceMetrics {
  total_area_sqm: number | null
  usable_area_sqm: number | null
  room_count: number | null
  efficiency_ratio: number | null
  parking_spaces: number | null
  floors_detected: number | null
}

export interface ConditionAssessment {
  overall_condition: string | null
  condition_score: number | null
  issues_detected: string[]
  maintenance_recommendations: string[]
  estimated_capex: string | null
  age_assessment: string | null
}

export interface ImageAnalysisResponse {
  id: string
  image_type: string
  analysis_type: string
  space_metrics: SpaceMetrics | null
  condition: ConditionAssessment | null
  extracted_text: string | null
  confidence: number
  processing_time_ms: number
}

// ============================================================================
// Competitive Intelligence Types
// ============================================================================

export interface Competitor {
  id: string
  name: string
  competitor_type: string
  focus_sectors: string[]
  focus_districts: string[]
  tracked_since: string
}

export interface CompetitorActivity {
  id: string
  competitor_id: string
  competitor_name: string
  category: string
  title: string
  description: string
  location: string | null
  relevance_score: number
  detected_at: string
}

export interface CompetitiveAlert {
  id: string
  priority: string
  title: string
  description: string
  competitor_id: string
  competitor_name: string
  action_required: string
  expires_at: string
}

export interface CompetitiveIntelligenceResponse {
  competitors: Competitor[]
  activities: CompetitorActivity[]
  alerts: CompetitiveAlert[]
  summary: string
}

// ============================================================================
// Workflow Types
// ============================================================================

export type WorkflowTrigger =
  | 'deal_created'
  | 'deal_stage_changed'
  | 'deadline_approaching'
  | 'document_uploaded'
  | 'approval_required'
  | 'compliance_flag'
  | 'market_alert'

export interface WorkflowStep {
  action_id: string
  action_type: string
  status: string
  started_at: string | null
  completed_at: string | null
  result: Record<string, unknown> | null
  error: string | null
}

export interface WorkflowResult {
  workflow_id: string
  workflow_name: string
  instance_id: string
  status: string
  started_at: string
  completed_at: string | null
  steps: WorkflowStep[]
}

export interface WorkflowDefinition {
  id: string
  name: string
  description: string
  trigger: string
  is_active: boolean
  action_count: number
}

// ============================================================================
// Anomaly Detection Types
// ============================================================================

export interface AnomalyAlert {
  id: string
  alert_type: string
  severity: string
  title: string
  description: string
  entity_type: string
  entity_id: string
  detected_value: unknown
  expected_range: Record<string, unknown> | null
  recommendation: string
  detected_at: string
}

export interface AnomalyDetectionResponse {
  alerts: AnomalyAlert[]
  entities_scanned: number
  scan_time_ms: number
}

// ============================================================================
// Document Extraction Types
// ============================================================================

export interface ExtractedClause {
  clause_type: string
  text: string
  page_number: number | null
  confidence: number
}

export interface ExtractedTable {
  table_id: string
  headers: string[]
  rows: string[][]
  page_number: number | null
}

export interface DocumentExtractionResponse {
  document_type: string
  clauses: ExtractedClause[]
  tables: ExtractedTable[]
  key_dates: Record<string, string>
  parties: string[]
  summary: string
  processing_time_ms: number
}

// ============================================================================
// API Functions
// ============================================================================

async function fetchApi<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(buildUrl(path), {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

// Health check
export async function checkAIHealth(): Promise<AIHealthStatus> {
  return fetchApi<AIHealthStatus>('/api/v1/ai/health')
}

// Natural Language Query
export async function processNaturalLanguageQuery(
  request: NLQueryRequest,
): Promise<NLQueryResponse> {
  return fetchApi<NLQueryResponse>('/api/v1/ai/query', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Knowledge Base
export async function searchKnowledge(
  request: KnowledgeSearchRequest,
): Promise<KnowledgeSearchResponse> {
  return fetchApi<KnowledgeSearchResponse>('/api/v1/ai/knowledge/search', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function ingestProperty(
  propertyId: string,
): Promise<IngestionResponse> {
  return fetchApi<IngestionResponse>('/api/v1/ai/knowledge/ingest/property', {
    method: 'POST',
    body: JSON.stringify({ property_id: propertyId }),
  })
}

export async function ingestDeal(dealId: string): Promise<IngestionResponse> {
  return fetchApi<IngestionResponse>('/api/v1/ai/knowledge/ingest/deal', {
    method: 'POST',
    body: JSON.stringify({ deal_id: dealId }),
  })
}

export async function ingestDocument(
  documentId: string,
  content: string,
  metadata: Record<string, unknown> = {},
): Promise<IngestionResponse> {
  return fetchApi<IngestionResponse>('/api/v1/ai/knowledge/ingest/document', {
    method: 'POST',
    body: JSON.stringify({ document_id: documentId, content, metadata }),
  })
}

// Deal Scoring
export async function scoreDeal(dealId: string): Promise<DealScoreResponse> {
  return fetchApi<DealScoreResponse>('/api/v1/ai/deals/score', {
    method: 'POST',
    body: JSON.stringify({ deal_id: dealId }),
  })
}

// Scenario Optimizer
export async function optimizeScenarios(
  request: ScenarioOptimizeRequest,
): Promise<ScenarioOptimizeResponse> {
  return fetchApi<ScenarioOptimizeResponse>('/api/v1/ai/scenarios/optimize', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Market Predictor
export async function predictMarket(
  request: MarketPredictionRequest,
): Promise<MarketPredictionResponse> {
  return fetchApi<MarketPredictionResponse>('/api/v1/ai/market/predict', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Due Diligence
export async function generateDueDiligence(
  dealId: string,
): Promise<DDChecklistResponse> {
  return fetchApi<DDChecklistResponse>('/api/v1/ai/due-diligence/generate', {
    method: 'POST',
    body: JSON.stringify({ deal_id: dealId }),
  })
}

// Report Generator
export async function generateICMemo(dealId: string): Promise<ReportResponse> {
  return fetchApi<ReportResponse>('/api/v1/ai/reports/ic-memo', {
    method: 'POST',
    body: JSON.stringify({ deal_id: dealId }),
  })
}

export async function generatePortfolioReport(
  userId: string,
): Promise<ReportResponse> {
  return fetchApi<ReportResponse>('/api/v1/ai/reports/portfolio', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  })
}

// Communication Drafter
export async function draftCommunication(
  request: DraftCommunicationRequest,
): Promise<CommunicationDraftResponse> {
  return fetchApi<CommunicationDraftResponse>('/api/v1/ai/communications/draft', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Conversational Assistant
export async function sendChatMessage(
  request: ChatMessageRequest,
): Promise<ChatMessageResponse> {
  return fetchApi<ChatMessageResponse>('/api/v1/ai/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function listConversations(
  userId: string,
): Promise<ConversationSummary[]> {
  return fetchApi<ConversationSummary[]>(
    `/api/v1/ai/chat/conversations?user_id=${encodeURIComponent(userId)}`,
  )
}

export async function clearConversation(
  conversationId: string,
): Promise<{ success: boolean }> {
  return fetchApi<{ success: boolean }>(
    `/api/v1/ai/chat/conversations/${encodeURIComponent(conversationId)}`,
    { method: 'DELETE' },
  )
}

// Portfolio Optimizer
export async function optimizePortfolio(
  request: PortfolioOptimizeRequest,
): Promise<PortfolioOptimizeResponse> {
  return fetchApi<PortfolioOptimizeResponse>('/api/v1/ai/portfolio/optimize', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Image Analysis
export async function analyzeImage(
  request: ImageAnalysisRequest,
): Promise<ImageAnalysisResponse> {
  return fetchApi<ImageAnalysisResponse>('/api/v1/ai/images/analyze', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Competitive Intelligence
export async function trackCompetitor(
  name: string,
  competitorType: string,
  focusSectors: string[] = [],
  focusDistricts: string[] = [],
  notes?: string,
): Promise<Competitor> {
  return fetchApi<Competitor>('/api/v1/ai/competitors/track', {
    method: 'POST',
    body: JSON.stringify({
      name,
      competitor_type: competitorType,
      focus_sectors: focusSectors,
      focus_districts: focusDistricts,
      notes,
    }),
  })
}

export async function listCompetitors(): Promise<Competitor[]> {
  return fetchApi<Competitor[]>('/api/v1/ai/competitors')
}

export async function gatherIntelligence(
  userId: string,
): Promise<CompetitiveIntelligenceResponse> {
  return fetchApi<CompetitiveIntelligenceResponse>('/api/v1/ai/intelligence/gather', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  })
}

// Workflow Engine
export async function triggerWorkflow(
  trigger: WorkflowTrigger,
  eventData: Record<string, unknown>,
): Promise<WorkflowResult[]> {
  return fetchApi<WorkflowResult[]>('/api/v1/ai/workflows/trigger', {
    method: 'POST',
    body: JSON.stringify({ trigger, event_data: eventData }),
  })
}

export async function listWorkflows(): Promise<WorkflowDefinition[]> {
  return fetchApi<WorkflowDefinition[]>('/api/v1/ai/workflows')
}

export async function checkDeadlines(): Promise<WorkflowResult[]> {
  return fetchApi<WorkflowResult[]>('/api/v1/ai/workflows/check-deadlines', {
    method: 'POST',
  })
}

// Anomaly Detection
export async function detectAnomalies(params: {
  deal_id?: string
  property_id?: string
  project_id?: string
}): Promise<AnomalyDetectionResponse> {
  return fetchApi<AnomalyDetectionResponse>('/api/v1/ai/anomalies/detect', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

// Document Extraction
export async function extractDocument(params: {
  document_base64?: string
  document_url?: string
  document_type?: string
  extract_tables?: boolean
  extract_clauses?: boolean
}): Promise<DocumentExtractionResponse> {
  return fetchApi<DocumentExtractionResponse>('/api/v1/ai/documents/extract', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}
