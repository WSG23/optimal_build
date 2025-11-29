import {
  coerceNumber,
  coerceString,
  coerceBoolean,
  buildUrl,
  apiBaseUrl,
} from './shared'

const API_PREFIX = 'api/v1/agents/commercial-property/properties/log-gps'

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

/** Accuracy band for a metric value (±% range based on data quality and asset class) */
export interface AccuracyBand {
  low_pct: number // negative percentage (e.g., -10 for -10%)
  high_pct: number // positive percentage (e.g., 8 for +8%)
  source?: string // source of the band calculation
  asset_class?: string // asset class adjustment applied
}

/** Metrics with optional accuracy_bands key containing bands per metric */
export interface QuickAnalysisMetrics {
  [key: string]: MetricValue | Record<string, AccuracyBand> | undefined
  accuracy_bands?: Record<string, AccuracyBand>
}

export interface QuickAnalysisScenarioSummary {
  scenario: DevelopmentScenario
  headline: string
  metrics: QuickAnalysisMetrics
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
  jurisdictionCode: string
  currencySymbol: string
}

export interface LogPropertyByGpsRequest {
  latitude: number
  longitude: number
  developmentScenarios?: DevelopmentScenario[]
  jurisdictionCode?: string
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

export interface RawQuickAnalysis {
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
  jurisdiction_code: string
  currency_symbol: string
}

function mapAddress(payload: Record<string, unknown>): AddressSummary {
  return {
    fullAddress: coerceString(payload.full_address) ?? '',
    streetName: coerceString(payload.street_name) ?? undefined,
    buildingName: coerceString(payload.building_name) ?? undefined,
    blockNumber: coerceString(payload.block_number) ?? undefined,
    postalCode: coerceString(payload.postal_code) ?? undefined,
    district: coerceString(payload.district) ?? undefined,
    country: coerceString(payload.country) ?? undefined,
  }
}

export { buildUrl }

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
    zoneCode: coerceString(payload.zone_code) ?? undefined,
    zoneDescription: coerceString(payload.zone_description) ?? undefined,
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
): QuickAnalysisMetrics {
  if (!metrics) {
    return {}
  }

  const result: QuickAnalysisMetrics = {}

  for (const [key, value] of Object.entries(metrics)) {
    if (key === 'accuracy_bands' && value && typeof value === 'object') {
      // Preserve accuracy_bands object as-is
      result.accuracy_bands = value as Record<string, AccuracyBand>
    } else if (value == null) {
      result[key] = null
    } else if (typeof value === 'number') {
      result[key] = value
    } else if (typeof value === 'string') {
      result[key] = value
    } else if (typeof value === 'boolean') {
      result[key] = value ? 'true' : 'false'
    } else {
      result[key] = String(value)
    }
  }

  return result
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

export const OFFLINE_PROPERTY_ID = 'offline-property'

// Developer feature types for hybrid API function
export interface DeveloperVisualizationSummary {
  status: string
  previewAvailable: boolean
  notes: string[]
  conceptMeshUrl: string | null
  previewMetadataUrl: string | null
  thumbnailUrl: string | null
  cameraOrbitHint: Record<string, number> | null
  previewSeed: number | null
  previewJobId: string | null
  massingLayers: DeveloperMassingLayer[]
  colorLegend: DeveloperColorLegendEntry[]
}

export interface DeveloperMassingLayer {
  assetType: string
  allocationPct: number
  gfaSqm: number | null
  niaSqm: number | null
  estimatedHeightM: number | null
  color: string
}

export interface DeveloperColorLegendEntry {
  assetType: string
  label: string
  color: string
  description: string | null
}

export interface DeveloperAssetOptimization {
  assetType: string
  allocationPct: number
  allocatedGfaSqm: number | null
  niaEfficiency: number | null
  targetFloorHeightM: number | null
  parkingRatioPer1000Sqm: number | null
  rentPsmMonth: number | null
  stabilisedVacancyPct: number | null
  opexPctOfRent: number | null
  estimatedRevenueSgd: number | null
  estimatedCapexSgd: number | null
  fitoutCostPsm: number | null
  absorptionMonths: number | null
  riskLevel: string | null
  heritagePremiumPct: number | null
  notes: string[]
}

export interface DeveloperFinancialSummary {
  totalEstimatedRevenueSgd: number | null
  totalEstimatedCapexSgd: number | null
  dominantRiskProfile: string | null
  notes: string[]
}

export interface DeveloperHeritageContext {
  flag: boolean
  risk: string | null
  notes: string[]
  constraints: string[]
  assumption: string | null
  overlay: {
    name: string | null
    source: string | null
    heritagePremiumPct: number | null
  } | null
}

export interface DeveloperFeatureData {
  visualization: DeveloperVisualizationSummary | null
  optimizations: DeveloperAssetOptimization[]
  financialSummary: DeveloperFinancialSummary | null
  heritageContext: DeveloperHeritageContext | null
}

export interface GpsCaptureSummaryWithFeatures extends GpsCaptureSummary {
  developerFeatures: DeveloperFeatureData | null
}
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
  jurisdictionCode: 'SG',
  currencySymbol: 'S$',
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
    jurisdictionCode: summary.jurisdictionCode,
    currencySymbol: summary.currencySymbol,
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
      jurisdiction_code: payload.jurisdictionCode,
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
      jurisdictionCode: payload.jurisdiction_code,
      currencySymbol: payload.currency_symbol,
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

// ========== Hybrid API for optional developer features ==========

const DEVELOPER_GPS_ENDPOINT = '/api/v1/developers/properties/log-gps'

export interface FeatureEnabledRequest extends LogPropertyByGpsRequest {
  enabledFeatures: {
    preview3D: boolean
    assetOptimization: boolean
    financialSummary: boolean
    heritageContext: boolean
  }
}

interface RawDeveloperResponse extends RawGpsResponse {
  visualization?: Record<string, unknown>
  optimizations?: Record<string, unknown>[]
  financial_summary?: Record<string, unknown>
  heritage_context?: Record<string, unknown>
}

function mapVisualization(
  raw: Record<string, unknown> | undefined,
): DeveloperVisualizationSummary | null {
  if (!raw) return null

  const massingLayers = Array.isArray(raw.massing_layers)
    ? (raw.massing_layers as Record<string, unknown>[]).map((layer) => ({
        assetType: String(layer.asset_type ?? ''),
        allocationPct: Number(layer.allocation_pct ?? 0),
        gfaSqm: layer.gfa_sqm != null ? Number(layer.gfa_sqm) : null,
        niaSqm: layer.nia_sqm != null ? Number(layer.nia_sqm) : null,
        estimatedHeightM:
          layer.estimated_height_m != null
            ? Number(layer.estimated_height_m)
            : null,
        color: String(layer.color ?? '#888888'),
      }))
    : []

  const colorLegend = Array.isArray(raw.color_legend)
    ? (raw.color_legend as Record<string, unknown>[]).map((entry) => ({
        assetType: String(entry.asset_type ?? ''),
        label: String(entry.label ?? ''),
        color: String(entry.color ?? '#888888'),
        description:
          entry.description != null ? String(entry.description) : null,
      }))
    : []

  return {
    status: String(raw.status ?? 'unknown'),
    previewAvailable: Boolean(raw.preview_available),
    notes: Array.isArray(raw.notes) ? (raw.notes as string[]) : [],
    conceptMeshUrl:
      raw.concept_mesh_url != null ? String(raw.concept_mesh_url) : null,
    previewMetadataUrl:
      raw.preview_metadata_url != null
        ? String(raw.preview_metadata_url)
        : null,
    thumbnailUrl: raw.thumbnail_url != null ? String(raw.thumbnail_url) : null,
    cameraOrbitHint: raw.camera_orbit_hint as Record<string, number> | null,
    previewSeed: raw.preview_seed != null ? Number(raw.preview_seed) : null,
    previewJobId:
      raw.preview_job_id != null ? String(raw.preview_job_id) : null,
    massingLayers,
    colorLegend,
  }
}

function mapOptimizations(
  raw: Record<string, unknown>[] | undefined,
): DeveloperAssetOptimization[] {
  if (!Array.isArray(raw)) return []

  return raw.map((opt) => ({
    assetType: String(opt.asset_type ?? ''),
    allocationPct: Number(opt.allocation_pct ?? 0),
    allocatedGfaSqm:
      opt.allocated_gfa_sqm != null ? Number(opt.allocated_gfa_sqm) : null,
    niaEfficiency:
      opt.nia_efficiency != null ? Number(opt.nia_efficiency) : null,
    targetFloorHeightM:
      opt.target_floor_height_m != null
        ? Number(opt.target_floor_height_m)
        : null,
    parkingRatioPer1000Sqm:
      opt.parking_ratio_per_1000_sqm != null
        ? Number(opt.parking_ratio_per_1000_sqm)
        : null,
    rentPsmMonth:
      opt.rent_psm_month != null ? Number(opt.rent_psm_month) : null,
    stabilisedVacancyPct:
      opt.stabilised_vacancy_pct != null
        ? Number(opt.stabilised_vacancy_pct)
        : null,
    opexPctOfRent:
      opt.opex_pct_of_rent != null ? Number(opt.opex_pct_of_rent) : null,
    estimatedRevenueSgd:
      opt.estimated_revenue_sgd != null
        ? Number(opt.estimated_revenue_sgd)
        : null,
    estimatedCapexSgd:
      opt.estimated_capex_sgd != null ? Number(opt.estimated_capex_sgd) : null,
    fitoutCostPsm:
      opt.fitout_cost_psm != null ? Number(opt.fitout_cost_psm) : null,
    absorptionMonths:
      opt.absorption_months != null ? Number(opt.absorption_months) : null,
    riskLevel: opt.risk_level != null ? String(opt.risk_level) : null,
    heritagePremiumPct:
      opt.heritage_premium_pct != null
        ? Number(opt.heritage_premium_pct)
        : null,
    notes: Array.isArray(opt.notes) ? (opt.notes as string[]) : [],
  }))
}

function mapFinancialSummary(
  raw: Record<string, unknown> | undefined,
): DeveloperFinancialSummary | null {
  if (!raw) return null

  return {
    totalEstimatedRevenueSgd:
      raw.total_estimated_revenue_sgd != null
        ? Number(raw.total_estimated_revenue_sgd)
        : null,
    totalEstimatedCapexSgd:
      raw.total_estimated_capex_sgd != null
        ? Number(raw.total_estimated_capex_sgd)
        : null,
    dominantRiskProfile:
      raw.dominant_risk_profile != null
        ? String(raw.dominant_risk_profile)
        : null,
    notes: Array.isArray(raw.notes) ? (raw.notes as string[]) : [],
  }
}

function mapHeritageContext(
  raw: Record<string, unknown> | undefined,
): DeveloperHeritageContext | null {
  if (!raw) return null

  const overlayRaw = raw.overlay as Record<string, unknown> | null | undefined
  const overlay = overlayRaw
    ? {
        name: overlayRaw.name != null ? String(overlayRaw.name) : null,
        source: overlayRaw.source != null ? String(overlayRaw.source) : null,
        heritagePremiumPct:
          overlayRaw.heritage_premium_pct != null
            ? Number(overlayRaw.heritage_premium_pct)
            : null,
      }
    : null

  return {
    flag: Boolean(raw.flag),
    risk: raw.risk != null ? String(raw.risk) : null,
    notes: Array.isArray(raw.notes) ? (raw.notes as string[]) : [],
    constraints: Array.isArray(raw.constraints)
      ? (raw.constraints as string[])
      : [],
    assumption: raw.assumption != null ? String(raw.assumption) : null,
    overlay,
  }
}

/**
 * Hybrid GPS capture function that routes to developer endpoint when features are enabled
 * Falls back to standard agent endpoint when no developer features are requested
 */
export async function logPropertyByGpsWithFeatures(
  request: FeatureEnabledRequest,
  signal?: AbortSignal,
): Promise<GpsCaptureSummaryWithFeatures> {
  const { enabledFeatures, ...baseRequest } = request

  const anyFeatureEnabled =
    enabledFeatures.preview3D ||
    enabledFeatures.assetOptimization ||
    enabledFeatures.financialSummary ||
    enabledFeatures.heritageContext

  // If no developer features enabled, use standard agent endpoint
  if (!anyFeatureEnabled) {
    const summary = await logPropertyByGps(baseRequest, undefined, signal)
    return { ...summary, developerFeatures: null }
  }

  // Use developer endpoint for enhanced features
  try {
    const response = await fetch(buildUrl(DEVELOPER_GPS_ENDPOINT), {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        latitude: baseRequest.latitude,
        longitude: baseRequest.longitude,
        development_scenarios: baseRequest.developmentScenarios,
        jurisdiction_code: baseRequest.jurisdictionCode,
      }),
      signal,
    })

    if (!response.ok) {
      const detail = await response.text()
      throw new Error(
        detail ||
          `Request to ${DEVELOPER_GPS_ENDPOINT} failed with ${response.status}`,
      )
    }

    const rawPayload = (await response.json()) as RawDeveloperResponse

    const quickAnalysisPayload =
      rawPayload.quick_analysis ??
      ({
        generated_at: rawPayload.timestamp,
        scenarios: [],
      } satisfies RawQuickAnalysis)

    const baseSummary: GpsCaptureSummary = {
      propertyId: rawPayload.property_id,
      address: mapAddress(rawPayload.address),
      coordinates: {
        latitude: rawPayload.coordinates.latitude,
        longitude: rawPayload.coordinates.longitude,
      },
      uraZoning: mapUraZoning(rawPayload.ura_zoning),
      existingUse: rawPayload.existing_use,
      propertyInfo: mapPropertyInfo(rawPayload.property_info),
      nearbyAmenities: mapNearbyAmenities(rawPayload.nearby_amenities),
      quickAnalysis: mapQuickAnalysis(quickAnalysisPayload),
      timestamp: rawPayload.timestamp,
      jurisdictionCode: rawPayload.jurisdiction_code,
      currencySymbol: rawPayload.currency_symbol,
    }

    const developerFeatures: DeveloperFeatureData = {
      visualization: enabledFeatures.preview3D
        ? mapVisualization(rawPayload.visualization)
        : null,
      optimizations: enabledFeatures.assetOptimization
        ? mapOptimizations(rawPayload.optimizations)
        : [],
      financialSummary: enabledFeatures.financialSummary
        ? mapFinancialSummary(rawPayload.financial_summary)
        : null,
      heritageContext: enabledFeatures.heritageContext
        ? mapHeritageContext(rawPayload.heritage_context)
        : null,
    }

    return { ...baseSummary, developerFeatures }
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    if (error instanceof TypeError) {
      console.warn(
        '[agents] Developer GPS capture request failed, using offline fallback data',
        error,
      )
      const fallback = createGpsFallbackSummary(baseRequest)
      return { ...fallback, developerFeatures: null }
    }
    throw error
  }
}

