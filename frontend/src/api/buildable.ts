function normaliseBaseUrl(value: string | undefined | null): string {
  if (!value) {
    return '/'
  }
  const trimmed = value.trim()
  return trimmed === '' ? '/' : trimmed
}

const API_PREFIX = 'api/v1/screen/buildable'
const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL
const apiBaseUrl = normaliseBaseUrl(rawApiBaseUrl)

export type RuleProvenance = {
  rule_id: number
  clause_ref?: string | null
  document_id?: number | null
  pages?: number[] | null
  seed_tag?: string | null
  source?: string | null
}

export type RuleItem = {
  id: number
  authority: string
  parameter_key: string
  operator: string
  value: string
  unit?: string | null
  provenance: RuleProvenance
}

export type ZoneSource = {
  kind: 'parcel' | 'geometry' | 'unknown'
  layer_name?: string | null
  jurisdiction?: string | null
  parcel_ref?: string | null
  parcel_source?: string | null
  note?: string | null
}

export type BuildableResponse = {
  input_kind: 'address' | 'geometry'
  zone_code: string | null
  overlays: string[]
  advisory_hints?: string[] | null
  metrics: {
    gfa_cap_m2: number
    floors_max: number
    footprint_m2: number
    nsa_est_m2: number
  }
  zone_source: ZoneSource
  rules: RuleItem[]
}

export interface BuildableRequest {
  address: string
  typFloorToFloorM: number
  efficiencyRatio: number
}

export interface BuildableMetrics {
  gfaCapM2: number
  floorsMax: number
  footprintM2: number
  nsaEstM2: number
}

export interface BuildableRuleProvenance {
  ruleId: number
  clauseRef?: string
  documentId?: number
  pages?: number[]
  seedTag?: string
}

export interface BuildableRule {
  id: number
  authority: string
  parameterKey: string
  operator: string
  value: string
  unit?: string
  provenance: BuildableRuleProvenance
}

export interface ZoneSourceInfo {
  kind: 'parcel' | 'geometry' | 'unknown'
  layerName?: string
  jurisdiction?: string
  parcelRef?: string
  parcelSource?: string
  note?: string
}

export interface BuildableSummary {
  inputKind: 'address' | 'geometry'
  zoneCode: string | null
  overlays: string[]
  advisoryHints: string[]
  metrics: BuildableMetrics
  zoneSource: ZoneSourceInfo
  rules: BuildableRule[]
}

export interface BuildableTransportOptions {
  signal?: AbortSignal
}

export type BuildableTransport = (
  baseUrl: string,
  body: BuildableRequest,
  options?: BuildableTransportOptions,
) => Promise<BuildableResponse>

export interface BuildableRequestOptions extends BuildableTransportOptions {
  transport?: BuildableTransport
}

function buildUrl(path: string, base: string = apiBaseUrl) {
  if (/^https?:/i.test(path)) {
    return path
  }
  const trimmed = path.startsWith('/') ? path.slice(1) : path
  const root = normaliseBaseUrl(base)
  if (/^https?:/i.test(root)) {
    return new URL(trimmed, root.endsWith('/') ? root : `${root}/`).toString()
  }
  const normalisedRoot = root.endsWith('/') ? root : `${root}/`
  return `${normalisedRoot}${trimmed}`
}

function mapRule(rule: RuleItem): BuildableRule {
  return {
    id: rule.id,
    authority: rule.authority,
    parameterKey: rule.parameter_key,
    operator: rule.operator,
    value: rule.value,
    unit: rule.unit ?? undefined,
    provenance: {
      ruleId: rule.provenance.rule_id,
      clauseRef: rule.provenance.clause_ref ?? undefined,
      documentId: rule.provenance.document_id ?? undefined,
      pages: rule.provenance.pages ?? undefined,
      seedTag: rule.provenance.seed_tag ?? undefined,
    },
  }
}

function mapResponse(payload: BuildableResponse): BuildableSummary {
  const advisoryHints = Array.isArray(payload.advisory_hints)
    ? payload.advisory_hints.filter((hint): hint is string => typeof hint === 'string')
    : []

  return {
    inputKind: payload.input_kind,
    zoneCode: payload.zone_code,
    overlays: [...payload.overlays],
    advisoryHints: [...advisoryHints],
    metrics: {
      gfaCapM2: payload.metrics.gfa_cap_m2,
      floorsMax: payload.metrics.floors_max,
      footprintM2: payload.metrics.footprint_m2,
      nsaEstM2: payload.metrics.nsa_est_m2,
    },
    zoneSource: {
      kind: payload.zone_source.kind,
      layerName: payload.zone_source.layer_name ?? undefined,
      jurisdiction: payload.zone_source.jurisdiction ?? undefined,
      parcelRef: payload.zone_source.parcel_ref ?? undefined,
      parcelSource: payload.zone_source.parcel_source ?? undefined,
      note: payload.zone_source.note ?? undefined,
    },
    rules: payload.rules.map(mapRule),
  }
}

export async function postBuildable(
  baseUrl: string,
  body: BuildableRequest,
  options: BuildableTransportOptions = {},
): Promise<BuildableResponse> {
  const response = await fetch(buildUrl(API_PREFIX, baseUrl), {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      address: body.address,
      typ_floor_to_floor_m: body.typFloorToFloorM,
      efficiency_ratio: body.efficiencyRatio,
    }),
    signal: options.signal,
  })

  const contentType = response.headers.get('content-type') ?? ''

  if (!response.ok) {
    if (contentType.includes('application/json')) {
      const payload = (await response.json()) as { detail?: unknown; error?: unknown }
      const detail = typeof payload.detail === 'string' ? payload.detail : undefined
      const error = typeof payload.error === 'string' ? payload.error : undefined
      throw new Error(
        detail ?? error ?? `Request to /${API_PREFIX} failed with ${response.status}`,
      )
    }
    const message = await response.text()
    throw new Error(message || `Request to /${API_PREFIX} failed with ${response.status}`)
  }

  if (!contentType.includes('application/json')) {
    throw new Error(`Expected JSON response from /${API_PREFIX}`)
  }

  return (await response.json()) as BuildableResponse
}

export async function fetchBuildable(
  request: BuildableRequest,
  options: BuildableRequestOptions = {},
): Promise<BuildableSummary> {
  const { transport = postBuildable, signal } = options
  const payload = await transport(apiBaseUrl, request, { signal })
  return mapResponse(payload)
}
