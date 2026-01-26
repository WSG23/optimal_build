/**
 * Site Acquisition API client for developers
 * Wraps GPS logging and feasibility APIs with developer-specific features
 */

import {
  buildUrl,
  coerceNumber as coerceNumeric,
  coerceString,
  boolish,
  roundOptional,
} from './shared'
import { applyIdentityHeaders } from './identity'

import {
  fetchChecklistSummary as fetchChecklistSummaryFromAgents,
  fetchPropertyChecklist as fetchPropertyChecklistFromAgents,
  logPropertyByGps,
  updateChecklistItem as updateChecklistItemFromAgents,
  fetchChecklistTemplates as fetchChecklistTemplatesFromAgents,
  createChecklistTemplate as createChecklistTemplateFromAgents,
  updateChecklistTemplate as updateChecklistTemplateFromAgents,
  deleteChecklistTemplate as deleteChecklistTemplateFromAgents,
  importChecklistTemplates as importChecklistTemplatesFromAgents,
  DEFAULT_SCENARIO_ORDER,
  type ChecklistItem,
  type ChecklistStatus,
  type ChecklistSummary,
  type ChecklistTemplate as AgentsChecklistTemplate,
  type ChecklistTemplateDraft as AgentsChecklistTemplateDraft,
  type ChecklistTemplateUpdate as AgentsChecklistTemplateUpdate,
  type ChecklistTemplateImportResult as AgentsChecklistTemplateImportResult,
  type ChecklistCategory,
  type ChecklistPriority,
  type DevelopmentScenario,
  type GpsCaptureSummary,
  type UpdateChecklistRequest,
  type RawQuickAnalysis,
} from './agents'

export interface SiteAcquisitionRequest {
  latitude: number
  longitude: number
  developmentScenarios: DevelopmentScenario[]
  previewDetailLevel?: GeometryDetailLevel
  jurisdictionCode?: string
}

export interface DeveloperBuildEnvelope {
  zoneCode: string | null
  zoneDescription: string | null
  siteAreaSqm: number | null
  allowablePlotRatio: number | null
  maxBuildableGfaSqm: number | null
  currentGfaSqm: number | null
  additionalPotentialGfaSqm: number | null
  buildingHeightLimitM: number | null
  siteCoveragePct: number | null
  assumptions: string[]
  sourceReference: string | null
}

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

