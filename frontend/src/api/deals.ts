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

export type DealStage =
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

export const DEAL_STAGE_ORDER: DealStage[] = [
  'lead_captured',
  'qualification',
  'needs_analysis',
  'proposal',
  'negotiation',
  'agreement',
  'due_diligence',
  'awaiting_closure',
  'closed_won',
  'closed_lost',
]

export interface DealSummary {
  id: string
  agentId: string
  title: string
  description: string | null
  assetType: string
  dealType: string
  pipelineStage: DealStage
  status: string
  leadSource: string | null
  estimatedValueAmount: number | null
  estimatedValueCurrency: string
  expectedCloseDate: string | null
  actualCloseDate: string | null
  confidence: number | null
  metadata: Record<string, unknown>
  createdAt: string
  updatedAt: string
}

export interface AuditLogSummary {
  id: number
  projectId: number
  eventType: string
  version: number
  baselineSeconds: number | null
  actualSeconds: number | null
  context: Record<string, unknown>
  recordedAt: string | null
  hash: string
  prevHash: string | null
  signature: string
}

export interface DealTimelineEvent {
  id: string
  dealId: string
  fromStage: DealStage | null
  toStage: DealStage
  changedBy: string | null
  note: string | null
  recordedAt: string
  metadata: Record<string, unknown>
  durationSeconds: number | null
  auditLog: AuditLogSummary | null
}

function toNumberOrNull(value: unknown): number | null {
  if (typeof value === 'number') {
    return Number.isNaN(value) ? null : value
  }
  if (value === null || value === undefined) {
    return null
  }
  const parsed = Number(value)
  return Number.isNaN(parsed) ? null : parsed
}

function mapDeal(payload: Record<string, unknown>): DealSummary {
  return {
    id: String(payload.id ?? ''),
    agentId: String(payload.agent_id ?? ''),
    title: String(payload.title ?? ''),
    description:
      typeof payload.description === 'string' || payload.description === null
        ? (payload.description as string | null)
        : null,
    assetType: String(payload.asset_type ?? ''),
    dealType: String(payload.deal_type ?? ''),
    pipelineStage: String(
      payload.pipeline_stage ?? 'lead_captured',
    ) as DealStage,
    status: String(payload.status ?? ''),
    leadSource:
      typeof payload.lead_source === 'string' || payload.lead_source === null
        ? (payload.lead_source as string | null)
        : null,
    estimatedValueAmount: toNumberOrNull(payload.estimated_value_amount),
    estimatedValueCurrency: String(payload.estimated_value_currency ?? 'SGD'),
    expectedCloseDate:
      typeof payload.expected_close_date === 'string'
        ? payload.expected_close_date
        : null,
    actualCloseDate:
      typeof payload.actual_close_date === 'string'
        ? payload.actual_close_date
        : null,
    confidence: toNumberOrNull(payload.confidence),
    metadata:
      typeof payload.metadata === 'object' && payload.metadata !== null
        ? (payload.metadata as Record<string, unknown>)
        : {},
    createdAt: typeof payload.created_at === 'string' ? payload.created_at : '',
    updatedAt: typeof payload.updated_at === 'string' ? payload.updated_at : '',
  }
}

export async function fetchDeals(signal?: AbortSignal): Promise<DealSummary[]> {
  const response = await fetch(buildUrl('/api/v1/deals'), { signal })
  if (!response.ok) {
    throw new Error('Failed to load deals')
  }
  const payload = (await response.json()) as Record<string, unknown>[]
  return payload.map(mapDeal)
}

function mapAuditSummary(payload: unknown): AuditLogSummary | null {
  if (!payload || typeof payload !== 'object') {
    return null
  }
  const value = payload as Record<string, unknown>
  const id = toNumberOrNull(value.id)
  const projectId = toNumberOrNull(value.project_id)
  if (id === null || projectId === null) {
    return null
  }
  return {
    id,
    projectId,
    eventType: String(value.event_type ?? ''),
    version: toNumberOrNull(value.version) ?? 0,
    baselineSeconds: toNumberOrNull(value.baseline_seconds),
    actualSeconds: toNumberOrNull(value.actual_seconds),
    context:
      typeof value.context === 'object' && value.context !== null
        ? (value.context as Record<string, unknown>)
        : {},
    recordedAt:
      typeof value.recorded_at === 'string' ? value.recorded_at : null,
    hash: String(value.hash ?? ''),
    prevHash:
      typeof value.prev_hash === 'string' || value.prev_hash === null
        ? (value.prev_hash as string | null)
        : null,
    signature: String(value.signature ?? ''),
  }
}

function mapTimelineEvent(payload: Record<string, unknown>): DealTimelineEvent {
  return {
    id: String(payload.id ?? ''),
    dealId: String(payload.deal_id ?? ''),
    fromStage:
      typeof payload.from_stage === 'string'
        ? (payload.from_stage as DealStage)
        : null,
    toStage: String(payload.to_stage ?? '') as DealStage,
    changedBy:
      typeof payload.changed_by === 'string' ? payload.changed_by : null,
    note:
      typeof payload.note === 'string' || payload.note === null
        ? (payload.note as string | null)
        : null,
    recordedAt: String(payload.recorded_at ?? ''),
    metadata:
      typeof payload.metadata === 'object' && payload.metadata !== null
        ? (payload.metadata as Record<string, unknown>)
        : {},
    durationSeconds: toNumberOrNull(payload.duration_seconds),
    auditLog: mapAuditSummary(payload.audit_log),
  }
}

export async function fetchDealTimeline(
  dealId: string,
  signal?: AbortSignal,
): Promise<DealTimelineEvent[]> {
  const response = await fetch(buildUrl(`/api/v1/deals/${dealId}/timeline`), {
    signal,
  })
  if (!response.ok) {
    throw new Error('Failed to load deal timeline')
  }
  const payload = (await response.json()) as Record<string, unknown>[]
  return payload.map(mapTimelineEvent)
}

export async function fetchDealSummary(
  dealId: string,
  signal?: AbortSignal,
): Promise<DealSummary> {
  const response = await fetch(buildUrl(`/api/v1/deals/${dealId}`), { signal })
  if (!response.ok) {
    throw new Error('Failed to load deal')
  }
  const payload = (await response.json()) as Record<string, unknown>
  return mapDeal(payload)
}
