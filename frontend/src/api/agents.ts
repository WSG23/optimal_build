function normaliseBaseUrl(value: string | undefined | null): string {
  if (typeof value !== 'string') {
    return '/'
  }
  const trimmed = value.trim()
  return trimmed === '' ? '/' : trimmed
}

const API_PREFIX = 'api/v1/agents/commercial-property/properties/log-gps'
const _PROPERTY_PREFIX = 'api/v1/agents/commercial-property/properties'
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

export type DevelopmentScenario =
  | 'raw_land'
  | 'existing_building'
  | 'heritage_property'
  | 'underused_asset'

export interface CoordinatePair {
  latitude: number
  longitude: number
}

export interface AddressSummary {
  fullAddress: string
  streetName?: string
  buildingName?: string
  blockNumber?: string
  postalCode?: string
  district?: string
  country?: string
}

export interface UraZoningSummary {
  zoneCode?: string
  zoneDescription?: string
  plotRatio?: number | null
  buildingHeightLimit?: number | null
  siteCoverage?: number | null
  useGroups: string[]
  specialConditions?: string | null
}

export interface PropertyInfoSummary {
  propertyName?: string | null
  tenure?: string | null
  siteAreaSqm?: number | null
  gfaApproved?: number | null
  buildingHeight?: number | null
  completionYear?: number | null
  lastTransactionDate?: string | null
  lastTransactionPrice?: number | null
}

export interface AmenitySummary {
  name: string
  distanceM: number | null
}

export interface NearbyAmenitySummary {
  mrtStations: AmenitySummary[]
  busStops: AmenitySummary[]
  schools: AmenitySummary[]
  shoppingMalls: AmenitySummary[]
  parks: AmenitySummary[]
}

export type MetricValue = number | string | null

export interface QuickAnalysisScenarioSummary {
  scenario: DevelopmentScenario
  headline: string
  metrics: Record<string, MetricValue>
  notes: string[]
}

export interface QuickAnalysisSummary {
  generatedAt: string
  scenarios: QuickAnalysisScenarioSummary[]
}

export interface PropertyPhoto {
  photoId: string
  storageKey: string | null
  captureTimestamp: string | null
  autoTags: string[]
  publicUrl: string | null
  location?: {
    latitude: number | null
    longitude: number | null
  } | null
  notes?: string | null
  tags?: string[] | null
}

export interface UploadPhotoOptions {
  notes?: string
  tags?: string[]
}

export interface GpsCaptureSummary {
  propertyId: string
  address: AddressSummary
  coordinates: CoordinatePair
  uraZoning: UraZoningSummary
  existingUse: string
  propertyInfo: PropertyInfoSummary | null
  nearbyAmenities: NearbyAmenitySummary | null
  quickAnalysis: QuickAnalysisSummary
  timestamp: string
}

export interface LogPropertyByGpsRequest {
  latitude: number
  longitude: number
  developmentScenarios?: DevelopmentScenario[]
}

interface RawAmenity {
  name?: unknown
  distance_m?: unknown
}

interface RawQuickScenario {
  scenario?: string
  headline?: unknown
  metrics?: Record<string, unknown> | null
  notes?: unknown
}

interface RawQuickAnalysis {
  generated_at?: string
  scenarios?: RawQuickScenario[]
}

interface RawGpsResponse {
  property_id: string
  address: Record<string, unknown>
  coordinates: {
    latitude: number
    longitude: number
  }
  ura_zoning: Record<string, unknown> | null
  existing_use: string
  property_info: Record<string, unknown> | null
  nearby_amenities: Record<string, unknown> | null
  quick_analysis?: RawQuickAnalysis | null
  timestamp: string
}

function coerceNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function coerceString(value: unknown): string | undefined {
  if (typeof value === 'string') {
    return value
  }
  return undefined
}

function mapAddress(payload: Record<string, unknown>): AddressSummary {
  return {
    fullAddress: coerceString(payload.full_address) ?? '',
    streetName: coerceString(payload.street_name),
    buildingName: coerceString(payload.building_name),
    blockNumber: coerceString(payload.block_number),
    postalCode: coerceString(payload.postal_code),
    district: coerceString(payload.district),
    country: coerceString(payload.country),
  }
}

function mapUraZoning(
  payload: Record<string, unknown> | null,
): UraZoningSummary {
  if (!payload) {
    return {
      zoneCode: undefined,
      zoneDescription: undefined,
      plotRatio: null,
      buildingHeightLimit: null,
      siteCoverage: null,
      useGroups: [],
      specialConditions: undefined,
    }
  }
  const useGroups = Array.isArray(payload.use_groups)
    ? payload.use_groups.filter(
        (item): item is string => typeof item === 'string',
      )
    : []

  return {
    zoneCode: coerceString(payload.zone_code),
    zoneDescription: coerceString(payload.zone_description),
    plotRatio: coerceNumber(payload.plot_ratio),
    buildingHeightLimit: coerceNumber(payload.building_height_limit),
    siteCoverage: coerceNumber(payload.site_coverage),
    useGroups,
    specialConditions: coerceString(payload.special_conditions) ?? null,
  }
}