export interface SiteAcquisitionResult extends GpsCaptureSummary {
  buildEnvelope: DeveloperBuildEnvelope
  visualization: DeveloperVisualizationSummary
  optimizations: DeveloperAssetOptimization[]
  financialSummary: DeveloperFinancialSummary
  heritageContext: DeveloperHeritageContext | null
  previewJobs: DeveloperPreviewJob[]
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
  financeBlueprint: DeveloperFinanceBlueprint | null
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

export interface DeveloperCapitalStructureScenario {
  scenario: string
  equityPct: number
  debtPct: number
  preferredEquityPct: number
  targetLtv: number
  targetLtc: number
  targetDscr: number
  comments: string | null
}

export interface DeveloperDebtFacility {
  facilityType: string
  amountExpression: string
  interestRate: string
  tenorYears: number | null
  amortisation: string | null
  drawdownScheduleNotes: string | null
  covenantsTriggers: string | null
}

export interface DeveloperEquityWaterfallTier {
  hurdleIrrPct: number
  promotePct: number
}

export interface DeveloperEquityWaterfall {
  tiers: DeveloperEquityWaterfallTier[]
  preferredReturnPct: number | null
  catchUpNotes: string | null
}

export interface DeveloperCashFlowMilestone {
  item: string
  startMonth: number
  durationMonths: number
  notes: string | null
}

export interface DeveloperExitAssumptions {
  exitCapRates: Record<string, number>
  saleCostsPct: number
  saleCostsBreakdown: string | null
  refinanceTerms: string | null
}

export interface DeveloperSensitivityBand {
  parameter: string
  low: number
  base: number
  high: number
  comments: string | null
}

export interface DeveloperFinanceBlueprint {
  capitalStructure: DeveloperCapitalStructureScenario[]
  debtFacilities: DeveloperDebtFacility[]
  equityWaterfall: DeveloperEquityWaterfall | null
  cashFlowTimeline: DeveloperCashFlowMilestone[]
  exitAssumptions: DeveloperExitAssumptions | null
  sensitivityBands: DeveloperSensitivityBand[]
}

export interface FinanceProjectCreatePayload {
  projectName?: string | null
  scenarioName?: string | null
  totalEstimatedCapexSgd?: number | null
  totalEstimatedRevenueSgd?: number | null
}

export interface FinanceProjectCreateResult {
  projectId: string
  projectName: string
  finProjectId: number
  scenarioId: number
}

export interface CaptureProjectLinkResult {
  projectId: string
  projectName: string
}

export interface ConditionSystem {
  name: string
  rating: string
  score: number
  notes: string
  recommendedActions: string[]
}

export interface ConditionInsight {
  id: string
  severity: 'critical' | 'warning' | 'positive' | 'info'
  title: string
  detail: string
  specialist?: string | null
}

export interface ConditionAttachment {
  label: string
  url: string | null
}

export interface ConditionAssessment {
  propertyId: string
  scenario?: DevelopmentScenario | 'all' | null
  overallScore: number
  overallRating: string
  riskLevel: string
  summary: string
  scenarioContext?: string | null
  systems: ConditionSystem[]
  recommendedActions: string[]
  inspectorName?: string | null
  recordedBy?: string | null
  recordedAt?: string | null
  attachments: ConditionAttachment[]
  insights: ConditionInsight[]
}

export interface ConditionAssessmentUpsertRequest {
  scenario?: DevelopmentScenario | 'all'
  overallRating: string
  overallScore: number
  riskLevel: string
  summary: string
  scenarioContext?: string | null
  systems: ConditionSystem[]
  recommendedActions: string[]
  inspectorName?: string | null
  recordedAt?: string | null
  attachments: ConditionAttachment[]
}

export type ChecklistTemplate = AgentsChecklistTemplate
export type ChecklistTemplateDraft = AgentsChecklistTemplateDraft
export type ChecklistTemplateUpdate = AgentsChecklistTemplateUpdate
export type ChecklistTemplateImportResult = AgentsChecklistTemplateImportResult

// Re-export types from agents.ts
export type {
  ChecklistItem,
  ChecklistSummary,
  ChecklistCategory,
  ChecklistPriority,
  DevelopmentScenario,
  ChecklistStatus,
  GpsCaptureSummary,
  UpdateChecklistRequest,
}

// Type aliases for backward compatibility
export type ConditionAssessmentEntry = ConditionAssessment
export type PreviewJob = DeveloperPreviewJob
export type PreviewJobInfo = DeveloperPreviewJob
export type CapturedProperty = SiteAcquisitionResult

function mapConditionAssessmentPayload(
  payload: Record<string, unknown>,
  fallbackPropertyId: string,
): ConditionAssessment {
  const propertyId = String(payload.property_id ?? fallbackPropertyId)
  const systems = Array.isArray(payload.systems)
    ? payload.systems.map((system: Record<string, unknown>) => ({
        name: String(system.name ?? ''),
        rating: String(system.rating ?? ''),
        score: Number(system.score ?? 0),
        notes: String(system.notes ?? ''),
        recommendedActions: Array.isArray(system.recommended_actions)
          ? (system.recommended_actions as string[])
          : [],
      }))
    : []

  const insights = Array.isArray(payload.insights)
    ? payload.insights
        .map(
          (entry: Record<string, unknown>, index: number): ConditionInsight => {
            const rawSeverity = String(
              entry.severity ?? 'warning',
            ).toLowerCase()
            const severity: ConditionInsight['severity'] = (
              ['critical', 'warning', 'positive', 'info'].includes(rawSeverity)
                ? rawSeverity
                : 'warning'
            ) as ConditionInsight['severity']
            const specialistValue =
              typeof entry.specialist === 'string' &&
              entry.specialist.trim() !== ''
                ? entry.specialist
                : null
            return {
              id: String(entry.id ?? `insight-${index}`),
              severity,
              title: String(entry.title ?? 'Condition insight'),
              detail: String(entry.detail ?? ''),
              specialist: specialistValue,
            }
          },
        )
        .filter((insight) => insight.detail !== '')
    : []

  const attachments = Array.isArray(payload.attachments)
    ? payload.attachments
        .map((entry: Record<string, unknown>) => {
          const label = String(entry.label ?? '').trim()
          const urlValue =
            typeof entry.url === 'string' && entry.url.trim().length > 0
              ? entry.url.trim()
              : null
          if (!label && !urlValue) {
            return null
          }
          return {
            label: label || (urlValue ?? ''),
            url: urlValue,
          }
        })
        .filter((item): item is ConditionAttachment => item !== null)
    : []

  return {
    propertyId,
    scenario:
      typeof payload.scenario === 'string'
        ? (payload.scenario as DevelopmentScenario)
        : typeof payload.scenario === 'undefined' &&
            typeof payload['scenario'] === 'string'
          ? (payload['scenario'] as DevelopmentScenario)
          : ((payload.scenario as DevelopmentScenario | null | undefined) ??
            null),
    overallScore: Number(payload.overall_score ?? payload.overallScore ?? 0),
    overallRating: String(
      payload.overall_rating ?? payload.overallRating ?? 'C',
    ),
    riskLevel: String(payload.risk_level ?? payload.riskLevel ?? 'moderate'),
    summary: String(payload.summary ?? ''),
    scenarioContext:
      typeof payload.scenario_context === 'string'
        ? payload.scenario_context
        : typeof payload.scenarioContext === 'string'
          ? payload.scenarioContext
          : null,
    systems,
    recommendedActions: Array.isArray(payload.recommended_actions)
      ? (payload.recommended_actions as string[])
      : Array.isArray(payload.recommendedActions)
        ? (payload.recommendedActions as string[])
        : [],
    inspectorName:
      typeof payload.inspector_name === 'string'
        ? payload.inspector_name
        : typeof payload.inspectorName === 'string'
          ? payload.inspectorName
          : null,
    recordedBy:
      typeof payload.recorded_by === 'string'
        ? payload.recorded_by
        : typeof payload.recordedBy === 'string'
          ? payload.recordedBy
          : null,
    recordedAt:
      typeof payload.recorded_at === 'string'
        ? payload.recorded_at
        : typeof payload.recordedAt === 'string'
          ? payload.recordedAt
          : null,
    attachments,
    insights,
  }
}

export type GeometryDetailLevel = 'simple' | 'medium'

export interface DeveloperPreviewJob {
  id: string
  propertyId: string
  scenario: string
  status: string
  previewUrl: string | null
  metadataUrl: string | null
  thumbnailUrl: string | null
  assetVersion: string | null
  requestedAt: string
  startedAt: string | null
  finishedAt: string | null
  message: string | null
  geometryDetailLevel: GeometryDetailLevel | null
}

const DEVELOPER_GPS_ENDPOINT = '/api/v1/developers/properties/log-gps'

interface RawDeveloperEnvelope {
  zone_code?: unknown
  zoneCode?: unknown
  zone_description?: unknown
  zoneDescription?: unknown
  site_area_sqm?: unknown
  siteAreaSqm?: unknown
  allowable_plot_ratio?: unknown
  allowablePlotRatio?: unknown
  max_buildable_gfa_sqm?: unknown
  maxBuildableGfaSqm?: unknown
  current_gfa_sqm?: unknown
  currentGfaSqm?: unknown
  additional_potential_gfa_sqm?: unknown
  additionalPotentialGfaSqm?: unknown
  building_height_limit_m?: unknown
  buildingHeightLimitM?: unknown
  site_coverage_pct?: unknown
  siteCoveragePct?: unknown
  assumptions?: unknown
  source_reference?: unknown
  sourceReference?: unknown
}

interface RawDeveloperVisualization {
  status?: unknown
  preview_available?: unknown
  previewAvailable?: unknown
  concept_mesh_url?: unknown
  conceptMeshUrl?: unknown
  preview_metadata_url?: unknown
  previewMetadataUrl?: unknown
  thumbnail_url?: unknown
  thumbnailUrl?: unknown
  camera_orbit_hint?: unknown
  cameraOrbitHint?: unknown
  preview_seed?: unknown
  previewSeed?: unknown
  preview_job_id?: unknown
  previewJobId?: unknown
  notes?: unknown
  massing_layers?: unknown
  massingLayers?: unknown
  color_legend?: unknown
  colorLegend?: unknown
}

interface RawDeveloperGpsResponse {
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
  build_envelope?: RawDeveloperEnvelope | null
  visualization?: RawDeveloperVisualization | null
  optimizations?: Array<Record<string, unknown>> | null
  financial_summary?: RawDeveloperFinancialSummary | null
  preview_jobs?: Array<Record<string, unknown>> | null
  heritage_context?: Record<string, unknown> | null
}

interface RawDeveloperFinancialSummary extends Record<string, unknown> {
  total_estimated_revenue_sgd?: unknown
  total_estimated_capex_sgd?: unknown
  dominant_risk_profile?: unknown
  notes?: unknown
  finance_blueprint?: Record<string, unknown> | null
  financeBlueprint?: Record<string, unknown> | null
}

function mapDeveloperEnvelope(
  payload: RawDeveloperEnvelope | null | undefined,
): DeveloperBuildEnvelope {
  const zoneCode =
    coerceString(payload?.zone_code) ?? coerceString(payload?.zoneCode)
  const zoneDescription =
    coerceString(payload?.zone_description) ??
    coerceString(payload?.zoneDescription)
  const siteArea =
    coerceNumeric(payload?.site_area_sqm) ?? coerceNumeric(payload?.siteAreaSqm)
  const plotRatio =
    coerceNumeric(payload?.allowable_plot_ratio) ??
    coerceNumeric(payload?.allowablePlotRatio)
  const maxBuildable =
    coerceNumeric(payload?.max_buildable_gfa_sqm) ??
    coerceNumeric(payload?.maxBuildableGfaSqm)
  const currentGfa =
    coerceNumeric(payload?.current_gfa_sqm) ??
    coerceNumeric(payload?.currentGfaSqm)
  const additional =
    coerceNumeric(payload?.additional_potential_gfa_sqm) ??
    coerceNumeric(payload?.additionalPotentialGfaSqm)
  const buildingHeightLimitM =
    coerceNumeric(payload?.building_height_limit_m) ??
    coerceNumeric(payload?.buildingHeightLimitM)
  const siteCoveragePct =
    coerceNumeric(payload?.site_coverage_pct) ??
    coerceNumeric(payload?.siteCoveragePct)
  const sourceReference =
    coerceString(payload?.source_reference) ??
    coerceString(payload?.sourceReference)

  const assumptions = Array.isArray(payload?.assumptions)
    ? payload!.assumptions
        .map((entry) => coerceString(entry) ?? '')
        .filter((entry): entry is string => entry.length > 0)
    : []

  return {
    zoneCode: zoneCode ?? null,
    zoneDescription: zoneDescription ?? null,
    siteAreaSqm: roundOptional(siteArea),
    allowablePlotRatio: roundOptional(plotRatio),
    maxBuildableGfaSqm: roundOptional(maxBuildable),
    currentGfaSqm: roundOptional(currentGfa),
    additionalPotentialGfaSqm: roundOptional(additional),
    buildingHeightLimitM: roundOptional(buildingHeightLimitM),
    siteCoveragePct: roundOptional(siteCoveragePct),
    assumptions,
    sourceReference: sourceReference ?? null,
  }
}

function mapDeveloperVisualization(
  payload: RawDeveloperVisualization | null | undefined,
): DeveloperVisualizationSummary {
  const status = coerceString(payload?.status) ?? 'placeholder'
  const preview =
    typeof payload?.preview_available === 'boolean'
      ? payload.preview_available
      : typeof payload?.previewAvailable === 'boolean'
        ? payload.previewAvailable
        : false
  const conceptMeshUrl =
    coerceString(payload?.concept_mesh_url) ??
    coerceString(payload?.conceptMeshUrl) ??
    null
  const previewMetadataUrl =
    coerceString(payload?.preview_metadata_url) ??
    coerceString(payload?.previewMetadataUrl) ??
    null
  const thumbnailUrl =
    coerceString(payload?.thumbnail_url) ??
    coerceString(payload?.thumbnailUrl) ??
    null
  const cameraOrbitHint =
    typeof payload?.camera_orbit_hint === 'object' && payload?.camera_orbit_hint
      ? (payload?.camera_orbit_hint as Record<string, number>)
      : typeof payload?.cameraOrbitHint === 'object' && payload?.cameraOrbitHint
        ? (payload?.cameraOrbitHint as Record<string, number>)
        : null
  const previewSeed = coerceNumeric(
    payload?.preview_seed ?? payload?.previewSeed,
  )
  const previewJobId =
    coerceString(payload?.preview_job_id) ??
    coerceString(payload?.previewJobId) ??
    null
  const notes = Array.isArray(payload?.notes)
    ? payload.notes
        .map((note) => coerceString(note) ?? '')
        .filter((note): note is string => note.length > 0)
    : []
  const rawMassing = Array.isArray(payload?.massing_layers)
    ? payload.massing_layers
    : Array.isArray(payload?.massingLayers)
      ? payload.massingLayers
      : []
  const massingLayers = Array.isArray(rawMassing)
    ? rawMassing
        .map((entry) => {
          if (!entry || typeof entry !== 'object') {
            return null
          }
          const item = entry as Record<string, unknown>
          const assetType =
            coerceString(item.asset_type) ?? coerceString(item.assetType)
          const allocationPct =
            coerceNumeric(item.allocation_pct) ??
            coerceNumeric(item.allocationPct)
          const gfaSqm =
            coerceNumeric(item.gfa_sqm) ?? coerceNumeric(item.gfaSqm) ?? null
          const niaSqm =
            coerceNumeric(item.nia_sqm) ?? coerceNumeric(item.niaSqm) ?? null
          const estimatedHeight =
            coerceNumeric(item.estimated_height_m) ??
            coerceNumeric(item.estimatedHeightM) ??
            null
          const color = coerceString(item.color) ?? 'var(--ob-neutral-400)'
          if (!assetType || allocationPct === null) {
            return null
          }
          return {
            assetType,
            allocationPct,
            gfaSqm,
            niaSqm,
            estimatedHeightM: estimatedHeight,
            color,
          }
        })
        .filter((layer): layer is DeveloperMassingLayer => layer !== null)
    : []

  const rawLegend = Array.isArray(payload?.color_legend)
    ? payload.color_legend
    : Array.isArray(payload?.colorLegend)
      ? payload.colorLegend
      : []
  const colorLegend = Array.isArray(rawLegend)
    ? rawLegend
        .map((entry) => {
          if (!entry || typeof entry !== 'object') {
            return null
          }
          const item = entry as Record<string, unknown>
          const assetType =
            coerceString(item.asset_type) ?? coerceString(item.assetType)
          const label = coerceString(item.label)
          const color = coerceString(item.color)
          const description =
            coerceString(item.description) ??
            coerceString(item.legendDescription) ??
            null
          if (!assetType || !label || !color) {
            return null
          }
          return {
            assetType,
            label,
            color,
            description,
          }
        })
        .filter((entry): entry is DeveloperColorLegendEntry => entry !== null)
    : []

  if (!notes.length) {
    notes.push(
      'High-fidelity 3D previews will ship with Phase 2B visualisation work.',
    )
  }
  return {
    status,
    previewAvailable: preview,
    notes,
    conceptMeshUrl,
    previewMetadataUrl,
    thumbnailUrl,
    cameraOrbitHint,
    previewSeed: previewSeed ?? null,
    previewJobId,
    massingLayers,
    colorLegend,
  }
}

function mapDeveloperOptimizations(
  payload: Array<Record<string, unknown>> | null | undefined,
): DeveloperAssetOptimization[] {
  if (!Array.isArray(payload)) {
    return []
  }
  return payload
    .map((entry) => {
      const assetType =
        coerceString(entry.asset_type) ?? coerceString(entry.assetType)
      const allocation =
        coerceNumeric(entry.allocation_pct) ??
        coerceNumeric(entry.allocationPct)
      const efficiency =
        coerceNumeric(entry.nia_efficiency) ??
        coerceNumeric(entry.niaEfficiency)
      const allocated =
        coerceNumeric(entry.allocated_gfa_sqm) ??
        coerceNumeric(entry.allocatedGfaSqm)
      const floorHeight =
        coerceNumeric(entry.target_floor_height_m) ??
        coerceNumeric(entry.targetFloorHeightM)
      const parking =
        coerceNumeric(entry.parking_ratio_per_1000sqm) ??
        coerceNumeric(entry.parkingRatioPer1000Sqm)
      const rent =
        coerceNumeric(entry.rent_psm_month) ?? coerceNumeric(entry.rentPsmMonth)
      const vacancy =
        coerceNumeric(entry.stabilised_vacancy_pct) ??
        coerceNumeric(entry.stabilisedVacancyPct)
      const opex =
        coerceNumeric(entry.opex_pct_of_rent) ??
        coerceNumeric(entry.opexPctOfRent)
      const revenue =
        coerceNumeric(entry.estimated_revenue_sgd) ??
        coerceNumeric(entry.estimatedRevenueSgd)
      const capex =
        coerceNumeric(entry.estimated_capex_sgd) ??
        coerceNumeric(entry.estimatedCapexSgd)
      const fitout =
        coerceNumeric(entry.fitout_cost_psm) ??
        coerceNumeric(entry.fitoutCostPsm)
      const absorption =
        coerceNumeric(entry.absorption_months) ??
        coerceNumeric(entry.absorptionMonths)
      const riskLevel =
        coerceString(entry.risk_level) ?? coerceString(entry.riskLevel)
      const heritagePremium =
        coerceNumeric(entry.heritage_premium_pct) ??
        coerceNumeric(entry.heritagePremiumPct)
      const notes = Array.isArray(entry.notes)
        ? entry.notes
            .map((note) => coerceString(note) ?? '')
            .filter((note): note is string => note.length > 0)
        : []
      if (!assetType || allocation === null) {
        return null
      }
      return {
        assetType,
        allocationPct: allocation,
        niaEfficiency: efficiency,
        allocatedGfaSqm: allocated,
        targetFloorHeightM: floorHeight,
        parkingRatioPer1000Sqm: parking,
        rentPsmMonth: rent ?? null,
        stabilisedVacancyPct: vacancy ?? null,
        opexPctOfRent: opex ?? null,
        estimatedRevenueSgd: revenue,
        estimatedCapexSgd: capex,
        fitoutCostPsm: fitout ?? null,
        absorptionMonths: absorption ? Math.round(absorption) : null,
        riskLevel: riskLevel ?? null,
        heritagePremiumPct: heritagePremium ?? null,
        notes,
      }
    })
    .filter((item): item is DeveloperAssetOptimization => item !== null)
}

function mapHeritageContext(payload: unknown): DeveloperHeritageContext | null {
  if (!payload || typeof payload !== 'object') {
    return null
  }

  const source = payload as Record<string, unknown>
  const risk = coerceString(source.risk) ?? null
  const notes = Array.isArray(source.notes)
    ? source.notes
        .map((entry) => coerceString(entry) ?? '')
        .filter((entry): entry is string => entry.length > 0)
    : []
  const constraints = Array.isArray(source.constraints)
    ? source.constraints
        .map((entry) => coerceString(entry) ?? '')
        .filter((entry): entry is string => entry.length > 0)
    : []

  let overlay: DeveloperHeritageContext['overlay'] = null
  const overlayRaw = source.overlay
  if (overlayRaw && typeof overlayRaw === 'object') {
    const raw = overlayRaw as Record<string, unknown>
    overlay = {
      name: coerceString(raw.name) ?? coerceString(raw.overlayName) ?? null,
      source: coerceString(raw.source) ?? null,
      heritagePremiumPct:
        coerceNumeric(raw.heritage_premium_pct) ??
        coerceNumeric(raw.heritagePremiumPct) ??
        null,
    }
  }

  const flagValue = source.flag
  const flag = typeof flagValue === 'boolean' ? flagValue : boolish(flagValue)

  return {
    flag,
    risk,
    notes,
    constraints,
    assumption: coerceString(source.assumption) ?? null,
    overlay,
  }
}

function normaliseGeometryDetailLevel(
  value: unknown,
): GeometryDetailLevel | null {
  const text = coerceString(value)?.toLowerCase()
  if (text === 'simple' || text === 'medium') {
    return text
  }
  return null
}

function mapPreviewJobs(payload: unknown): DeveloperPreviewJob[] {
  if (!Array.isArray(payload)) {
    return []
  }

  return payload
    .map((entry) => {
      if (!entry || typeof entry !== 'object') {
        return null
      }
      const item = entry as Record<string, unknown>
      const id = coerceString(item.id) ?? coerceString(item.preview_job_id)
      const propertyId =
        coerceString(item.property_id) ?? coerceString(item.propertyId)
      const scenario = coerceString(item.scenario)
      const status = coerceString(item.status)
      if (!id || !propertyId || !scenario || !status) {
        return null
      }
      return {
        id,
        propertyId,
        scenario,
        status,
        previewUrl:
          coerceString(item.preview_url) ??
          coerceString(item.previewUrl) ??
          null,
        metadataUrl:
          coerceString(item.metadata_url) ??
          coerceString(item.metadataUrl) ??
          null,
        thumbnailUrl:
          coerceString(item.thumbnail_url) ??
          coerceString(item.thumbnailUrl) ??
          null,
        assetVersion:
          coerceString(item.asset_version) ??
          coerceString(item.assetVersion) ??
          null,
        requestedAt:
          coerceString(item.requested_at) ??
          coerceString(item.requestedAt) ??
          '',
        startedAt:
          coerceString(item.started_at) ?? coerceString(item.startedAt) ?? null,
        finishedAt:
          coerceString(item.finished_at) ??
          coerceString(item.finishedAt) ??
          null,
        message: coerceString(item.message) ?? null,
        geometryDetailLevel: normaliseGeometryDetailLevel(
          item.geometry_detail_level ?? item.geometryDetailLevel,
        ),
      }
    })
    .filter((entry): entry is DeveloperPreviewJob => entry !== null)
}

function mapFinanceBlueprint(
  payload: unknown,
): DeveloperFinanceBlueprint | null {
  if (!payload || typeof payload !== 'object') {
    return null
  }

  const source = payload as Record<string, unknown>

  const capitalStructure = Array.isArray(source.capital_structure)
    ? source.capital_structure
        .map((entry) => {
          if (!entry || typeof entry !== 'object') {
            return null
          }
          const item = entry as Record<string, unknown>
          const scenario =
            coerceString(item.scenario) ?? coerceString(item.scenarioName)
          const equity =
            coerceNumeric(item.equity_pct) ?? coerceNumeric(item.equityPct)
          const debt =
            coerceNumeric(item.debt_pct) ?? coerceNumeric(item.debtPct)
          const pref =
            coerceNumeric(item.preferred_equity_pct) ??
            coerceNumeric(item.preferredEquityPct)
          const targetLtv =
            coerceNumeric(item.target_ltv) ?? coerceNumeric(item.targetLtv)
          const targetLtc =
            coerceNumeric(item.target_ltc) ?? coerceNumeric(item.targetLtc)
          const targetDscr =
            coerceNumeric(item.target_dscr) ?? coerceNumeric(item.targetDscr)
          if (
            !scenario ||
            equity === null ||
            debt === null ||
            pref === null ||
            targetLtv === null ||
            targetLtc === null ||
            targetDscr === null
          ) {
            return null
          }
          return {
            scenario,
            equityPct: equity,
            debtPct: debt,
            preferredEquityPct: pref,
            targetLtv,
            targetLtc,
            targetDscr,
            comments: coerceString(item.comments) ?? null,
          }
        })
        .filter(
          (entry): entry is DeveloperCapitalStructureScenario => entry !== null,
        )
    : []

  const debtFacilities = Array.isArray(source.debt_facilities)
    ? source.debt_facilities
        .map((entry) => {
          if (!entry || typeof entry !== 'object') {
            return null
          }
          const item = entry as Record<string, unknown>
          const facilityType =
            coerceString(item.facility_type) ?? coerceString(item.facilityType)
          const amountExpression =
            coerceString(item.amount_expression) ??
            coerceString(item.amountExpression)
          const interestRate =
            coerceString(item.interest_rate) ?? coerceString(item.interestRate)
          if (!facilityType || !amountExpression || !interestRate) {
            return null
          }
          return {
            facilityType,
            amountExpression,
            interestRate,
            tenorYears:
              coerceNumeric(item.tenor_years) ?? coerceNumeric(item.tenorYears),
            amortisation: coerceString(item.amortisation) ?? null,
            drawdownScheduleNotes:
              coerceString(item.drawdown_schedule_notes) ??
              coerceString(item.drawdownScheduleNotes) ??
              null,
            covenantsTriggers:
              coerceString(item.covenants_triggers) ??
              coerceString(item.covenantsTriggers) ??
              null,
          }
        })
        .filter((entry): entry is DeveloperDebtFacility => entry !== null)
    : []

  const rawWaterfall = source.equity_waterfall
  let equityWaterfall: DeveloperEquityWaterfall | null = null
  if (rawWaterfall && typeof rawWaterfall === 'object') {
    const item = rawWaterfall as Record<string, unknown>
    const tiers = Array.isArray(item.tiers)
      ? item.tiers
          .map((tier) => {
            if (!tier || typeof tier !== 'object') {
              return null
            }
            const tierItem = tier as Record<string, unknown>
            const hurdle =
              coerceNumeric(tierItem.hurdle_irr_pct) ??
              coerceNumeric(tierItem.hurdleIrrPct)
            const promote =
              coerceNumeric(tierItem.promote_pct) ??
              coerceNumeric(tierItem.promotePct)
            if (hurdle === null || promote === null) {
              return null
            }
            return { hurdleIrrPct: hurdle, promotePct: promote }
          })
          .filter((tier): tier is DeveloperEquityWaterfallTier => tier !== null)
      : []
    equityWaterfall = {
      tiers,
      preferredReturnPct:
        coerceNumeric(item.preferred_return_pct) ??
        coerceNumeric(item.preferredReturnPct),
      catchUpNotes:
        coerceString(item.catch_up_notes) ??
        coerceString(item.catchUpNotes) ??
        null,
    }
  }

  const cashFlowTimeline = Array.isArray(source.cash_flow_timeline)
    ? source.cash_flow_timeline
        .map((entry) => {
          if (!entry || typeof entry !== 'object') {
            return null
          }
          const item = entry as Record<string, unknown>
          const itemLabel = coerceString(item.item) ?? coerceString(item.name)
          const start =
            coerceNumeric(item.start_month) ?? coerceNumeric(item.startMonth)
          const duration =
            coerceNumeric(item.duration_months) ??
            coerceNumeric(item.durationMonths)
          if (!itemLabel || start === null || duration === null) {
            return null
          }
          return {
            item: itemLabel,
            startMonth: Math.round(start),
            durationMonths: Math.round(duration),
            notes: coerceString(item.notes) ?? null,
          }
        })
        .filter((entry): entry is DeveloperCashFlowMilestone => entry !== null)
    : []

  const exitSource = source.exit_assumptions
  let exitAssumptions: DeveloperExitAssumptions | null = null
  if (exitSource && typeof exitSource === 'object') {
    const item = exitSource as Record<string, unknown>
    const exitCapRates: Record<string, number> = {}
    const rawRates = item.exit_cap_rates ?? item.exitCapRates
    if (rawRates && typeof rawRates === 'object') {
      Object.entries(rawRates as Record<string, unknown>).forEach(
        ([key, value]) => {
          const numeric = coerceNumeric(value)
          if (numeric !== null) {
            exitCapRates[key] = numeric
          }
        },
      )
    }
    const saleCostsPct =
      coerceNumeric(item.sale_costs_pct) ?? coerceNumeric(item.saleCostsPct)
    if (saleCostsPct !== null) {
      exitAssumptions = {
        exitCapRates,
        saleCostsPct,
        saleCostsBreakdown:
          coerceString(item.sale_costs_breakdown) ??
          coerceString(item.saleCostsBreakdown) ??
          null,
        refinanceTerms:
          coerceString(item.refinance_terms) ??
          coerceString(item.refinanceTerms) ??
          null,
      }
    }
  }

  const sensitivityBands = Array.isArray(source.sensitivity_bands)
    ? source.sensitivity_bands
        .map((entry) => {
          if (!entry || typeof entry !== 'object') {
            return null
          }
          const item = entry as Record<string, unknown>
          const parameter =
            coerceString(item.parameter) ?? coerceString(item.name)
          const low = coerceNumeric(item.low) ?? coerceNumeric(item.min)
          const base = coerceNumeric(item.base) ?? coerceNumeric(item.mid)
          const high = coerceNumeric(item.high) ?? coerceNumeric(item.max)
          if (!parameter || low === null || base === null || high === null) {
            return null
          }
          return {
            parameter,
            low,
            base,
            high,
            comments: coerceString(item.comments) ?? null,
          }
        })
        .filter((entry): entry is DeveloperSensitivityBand => entry !== null)
    : []

  return {
    capitalStructure,
    debtFacilities,
    equityWaterfall,
    cashFlowTimeline,
    exitAssumptions,
    sensitivityBands,
  }
}

function deriveEnvelopeFromSummary(
  summary: GpsCaptureSummary,
): DeveloperBuildEnvelope {
  const zoneCode = summary.uraZoning.zoneCode ?? null
  const zoneDescription = summary.uraZoning.zoneDescription ?? null
  const plotRatio = coerceNumeric(summary.uraZoning.plotRatio)
  const siteArea = coerceNumeric(summary.propertyInfo?.siteAreaSqm)
  const currentGfa =
    coerceNumeric(summary.propertyInfo?.gfaApproved ?? null) ??
    coerceNumeric(
      (summary.propertyInfo as Record<string, unknown> | null)
        ?.grossFloorAreaSqm ?? null,
    )

  const maxBuildable =
    siteArea !== null && plotRatio !== null ? siteArea * plotRatio : null
  const additional =
    maxBuildable !== null && currentGfa !== null
      ? Math.max(maxBuildable - currentGfa, 0)
      : null

  const assumptions: string[] = []
  if (plotRatio !== null && siteArea !== null) {
    assumptions.push(
      `Assumes plot ratio ${plotRatio} applied across ${siteArea.toLocaleString()} sqm site area.`,
    )
  }
  if (zoneDescription) {
    assumptions.push(
      `Envelope derived from ${zoneDescription.toLowerCase()} zoning guidance.`,
    )
  }
  if (!assumptions.length) {
    assumptions.push(
      'Plot ratio or site area unavailable; envelope estimated from captured metadata.',
    )
  }

  return {
    zoneCode,
    zoneDescription,
    siteAreaSqm: roundOptional(siteArea),
    allowablePlotRatio: roundOptional(plotRatio),
    maxBuildableGfaSqm: roundOptional(maxBuildable),
    currentGfaSqm: roundOptional(currentGfa),
    additionalPotentialGfaSqm: roundOptional(additional),
    buildingHeightLimitM: null,
    siteCoveragePct: null,
    assumptions,
    sourceReference: null,
  }
}

function deriveVisualizationFromSummary(
  summary: GpsCaptureSummary,
): DeveloperVisualizationSummary {
  const scenarioCount = summary.quickAnalysis.scenarios.length
  const notes: string[] = []
  if (scenarioCount > 0) {
    notes.push(
      `${scenarioCount} scenario${scenarioCount === 1 ? '' : 's'} prepared for feasibility review.`,
    )
  }
  notes.push(
    'High-fidelity 3D previews will ship with Phase 2B visualisation work.',
  )
  return {
    status: 'placeholder',
    previewAvailable: false,
    notes,
    conceptMeshUrl: null,
    cameraOrbitHint: null,
    previewSeed: scenarioCount || null,
    previewMetadataUrl: null,
    thumbnailUrl: null,
    previewJobId: null,
    massingLayers: [],
    colorLegend: [],
  }
}

function createFallbackOptimization(
  base: Pick<
    DeveloperAssetOptimization,
    | 'assetType'
    | 'allocationPct'
    | 'niaEfficiency'
    | 'allocatedGfaSqm'
    | 'targetFloorHeightM'
    | 'parkingRatioPer1000Sqm'
    | 'estimatedRevenueSgd'
    | 'estimatedCapexSgd'
    | 'absorptionMonths'
    | 'riskLevel'
    | 'notes'
  >,
): DeveloperAssetOptimization {
  return {
    rentPsmMonth: null,
    stabilisedVacancyPct: null,
    opexPctOfRent: null,
    fitoutCostPsm: null,
    heritagePremiumPct: null,
    ...base,
  }
}

function deriveOptimizationsFallback(
  landUse: string | null | undefined,
): DeveloperAssetOptimization[] {
  const key = (landUse ?? '').toLowerCase()
  if (key.includes('residential')) {
    return [
      createFallbackOptimization({
        assetType: 'residential',
        allocationPct: 70,
        niaEfficiency: 0.78,
        allocatedGfaSqm: null,
        targetFloorHeightM: 3.3,
        parkingRatioPer1000Sqm: 0.8,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        absorptionMonths: 14,
        riskLevel: 'moderate',
        notes: [],
      }),
      createFallbackOptimization({
        assetType: 'serviced_apartments',
        allocationPct: 20,
        niaEfficiency: 0.72,
        allocatedGfaSqm: null,
        targetFloorHeightM: 3.1,
        parkingRatioPer1000Sqm: 0.5,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        absorptionMonths: 12,
        riskLevel: 'balanced',
        notes: [],
      }),
      createFallbackOptimization({
        assetType: 'amenities',
        allocationPct: 10,
        niaEfficiency: 0.5,
        allocatedGfaSqm: null,
        targetFloorHeightM: 4,
        parkingRatioPer1000Sqm: 0.4,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        absorptionMonths: 6,
        riskLevel: 'low',
        notes: [],
      }),
    ]
  }
  if (key.includes('industrial') || key.includes('logistics')) {
    return [
      createFallbackOptimization({
        assetType: 'high-spec logistics',
        allocationPct: 50,
        niaEfficiency: 0.75,
        allocatedGfaSqm: null,
        targetFloorHeightM: 10,
        parkingRatioPer1000Sqm: 1.1,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        absorptionMonths: 16,
        riskLevel: 'balanced',
        notes: [],
      }),
      createFallbackOptimization({
        assetType: 'production',
        allocationPct: 30,
        niaEfficiency: 0.7,
        allocatedGfaSqm: null,
        targetFloorHeightM: 8,
        parkingRatioPer1000Sqm: 0.9,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        absorptionMonths: 18,
        riskLevel: 'elevated',
        notes: [],
      }),
      createFallbackOptimization({
        assetType: 'support services',
        allocationPct: 20,
        niaEfficiency: 0.6,
        allocatedGfaSqm: null,
        targetFloorHeightM: 4.5,
        parkingRatioPer1000Sqm: 0.6,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        absorptionMonths: 9,
        riskLevel: 'moderate',
        notes: [],
      }),
    ]
  }
  return [
    createFallbackOptimization({
      assetType: 'office',
      allocationPct: 60,
      niaEfficiency: 0.82,
      allocatedGfaSqm: null,
      targetFloorHeightM: 4.2,
      parkingRatioPer1000Sqm: 1.2,
      estimatedRevenueSgd: null,
      estimatedCapexSgd: null,
      absorptionMonths: 12,
      riskLevel: 'moderate',
      notes: [],
    }),
    createFallbackOptimization({
      assetType: 'retail',
      allocationPct: 25,
      niaEfficiency: 0.68,
      allocatedGfaSqm: null,
      targetFloorHeightM: 5,
      parkingRatioPer1000Sqm: 3.5,
      estimatedRevenueSgd: null,
      estimatedCapexSgd: null,
      absorptionMonths: 10,
      riskLevel: 'balanced',
      notes: [],
    }),
    createFallbackOptimization({
      assetType: 'amenities',
      allocationPct: 15,
      niaEfficiency: 0.55,
      allocatedGfaSqm: null,
      targetFloorHeightM: 4.5,
      parkingRatioPer1000Sqm: 0.8,
      estimatedRevenueSgd: null,
      estimatedCapexSgd: null,
      absorptionMonths: 6,
      riskLevel: 'low',
      notes: [],
    }),
  ]
}

/**
 * Capture a property for site acquisition with enhanced developer features
 */
export async function capturePropertyForDevelopment(
  request: SiteAcquisitionRequest,
  signal?: AbortSignal,
): Promise<SiteAcquisitionResult> {
  let rawPayload: RawDeveloperGpsResponse | null = null

  const summary = await logPropertyByGps(
    {
      latitude: request.latitude,
      longitude: request.longitude,
      developmentScenarios: request.developmentScenarios,
    },
    async (_baseUrl, payload, options = {}) => {
      const requestBody: Record<string, unknown> = {
        latitude: payload.latitude,
        longitude: payload.longitude,
        development_scenarios: payload.developmentScenarios,
      }
      if (request.previewDetailLevel) {
        requestBody.preview_geometry_detail_level = request.previewDetailLevel
      }
      if (request.jurisdictionCode) {
        requestBody.jurisdiction_code = request.jurisdictionCode
      }

      const response = await fetch(buildUrl(DEVELOPER_GPS_ENDPOINT), {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(requestBody),
        signal: options.signal,
      })

      if (!response.ok) {
        const detail = await response.text()
        throw new Error(
          detail ||
            `Request to ${DEVELOPER_GPS_ENDPOINT} failed with ${response.status}`,
        )
      }

      rawPayload = (await response.json()) as RawDeveloperGpsResponse
      return rawPayload
    },
    signal,
  )

  const developerPayload = rawPayload as RawDeveloperGpsResponse | null

  const buildEnvelope = developerPayload
    ? mapDeveloperEnvelope(developerPayload.build_envelope)
    : deriveEnvelopeFromSummary(summary)

  const visualization = developerPayload
    ? mapDeveloperVisualization(developerPayload.visualization)
    : deriveVisualizationFromSummary(summary)

  const optimizations = developerPayload
    ? mapDeveloperOptimizations(developerPayload.optimizations)
    : deriveOptimizationsFallback(summary.existingUse ?? null)

  const financialSummary = developerPayload?.financial_summary
    ? {
        totalEstimatedRevenueSgd:
          coerceNumeric(
            developerPayload.financial_summary.total_estimated_revenue_sgd,
          ) ?? null,
        totalEstimatedCapexSgd:
          coerceNumeric(
            developerPayload.financial_summary.total_estimated_capex_sgd,
          ) ?? null,
        dominantRiskProfile:
          coerceString(
            developerPayload.financial_summary.dominant_risk_profile,
          ) ?? null,
        notes: Array.isArray(developerPayload.financial_summary.notes)
          ? (developerPayload.financial_summary.notes as unknown[])
              .map((entry) => coerceString(entry) ?? '')
              .filter((entry): entry is string => entry.length > 0)
          : [],
        financeBlueprint: mapFinanceBlueprint(
          developerPayload.financial_summary.finance_blueprint ??
            (developerPayload.financial_summary as Record<string, unknown>)
              .financeBlueprint,
        ),
      }
    : {
        totalEstimatedRevenueSgd: null,
        totalEstimatedCapexSgd: null,
        dominantRiskProfile: null,
        notes: [],
        financeBlueprint: null,
      }

  const heritageContext = developerPayload
    ? mapHeritageContext(
        developerPayload.heritage_context ??
          (developerPayload as unknown as Record<string, unknown>)
            .heritageContext,
      )
    : null

  const previewJobs = developerPayload?.preview_jobs
    ? mapPreviewJobs(developerPayload.preview_jobs)
    : []

  return {
    ...summary,
    buildEnvelope,
    visualization,
    optimizations,
    financialSummary,
    heritageContext,
    previewJobs,
  }
}

/**
 * Fetch due diligence checklist for a property
 */
export async function fetchPropertyChecklist(
  propertyId: string,
  developmentScenario?: DevelopmentScenario,
  status?: ChecklistStatus,
): Promise<ChecklistItem[]> {
  return fetchPropertyChecklistFromAgents(
    propertyId,
    developmentScenario,
    status,
  )
}

/**
 * Fetch checklist summary statistics
 */
export async function fetchChecklistSummary(
  propertyId: string,
): Promise<ChecklistSummary | null> {
  return fetchChecklistSummaryFromAgents(propertyId)
}

/**
 * Update a checklist item status or notes
 */
export async function updateChecklistItem(
  checklistId: string,
  updates: UpdateChecklistRequest,
): Promise<ChecklistItem | null> {
  return updateChecklistItemFromAgents(checklistId, updates)
}

export async function fetchPreviewJob(
  jobId: string,
  signal?: AbortSignal,
): Promise<DeveloperPreviewJob | null> {
  const response = await fetch(
    buildUrl(`api/v1/developers/preview-jobs/${jobId}`),
    {
      method: 'GET',
      signal,
    },
  )
  if (!response.ok) {
    return null
  }
  const payload = await response.json()
  const [job] = mapPreviewJobs([payload])
  return job ?? null
}

export async function refreshPreviewJob(
  jobId: string,
  detailLevel?: GeometryDetailLevel,
  colorLegend?: DeveloperColorLegendEntry[],
): Promise<DeveloperPreviewJob | null> {
  const requestPayload: Record<string, unknown> = {}
  if (detailLevel) {
    requestPayload.geometry_detail_level = detailLevel
  }
  if (colorLegend && colorLegend.length > 0) {
    requestPayload.color_legend = colorLegend.map((entry) => ({
      asset_type: entry.assetType,
      label: entry.label,
      color: entry.color,
      description: entry.description,
    }))
  }
  const requestInit: RequestInit = { method: 'POST' }
  if (Object.keys(requestPayload).length > 0) {
    requestInit.headers = { 'Content-Type': 'application/json' }
    requestInit.body = JSON.stringify(requestPayload)
  }
  const response = await fetch(
    buildUrl(`api/v1/developers/preview-jobs/${jobId}/refresh`),
    requestInit,
  )
  if (!response.ok) {
    return null
  }
  const payload = await response.json()
  const [job] = mapPreviewJobs([payload])
  return job ?? null
}

export async function listPreviewJobs(
  propertyId: string,
): Promise<DeveloperPreviewJob[]> {
  const response = await fetch(
    buildUrl(`api/v1/developers/properties/${propertyId}/preview-jobs`),
    { method: 'GET' },
  )
  if (!response.ok) {
    return []
  }
  const payload = await response.json()
  return mapPreviewJobs(payload)
}

export async function createFinanceProjectFromCapture(
  propertyId: string,
  payload: FinanceProjectCreatePayload = {},
  signal?: AbortSignal,
): Promise<FinanceProjectCreateResult> {
  const response = await fetch(
    buildUrl(`api/v1/developers/properties/${propertyId}/create-project`),
    {
      method: 'POST',
      headers: applyIdentityHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        projectName: payload.projectName ?? undefined,
        scenarioName: payload.scenarioName ?? undefined,
        totalEstimatedCapexSgd: payload.totalEstimatedCapexSgd ?? undefined,
        totalEstimatedRevenueSgd: payload.totalEstimatedRevenueSgd ?? undefined,
      }),
      signal,
    },
  )

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(
      detail ||
        `Request to create finance project failed with status ${response.status}`,
    )
  }

  const parsed = (await response.json()) as {
    project_id?: string
    fin_project_id?: number
    scenario_id?: number
    project_name?: string
  }
  const projectId = String(parsed.project_id ?? '').trim()
  if (!projectId) {
    throw new Error('Finance project creation response missing project_id')
  }
  return {
    projectId,
    projectName: String(parsed.project_name ?? '').trim() || projectId,
    finProjectId: Number(parsed.fin_project_id ?? 0),
    scenarioId: Number(parsed.scenario_id ?? 0),
  }
}

