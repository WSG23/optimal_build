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
const useMockData = import.meta.env.VITE_FEASIBILITY_USE_MOCKS === 'true'

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
  advisory_hints: string[]
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

export interface BuildableRequestOptions {
  signal?: AbortSignal
}

const MOCK_RESPONSES: Record<string, BuildableResponse> = {
  '123 example ave': {
    input_kind: 'address',
    zone_code: 'R2',
    overlays: ['heritage', 'daylight'],
    advisory_hints: [
      'Heritage impact assessment required before façade alterations.',
      'Respect daylight plane controls along the street frontage.',
    ],
    metrics: {
      gfa_cap_m2: 4375,
      floors_max: 8,
      footprint_m2: 563,
      nsa_est_m2: 3588,
    },
    zone_source: {
      kind: 'parcel',
      layer_name: 'MasterPlan',
      jurisdiction: 'SG',
      parcel_ref: 'MK01-01234',
      parcel_source: 'sample_loader',
    },
    rules: [
      {
        id: 1,
        authority: 'URA',
        parameter_key: 'parking.min_car_spaces_per_unit',
        operator: '>=',
        value: '1.5',
        unit: 'spaces_per_unit',
        provenance: {
          rule_id: 1,
          clause_ref: '4.2.1',
          document_id: 345,
          pages: [7],
          seed_tag: 'zoning',
        },
      },
    ],
  },
  '456 river road': {
    input_kind: 'address',
    zone_code: 'C1',
    overlays: ['airport'],
    advisory_hints: ['Coordinate with CAAS on height limits under the airport safeguarding zone.'],
    metrics: {
      gfa_cap_m2: 3430,
      floors_max: 8,
      footprint_m2: 441,
      nsa_est_m2: 2813,
    },
    zone_source: {
      kind: 'parcel',
      layer_name: 'MasterPlan',
      jurisdiction: 'SG',
      parcel_ref: 'MK02-00021',
      parcel_source: 'sample_loader',
    },
    rules: [],
  },
  '789 coastal way': {
    input_kind: 'address',
    zone_code: 'B1',
    overlays: ['coastal'],
    advisory_hints: [
      'Implement coastal flood resilience measures for ground floors.',
      'Consult PUB on shoreline protection obligations.',
    ],
    metrics: {
      gfa_cap_m2: 3920,
      floors_max: 8,
      footprint_m2: 504,
      nsa_est_m2: 3214,
    },
    zone_source: {
      kind: 'parcel',
      layer_name: 'MasterPlan',
      jurisdiction: 'SG',
      parcel_ref: 'MK03-04567',
      parcel_source: 'sample_loader',
    },
    rules: [],
  },
}

function normaliseAddress(address: string): string {
  return address.trim().toLowerCase()
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
  return {
    inputKind: payload.input_kind,
    zoneCode: payload.zone_code,
    overlays: [...payload.overlays],
    advisoryHints: [...payload.advisory_hints],
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

function selectMockResponse(address: string): BuildableResponse {
  const key = normaliseAddress(address)
  return (
    MOCK_RESPONSES[key] ?? {
      input_kind: 'address',
      zone_code: null,
      overlays: [],
      advisory_hints: [],
      metrics: {
        gfa_cap_m2: 0,
        floors_max: 0,
        footprint_m2: 0,
        nsa_est_m2: 0,
      },
      zone_source: {
        kind: 'unknown',
        layer_name: null,
        jurisdiction: null,
        parcel_ref: null,
        parcel_source: null,
        note: null,
      },
      rules: [],
    }
  )
}

export async function postBuildable(
  baseUrl: string,
  body: BuildableRequest,
  options: BuildableRequestOptions = {},
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
  if (useMockData) {
    return mapResponse(selectMockResponse(request.address))
  }

  const payload = await postBuildable(apiBaseUrl, request, options)
  return mapResponse(payload)
}
