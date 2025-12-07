import type { DealStage } from '../../../api/deals'

export type {
  DealStage,
  DealSummary,
  DealTimelineEvent,
} from '../../../api/deals'
export type {
  PerformanceBenchmarkEntry,
  PerformanceSnapshot,
} from '../../../api/performance'

export const STAGE_TRANSLATION_KEYS: Record<DealStage, string> = {
  lead_captured: 'agentPerformance.stages.lead_captured',
  qualification: 'agentPerformance.stages.qualification',
  needs_analysis: 'agentPerformance.stages.needs_analysis',
  proposal: 'agentPerformance.stages.proposal',
  negotiation: 'agentPerformance.stages.negotiation',
  agreement: 'agentPerformance.stages.agreement',
  due_diligence: 'agentPerformance.stages.due_diligence',
  awaiting_closure: 'agentPerformance.stages.awaiting_closure',
  closed_won: 'agentPerformance.stages.closed_won',
  closed_lost: 'agentPerformance.stages.closed_lost',
}

export interface BenchmarkComparison {
  key: string
  label: string
  actual: string
  benchmark: string | null
  cohort: string | null
  deltaText: string
  deltaPositive: boolean
}

export interface TrendDataPoint {
  label: string
  gross: number | null
  weighted: number | null
  conversion: number | null
  cycle: number | null
}

export interface BenchmarkSet {
  conversion:
    | import('../../../api/performance').PerformanceBenchmarkEntry
    | null
  cycle: import('../../../api/performance').PerformanceBenchmarkEntry | null
  pipeline: import('../../../api/performance').PerformanceBenchmarkEntry | null
}
