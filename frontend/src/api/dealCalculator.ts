import { applyIdentityHeaders } from './identity'
import { buildUrl, coerceNumber as coerceNumeric, coerceString } from './shared'
import {
  mapExternalSourceMetadata,
  type ExternalSourceMetadata,
} from './externalSources'

const API_PREFIX = '/api/v1/developers/deal-calculator/evaluate'

export interface DealCalculatorRequest {
  projectName?: string
  address?: string
  landUse?: string
  zoneCode?: string
  siteAreaSqm?: number
  allowablePlotRatio?: number
  currentGfaSqm?: number
  targetGrossFloorAreaSqm?: number
  buildingHeightMeters?: number
  existingUse?: string
  financing?: {
    equityPct?: number
    debtPct?: number
    annualInterestRatePct?: number
    discountRatePct?: number
    exitCapRatePct?: number
    saleCostPct?: number
    holdYears?: number
  }
}

export interface RuleCorpusStatus {
  zoneCode: string | null
  coverageState: string
  confidence: string
  counts: {
    applicable: number
    approved: number
    published: number
    traceable: number
    needsReview: number
    rejected: number
  }
  appliedRuleIds: number[]
}

export interface DealCalculatorSite {
  inputMode: 'address' | 'manual'
  formattedAddress: string
  coordinates: { latitude: number; longitude: number } | null
  jurisdictionCode: string
  landUse: string
  existingUse: string | null
  zoneCode: string | null
  zoneDescription: string | null
  geocodingSource: ExternalSourceMetadata | null
  amenitiesSource: ExternalSourceMetadata | null
  uraSource: ExternalSourceMetadata | null
}

export interface DealCalculatorBuildEnvelope {
  zoneCode: string | null
  zoneDescription: string | null
  siteAreaSqm: number | null
  allowablePlotRatio: number | null
  maxBuildableGfaSqm: number | null
  currentGfaSqm: number | null
  additionalPotentialGfaSqm: number | null
  assumptions: string[]
  sourceReference: string | null
  ruleCorpusStatus: RuleCorpusStatus | null
}

export interface DealCalculatorFinanceSummary {
  totalCapexSgd: number | null
  totalAnnualRevenueSgd: number | null
  totalAnnualNoiSgd: number | null
  blendedYieldPct: number | null
  equityRequiredSgd: number | null
  debtAmountSgd: number | null
  annualDebtServiceSgd: number | null
  capRatePct: number | null
  dscr: number | null
  npvSgd: number | null
  irr: number | null
  moic: number | null
  estimatedExitValueSgd: number | null
  notes: string[]
}

export interface DealCalculatorRule {
  id: string
  title: string
  status: string
  notes: string | null
}

export interface DealCalculatorAssetBreakdown {
  assetType: string
  allocationPct: string | null
  niaSqm: string | null
  rentPsmMonth: string | null
  noiAnnualSgd: string | null
  estimatedCapexSgd: string | null
  absorptionMonths: string | null
  riskLevel: string | null
  notes: string[]
}

export interface DealCalculatorResult {
  generatedAt: string
  site: DealCalculatorSite
  buildEnvelope: DealCalculatorBuildEnvelope
  ruleCorpusStatus: RuleCorpusStatus | null
  recommendedRuleIds: string[]
  feasibilitySummary: {
    maxPermissibleGfaSqm: number
    estimatedAchievableGfaSqm: number
    estimatedUnitCount: number
    siteCoveragePercent: number
    remarks: string | null
    accuracyRange: string | null
  }
  feasibilityRules: DealCalculatorRule[]
  recommendations: string[]
  financeSummary: DealCalculatorFinanceSummary
  assetBreakdowns: DealCalculatorAssetBreakdown[]
}

