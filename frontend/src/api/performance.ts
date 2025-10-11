function normaliseBaseUrl(value: string | undefined | null): string {
  if (typeof value !== 'string') {
    return '/'
  }
  const trimmed = value.trim()
  return trimmed === '' ? '/' : trimmed
}

const metaEnv =
  typeof import.meta !== 'undefined' && import.meta
    ? (import.meta as ImportMeta).env
    : undefined
const rawApiBaseUrl = metaEnv?.VITE_API_BASE_URL ?? null
const apiBaseUrl = normaliseBaseUrl(rawApiBaseUrl)

function buildUrl(path: string, base: string = apiBaseUrl) {
  const normalised = base.endsWith('/') ? base.slice(0, -1) : base
  if (path.startsWith('/')) {
    return `${normalised}${path}`
  }
  return `${normalised}/${path}`
}

export interface PerformanceSnapshotSummary {
  id: string
  agentId: string
  asOfDate: string
  dealsOpen: number
  dealsClosedWon: number
  dealsClosedLost: number
  grossPipelineValue: number | null
  weightedPipelineValue: number | null
  confirmedCommissionAmount: number | null
  disputedCommissionAmount: number | null
  avgCycleDays: number | null
  conversionRate: number | null
  roiMetrics: Record<string, unknown>
  snapshotContext: Record<string, unknown>
}

export interface PerformanceBenchmarkEntry {
  id: string
  metricKey: string
  assetType: string | null
  dealType: string | null
  cohort: string
  valueNumeric: number | null
  valueText: string | null
  source: string | null
  effectiveDate: string | null
}

function mapSnapshot(payload: Record<string, unknown>): PerformanceSnapshotSummary {
  return {
    id: String(payload.id ?? ''),
    agentId: String(payload.agent_id ?? ''),
    asOfDate: String(payload.as_of_date ?? ''),
    dealsOpen: Number(payload.deals_open ?? 0),
    dealsClosedWon: Number(payload.deals_closed_won ?? 0),
    dealsClosedLost: Number(payload.deals_closed_lost ?? 0),
    grossPipelineValue:
      typeof payload.gross_pipeline_value === 'number'
        ? payload.gross_pipeline_value
        : payload.gross_pipeline_value !== null
        ? Number(payload.gross_pipeline_value)
        : null,
    weightedPipelineValue:
      typeof payload.weighted_pipeline_value === 'number'
        ? payload.weighted_pipeline_value
        : payload.weighted_pipeline_value !== null
        ? Number(payload.weighted_pipeline_value)
        : null,
    confirmedCommissionAmount:
      typeof payload.confirmed_commission_amount === 'number'
        ? payload.confirmed_commission_amount
        : payload.confirmed_commission_amount !== null
        ? Number(payload.confirmed_commission_amount)
        : null,
    disputedCommissionAmount:
      typeof payload.disputed_commission_amount === 'number'
        ? payload.disputed_commission_amount
        : payload.disputed_commission_amount !== null
        ? Number(payload.disputed_commission_amount)
        : null,
    avgCycleDays:
      typeof payload.avg_cycle_days === 'number'
        ? payload.avg_cycle_days
        : payload.avg_cycle_days !== null
        ? Number(payload.avg_cycle_days)
        : null,
    conversionRate:
      typeof payload.conversion_rate === 'number'
        ? payload.conversion_rate
        : payload.conversion_rate !== null
        ? Number(payload.conversion_rate)
        : null,
    roiMetrics:
      typeof payload.roi_metrics === 'object' && payload.roi_metrics !== null
        ? (payload.roi_metrics as Record<string, unknown>)
        : {},
    snapshotContext:
      typeof payload.snapshot_context === 'object' && payload.snapshot_context !== null
        ? (payload.snapshot_context as Record<string, unknown>)
        : {},
  }
}

function mapBenchmark(payload: Record<string, unknown>): PerformanceBenchmarkEntry {
  return {
    id: String(payload.id ?? ''),
    metricKey: String(payload.metric_key ?? ''),
    assetType:
      typeof payload.asset_type === 'string' || payload.asset_type === null
        ? (payload.asset_type as string | null)
        : null,
    dealType:
      typeof payload.deal_type === 'string' || payload.deal_type === null
        ? (payload.deal_type as string | null)
        : null,
    cohort: String(payload.cohort ?? ''),
    valueNumeric:
      typeof payload.value_numeric === 'number'
        ? payload.value_numeric
        : payload.value_numeric !== null
        ? Number(payload.value_numeric)
        : null,
    valueText:
      typeof payload.value_text === 'string' || payload.value_text === null
        ? (payload.value_text as string | null)
        : null,
    source:
      typeof payload.source === 'string' || payload.source === null
        ? (payload.source as string | null)
        : null,
    effectiveDate:
      typeof payload.effective_date === 'string' || payload.effective_date === null
        ? (payload.effective_date as string | null)
        : null,
  }
}

export async function fetchLatestSnapshot(agentId: string, signal?: AbortSignal) {
  const response = await fetch(
    buildUrl(`/api/v1/performance/snapshots?agent_id=${agentId}&limit=1`),
    { signal },
  )
  if (!response.ok) {
    throw new Error('Failed to load performance snapshots')
  }
  const payload = (await response.json()) as Record<string, unknown>[]
  const [first] = payload
  return first ? mapSnapshot(first) : null
}

export async function fetchSnapshotsHistory(
  agentId: string,
  limit = 30,
  signal?: AbortSignal,
) {
  const response = await fetch(
    buildUrl(`/api/v1/performance/snapshots?agent_id=${agentId}&limit=${limit}`),
    { signal },
  )
  if (!response.ok) {
    throw new Error('Failed to load performance snapshots history')
  }
  const payload = (await response.json()) as Record<string, unknown>[]
  return payload.map(mapSnapshot)
}

export async function fetchBenchmarks(
  metricKey: string,
  options: {
    assetType?: string | null
    dealType?: string | null
    cohort?: string | null
    signal?: AbortSignal
  } = {},
) {
  const params = new URLSearchParams({ metric_key: metricKey })
  if (options.assetType) params.set('asset_type', options.assetType)
  if (options.dealType) params.set('deal_type', options.dealType)
  if (options.cohort) params.set('cohort', options.cohort)
  const response = await fetch(
    buildUrl(`/api/v1/performance/benchmarks?${params.toString()}`),
    { signal: options.signal },
  )
  if (!response.ok) {
    throw new Error('Failed to load performance benchmarks')
  }
  const payload = (await response.json()) as Record<string, unknown>[]
  return payload.map(mapBenchmark)
}

export type { PerformanceSnapshotSummary as PerformanceSnapshot, PerformanceBenchmarkEntry }