export async function saveProjectFromCapture(
  propertyId: string,
  payload: { projectName?: string } = {},
  signal?: AbortSignal,
): Promise<CaptureProjectLinkResult> {
  const response = await fetch(
    buildUrl(`api/v1/developers/properties/${propertyId}/save-project`),
    {
      method: 'POST',
      headers: applyIdentityHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        projectName: payload.projectName ?? undefined,
      }),
      signal,
    },
  )
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed with status ${response.status}`)
  }
  const parsed = (await response.json()) as {
    project_id?: string
    project_name?: string
  }
  const projectId = String(parsed.project_id ?? '').trim()
  if (!projectId) {
    throw new Error('Project creation response missing project_id')
  }
  return {
    projectId,
    projectName: String(parsed.project_name ?? '').trim() || projectId,
  }
}

export async function linkCaptureToProject(
  propertyId: string,
  projectId: string,
  signal?: AbortSignal,
): Promise<CaptureProjectLinkResult> {
  const response = await fetch(
    buildUrl(`api/v1/developers/properties/${propertyId}/link-project`),
    {
      method: 'POST',
      headers: applyIdentityHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ projectId }),
      signal,
    },
  )
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed with status ${response.status}`)
  }
  const parsed = (await response.json()) as {
    project_id?: string
    project_name?: string
  }
  const resolvedId = String(parsed.project_id ?? '').trim()
  if (!resolvedId) {
    throw new Error('Project link response missing project_id')
  }
  return {
    projectId: resolvedId,
    projectName: String(parsed.project_name ?? '').trim() || resolvedId,
  }
}

