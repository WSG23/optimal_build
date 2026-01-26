/**
 * Page-specific types for SiteAcquisitionPage
 *
 * Note: API types live in frontend/src/api/siteAcquisition.ts
 * These types are for UI state and derived data structures only.
 */

import type {
  DevelopmentScenario,
  SiteAcquisitionResult,
  ConditionAttachment,
} from '../../../api/siteAcquisition'

// ============================================================================
// Condition Assessment Draft Types
// ============================================================================

export type AssessmentDraftSystem = {
  name: string
  rating: string
  score: string
  notes: string
  recommendedActions: string
}

export type ConditionAssessmentDraft = {
  scenario: DevelopmentScenario | 'all'
  overallRating: string
  overallScore: string
  riskLevel: string
  summary: string
  scenarioContext: string
  systems: AssessmentDraftSystem[]
  recommendedActionsText: string
  inspectorName: string
  recordedAtLocal: string
  attachmentsText: string
}

// ============================================================================
// Scenario Comparison Types
// ============================================================================

export type ScenarioComparisonKey = 'all' | DevelopmentScenario

export type ScenarioComparisonMetric = {
  key: string
  label: string
  value: string
}

export type InsightSeverity = 'critical' | 'warning' | 'positive' | 'info'

export type ConditionInsightView = {
  id: string
  severity: InsightSeverity
  title: string
  detail: string
  specialist: string | null
}

export type ScenarioComparisonDatum = {
  key: ScenarioComparisonKey
  label: string
  icon: string
  quickHeadline: string | null
  quickMetrics: ScenarioComparisonMetric[]
  conditionRating: string | null
  conditionScore: number | null
  riskLevel: string | null
  checklistCompleted: number | null
  checklistTotal: number | null
  checklistPercent: number | null
  insights: ConditionInsightView[]
  primaryInsight: ConditionInsightView | null
  recommendedAction: string | null
  recordedAt: string | null
  inspectorName: string | null
  source: 'manual' | 'heuristic'
}

// ============================================================================
// Quick Analysis Types
// ============================================================================

export type QuickAnalysisEntry =
  SiteAcquisitionResult['quickAnalysis']['scenarios'][number]

export type QuickAnalysisSnapshot = {
  propertyId: string
  generatedAt: string
  scenarios: SiteAcquisitionResult['quickAnalysis']['scenarios']
  comparison: ScenarioComparisonDatum[]
}

// ============================================================================
// Preview Layer Types
// ============================================================================

export type LayerBreakdownItem = {
  id: string
  label: string
  subtitle: string
  color: string
  description: string | null
  metrics: Array<{ label: string; value: string }>
}

// ============================================================================
// Property Overview Card Types
// ============================================================================

export type PropertyOverviewCard = {
  title: string
  subtitle?: string | null
  items: Array<{ label: string; value: string }>
  tags?: string[]
  note?: string | null
}

// ============================================================================
// Feasibility Signal Types
// ============================================================================

export type FeasibilitySignals = {
  opportunities: string[]
  risks: string[]
}

export type FeasibilitySignalEntry = {
  scenario: DevelopmentScenario
  label: string
  opportunities: string[]
  risks: string[]
}

// ============================================================================
// System Comparison Types (for inspection history)
// ============================================================================

export type SystemComparisonEntry = {
  name: string
  latest: {
    rating: string
    score: number
    notes: string
    recommendedActions: string[]
  } | null
  previous: {
    rating: string
    score: number
    notes: string
    recommendedActions: string[]
  } | null
  scoreDelta: number | undefined
}

// ============================================================================
// Attachment Parsing
// ============================================================================

export type ParsedAttachment = ConditionAttachment

// ============================================================================
// Scenario Option Types
// ============================================================================

export type ScenarioOption = {
  value: DevelopmentScenario
  label: string
  icon: string
  description?: string
}

// ============================================================================
// Checklist Progress Types
// ============================================================================

export type ChecklistProgressSummary = {
  total: number
  completed: number
  inProgress: number
  pending: number
  notApplicable: number
  completionPercentage: number
}
