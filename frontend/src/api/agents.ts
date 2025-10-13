function normaliseBaseUrl(value: string | undefined | null): string {
  if (typeof value !== 'string') {
    return '/'
  }
  const trimmed = value.trim()
  return trimmed === '' ? '/' : trimmed
}

const API_PREFIX = 'api/v1/agents/commercial-property/properties/log-gps'
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
  | 'mixed_use_redevelopment'

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

const OFFLINE_PROPERTY_ID = 'offline-property'
const OFFLINE_MARKET_WARNING =
  'Using offline market intelligence preview. Backend data unavailable.'
const OFFLINE_PACK_WARNING =
  'Using offline preview pack. Backend generator unavailable.'

const GPS_FALLBACK_SUMMARY: GpsCaptureSummary = {
  propertyId: OFFLINE_PROPERTY_ID,
  address: {
    fullAddress: '123 Offline Road, Singapore',
    streetName: 'Offline Road',
    buildingName: 'Offline Hub',
    blockNumber: '12',
    postalCode: '049123',
    district: 'D01',
    country: 'Singapore',
  },
  coordinates: {
    latitude: 1.285,
    longitude: 103.853,
  },
  uraZoning: {
    zoneCode: 'Commercial',
    zoneDescription: 'Central Business District',
    plotRatio: 4.2,
    buildingHeightLimit: 160,
    siteCoverage: 80,
    useGroups: ['Office', 'Retail', 'F&B'],
    specialConditions: 'Refer to urban design guidelines for facade upgrades.',
  },
  existingUse: 'Integrated mixed-use podium with office tower',
  propertyInfo: {
    propertyName: 'Offline Hub',
    tenure: '99-year leasehold',
    siteAreaSqm: 5200,
    gfaApproved: 20800,
    buildingHeight: 34,
    completionYear: 2008,
    lastTransactionDate: '2024-03-31',
    lastTransactionPrice: 185000000,
  },
  nearbyAmenities: {
    mrtStations: [
      { name: 'Downtown MRT', distanceM: 220 },
      { name: 'Raffles Place MRT', distanceM: 410 },
    ],
    busStops: [{ name: 'One Raffles Quay', distanceM: 120 }],
    schools: [],
    shoppingMalls: [{ name: 'Marina One Retail', distanceM: 310 }],
    parks: [{ name: 'Central Linear Park', distanceM: 450 }],
  },
  quickAnalysis: {
    generatedAt: '2025-01-15T08:00:00Z',
    scenarios: [
      {
        scenario: 'existing_building',
        headline: 'Stabilised NOI supports 4.3% yield post-refresh',
        metrics: {
          occupancy_pct: 0.94,
          annual_noi: 8650000,
          valuation_cap_rate: 0.043,
        },
        notes: [
          'Reposition ground-floor podium for F&B and lifestyle concepts.',
          'Upgrade end-of-trip facilities to attract flex-office tenants.',
        ],
      },
      {
        scenario: 'heritage_property',
        headline: 'Adaptive reuse opportunity respecting facade guidelines',
        metrics: {
          conservation_status: 'partial',
          estimated_capex: 4200000,
        },
        notes: [
          'Consult URA on conservation requirements for street-facing facade.',
        ],
      },
      {
        scenario: 'underused_asset',
        headline: 'Introduce wellness suites to lift blended rents by 8%',
        metrics: {
          potential_rent_uplift_pct: 0.08,
          target_lease_term_years: 5,
        },
        notes: [
          'Demand from healthcare operators for central locations remains strong.',
        ],
      },
    ],
  },
  timestamp: '2025-01-15T08:05:00Z',
}

function cloneGpsSummary(summary: GpsCaptureSummary): GpsCaptureSummary {
  return {
    propertyId: summary.propertyId,
    address: { ...summary.address },
    coordinates: { ...summary.coordinates },
    uraZoning: {
      zoneCode: summary.uraZoning.zoneCode,
      zoneDescription: summary.uraZoning.zoneDescription,
      plotRatio: summary.uraZoning.plotRatio ?? null,
      buildingHeightLimit: summary.uraZoning.buildingHeightLimit ?? null,
      siteCoverage: summary.uraZoning.siteCoverage ?? null,
      useGroups: [...summary.uraZoning.useGroups],
      specialConditions: summary.uraZoning.specialConditions ?? null,
    },
    existingUse: summary.existingUse,
    propertyInfo: summary.propertyInfo ? { ...summary.propertyInfo } : null,
    nearbyAmenities: summary.nearbyAmenities
      ? {
          mrtStations: summary.nearbyAmenities.mrtStations.map((item) => ({
            ...item,
          })),
          busStops: summary.nearbyAmenities.busStops.map((item) => ({
            ...item,
          })),
          schools: summary.nearbyAmenities.schools.map((item) => ({
            ...item,
          })),
          shoppingMalls: summary.nearbyAmenities.shoppingMalls.map((item) => ({
            ...item,
          })),
          parks: summary.nearbyAmenities.parks.map((item) => ({ ...item })),
        }
      : null,
    quickAnalysis: {
      generatedAt: summary.quickAnalysis.generatedAt,
      scenarios: summary.quickAnalysis.scenarios.map((scenario) => ({
        scenario: scenario.scenario,
        headline: scenario.headline,
        metrics: { ...scenario.metrics },
        notes: [...scenario.notes],
      })),
    },
    timestamp: summary.timestamp,
  }
}

