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

export interface AdvisoryAssetMixSegment {
  use: string
  allocation_pct: number
  target_gfa_sqm: number | null
  rationale: string
}

export interface AdvisoryAssetMix {
  property_id: string
  total_programmable_gfa_sqm: number | null
  mix_recommendations: AdvisoryAssetMixSegment[]
  notes: string[]
}

export interface AdvisoryMarketPositioning {
  market_tier: string
  pricing_guidance: Record<string, Record<string, number>>
  target_segments: Array<Record<string, unknown>>
  messaging: string[]
}

export interface AdvisoryTimelineMilestone {
  milestone: string
  month: number
  expected_absorption_pct: number
}

export interface AdvisoryAbsorptionForecast {
  expected_months_to_stabilize: number
  monthly_velocity_target: number
  confidence: string
  timeline: AdvisoryTimelineMilestone[]
}

export interface AdvisoryFeedbackItem {
  id: string
  property_id: string
  submitted_by?: string | null
  channel?: string | null
  sentiment: string
  notes: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface AdvisorySummary {
  asset_mix: AdvisoryAssetMix
  market_positioning: AdvisoryMarketPositioning
  absorption_forecast: AdvisoryAbsorptionForecast
  feedback: AdvisoryFeedbackItem[]
}

export interface AdvisoryFeedbackPayload {
  sentiment: string
  notes: string
  channel?: string
  submitted_by?: string
  metadata?: Record<string, unknown>
}

export async function fetchAdvisorySummary(
  propertyId: string,
  signal?: AbortSignal,
): Promise<AdvisorySummary> {
  const response = await fetch(
    buildUrl(
      `/api/v1/agents/commercial-property/properties/${propertyId}/advisory`,
    ),
    { signal },
  )

  if (!response.ok) {
    throw new Error(
      `Failed to fetch advisory summary: ${response.status} ${response.statusText}`,
    )
  }

  const payload = (await response.json()) as AdvisorySummary
  return payload
}

export async function submitAdvisoryFeedback(
  propertyId: string,
  payload: AdvisoryFeedbackPayload,
  signal?: AbortSignal,
): Promise<AdvisoryFeedbackItem> {
  const response = await fetch(
    buildUrl(
      `/api/v1/agents/commercial-property/properties/${propertyId}/advisory/feedback`,
    ),
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    },
  )

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || 'Failed to submit advisory feedback')
  }

  const record = (await response.json()) as AdvisoryFeedbackItem
  return record
}

export async function fetchAdvisoryFeedback(
  propertyId: string,
  signal?: AbortSignal,
): Promise<AdvisoryFeedbackItem[]> {
  const response = await fetch(
    buildUrl(
      `/api/v1/agents/commercial-property/properties/${propertyId}/advisory/feedback`,
    ),
    { signal },
  )

  if (!response.ok) {
    throw new Error('Failed to load advisory feedback')
  }

  const payload = (await response.json()) as AdvisoryFeedbackItem[]
  return payload
}
