const API_PREFIX = 'api/v1/screen/buildable'
const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL
const apiBaseUrl = rawApiBaseUrl && rawApiBaseUrl.trim() !== '' ? rawApiBaseUrl : '/'
const useMockData = import.meta.env.VITE_FEASIBILITY_USE_MOCKS === 'true'

interface RawBuildableMetrics {
  gfa_cap_m2: number
  floors_max: number
  footprint_m2: number
  nsa_est_m2: number
}

interface RawBuildableRuleProvenance {
  rule_id: number
  clause_ref?: string | null
  document_id?: number | null
  pages?: number[] | null
  seed_tag?: string | null
}

interface RawBuildableRule {
  id: number
  authority: string
  parameter_key: string
  operator: string
  value: string
  unit?: string | null
  provenance: RawBuildableRuleProvenance
}

interface RawZoneSource {
  kind: 'parcel' | 'geometry' | 'unknown'
  layer_name?: string | null
  jurisdiction?: string | null
  parcel_ref?: string | null
  parcel_source?: string | null
  note?: string | null
}

interface RawBuildableResponse {
  input_kind: 'address' | 'geometry'
  zone_code: string | null
  overlays: string[]
  advisory_hints: string[]
  metrics: RawBuildableMetrics
  zone_source: RawZoneSource
  rules: RawBuildableRule[]
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

export interface BuildableResponse {
  inputKind: 'address' | 'geometry'
  zoneCode: string | null
  overlays: string[]
  advisoryHints: string[]
  metrics: BuildableMetrics
  zoneSource: ZoneSourceInfo
  rules: BuildableRule[]
}

interface FetchOptions {
  signal?: AbortSignal
}

const MOCK_RESPONSES: Record<string, RawBuildableResponse> = {
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

function buildUrl(path: string) {
  if (/^https?:/i.test(path)) {
    return path
  }
  const trimmed = path.startsWith('/') ? path.slice(1) : path
  const root = apiBaseUrl || '/'
  if (/^https?:/i.test(root)) {
    return new URL(trimmed, root.endsWith('/') ? root : `${root}/`).toString()
  }
  const normalisedRoot = root.endsWith('/') ? root : `${root}/`
  return `${normalisedRoot}${trimmed}`
}

function mapRule(rule: RawBuildableRule): BuildableRule {
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

function mapResponse(payload: RawBuildableResponse): BuildableResponse {
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

function selectMockResponse(address: string): RawBuildableResponse {
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

export async function fetchBuildable(
  request: BuildableRequest,
  options: FetchOptions = {},
): Promise<BuildableResponse> {
  if (useMockData) {
    return mapResponse(selectMockResponse(request.address))
  }

  const response = await fetch(buildUrl(API_PREFIX), {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      address: request.address,
      typ_floor_to_floor_m: request.typFloorToFloorM,
      efficiency_ratio: request.efficiencyRatio,
    }),
    signal: options.signal,
  })

  const contentType = response.headers.get('content-type') ?? ''

  if (!response.ok) {
    if (contentType.includes('application/json')) {
      const body = (await response.json()) as { detail?: unknown; error?: unknown }
      const detail = typeof body.detail === 'string' ? body.detail : undefined
      const error = typeof body.error === 'string' ? body.error : undefined
      throw new Error(detail ?? error ?? `Request to ${API_PREFIX} failed with ${response.status}`)
    }
    const message = await response.text()
    throw new Error(message || `Request to ${API_PREFIX} failed with ${response.status}`)
  }

  if (!contentType.includes('application/json')) {
    throw new Error(`Expected JSON response from ${API_PREFIX}`)
  }

  const payload = (await response.json()) as RawBuildableResponse
  return mapResponse(payload)
}