const DEVELOPMENT_SCENARIOS_SET = new Set<DevelopmentScenario>(
  DEFAULT_SCENARIO_ORDER,
)

function isDevelopmentScenario(
  value: string | undefined,
): value is DevelopmentScenario {
  return Boolean(
    value && DEVELOPMENT_SCENARIOS_SET.has(value as DevelopmentScenario),
  )
}

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
      error instanceof Error
        ? error.message
        : 'Unable to load market intelligence.'
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
    return createOfflinePackSummary(propertyId, packType, OFFLINE_PACK_WARNING)
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
        detail ? `${OFFLINE_PACK_WARNING} (${detail})` : OFFLINE_PACK_WARNING,
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
      headline:
        'Limited new supply supports rental stability through the next cycle.',
    },
    yield_benchmarks: {
      core_yield: 0.041,
      value_add_yield: 0.047,
      opportunistic_yield: 0.052,
      commentary:
        'CBD mixed-use yields tightened 15 bps over the past quarter.',
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

// ========== Developer Checklist Types ==========

export type ChecklistCategory =
  | 'title_verification'
  | 'zoning_compliance'
  | 'environmental_assessment'
  | 'structural_survey'
  | 'heritage_constraints'
  | 'utility_capacity'
  | 'access_rights'

const CHECKLIST_CATEGORIES: readonly ChecklistCategory[] = [
  'title_verification',
  'zoning_compliance',
  'environmental_assessment',
  'structural_survey',
  'heritage_constraints',
  'utility_capacity',
  'access_rights',
]

function isChecklistCategory(
  value: string | undefined,
): value is ChecklistCategory {
  return Boolean(
    value && CHECKLIST_CATEGORIES.includes(value as ChecklistCategory),
  )
}

export type ChecklistStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'not_applicable'

const CHECKLIST_STATUSES: readonly ChecklistStatus[] = [
  'pending',
  'in_progress',
  'completed',
  'not_applicable',
]

function isChecklistStatus(
  value: string | undefined,
): value is ChecklistStatus {
  return Boolean(value && CHECKLIST_STATUSES.includes(value as ChecklistStatus))
}

export type ChecklistPriority = 'critical' | 'high' | 'medium' | 'low'

const CHECKLIST_PRIORITIES: readonly ChecklistPriority[] = [
  'critical',
  'high',
  'medium',
  'low',
]

function isChecklistPriority(
  value: string | undefined,
): value is ChecklistPriority {
  return Boolean(
    value && CHECKLIST_PRIORITIES.includes(value as ChecklistPriority),
  )
}

export interface ChecklistItem {
  id: string
  propertyId: string
  developmentScenario: DevelopmentScenario
  category: ChecklistCategory
  itemTitle: string
  itemDescription?: string
  status: ChecklistStatus
  priority: ChecklistPriority
  assignedTo?: string | null
  dueDate?: string | null
  completedAt?: string | null
  notes?: string | null
  requiresProfessional: boolean
  professionalType?: string | null
  typicalDurationDays?: number | null
  displayOrder?: number | null
  createdAt: string
  updatedAt: string
}

export interface ChecklistCategoryStatus {
  total: number
  completed: number
  inProgress: number
  pending: number
  notApplicable: number
}

export interface ChecklistSummary {
  propertyId: string
  total: number
  completed: number
  inProgress: number
  pending: number
  notApplicable: number
  completionPercentage: number
  byCategoryStatus: Record<string, ChecklistCategoryStatus>
}

export interface UpdateChecklistRequest {
  status?: ChecklistStatus
  notes?: string
  assignedTo?: string
  completedAt?: string
}

export interface ChecklistTemplate {
  id: string
  developmentScenario: string
  category: ChecklistCategory
  itemTitle: string
  itemDescription?: string | null
  priority: ChecklistPriority
  typicalDurationDays?: number | null
  requiresProfessional: boolean
  professionalType?: string | null
  displayOrder: number
  createdAt: string
  updatedAt: string
}

export interface ChecklistTemplateDraft {
  developmentScenario: string
  category: ChecklistCategory
  itemTitle: string
  itemDescription?: string | null
  priority: ChecklistPriority
  typicalDurationDays?: number | string | null
  requiresProfessional?: boolean
  professionalType?: string | null
  displayOrder?: number | string | null
}

export interface ChecklistTemplateUpdate {
  developmentScenario?: string
  category?: ChecklistCategory
  itemTitle?: string
  itemDescription?: string | null
  priority?: ChecklistPriority
  typicalDurationDays?: number | string | null
  requiresProfessional?: boolean
  professionalType?: string | null
  displayOrder?: number | string | null
}

export interface ChecklistTemplateImportResult {
  created: number
  updated: number
  deleted: number
}

// ========== Developer Checklist API Functions ==========

export async function fetchPropertyChecklist(
  propertyId: string,
  developmentScenario?: DevelopmentScenario,
  status?: ChecklistStatus,
): Promise<ChecklistItem[]> {
  const params = new URLSearchParams()
  if (developmentScenario) {
    params.append('development_scenario', developmentScenario)
  }
  if (status) {
    params.append('status', status)
  }

  const queryString = params.toString()
  const url = buildUrl(
    `api/v1/developers/properties/${propertyId}/checklists${queryString ? `?${queryString}` : ''}`,
  )

  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Checklist fetch failed: ${response.statusText}`)
    }
    const data = await response.json()

    const itemsArray: Record<string, unknown>[] = Array.isArray(data?.items)
      ? (data.items as Record<string, unknown>[])
      : Array.isArray(data)
        ? (data as Record<string, unknown>[])
        : []

    return itemsArray
      .map((item) => mapChecklistItem(item))
      .filter((item): item is ChecklistItem => item !== null)
  } catch (error) {
    console.error('Failed to fetch property checklist:', error)
    return []
  }
}

function mapChecklistItem(item: Record<string, unknown>): ChecklistItem | null {
  const id = coerceString(item.id)
  const propertyId = coerceString(item.property_id)
  const scenarioValue = coerceString(item.development_scenario)
  const categoryValue = coerceString(item.category)
  const itemTitle = coerceString(item.item_title)
  const statusValue = coerceString(item.status)
  const priorityValue = coerceString(item.priority)
  const createdAt = coerceString(item.created_at)
  const updatedAt = coerceString(item.updated_at)

  if (
    !id ||
    !propertyId ||
    !itemTitle ||
    !createdAt ||
    !updatedAt ||
    !scenarioValue ||
    !isDevelopmentScenario(scenarioValue) ||
    !categoryValue ||
    !isChecklistCategory(categoryValue) ||
    !statusValue ||
    !isChecklistStatus(statusValue) ||
    !priorityValue ||
    !isChecklistPriority(priorityValue)
  ) {
    return null
  }

  const assignedTo = coerceString(item.assigned_to) ?? null
  const dueDate = coerceString(item.due_date) ?? null
  const completedAt =
    coerceString(item.completed_at) ?? coerceString(item.completed_date) ?? null
  const notes = coerceString(item.notes) ?? null
  const requiresProfessional =
    coerceBoolean(item.requires_professional) ?? false
  const professionalType = coerceString(item.professional_type) ?? null
  const typicalDurationDays = coerceNumber(item.typical_duration_days)
  const displayOrder = coerceNumber(item.display_order)

  return {
    id,
    propertyId,
    developmentScenario: scenarioValue,
    category: categoryValue,
    itemTitle,
    itemDescription: coerceString(item.item_description) ?? undefined,
    status: statusValue,
    priority: priorityValue,
    assignedTo,
    dueDate,
    completedAt,
    notes,
    requiresProfessional,
    professionalType,
    typicalDurationDays,
    displayOrder,
    createdAt,
    updatedAt,
  }
}

export async function fetchChecklistSummary(
  propertyId: string,
): Promise<ChecklistSummary | null> {
  const url = buildUrl(
    `api/v1/developers/properties/${propertyId}/checklists/summary`,
  )

  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Checklist summary fetch failed: ${response.statusText}`)
    }
    const data = await response.json()

    const byCategoryStatusRaw = data.by_category_status ?? {}
    const byCategoryStatus: Record<string, ChecklistCategoryStatus> = {}
    if (
      byCategoryStatusRaw &&
      typeof byCategoryStatusRaw === 'object' &&
      !Array.isArray(byCategoryStatusRaw)
    ) {
      for (const [category, summary] of Object.entries(byCategoryStatusRaw)) {
        if (summary && typeof summary === 'object') {
          const typedSummary = summary as Record<string, unknown>
          byCategoryStatus[category] = {
            total: Number(typedSummary.total ?? 0),
            completed: Number(typedSummary.completed ?? 0),
            inProgress: Number(typedSummary.in_progress ?? 0),
            pending: Number(typedSummary.pending ?? 0),
            notApplicable: Number(typedSummary.not_applicable ?? 0),
          }
        }
      }
    }

    return {
      propertyId: data.property_id ?? propertyId,
      total: data.total ?? 0,
      completed: data.completed ?? 0,
      inProgress: data.in_progress ?? 0,
      pending: data.pending ?? 0,
      notApplicable: data.not_applicable ?? 0,
      completionPercentage: data.completion_percentage ?? 0,
      byCategoryStatus,
    }
  } catch (error) {
    console.error('Failed to fetch checklist summary:', error)
    return null
  }
}

