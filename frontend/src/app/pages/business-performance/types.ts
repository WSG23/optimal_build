export type PipelineStageKey =
  | 'lead_captured'
  | 'qualification'
  | 'needs_analysis'
  | 'proposal'
  | 'negotiation'
  | 'agreement'
  | 'due_diligence'
  | 'awaiting_closure'
  | 'closed_won'
  | 'closed_lost'

export interface PipelineDealCard {
  id: string
  title: string
  assetType: string
  dealType: string
  estimatedValue: number | null
  currency: string
  confidence: number | null
  latestActivity?: string | null
  hasDispute?: boolean
}

export interface PipelineColumn {
  key: PipelineStageKey
  label: string
  deals: PipelineDealCard[]
  totalCount: number
  totalValue: number | null
  weightedValue: number | null
}

export interface DealSnapshot {
  id: string
  agentName: string
  title: string
  leadSource?: string | null
  stage: PipelineStageKey
  expectedCloseDate?: string | null
  notes?: string | null
}

export interface StageEvent {
  id: string
  toStage: PipelineStageKey
  fromStage?: PipelineStageKey | null
  recordedAt: string
  durationSeconds?: number | null
  changedBy?: string | null
  note?: string | null
  auditHash?: string | null
  auditSignature?: string | null
}

export interface CommissionEntry {
  id: string
  type: string
  status: string
  amount: number | null
  currency: string
  basisAmount?: number | null
  confirmedAt?: string | null
  disputedAt?: string | null
}

export interface AnalyticsMetric {
  key:
    | 'dealsOpen'
    | 'dealsWon'
    | 'grossPipeline'
    | 'weightedPipeline'
    | 'conversionRate'
    | 'avgCycle'
    | 'confirmedCommission'
    | 'disputedCommission'
  label: string
  value: string
  helperText?: string
}

export interface TrendPoint {
  label: string
  gross: number | null
  weighted: number | null
  conversion: number | null
  cycle: number | null
}

export interface BenchmarkEntry {
  key: 'conversion' | 'cycle' | 'pipeline'
  label: string
  actual: string
  benchmark?: string | null
  cohort?: string | null
  deltaText?: string | null
  deltaPositive?: boolean
}

export interface RoiProjectEntry {
  projectId: number
  hoursSaved: number | null
  automationScore: number | null
  acceptanceRate: number | null
  paybackWeeks: number | null
}

export interface RoiSummary {
  projectCount: number
  totalReviewHoursSaved: number | null
  averageAutomationScore: number | null
  averageAcceptanceRate: number | null
  averageSavingsPercent: number | null
  bestPaybackWeeks: number | null
  projects: RoiProjectEntry[]
}