function mapPropertyInfo(
  payload: Record<string, unknown> | null,
): PropertyInfoSummary | null {
  if (!payload) {
    return null
  }
  return {
    propertyName: coerceString(payload.property_name) ?? null,
    tenure: coerceString(payload.tenure) ?? null,
    siteAreaSqm: coerceNumber(payload.site_area_sqm),
    gfaApproved: coerceNumber(payload.gfa_approved),
    buildingHeight: coerceNumber(payload.building_height),
    completionYear: coerceNumber(payload.completion_year),
    lastTransactionDate: coerceString(payload.last_transaction_date) ?? null,
    lastTransactionPrice: coerceNumber(payload.last_transaction_price),
  }
}

function mapAmenityList(value: unknown): AmenitySummary[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value
    .map((item): AmenitySummary | null => {
      if (!item || typeof item !== 'object') {
        return null
      }
      const data = item as RawAmenity
      const name = coerceString(data.name) ?? 'Unknown'
      const distance = coerceNumber(data.distance_m)
      return { name, distanceM: distance }
    })
    .filter((item): item is AmenitySummary => item !== null)
}

function mapNearbyAmenities(
  payload: Record<string, unknown> | null,
): NearbyAmenitySummary | null {
  if (!payload) {
    return null
  }

  return {
    mrtStations: mapAmenityList(payload.mrt_stations),
    busStops: mapAmenityList(payload.bus_stops),
    schools: mapAmenityList(payload.schools),
    shoppingMalls: mapAmenityList(payload.shopping_malls),
    parks: mapAmenityList(payload.parks),
  }
}

function mapPhotoLocation(value: unknown): PropertyPhoto['location'] {
  if (!value || typeof value !== 'object') {
    return null
  }
  const payload = value as Record<string, unknown>
  const latitude = coerceNumber(payload.latitude)
  const longitude = coerceNumber(payload.longitude)
  if (latitude == null && longitude == null) {
    return null
  }
  return {
    latitude,
    longitude,
  }
}

function _mapPhoto(payload: Record<string, unknown>): PropertyPhoto {
  const autoTags = Array.isArray(payload.auto_tags)
    ? payload.auto_tags.filter(
        (item): item is string => typeof item === 'string',
      )
    : []
  const tagList = Array.isArray(payload.tags)
    ? payload.tags.filter((item): item is string => typeof item === 'string')
    : null

  return {
    photoId: coerceString(payload.photo_id) ?? '',
    storageKey: coerceString(payload.storage_key) ?? null,
    captureTimestamp: coerceString(payload.capture_timestamp) ?? null,
    autoTags,
    publicUrl: coerceString(payload.public_url) ?? null,
    location: mapPhotoLocation(payload.location),
    notes: coerceString(payload.notes) ?? null,
    tags: tagList,
  }
}

function mapMetrics(
  metrics: Record<string, unknown> | null | undefined,
): Record<string, MetricValue> {
  if (!metrics) {
    return {}
  }

  return Object.fromEntries(
    Object.entries(metrics).map(([key, value]) => {
      if (value == null) {
        return [key, null]
      }
      if (typeof value === 'number') {
        return [key, value]
      }
      if (typeof value === 'string') {
        return [key, value]
      }
      if (typeof value === 'boolean') {
        return [key, value ? 'true' : 'false']
      }
      return [key, String(value)]
    }),
  )
}

function mapScenario(
  payload: RawQuickScenario,
): QuickAnalysisScenarioSummary | null {
  if (!payload.scenario || typeof payload.scenario !== 'string') {
    return null
  }

  const scenario = payload.scenario as DevelopmentScenario

  const notes = Array.isArray(payload.notes)
    ? payload.notes.filter((item): item is string => typeof item === 'string')
    : []

  return {
    scenario,
    headline:
      typeof payload.headline === 'string'
        ? payload.headline
        : 'Insight generated',
    metrics: mapMetrics(payload.metrics),
    notes,
  }
}

function mapQuickAnalysis(payload: RawQuickAnalysis): QuickAnalysisSummary {
  const scenarios = Array.isArray(payload.scenarios)
    ? payload.scenarios
        .map((item) => mapScenario(item))
        .filter((item): item is QuickAnalysisScenarioSummary => item !== null)
    : []

  return {
    generatedAt: payload.generated_at ?? new Date().toISOString(),
    scenarios,
  }
}

export type LogTransport = (
  baseUrl: string,
  payload: LogPropertyByGpsRequest,
  options?: { signal?: AbortSignal },
) => Promise<RawGpsResponse>