export async function updateChecklistItem(
  checklistId: string,
  updates: UpdateChecklistRequest,
): Promise<ChecklistItem | null> {
  const url = buildUrl(`api/v1/developers/checklists/${checklistId}`)

  try {
    const response = await fetch(url, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    })

    if (!response.ok) {
      throw new Error(`Checklist update failed: ${response.statusText}`)
    }

    const data = await response.json()

    return {
      id: data.id,
      propertyId: data.property_id,
      developmentScenario: data.development_scenario,
      category: data.category,
      itemTitle: data.item_title,
      itemDescription: data.item_description ?? undefined,
      status: data.status,
      priority: data.priority,
      assignedTo: data.assigned_to ?? null,
      dueDate: data.due_date ?? null,
      completedAt: data.completed_at ?? null,
      notes: data.notes ?? null,
      requiresProfessional: data.requires_professional ?? false,
      professionalType: data.professional_type ?? null,
      typicalDurationDays: data.typical_duration_days ?? null,
      createdAt: data.created_at,
      updatedAt: data.updated_at,
    }
  } catch (error) {
    console.error('Failed to update checklist item:', error)
    return null
  }
}

function mapChecklistTemplateResponse(
  payload: Record<string, unknown>,
): ChecklistTemplate {
  const requiresProfessionalRaw = payload.requiresProfessional
  const requiresProfessional =
    typeof requiresProfessionalRaw === 'boolean'
      ? requiresProfessionalRaw
      : Boolean(requiresProfessionalRaw)

  const durationValue = payload.typicalDurationDays
  const typicalDurationNumber =
    typeof durationValue === 'number'
      ? durationValue
      : typeof durationValue === 'string' && durationValue.trim() !== ''
        ? Number(durationValue)
        : null

  const displayOrderValue = payload.displayOrder
  const displayOrderNumber =
    typeof displayOrderValue === 'number'
      ? displayOrderValue
      : typeof displayOrderValue === 'string' && displayOrderValue.trim() !== ''
        ? Number(displayOrderValue)
        : null

  return {
    id: String(payload.id ?? ''),
    developmentScenario: String(payload.developmentScenario ?? ''),
    category: String(payload.category ?? '') as ChecklistCategory,
    itemTitle: String(payload.itemTitle ?? ''),
    itemDescription:
      typeof payload.itemDescription === 'string'
        ? payload.itemDescription
        : null,
    priority: String(payload.priority ?? 'medium') as ChecklistPriority,
    typicalDurationDays:
      typeof typicalDurationNumber === 'number' &&
      Number.isFinite(typicalDurationNumber)
        ? typicalDurationNumber
        : null,
    requiresProfessional,
    professionalType:
      requiresProfessional &&
      typeof payload.professionalType === 'string' &&
      payload.professionalType.trim() !== ''
        ? payload.professionalType
        : null,
    displayOrder:
      typeof displayOrderNumber === 'number' &&
      Number.isFinite(displayOrderNumber)
        ? displayOrderNumber
        : 0,
    createdAt: String(payload.createdAt ?? ''),
    updatedAt: String(payload.updatedAt ?? ''),
  }
}