/**
 * Fetch developer condition assessment for the property.
 */
export async function fetchConditionAssessment(
  propertyId: string,
  scenario?: DevelopmentScenario | 'all',
): Promise<ConditionAssessment | null> {
  const params = new URLSearchParams()
  if (scenario && scenario !== 'all') {
    params.append('scenario', scenario)
  }

  const url = buildUrl(
    `api/v1/developers/properties/${propertyId}/condition-assessment${
      params.toString() ? `?${params.toString()}` : ''
    }`,
  )
  const response = await fetch(url)
  if (!response.ok) {
    console.error('Failed to fetch condition assessment:', response.statusText)
    return null
  }

  const payload = await response.json()
  return mapConditionAssessmentPayload(payload, propertyId)
}

export async function saveConditionAssessment(
  propertyId: string,
  payload: ConditionAssessmentUpsertRequest,
): Promise<ConditionAssessment | null> {
  const response = await fetch(
    buildUrl(`api/v1/developers/properties/${propertyId}/condition-assessment`),
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )

  if (!response.ok) {
    console.error('Failed to save condition assessment:', response.statusText)
    return null
  }

  const data = await response.json()
  return mapConditionAssessmentPayload(data, propertyId)
}

export async function fetchConditionAssessmentHistory(
  propertyId: string,
  scenario?: DevelopmentScenario | 'all',
  limit = 20,
): Promise<ConditionAssessment[]> {
  const params = new URLSearchParams()
  if (scenario && scenario !== 'all') {
    params.append('scenario', scenario)
  }
  if (limit) {
    params.append('limit', String(limit))
  }

  const url = buildUrl(
    `api/v1/developers/properties/${propertyId}/condition-assessment/history${
      params.toString() ? `?${params.toString()}` : ''
    }`,
  )
  const response = await fetch(url)
  if (!response.ok) {
    console.error(
      'Failed to fetch condition assessment history:',
      response.statusText,
    )
    return []
  }

  const data = await response.json()
  if (!Array.isArray(data)) {
    return []
  }

  return data.map((entry: Record<string, unknown>) =>
    mapConditionAssessmentPayload(entry, propertyId),
  )
}

