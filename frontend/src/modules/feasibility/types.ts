export const landUseOptions = [
  { value: 'residential', labelKey: 'wizard.step1.landUseOptions.residential' },
  { value: 'commercial', labelKey: 'wizard.step1.landUseOptions.commercial' },
  { value: 'mixed_use', labelKey: 'wizard.step1.landUseOptions.mixed_use' },
  { value: 'industrial', labelKey: 'wizard.step1.landUseOptions.industrial' },
  { value: 'institutional', labelKey: 'wizard.step1.landUseOptions.institutional' },
] as const

export type LandUseOption = (typeof landUseOptions)[number]

export type LandUseType = LandUseOption['value']

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
