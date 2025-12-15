import type {
  ProfessionalPackType,
  ProfessionalPackSummary,
} from '../../../api/agents'
import type { BuildableSummary } from '../../../api/buildable'

export type { ProfessionalPackType, ProfessionalPackSummary, BuildableSummary }

export type StoredAssetOptimization = {
  assetType: string
  allocationPct: number
  allocatedGfaSqm?: number | null
  niaEfficiency?: number | null
  targetFloorHeightM?: number | null
  parkingRatioPer1000Sqm?: number | null
  rentPsmMonth?: number | null
  stabilisedVacancyPct?: number | null
  opexPctOfRent?: number | null
  fitoutCostPsm?: number | null
  notes?: string[]
  estimatedRevenueSgd?: number | null
  estimatedCapexSgd?: number | null
  riskLevel?: string | null
  absorptionMonths?: number | null
}

export interface AssumptionInputs {
  typFloorToFloorM: string
  efficiencyRatio: string
  // Engineering
  structureType: 'rc' | 'steel' | 'mass_timber'
  mepLoadWpsm: string
}

export interface FinancialAssumptions {
  capRatePercent: string
  interestRatePercent: string
  targetMarginPercent: string
}

export interface AssumptionErrors {
  typFloorToFloorM?: 'required' | 'invalid'
  efficiencyRatio?: 'required' | 'invalid' | 'range'
  structureType?: 'required' | 'invalid'
  mepLoadWpsm?: 'required' | 'invalid' | 'range'
}

export type WizardStatus =
  | 'idle'
  | 'loading'
  | 'success'
  | 'partial'
  | 'empty'
  | 'error'

export type PendingPayload = {
  name: string
  address: string
  siteAreaSqm: number
  landUse: string
  typFloorToFloorM: number
  efficiencyRatio: number
  structureType: 'rc' | 'steel' | 'mass_timber'
  mepLoadWpsm: number
  // Financials
  capRatePercent: number
  interestRatePercent: number
  targetMarginPercent: number
}

export interface PackOption {
  value: ProfessionalPackType
  labelKey: string
  descriptionKey: string
}

export interface FinancialSummary {
  totalEstimatedRevenueSgd: number | null
  totalEstimatedCapexSgd: number | null
  dominantRiskProfile: string | null
  notes: string[]
}

export const ASSET_MIX_STORAGE_PREFIX = 'developer-asset-mix:'

export const DEFAULT_ASSUMPTIONS = {
  typFloorToFloorM: 3.4,
  efficiencyRatio: 0.8,
  structureType: 'rc',
  mepLoadWpsm: 150,
  capRatePercent: 4.5,
  interestRatePercent: 3.5,
  targetMarginPercent: 15.0,
} as const

export const DEBOUNCE_MS = 300

export type GenerativeStrategy =
  | 'max_density'
  | 'balanced'
  | 'iconic'
  | 'green_focus'

export interface GenerativeOption {
  value: GenerativeStrategy
  label: string
  description: string
  icon?: string // Placeholder for icon name or component
}

export const GENERATIVE_OPTIONS: readonly GenerativeOption[] = [
  {
    value: 'max_density',
    label: 'Max Density',
    description: 'Maximize GFA and efficiency.',
  },
  {
    value: 'balanced',
    label: 'Balanced',
    description: 'Optimal trade-off between GFA and open space.',
  },
  {
    value: 'iconic',
    label: 'Iconic Form',
    description: 'Unique geometry causing high visual impact.',
  },
  {
    value: 'green_focus',
    label: 'Eco-First',
    description: 'Prioritizing sustainability and biophilia.',
  },
] as const

export const PACK_OPTIONS: readonly PackOption[] = [
  {
    value: 'universal',
    labelKey: 'agentsCapture.pack.options.universal.title',
    descriptionKey: 'agentsCapture.pack.options.universal.description',
  },
  {
    value: 'investment',
    labelKey: 'agentsCapture.pack.options.investment.title',
    descriptionKey: 'agentsCapture.pack.options.investment.description',
  },
  {
    value: 'sales',
    labelKey: 'agentsCapture.pack.options.sales.title',
    descriptionKey: 'agentsCapture.pack.options.sales.description',
  },
  {
    value: 'lease',
    labelKey: 'agentsCapture.pack.options.lease.title',
    descriptionKey: 'agentsCapture.pack.options.lease.description',
  },
] as const