export async function fetchScenarioAssessments(
  propertyId: string,
): Promise<ConditionAssessment[]> {
  const url = buildUrl(
    `api/v1/developers/properties/${propertyId}/condition-assessment/scenarios`,
  )

  const response = await fetch(url)
  if (!response.ok) {
    console.error('Failed to fetch scenario assessments:', response.statusText)
    return []
  }

  const data = await response.json()
  if (!Array.isArray(data)) {
    return []
  }

  return data.map((entry: Record<string, unknown>) =>
    mapConditionAssessmentPayload(entry, propertyId),
  )
}

export interface ConditionReportChecklistSummary {
  total: number
  completed: number
  inProgress: number
  pending: number
  notApplicable: number
  completionPercentage: number
}

export interface ConditionReportScenarioComparisonEntry {
  scenario?: string | null
  label: string
  recordedAt?: string | null
  overallScore?: number | null
  overallRating?: string | null
  riskLevel?: string | null
  checklistCompleted?: number | null
  checklistTotal?: number | null
  checklistPercent?: number | null
  primaryInsight?: ConditionInsight | null
  insightCount: number
  recommendedAction?: string | null
  inspectorName?: string | null
  source: 'manual' | 'heuristic'
}

export interface ConditionReport {
  propertyId: string
  propertyName?: string | null
  address?: string | null
  generatedAt: string
  scenarioAssessments: ConditionAssessment[]
  history: ConditionAssessment[]
  checklistSummary?: ConditionReportChecklistSummary | null
  scenarioComparison: ConditionReportScenarioComparisonEntry[]
}