function mapRuleCorpusStatus(payload: unknown): RuleCorpusStatus | null {
  if (!payload || typeof payload !== 'object') {
    return null
  }
  const source = payload as Record<string, unknown>
  const counts = (source.counts ?? {}) as Record<string, unknown>
  return {
    zoneCode:
      coerceString(source.zoneCode) ?? coerceString(source.zone_code) ?? null,
    coverageState:
      coerceString(source.coverageState) ??
      coerceString(source.coverage_state) ??
      'unknown',
    confidence: coerceString(source.confidence) ?? 'unknown',
    counts: {
      applicable: coerceNumeric(counts.applicable) ?? 0,
      approved: coerceNumeric(counts.approved) ?? 0,
      published: coerceNumeric(counts.published) ?? 0,
      traceable: coerceNumeric(counts.traceable) ?? 0,
      needsReview:
        coerceNumeric(counts.needsReview) ??
        coerceNumeric(counts.needs_review) ??
        0,
      rejected: coerceNumeric(counts.rejected) ?? 0,
    },
    appliedRuleIds: Array.isArray(source.appliedRuleIds)
      ? source.appliedRuleIds
          .map((value) => coerceNumeric(value))
          .filter((value): value is number => value !== null)
      : Array.isArray(source.applied_rule_ids)
        ? source.applied_rule_ids
            .map((value) => coerceNumeric(value))
            .filter((value): value is number => value !== null)
        : [],
  }
}

function mapStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value
    .map((entry) => coerceString(entry) ?? '')
    .filter((entry): entry is string => entry.length > 0)
}

function mapFinanceSummary(payload: unknown): DealCalculatorFinanceSummary {
  const source =
    payload && typeof payload === 'object'
      ? (payload as Record<string, unknown>)
      : {}

  return {
    totalCapexSgd:
      coerceNumeric(source.totalCapexSgd) ??
      coerceNumeric(source.total_capex_sgd),
    totalAnnualRevenueSgd:
      coerceNumeric(source.totalAnnualRevenueSgd) ??
      coerceNumeric(source.total_annual_revenue_sgd),
    totalAnnualNoiSgd:
      coerceNumeric(source.totalAnnualNoiSgd) ??
      coerceNumeric(source.total_annual_noi_sgd),
    blendedYieldPct:
      coerceNumeric(source.blendedYieldPct) ??
      coerceNumeric(source.blended_yield_pct),
    equityRequiredSgd:
      coerceNumeric(source.equityRequiredSgd) ??
      coerceNumeric(source.equity_required_sgd),
    debtAmountSgd:
      coerceNumeric(source.debtAmountSgd) ??
      coerceNumeric(source.debt_amount_sgd),
    annualDebtServiceSgd:
      coerceNumeric(source.annualDebtServiceSgd) ??
      coerceNumeric(source.annual_debt_service_sgd),
    capRatePct:
      coerceNumeric(source.capRatePct) ?? coerceNumeric(source.cap_rate_pct),
    dscr: coerceNumeric(source.dscr),
    npvSgd: coerceNumeric(source.npvSgd) ?? coerceNumeric(source.npv_sgd),
    irr: coerceNumeric(source.irr),
    moic: coerceNumeric(source.moic),
    estimatedExitValueSgd:
      coerceNumeric(source.estimatedExitValueSgd) ??
      coerceNumeric(source.estimated_exit_value_sgd),
    notes: mapStringList(source.notes),
  }
}

