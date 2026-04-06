import type { DealCommission, DealTimelineEvent } from '../../../api/deals'
import type {
  PerformanceBenchmarkEntry,
  PerformanceSnapshot,
} from '../../../api/performance'
import type {
  AnalyticsMetric,
  BenchmarkEntry,
  CommissionEntry,
  RoiSummary,
  StageEvent,
  TrendPoint,
} from './types'

const NOT_AVAILABLE_TEXT = 'Not available yet'

export const EMPTY_ROI_SUMMARY: RoiSummary = {
  projectCount: 0,
  totalReviewHoursSaved: null,
  averageAutomationScore: null,
  averageAcceptanceRate: null,
  averageSavingsPercent: null,
  bestPaybackWeeks: null,
  projects: [],
}

export function mapCommissionEntry(entry: DealCommission): CommissionEntry {
  return {
    id: entry.id,
    type: entry.commissionType,
    status: entry.status,
    amount: entry.commissionAmount,
    currency: entry.basisCurrency,
    basisAmount: entry.basisAmount,
    confirmedAt: entry.confirmedAt,
    disputedAt: entry.disputedAt,
  }
}

export function convertTimeline(
  timelineData: DealTimelineEvent[],
): StageEvent[] {
  return timelineData.map((event) => ({
    id: event.id,
    toStage: event.toStage,
    fromStage: event.fromStage,
    recordedAt: formatDateTime(event.recordedAt),
    durationSeconds: event.durationSeconds,
    changedBy: event.changedBy,
    note: event.note,
    auditHash: event.auditLog?.hash ?? null,
    auditSignature: event.auditLog?.signature ?? null,
  }))
}

export function buildMetrics(
  snapshot: PerformanceSnapshot | null,
): AnalyticsMetric[] {
  if (!snapshot) {
    return []
  }
  const currencyFormatter = new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
    maximumFractionDigits: 0,
  })
  return [
    {
      key: 'dealsOpen',
      label: 'Open deals',
      value: snapshot.dealsOpen.toString(),
    },
    {
      key: 'dealsWon',
      label: 'Deals won (30d)',
      value: snapshot.dealsClosedWon.toString(),
    },
    {
      key: 'grossPipeline',
      label: 'Gross pipeline',
      value:
        snapshot.grossPipelineValue !== null
          ? currencyFormatter.format(snapshot.grossPipelineValue)
          : NOT_AVAILABLE_TEXT,
      helperText: 'All open opportunities, unweighted.',
    },
    {
      key: 'weightedPipeline',
      label: 'Weighted pipeline',
      value:
        snapshot.weightedPipelineValue !== null
          ? currencyFormatter.format(snapshot.weightedPipelineValue)
          : NOT_AVAILABLE_TEXT,
      helperText: 'Weighted by confidence percentage.',
    },
    {
      key: 'conversionRate',
      label: 'Conversion rate',
      value:
        snapshot.conversionRate !== null
          ? `${(snapshot.conversionRate * 100).toFixed(1)}%`
          : NOT_AVAILABLE_TEXT,
    },
    {
      key: 'avgCycle',
      label: 'Average cycle',
      value:
        snapshot.avgCycleDays !== null
          ? `${snapshot.avgCycleDays.toFixed(0)} days`
          : NOT_AVAILABLE_TEXT,
    },
    {
      key: 'confirmedCommission',
      label: 'Confirmed commission',
      value:
        snapshot.confirmedCommissionAmount !== null
          ? currencyFormatter.format(snapshot.confirmedCommissionAmount)
          : NOT_AVAILABLE_TEXT,
    },
    {
      key: 'disputedCommission',
      label: 'Disputed commission',
      value:
        snapshot.disputedCommissionAmount !== null
          ? currencyFormatter.format(snapshot.disputedCommissionAmount)
          : NOT_AVAILABLE_TEXT,
    },
  ]
}

export function buildTrend(history: PerformanceSnapshot[]): TrendPoint[] {
  return history
    .slice()
    .reverse()
    .map((snapshot) => ({
      label: snapshot.asOfDate,
      gross:
        snapshot.grossPipelineValue !== null
          ? snapshot.grossPipelineValue / 1_000_000
          : null,
      weighted:
        snapshot.weightedPipelineValue !== null
          ? snapshot.weightedPipelineValue / 1_000_000
          : null,
      conversion: snapshot.conversionRate,
      cycle: snapshot.avgCycleDays,
    }))
}