export async function fetchChecklistTemplates(
  developmentScenario?: string,
): Promise<ChecklistTemplate[]> {
  const params = new URLSearchParams()
  if (developmentScenario && developmentScenario !== 'all') {
    params.append('developmentScenario', developmentScenario)
  }

  const query = params.toString()
  const url = buildUrl(
    `api/v1/developers/checklists/templates${query ? `?${query}` : ''}`,
  )

  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Template fetch failed: ${response.statusText}`)
    }
    const data = await response.json()
    if (!Array.isArray(data)) {
      return []
    }
    return data.map((item: Record<string, unknown>) =>
      mapChecklistTemplateResponse(item),
    )
  } catch (error) {
    console.error('Failed to fetch checklist templates:', error)
    return []
  }
}

function buildTemplatePayload(
  template: ChecklistTemplateDraft | ChecklistTemplateUpdate,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {}

  if (Object.prototype.hasOwnProperty.call(template, 'developmentScenario')) {
    payload.developmentScenario = template.developmentScenario
  }
  if (Object.prototype.hasOwnProperty.call(template, 'category')) {
    payload.category = template.category
  }
  if (Object.prototype.hasOwnProperty.call(template, 'itemTitle')) {
    payload.itemTitle = template.itemTitle
  }
  if (Object.prototype.hasOwnProperty.call(template, 'itemDescription')) {
    payload.itemDescription = template.itemDescription
  }
  if (Object.prototype.hasOwnProperty.call(template, 'priority')) {
    payload.priority = template.priority
  }
  if (Object.prototype.hasOwnProperty.call(template, 'typicalDurationDays')) {
    const value = template.typicalDurationDays
    if (value === null || value === undefined) {
      payload.typicalDurationDays = null
    } else if (typeof value === 'string') {
      payload.typicalDurationDays = value.trim() === '' ? null : Number(value)
    } else {
      payload.typicalDurationDays = value
    }
  }
  if (Object.prototype.hasOwnProperty.call(template, 'requiresProfessional')) {
    payload.requiresProfessional = Boolean(template.requiresProfessional)
  }
  if (Object.prototype.hasOwnProperty.call(template, 'professionalType')) {
    payload.professionalType = template.professionalType
  }
  if (Object.prototype.hasOwnProperty.call(template, 'displayOrder')) {
    const value = template.displayOrder
    if (value === null || value === undefined) {
      payload.displayOrder = null
    } else if (typeof value === 'string') {
      payload.displayOrder = value.trim() === '' ? null : Number(value)
    } else {
      payload.displayOrder = value
    }
  }

  return payload
}

export async function createChecklistTemplate(
  template: ChecklistTemplateDraft,
): Promise<ChecklistTemplate | null> {
  const draftPayload = {
    ...template,
    requiresProfessional: template.requiresProfessional ?? false,
  }

  const response = await fetch(
    buildUrl('api/v1/developers/checklists/templates'),
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(buildTemplatePayload(draftPayload)),
    },
  )

  if (!response.ok) {
    console.error('Failed to create checklist template:', response.statusText)
    return null
  }

  const data = await response.json()
  return mapChecklistTemplateResponse(data)
}

export async function updateChecklistTemplate(
  templateId: string,
  updates: ChecklistTemplateUpdate,
): Promise<ChecklistTemplate | null> {
  const response = await fetch(
    buildUrl(`api/v1/developers/checklists/templates/${templateId}`),
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(buildTemplatePayload(updates)),
    },
  )

  if (!response.ok) {
    console.error('Failed to update checklist template:', response.statusText)
    return null
  }

  const data = await response.json()
  return mapChecklistTemplateResponse(data)
}

export async function deleteChecklistTemplate(
  templateId: string,
): Promise<boolean> {
  const response = await fetch(
    buildUrl(`api/v1/developers/checklists/templates/${templateId}`),
    {
      method: 'DELETE',
    },
  )

  if (response.status === 204) {
    return true
  }

  if (response.status === 404) {
    return false
  }

  console.error('Failed to delete checklist template:', response.statusText)
  return false
}

export async function importChecklistTemplates(
  templates: ChecklistTemplateDraft[],
  replaceExisting: boolean,
): Promise<ChecklistTemplateImportResult | null> {
  const response = await fetch(
    buildUrl('api/v1/developers/checklists/templates/import'),
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        templates: templates.map((template) => buildTemplatePayload(template)),
        replaceExisting,
      }),
    },
  )

  if (!response.ok) {
    console.error('Failed to import checklist templates:', response.statusText)
    return null
  }

  const data = await response.json()
  return {
    created: Number(data.created ?? 0),
    updated: Number(data.updated ?? 0),
    deleted: Number(data.deleted ?? 0),
  }
}