function mapResult(payload: unknown): DealCalculatorResult {
  const source = payload as Record<string, unknown>
  const site = (source.site ?? {}) as Record<string, unknown>
  const buildEnvelope = (source.buildEnvelope ??
    source.build_envelope ??
    {}) as Record<string, unknown>
  const feasibilitySummary = (source.feasibilitySummary ??
    source.feasibility_summary ??
    {}) as Record<string, unknown>

  return {
    generatedAt:
      coerceString(source.generatedAt) ??
      coerceString(source.generated_at) ??
      new Date().toISOString(),
    site: {
      inputMode: (coerceString(site.inputMode) ??
        coerceString(site.input_mode) ??
        'manual') as 'address' | 'manual',
      formattedAddress:
        coerceString(site.formattedAddress) ??
        coerceString(site.formatted_address) ??
        '',
      coordinates:
        site.coordinates && typeof site.coordinates === 'object'
          ? {
              latitude:
                coerceNumeric(
                  (site.coordinates as Record<string, unknown>).latitude,
                ) ?? 0,
              longitude:
                coerceNumeric(
                  (site.coordinates as Record<string, unknown>).longitude,
                ) ?? 0,
            }
          : null,
      jurisdictionCode:
        coerceString(site.jurisdictionCode) ??
        coerceString(site.jurisdiction_code) ??
        'SG',
      landUse: coerceString(site.landUse) ?? coerceString(site.land_use) ?? '',
      existingUse:
        coerceString(site.existingUse) ??
        coerceString(site.existing_use) ??
        null,
      zoneCode:
        coerceString(site.zoneCode) ?? coerceString(site.zone_code) ?? null,
      zoneDescription:
        coerceString(site.zoneDescription) ??
        coerceString(site.zone_description) ??
        null,
      geocodingSource: mapExternalSourceMetadata(
        site.geocodingSource ?? site.geocoding_source,
      ),
      amenitiesSource: mapExternalSourceMetadata(
        site.amenitiesSource ?? site.amenities_source,
      ),
      uraSource: mapExternalSourceMetadata(site.uraSource ?? site.ura_source),
    },
    buildEnvelope: {
      zoneCode:
        coerceString(buildEnvelope.zoneCode) ??
        coerceString(buildEnvelope.zone_code) ??
        null,
      zoneDescription:
        coerceString(buildEnvelope.zoneDescription) ??
        coerceString(buildEnvelope.zone_description) ??
        null,
      siteAreaSqm:
        coerceNumeric(buildEnvelope.siteAreaSqm) ??
        coerceNumeric(buildEnvelope.site_area_sqm),
      allowablePlotRatio:
        coerceNumeric(buildEnvelope.allowablePlotRatio) ??
        coerceNumeric(buildEnvelope.allowable_plot_ratio),
      maxBuildableGfaSqm:
        coerceNumeric(buildEnvelope.maxBuildableGfaSqm) ??
        coerceNumeric(buildEnvelope.max_buildable_gfa_sqm),
      currentGfaSqm:
        coerceNumeric(buildEnvelope.currentGfaSqm) ??
        coerceNumeric(buildEnvelope.current_gfa_sqm),
      additionalPotentialGfaSqm:
        coerceNumeric(buildEnvelope.additionalPotentialGfaSqm) ??
        coerceNumeric(buildEnvelope.additional_potential_gfa_sqm),
      assumptions: mapStringList(buildEnvelope.assumptions),
      sourceReference:
        coerceString(buildEnvelope.sourceReference) ??
        coerceString(buildEnvelope.source_reference) ??
        null,
      ruleCorpusStatus: mapRuleCorpusStatus(
        buildEnvelope.ruleCorpusStatus ?? buildEnvelope.rule_corpus_status,
      ),
    },
    ruleCorpusStatus: mapRuleCorpusStatus(
      source.ruleCorpusStatus ?? source.rule_corpus_status,
    ),
    recommendedRuleIds: Array.isArray(source.recommendedRuleIds)
      ? source.recommendedRuleIds
          .map((entry) => coerceString(entry) ?? '')
          .filter((entry): entry is string => entry.length > 0)
      : Array.isArray(source.recommended_rule_ids)
        ? source.recommended_rule_ids
            .map((entry) => coerceString(entry) ?? '')
            .filter((entry): entry is string => entry.length > 0)
        : [],
    feasibilitySummary: {
      maxPermissibleGfaSqm:
        coerceNumeric(feasibilitySummary.maxPermissibleGfaSqm) ??
        coerceNumeric(feasibilitySummary.max_permissible_gfa_sqm) ??
        0,
      estimatedAchievableGfaSqm:
        coerceNumeric(feasibilitySummary.estimatedAchievableGfaSqm) ??
        coerceNumeric(feasibilitySummary.estimated_achievable_gfa_sqm) ??
        0,
      estimatedUnitCount:
        coerceNumeric(feasibilitySummary.estimatedUnitCount) ??
        coerceNumeric(feasibilitySummary.estimated_unit_count) ??
        0,
      siteCoveragePercent:
        coerceNumeric(feasibilitySummary.siteCoveragePercent) ??
        coerceNumeric(feasibilitySummary.site_coverage_percent) ??
        0,
      remarks:
        coerceString(feasibilitySummary.remarks) ??
        coerceString(feasibilitySummary.summaryRemarks) ??
        null,
      accuracyRange:
        coerceString(feasibilitySummary.accuracyRange) ??
        coerceString(feasibilitySummary.accuracy_range) ??
        null,
    },
    feasibilityRules: Array.isArray(source.feasibilityRules)
      ? source.feasibilityRules
          .map((entry) => {
            if (!entry || typeof entry !== 'object') {
              return null
            }
            const rule = entry as Record<string, unknown>
            return {
              id: coerceString(rule.id) ?? '',
              title: coerceString(rule.title) ?? '',
              status: coerceString(rule.status) ?? 'warning',
              notes: coerceString(rule.notes) ?? null,
            }
          })
          .filter((entry): entry is DealCalculatorRule => entry !== null)
      : Array.isArray(source.feasibility_rules)
        ? source.feasibility_rules
            .map((entry) => {
              if (!entry || typeof entry !== 'object') {
                return null
              }
              const rule = entry as Record<string, unknown>
              return {
                id: coerceString(rule.id) ?? '',
                title: coerceString(rule.title) ?? '',
                status: coerceString(rule.status) ?? 'warning',
                notes: coerceString(rule.notes) ?? null,
              }
            })
            .filter((entry): entry is DealCalculatorRule => entry !== null)
        : [],
    recommendations: mapStringList(
      source.recommendations ?? source.advisories ?? [],
    ),
    financeSummary: mapFinanceSummary(
      source.financeSummary ?? source.finance_summary,
    ),
    assetBreakdowns: mapAssetBreakdowns(
      source.assetBreakdowns ?? source.asset_breakdowns,
    ),
  }
}