export function buildBenchmarks(
  conversion: PerformanceBenchmarkEntry[],
  cycle: PerformanceBenchmarkEntry[],
  pipeline: PerformanceBenchmarkEntry[],
): BenchmarkEntry[] {
  const entries: BenchmarkEntry[] = []
  const convertLabel = (cohort: string | null) => cohort ?? 'benchmark'
  if (conversion[0]) {
    entries.push({
      key: 'conversion',
      label: 'Conversion rate',
      actual:
        conversion[0].valueNumeric !== null
          ? `${(conversion[0].valueNumeric * 100).toFixed(1)}%`
          : (conversion[0].valueText ?? NOT_AVAILABLE_TEXT),
      benchmark:
        conversion[1]?.valueNumeric !== null
          ? `${(conversion[1].valueNumeric * 100).toFixed(1)}%`
          : (conversion[1]?.valueText ?? null),
      cohort: convertLabel(conversion[0].cohort),
      deltaText: null,
    })
  }
  if (cycle[0]) {
    entries.push({
      key: 'cycle',
      label: 'Average cycle time',
      actual:
        cycle[0].valueNumeric !== null
          ? `${cycle[0].valueNumeric.toFixed(0)} days`
          : (cycle[0].valueText ?? NOT_AVAILABLE_TEXT),
      benchmark:
        cycle[1]?.valueNumeric !== null
          ? `${cycle[1].valueNumeric.toFixed(0)} days`
          : (cycle[1]?.valueText ?? null),
      cohort: convertLabel(cycle[0].cohort),
      deltaText: null,
    })
  }
  if (pipeline[0]) {
    const currencyFormatter = new Intl.NumberFormat('en-SG', {
      style: 'currency',
      currency: 'SGD',
      maximumFractionDigits: 0,
    })
    entries.push({
      key: 'pipeline',
      label: 'Weighted pipeline value',
      actual:
        pipeline[0].valueNumeric !== null
          ? currencyFormatter.format(pipeline[0].valueNumeric)
          : (pipeline[0].valueText ?? NOT_AVAILABLE_TEXT),
      benchmark:
        pipeline[1]?.valueNumeric !== null
          ? currencyFormatter.format(pipeline[1].valueNumeric)
          : (pipeline[1]?.valueText ?? null),
      cohort: convertLabel(pipeline[0].cohort),
      deltaText: null,
    })
  }
  return entries
}

export function buildRoiSummary(
  snapshot: PerformanceSnapshot | null,
): RoiSummary {
  if (!snapshot) {
    return EMPTY_ROI_SUMMARY
  }
  const metrics = snapshot.roiMetrics
  const summary = (metrics?.summary ?? {}) as Record<string, unknown>
  const projects = Array.isArray(metrics?.projects)
    ? (metrics.projects as Record<string, unknown>[])
    : []
  return {
    projectCount: Number(summary.project_count ?? projects.length ?? 0),
    totalReviewHoursSaved: toNullableNumber(summary.total_review_hours_saved),
    averageAutomationScore: toNullableNumber(summary.average_automation_score),
    averageAcceptanceRate: toNullableNumber(summary.average_acceptance_rate),
    averageSavingsPercent: toNullableNumber(summary.savings_percent_average),
    bestPaybackWeeks: summary.best_payback_weeks
      ? Number(summary.best_payback_weeks)
      : null,
    projects: projects.map((project) => ({
      projectId: Number(project.project_id ?? 0),
      hoursSaved: toNullableNumber(project.review_hours_saved),
      automationScore: toNullableNumber(project.automation_score),
      acceptanceRate: toNullableNumber(project.acceptance_rate),
      paybackWeeks: project.payback_weeks
        ? Number(project.payback_weeks)
        : null,
    })),
  }
}

export function totalPipeline(
  columns: Array<{ totalValue: number | null }>,
): number | null {
  const total = columns.reduce(
    (sum, column) => sum + (column.totalValue ?? 0),
    0,
  )
  return total === 0 ? null : total
}

export function formatCurrency(value: number | null) {
  if (value === null) {
    return NOT_AVAILABLE_TEXT
  }
  return new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatRelativeDate(value: string | null) {
  if (!value) {
    return null
  }
  try {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) {
      return value
    }
    return date.toLocaleDateString()
  } catch {
    return value
  }
}

function formatDateTime(value: string | null) {
  if (!value) {
    return ''
  }
  try {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) {
      return value
    }
    return date.toLocaleString()
  } catch {
    return value
  }
}

function toNullableNumber(value: unknown): number | null {
  if (value === null || value === undefined) {
    return null
  }
  const parsed = Number(value)
  return Number.isNaN(parsed) ? null : parsed
}
