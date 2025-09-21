export const landUseOptions = [
  { value: 'residential', label: 'Residential' },
  { value: 'commercial', label: 'Commercial' },
  { value: 'mixed_use', label: 'Mixed Use' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'institutional', label: 'Institutional' },
] as const

export type LandUseType = (typeof landUseOptions)[number]['value']

export interface NewFeasibilityProjectInput {
  name: string
  siteAddress: string
  siteAreaSqm: number
  landUse: LandUseType
  targetGrossFloorAreaSqm?: number
  buildingHeightMeters?: number
}

export type FeasibilityRuleSeverity = 'critical' | 'important' | 'informational'

export interface FeasibilityRule {
  id: string
  title: string
  description: string
  authority: string
  topic: string
  parameterKey: string
  operator: string
  value: string
  unit?: string
  severity: FeasibilityRuleSeverity
  defaultSelected?: boolean
}

export interface FeasibilityRulesSummary {
  complianceFocus: string
  notes?: string
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

export type RuleAssessmentStatus = 'pass' | 'fail' | 'warning'

export interface RuleAssessmentResult extends FeasibilityRule {
  status: RuleAssessmentStatus
  actualValue?: string
  notes?: string
}

export interface BuildableAreaSummary {
  maxPermissibleGfaSqm: number
  estimatedAchievableGfaSqm: number
  estimatedUnitCount: number
  siteCoveragePercent: number
  remarks?: string
}

export interface FeasibilityAssessmentResponse {
  projectId: string
  summary: BuildableAreaSummary
  rules: RuleAssessmentResult[]
  recommendations: string[]
}