function mapAssetBreakdowns(payload: unknown): DealCalculatorAssetBreakdown[] {
  if (!Array.isArray(payload)) {
    return []
  }
  return payload
    .map((entry) => {
      if (!entry || typeof entry !== 'object') {
        return null
      }
      const asset = entry as Record<string, unknown>
      return {
        assetType:
          coerceString(asset.assetType) ??
          coerceString(asset.asset_type) ??
          'Asset',
        allocationPct:
          coerceString(asset.allocationPct) ??
          coerceString(asset.allocation_pct) ??
          null,
        niaSqm:
          coerceString(asset.niaSqm) ?? coerceString(asset.nia_sqm) ?? null,
        rentPsmMonth:
          coerceString(asset.rentPsmMonth) ??
          coerceString(asset.rent_psm_month) ??
          null,
        noiAnnualSgd:
          coerceString(asset.noiAnnualSgd) ??
          coerceString(asset.noi_annual_sgd) ??
          null,
        estimatedCapexSgd:
          coerceString(asset.estimatedCapexSgd) ??
          coerceString(asset.estimated_capex_sgd) ??
          null,
        absorptionMonths:
          coerceString(asset.absorptionMonths) ??
          coerceString(asset.absorption_months) ??
          null,
        riskLevel:
          coerceString(asset.riskLevel) ??
          coerceString(asset.risk_level) ??
          null,
        notes: mapStringList(asset.notes),
      }
    })
    .filter((entry): entry is DealCalculatorAssetBreakdown => entry !== null)
}

export async function evaluateDealCalculator(
  request: DealCalculatorRequest,
): Promise<DealCalculatorResult> {
  const response = await fetch(buildUrl(API_PREFIX), {
    method: 'POST',
    headers: applyIdentityHeaders({
      'content-type': 'application/json',
    }),
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(
      detail || `Deal calculator request failed with status ${response.status}`,
    )
  }

  return mapResult(await response.json())
}
