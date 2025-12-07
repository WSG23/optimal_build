import { buildUrl } from './shared'

const API_PREFIX = 'api/v1/feasibility'

export interface BuildEnvelopeSnapshot {
  siteAreaSqm?: number | null
  allowablePlotRatio?: number | null
  maxBuildableGfaSqm?: number | null
  currentGfaSqm?: number | null
  additionalPotentialGfaSqm?: number | null
}

export interface NewFeasibilityProjectInput {
  name: string
  siteAddress: string
  siteAreaSqm: number
  landUse: string
  targetGrossFloorAreaSqm?: number | null
  buildingHeightMeters?: number | null
  buildEnvelope?: BuildEnvelopeSnapshot | null
  typFloorToFloorM?: number | null
  efficiencyRatio?: number | null
  structureType?: string | null
  mepLoadWpsm?: number | null
}

export type FeasibilityRuleSeverity = 'critical' | 'important' | 'informational'
export type FeasibilityRuleStatus = 'pass' | 'fail' | 'warning'

export interface FeasibilityRule {
  id: string
  title: string
  description: string
  authority: string
  topic: string
  parameterKey: string
  operator: string
  value: string
  unit?: string | null
  severity: FeasibilityRuleSeverity
  defaultSelected: boolean
}

export interface FeasibilityRulesSummary {
  complianceFocus: string
  notes?: string | null
}

export interface FeasibilityRulesResponse {
  projectId: string
  rules: FeasibilityRule[]
  recommendedRuleIds: string[]
  summary: FeasibilityRulesSummary
}

export interface FeasibilityAssessmentRequest {
  project: NewFeasibilityProjectInput
  selectedRuleIds: string[]
}

export interface RuleAssessmentResult extends FeasibilityRule {
  status: FeasibilityRuleStatus
  actualValue?: string | null
  notes?: string | null
}

export interface BuildableAreaSummary {
  maxPermissibleGfaSqm: number
  estimatedAchievableGfaSqm: number
  estimatedUnitCount: number
  siteCoveragePercent: number
  remarks?: string | null
}

export interface AssetConstraintViolation {
  constraintType: string
  severity: string
  message: string
  assetType?: string | null
}

export interface AssetFinancialSummarySchema {
  totalEstimatedRevenueSgd?: number | null
  totalEstimatedCapexSgd?: number | null
  dominantRiskProfile?: string | null
  notes?: string[]
}

export interface AssetOptimizationRecommendation {
  assetType: string
  allocationPct: number
  allocatedGfaSqm?: number | null
  niaEfficiency?: number | null
  targetFloorHeightM?: number | null
  parkingRatioPer1000Sqm?: number | null
  rentPsmMonth?: number | null
  stabilisedVacancyPct?: number | null
  opexPctOfRent?: number | null
  estimatedRevenueSgd?: number | null
  estimatedCapexSgd?: number | null
  fitoutCostPsm?: number | null
  absorptionMonths?: number | null
  riskLevel?: string | null
  heritagePremiumPct?: number | null
  notes: string[]
  niaSqm?: number | null
  estimatedHeightM?: number | null
  totalParkingBaysRequired?: number | null
  revenueBasis?: string | null
  constraintViolations: AssetConstraintViolation[]
  confidenceScore?: number | null
  alternativeScenarios: string[]
}

export interface FeasibilityAssessmentResponse {
  projectId: string
  summary: BuildableAreaSummary
  rules: RuleAssessmentResult[]
  recommendations: string[]
  assetOptimizations: AssetOptimizationRecommendation[]
  assetMixSummary?: AssetFinancialSummarySchema | null
  constraintLog: AssetConstraintViolation[]
  optimizerConfidence?: number | null
}

export async function runFeasibilityAssessment(
  request: FeasibilityAssessmentRequest,
  signal?: AbortSignal,
): Promise<FeasibilityAssessmentResponse> {
  const response = await fetch(buildUrl(`${API_PREFIX}/assessment`), {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(
      detail || `Request to ${API_PREFIX}/assessment failed with ${response.status}`,
    )
  }

  return (await response.json()) as FeasibilityAssessmentResponse
}

export interface EngineeringDefaults {
  typFloorToFloorM: number
  efficiencyRatio: number
}

export async function getEngineeringDefaults(
  signal?: AbortSignal,
): Promise<EngineeringDefaults> {
  const response = await fetch(buildUrl(`${API_PREFIX}/defaults`), {
    method: 'GET',
    headers: { 'content-type': 'application/json' },
    signal,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(
      detail || `Request to ${API_PREFIX}/defaults failed with ${response.status}`,
    )
  }

  return (await response.json()) as EngineeringDefaults
}

// Alias for backward compatibility
export { runFeasibilityAssessment as submitFeasibilityAssessment }