function createGpsFallbackSummary(
  request: LogPropertyByGpsRequest,
): GpsCaptureSummary {
  const fallback = cloneGpsSummary(GPS_FALLBACK_SUMMARY)
  fallback.coordinates = {
    latitude: request.latitude,
    longitude: request.longitude,
  }
  const generatedAt = new Date().toISOString()
  fallback.timestamp = generatedAt
  fallback.quickAnalysis = {
    ...fallback.quickAnalysis,
    generatedAt,
    scenarios: fallback.quickAnalysis.scenarios.map((scenario) => ({
      ...scenario,
      metrics: { ...scenario.metrics },
      notes: [...scenario.notes],
    })),
  }
  return fallback
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
  try {
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
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    if (error instanceof TypeError) {
      console.warn(
        '[agents] GPS capture request failed, using offline fallback data',
        error,
      )
      return createGpsFallbackSummary(request)
    }
    throw error
  }
}

export const DEFAULT_SCENARIO_ORDER: readonly DevelopmentScenario[] = [
  'raw_land',
  'existing_building',
  'heritage_property',
  'underused_asset',
  'mixed_use_redevelopment',
]

export interface MarketIntelligenceSummary {
  propertyId: string
  report: Record<string, unknown>
  isFallback: boolean
  warning?: string
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
  isFallback: boolean
  warning?: string
}

export async function fetchPropertyMarketIntelligence(
  propertyId: string,
  months = 12,
  signal?: AbortSignal,
): Promise<MarketIntelligenceSummary> {
  if (propertyId === OFFLINE_PROPERTY_ID) {
    return {
      propertyId,
      report: createOfflineMarketIntelligenceReport(months),
      isFallback: true,
      warning: OFFLINE_MARKET_WARNING,
    }
  }

  const params = new URLSearchParams()
  if (months) {
    params.set('months', String(months))
  }

  try {
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

      return {
        propertyId,
        report: createOfflineMarketIntelligenceReport(months),
        isFallback: true,
        warning: detail
          ? `${OFFLINE_MARKET_WARNING} (${detail})`
          : OFFLINE_MARKET_WARNING,
      }
    }

    if (!contentType.includes('application/json')) {
      return {
        propertyId,
        report: createOfflineMarketIntelligenceReport(months),
        isFallback: true,
        warning: `${OFFLINE_MARKET_WARNING} (Unexpected response format)`,
      }
    }

    const payload = (await response.json()) as {
      property_id: string
      report: Record<string, unknown>
    }

    return {
      propertyId: payload.property_id,
      report: payload.report ?? {},
      isFallback: false,
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    const detail =
      error instanceof Error ? error.message : 'Unable to load market intelligence.'
    return {
      propertyId,
      report: createOfflineMarketIntelligenceReport(months),
      isFallback: true,
      warning: `${OFFLINE_MARKET_WARNING} (${detail})`,
    }
  }
}

export async function generateProfessionalPack(
  propertyId: string,
  packType: ProfessionalPackType,
  signal?: AbortSignal,
): Promise<ProfessionalPackSummary> {
  if (propertyId === OFFLINE_PROPERTY_ID) {
    return createOfflinePackSummary(
      propertyId,
      packType,
      OFFLINE_PACK_WARNING,
    )
  }

  const url = buildUrl(
    `api/v1/agents/commercial-property/properties/${propertyId}/generate-pack/${packType}`,
  )

  try {
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

      return createOfflinePackSummary(
        propertyId,
        packType,
        detail
          ? `${OFFLINE_PACK_WARNING} (${detail})`
          : OFFLINE_PACK_WARNING,
      )
    }

    if (!contentType.includes('application/json')) {
      return createOfflinePackSummary(
        propertyId,
        packType,
        `${OFFLINE_PACK_WARNING} (Unexpected response format)`,
      )
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
      isFallback: false,
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    const detail =
      error instanceof Error ? error.message : 'Unable to reach pack generator.'
    return createOfflinePackSummary(
      propertyId,
      packType,
      `${OFFLINE_PACK_WARNING} (${detail})`,
    )
  }
}

function createOfflinePackSummary(
  propertyId: string,
  packType: ProfessionalPackType,
  warning?: string,
): ProfessionalPackSummary {
  const timestamp = new Date().toISOString()
  const filename = `${packType}_pack_preview_${timestamp.slice(0, 10)}.pdf`
  return {
    packType,
    propertyId,
    filename,
    downloadUrl: null,
    generatedAt: timestamp,
    sizeBytes: null,
    isFallback: true,
    warning,
  }
}

function createOfflineMarketIntelligenceReport(months: number) {
  const end = new Date()
  const start = new Date(end)
  start.setMonth(end.getMonth() - Math.max(1, months))

  return {
    property_type: 'Mixed Use',
    location: 'CBD',
    generated_at: end.toISOString(),
    period: {
      start: start.toISOString(),
      end: end.toISOString(),
    },
    comparables_analysis: {
      transaction_count: 18,
      average_psf: 2480,
      median_psf: 2440,
      highest_psf: 2725,
      lowest_psf: 2190,
      trend: 'stable',
    },
    supply_dynamics: {
      projects_in_pipeline: 5,
      completions_next_12_months: 2,
      occupancy_rate: 0.93,
      headline: 'Limited new supply supports rental stability through the next cycle.',
    },
    yield_benchmarks: {
      core_yield: 0.041,
      value_add_yield: 0.047,
      opportunistic_yield: 0.052,
      commentary: 'CBD mixed-use yields tightened 15 bps over the past quarter.',
    },
    absorption_trends: {
      average_absorption_months: 7,
      leasing_velocity: 'improving',
      pre_commitment_rate: 0.68,
      notes: 'Flight-to-quality demand continues for premium CBD assets.',
    },
    market_cycle_position: {
      phase: 'Expansion',
      confidence: 'medium',
      catalysts: [
        'Office-to-flex conversions sustaining occupancy',
        'Retail footfall exceeding pre-pandemic baseline',
      ],
      risks: ['Interest rate volatility moderating investor bids'],
    },
  }
}