async function postLogProperty(
  baseUrl: string,
  payload: LogPropertyByGpsRequest,
  options: { signal?: AbortSignal } = {},
): Promise<RawGpsResponse> {
  const response = await fetch(buildUrl(API_PREFIX, baseUrl), {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      latitude: payload.latitude,
      longitude: payload.longitude,
      development_scenarios: payload.developmentScenarios,
    }),
    signal: options.signal,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(
      detail || `Request to ${API_PREFIX} failed with ${response.status}`,
    )
  }

  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    throw new Error(`Expected JSON response from ${API_PREFIX}`)
  }

  return (await response.json()) as RawGpsResponse
}

export async function logPropertyByGps(
  request: LogPropertyByGpsRequest,
  transport: LogTransport = postLogProperty,
  signal?: AbortSignal,
): Promise<GpsCaptureSummary> {
  const payload = await transport(apiBaseUrl, request, { signal })

  const quickAnalysisPayload =
    payload.quick_analysis ??
    ({
      generated_at: payload.timestamp,
      scenarios: [],
    } satisfies RawQuickAnalysis)

  return {
    propertyId: payload.property_id,
    address: mapAddress(payload.address),
    coordinates: {
      latitude: payload.coordinates.latitude,
      longitude: payload.coordinates.longitude,
    },
    uraZoning: mapUraZoning(payload.ura_zoning),
    existingUse: payload.existing_use,
    propertyInfo: mapPropertyInfo(payload.property_info),
    nearbyAmenities: mapNearbyAmenities(payload.nearby_amenities),
    quickAnalysis: mapQuickAnalysis(quickAnalysisPayload),
    timestamp: payload.timestamp,
  }
}

export const DEFAULT_SCENARIO_ORDER: readonly DevelopmentScenario[] = [
  'raw_land',
  'existing_building',
  'heritage_property',
  'underused_asset',
]

export interface MarketIntelligenceSummary {
  propertyId: string
  report: Record<string, unknown>
}

export type ProfessionalPackType =
  | 'universal'
  | 'investment'
  | 'sales'
  | 'lease'

export interface ProfessionalPackSummary {
  packType: ProfessionalPackType
  propertyId: string
  filename: string
  downloadUrl: string | null
  generatedAt: string
  sizeBytes: number | null
}

export async function fetchPropertyMarketIntelligence(
  propertyId: string,
  months = 12,
  signal?: AbortSignal,
): Promise<MarketIntelligenceSummary> {
  const params = new URLSearchParams()
  if (months) {
    params.set('months', String(months))
  }

  const response = await fetch(
    buildUrl(
      `api/v1/agents/commercial-property/properties/${propertyId}/market-intelligence?${params.toString()}`,
    ),
    {
      method: 'GET',
      signal,
    },
  )

  const contentType = response.headers?.get?.('content-type') ?? ''

  if (!response.ok) {
    const detail = contentType.includes('application/json')
      ? await response.json().then((data: Record<string, unknown>) => {
          const errorDetail = data?.detail
          return typeof errorDetail === 'string' ? errorDetail : undefined
        })
      : await response.text()

    throw new Error(
      detail ||
        `Request to market-intelligence failed with ${response.status}${response.statusText ? ` ${response.statusText}` : ''}`,
    )
  }

  if (!contentType.includes('application/json')) {
    throw new Error('Expected JSON response from market-intelligence endpoint')
  }

  const payload = (await response.json()) as {
    property_id: string
    report: Record<string, unknown>
  }

  return {
    propertyId: payload.property_id,
    report: payload.report ?? {},
  }
}

export async function generateProfessionalPack(
  propertyId: string,
  packType: ProfessionalPackType,
  signal?: AbortSignal,
): Promise<ProfessionalPackSummary> {
  const url = buildUrl(
    `api/v1/agents/commercial-property/properties/${propertyId}/generate-pack/${packType}`,
  )

  const response = await fetch(url, {
    method: 'POST',
    signal,
  })

  const contentType = response.headers?.get?.('content-type') ?? ''

  if (!response.ok) {
    const detail = contentType.includes('application/json')
      ? await response.json().then((data: Record<string, unknown>) => {
          const message = data?.detail
          return typeof message === 'string' ? message : undefined
        })
      : await response.text()

    throw new Error(
      detail ||
        `Request to generate ${packType} pack failed with ${response.status}${response.statusText ? ` ${response.statusText}` : ''}`,
    )
  }

  if (!contentType.includes('application/json')) {
    throw new Error('Expected JSON response from professional pack endpoint')
  }

  const payload = (await response.json()) as {
    pack_type: ProfessionalPackType
    property_id: string
    filename: string
    download_url?: string | null
    generated_at: string
    size_bytes?: number | null
  }

  return {
    packType: payload.pack_type,
    propertyId: payload.property_id,
    filename: payload.filename,
    downloadUrl: payload.download_url ?? null,
    generatedAt: payload.generated_at,
    sizeBytes:
      typeof payload.size_bytes === 'number' ? payload.size_bytes : null,
  }
}