export async function exportConditionReport(
  propertyId: string,
  format: 'json' | 'pdf' = 'json',
): Promise<{ blob: Blob; filename: string }> {
  const url = buildUrl(
    `api/v1/developers/properties/${propertyId}/condition-assessment/report?format=${format}`,
  )
  const response = await fetch(url)
  if (!response.ok) {
    let detail = response.statusText
    try {
      const errorPayload = await response.json()
      if (typeof errorPayload.detail === 'string') {
        detail = errorPayload.detail
      }
    } catch (_err) {
      // ignore JSON parsing errors and fall back to status text
    }
    throw new Error(detail || 'Failed to export condition report.')
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  const extension = format === 'pdf' ? 'pdf' : 'json'
  const filename = `condition-report-${propertyId}-${timestamp}.${extension}`

  if (format === 'pdf') {
    const blob = await response.blob()
    return { blob, filename }
  }

  const raw = await response.json()
  const normalized: ConditionReport = {
    propertyId: String(raw.propertyId ?? raw.property_id ?? propertyId),
    propertyName: raw.propertyName ?? raw.property_name ?? null,
    address: raw.address ?? null,
    generatedAt: String(
      raw.generatedAt ?? raw.generated_at ?? new Date().toISOString(),
    ),
    scenarioAssessments: Array.isArray(raw.scenarioAssessments)
      ? raw.scenarioAssessments.map((entry: Record<string, unknown>) =>
          mapConditionAssessmentPayload(entry, propertyId),
        )
      : [],
    history: Array.isArray(raw.history)
      ? raw.history.map((entry: Record<string, unknown>) =>
          mapConditionAssessmentPayload(entry, propertyId),
        )
      : [],
    checklistSummary: raw.checklistSummary ?? raw.checklist_summary ?? null,
    scenarioComparison: Array.isArray(raw.scenarioComparison)
      ? raw.scenarioComparison.map((entry: Record<string, unknown>) => ({
          scenario: typeof entry.scenario === 'string' ? entry.scenario : null,
          label: String(entry.label ?? entry.scenario ?? 'Scenario'),
          recordedAt:
            typeof entry.recordedAt === 'string'
              ? entry.recordedAt
              : typeof entry.recorded_at === 'string'
                ? entry.recorded_at
                : null,
          overallScore:
            typeof entry.overallScore === 'number'
              ? entry.overallScore
              : typeof entry.overall_score === 'number'
                ? entry.overall_score
                : null,
          overallRating:
            typeof entry.overallRating === 'string'
              ? entry.overallRating
              : typeof entry.overall_rating === 'string'
                ? entry.overall_rating
                : null,
          riskLevel:
            typeof entry.riskLevel === 'string'
              ? entry.riskLevel
              : typeof entry.risk_level === 'string'
                ? entry.risk_level
                : null,
          checklistCompleted:
            typeof entry.checklistCompleted === 'number'
              ? entry.checklistCompleted
              : typeof entry.checklist_completed === 'number'
                ? entry.checklist_completed
                : null,
          checklistTotal:
            typeof entry.checklistTotal === 'number'
              ? entry.checklistTotal
              : typeof entry.checklist_total === 'number'
                ? entry.checklist_total
                : null,
          checklistPercent:
            typeof entry.checklistPercent === 'number'
              ? entry.checklistPercent
              : typeof entry.checklist_percent === 'number'
                ? entry.checklist_percent
                : null,
          primaryInsight: entry.primaryInsight
            ? (mapConditionAssessmentPayload(
                { insights: [entry.primaryInsight] },
                propertyId,
              ).insights[0] ?? null)
            : null,
          insightCount: Number(entry.insightCount ?? entry.insight_count ?? 0),
          recommendedAction:
            typeof entry.recommendedAction === 'string'
              ? entry.recommendedAction
              : typeof entry.recommended_action === 'string'
                ? entry.recommended_action
                : null,
          inspectorName:
            typeof entry.inspectorName === 'string'
              ? entry.inspectorName
              : typeof entry.inspector_name === 'string'
                ? entry.inspector_name
                : null,
          source:
            entry.source === 'manual' || entry.source === 'heuristic'
              ? (entry.source as 'manual' | 'heuristic')
              : 'heuristic',
        }))
      : [],
  }

  const blob = new Blob([JSON.stringify(normalized, null, 2)], {
    type: 'application/json',
  })
  return { blob, filename }
}

// ============================================================================
// Voice Notes API
// ============================================================================

export interface PropertyVoiceNote {
  voiceNoteId: string
  propertyId: string
  photoId: string | null
  storageKey: string
  filename: string
  mimeType: string
  fileSize: number
  durationSeconds: number | null
  captureDate: string | null
  title: string | null
  tags: string[]
  transcript: string | null
  audioMetadata: Record<string, unknown> | null
  publicUrl: string
  location?: {
    latitude: number | null
    longitude: number | null
  } | null
}

function mapVoiceNote(payload: Record<string, unknown>): PropertyVoiceNote {
  return {
    voiceNoteId: String(payload.voice_note_id ?? payload.voiceNoteId ?? ''),
    propertyId: String(payload.property_id ?? payload.propertyId ?? ''),
    photoId:
      typeof payload.photo_id === 'string'
        ? payload.photo_id
        : typeof payload.photoId === 'string'
          ? payload.photoId
          : null,
    storageKey: String(payload.storage_key ?? payload.storageKey ?? ''),
    filename: String(payload.filename ?? ''),
    mimeType: String(payload.mime_type ?? payload.mimeType ?? 'audio/webm'),
    fileSize: Number(payload.file_size ?? payload.fileSize ?? 0),
    durationSeconds:
      typeof payload.duration_seconds === 'number'
        ? payload.duration_seconds
        : typeof payload.durationSeconds === 'number'
          ? payload.durationSeconds
          : null,
    captureDate:
      typeof payload.capture_date === 'string'
        ? payload.capture_date
        : typeof payload.captureDate === 'string'
          ? payload.captureDate
          : null,
    title: typeof payload.title === 'string' ? payload.title : null,
    tags: Array.isArray(payload.tags) ? payload.tags : [],
    transcript:
      typeof payload.transcript === 'string' ? payload.transcript : null,
    audioMetadata:
      payload.audio_metadata && typeof payload.audio_metadata === 'object'
        ? (payload.audio_metadata as Record<string, unknown>)
        : payload.audioMetadata && typeof payload.audioMetadata === 'object'
          ? (payload.audioMetadata as Record<string, unknown>)
          : null,
    publicUrl: String(payload.public_url ?? payload.publicUrl ?? ''),
    location: payload.location
      ? {
          latitude:
            typeof (payload.location as Record<string, unknown>).latitude ===
            'number'
              ? ((payload.location as Record<string, unknown>)
                  .latitude as number)
              : null,
          longitude:
            typeof (payload.location as Record<string, unknown>).longitude ===
            'number'
              ? ((payload.location as Record<string, unknown>)
                  .longitude as number)
              : null,
        }
      : null,
  }
}

/**
 * Fetch all voice notes for a property
 */
export async function fetchPropertyVoiceNotes(
  propertyId: string,
): Promise<PropertyVoiceNote[]> {
  const url = buildUrl(
    `api/v1/agents/commercial-property/properties/${propertyId}/voice-notes`,
  )
  const response = await fetch(url)
  if (!response.ok) {
    console.error('Failed to fetch voice notes:', response.statusText)
    return []
  }

  const data = await response.json()
  if (!Array.isArray(data)) {
    return []
  }

  return data.map((entry: Record<string, unknown>) => mapVoiceNote(entry))
}

/**
 * Delete a voice note
 */
export async function deleteVoiceNote(
  propertyId: string,
  voiceNoteId: string,
): Promise<boolean> {
  const url = buildUrl(
    `api/v1/agents/commercial-property/properties/${propertyId}/voice-notes/${voiceNoteId}`,
  )
  const response = await fetch(url, { method: 'DELETE' })
  return response.ok
}

// ============================================================================
// Property Photos API
// ============================================================================

/**
 * Photo version type - backend generates multiple versions for different uses
 */
export type PhotoVersion =
  | 'original' // Full quality, no watermark (internal use)
  | 'thumbnail' // 300x300, no watermark (UI previews)
  | 'medium' // 1200x1200, no watermark (reports)
  | 'web' // 1920x1920, no watermark (web display)
  | 'web_watermarked' // 1920x1920, corner watermark
  | 'marketing' // 1200x1200, diagonal repeating watermark

/**
 * Phase type determines watermark text for marketing materials
 */
export type PropertyPhase = 'acquisition' | 'sales'

export interface PropertyPhoto {
  photoId: string
  propertyId: string
  storageKey: string
  filename: string
  mimeType: string
  fileSize: number
  captureTimestamp: string | null
  autoTags: string[]
  location: {
    latitude: number | null
    longitude: number | null
  } | null
  notes: string | null
  tags: string[]
  versions: Partial<Record<PhotoVersion, string>>
}

function mapPropertyPhoto(payload: Record<string, unknown>): PropertyPhoto {
  const versions: Partial<Record<PhotoVersion, string>> = {}
  // Backend returns 'urls', frontend uses 'versions'
  const versionsRaw = payload.urls ?? payload.versions ?? payload.image_versions
  if (versionsRaw && typeof versionsRaw === 'object') {
    const v = versionsRaw as Record<string, unknown>
    if (typeof v.original === 'string') versions.original = v.original
    if (typeof v.thumbnail === 'string') versions.thumbnail = v.thumbnail
    if (typeof v.medium === 'string') versions.medium = v.medium
    if (typeof v.web === 'string') versions.web = v.web
    if (typeof v.web_watermarked === 'string')
      versions.web_watermarked = v.web_watermarked
    if (typeof v.marketing === 'string') versions.marketing = v.marketing
  }
  // Fall back to public_url if versions not provided
  if (Object.keys(versions).length === 0) {
    const publicUrl = payload.public_url ?? payload.publicUrl
    if (typeof publicUrl === 'string') {
      versions.original = publicUrl
    }
  }

  return {
    photoId: String(payload.photo_id ?? payload.photoId ?? ''),
    propertyId: String(payload.property_id ?? payload.propertyId ?? ''),
    storageKey: String(payload.storage_key ?? payload.storageKey ?? ''),
    filename: String(payload.filename ?? ''),
    mimeType: String(payload.mime_type ?? payload.mimeType ?? 'image/jpeg'),
    fileSize: Number(payload.file_size ?? payload.fileSize ?? 0),
    captureTimestamp:
      typeof payload.capture_timestamp === 'string'
        ? payload.capture_timestamp
        : typeof payload.captureTimestamp === 'string'
          ? payload.captureTimestamp
          : null,
    autoTags: Array.isArray(payload.auto_tags)
      ? payload.auto_tags
      : Array.isArray(payload.autoTags)
        ? payload.autoTags
        : Array.isArray(payload.auto_tagged_conditions)
          ? payload.auto_tagged_conditions
          : [],
    location: payload.location
      ? {
          latitude:
            typeof (payload.location as Record<string, unknown>).latitude ===
            'number'
              ? ((payload.location as Record<string, unknown>)
                  .latitude as number)
              : null,
          longitude:
            typeof (payload.location as Record<string, unknown>).longitude ===
            'number'
              ? ((payload.location as Record<string, unknown>)
                  .longitude as number)
              : null,
        }
      : null,
    notes: typeof payload.notes === 'string' ? payload.notes : null,
    tags: Array.isArray(payload.tags) ? payload.tags : [],
    versions,
  }
}

/**
 * Fetch all photos for a property
 */
export async function fetchPropertyPhotos(
  propertyId: string,
): Promise<PropertyPhoto[]> {
  const url = buildUrl(
    `api/v1/agents/commercial-property/properties/${propertyId}/photos`,
  )
  const response = await fetch(url)
  if (!response.ok) {
    console.error('Failed to fetch photos:', response.statusText)
    return []
  }

  const data = await response.json()
  if (!Array.isArray(data)) {
    return []
  }

  return data.map((entry: Record<string, unknown>) => mapPropertyPhoto(entry))
}

/**
 * Upload a photo for a property
 */
export async function uploadPropertyPhoto(
  propertyId: string,
  file: File,
  options?: {
    notes?: string
    tags?: string[]
    phase?: PropertyPhase
  },
): Promise<PropertyPhoto | null> {
  const formData = new FormData()
  formData.append('file', file)
  if (options?.notes) {
    formData.append('notes', options.notes)
  }
  if (options?.tags && options.tags.length > 0) {
    formData.append('tags', options.tags.join(','))
  }
  if (options?.phase) {
    formData.append('phase', options.phase)
  }

  const url = buildUrl(
    `api/v1/agents/commercial-property/properties/${propertyId}/photos`,
  )
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    console.error('Failed to upload photo:', response.statusText)
    return null
  }

  const data = await response.json()
  return mapPropertyPhoto(data)
}

/**
 * Delete a photo
 */
export async function deletePropertyPhoto(
  propertyId: string,
  photoId: string,
): Promise<boolean> {
  const url = buildUrl(
    `api/v1/agents/commercial-property/properties/${propertyId}/photos/${photoId}`,
  )
  const response = await fetch(url, { method: 'DELETE' })
  return response.ok
}

/**
 * Get the URL for a specific photo version
 */
export function getPhotoVersionUrl(
  photo: PropertyPhoto,
  version: PhotoVersion,
): string | null {
  return photo.versions[version] ?? photo.versions.original ?? null
}

export {
  fetchChecklistTemplatesFromAgents as fetchChecklistTemplates,
  createChecklistTemplateFromAgents as createChecklistTemplate,
  updateChecklistTemplateFromAgents as updateChecklistTemplate,
  deleteChecklistTemplateFromAgents as deleteChecklistTemplate,
  importChecklistTemplatesFromAgents as importChecklistTemplates,
  DEFAULT_SCENARIO_ORDER,
}
