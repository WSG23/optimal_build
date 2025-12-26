/**
 * Scenario & Development Constants - Single Source of Truth
 *
 * All development types, scenario options, and default assumptions.
 * These values MUST match backend/app/constants/defaults.py
 */

// =============================================================================
// DEVELOPMENT TYPES
// =============================================================================

export const DEVELOPMENT_TYPES = {
  NEW_DEVELOPMENT: 'NEW_DEVELOPMENT',
  REDEVELOPMENT: 'REDEVELOPMENT',
  RENOVATION: 'RENOVATION',
  CHANGE_OF_USE: 'CHANGE_OF_USE',
  ADDITION: 'ADDITION',
} as const

export type DevelopmentType =
  (typeof DEVELOPMENT_TYPES)[keyof typeof DEVELOPMENT_TYPES]

// =============================================================================
// PROPERTY TYPES
// =============================================================================

export const PROPERTY_TYPES = {
  OFFICE: 'office',
  RETAIL: 'retail',
  INDUSTRIAL: 'industrial',
  RESIDENTIAL: 'residential',
  MIXED_USE: 'mixed_use',
  HOTEL: 'hotel',
  WAREHOUSE: 'warehouse',
  LAND: 'land',
  SPECIAL_PURPOSE: 'special_purpose',
} as const

export type PropertyType = (typeof PROPERTY_TYPES)[keyof typeof PROPERTY_TYPES]

// =============================================================================
// PROPERTY TENURE
// =============================================================================

export const PROPERTY_TENURE = {
  FREEHOLD: 'freehold',
  LEASEHOLD_99: 'leasehold_99',
  LEASEHOLD_999: 'leasehold_999',
  STATE_LAND: 'state_land',
} as const

export type PropertyTenure =
  (typeof PROPERTY_TENURE)[keyof typeof PROPERTY_TENURE]

// =============================================================================
// STATUS ENUMS - Shared across jurisdictions
// =============================================================================

export const DEVELOPMENT_STATUS = {
  PLANNING: 'planning',
  APPROVED: 'approved',
  UNDER_CONSTRUCTION: 'under_construction',
  COMPLETED: 'completed',
  ON_HOLD: 'on_hold',
  CANCELLED: 'cancelled',
} as const

export const ACQUISITION_STATUS = {
  PROSPECTING: 'prospecting',
  DUE_DILIGENCE: 'due_diligence',
  NEGOTIATING: 'negotiating',
  UNDER_CONTRACT: 'under_contract',
  ACQUIRED: 'acquired',
  PASSED: 'passed',
} as const

export const FEASIBILITY_STATUS = {
  NOT_STARTED: 'not_started',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  APPROVED: 'approved',
  REJECTED: 'rejected',
} as const

export const COMPLIANCE_STATUS = {
  COMPLIANT: 'compliant',
  NON_COMPLIANT: 'non_compliant',
  PENDING_REVIEW: 'pending_review',
  EXEMPTED: 'exempted',
} as const

// =============================================================================
// DEFAULT ASSUMPTIONS - MUST MATCH BACKEND
// =============================================================================

/**
 * Default building assumptions for feasibility analysis.
 * These values are synchronized with backend/app/constants/defaults.py
 *
 * ⚠️ WARNING: If you change these values, you MUST also update:
 *    - backend/app/constants/defaults.py
 *    - backend/app/core/config.py (BUILDABLE_* settings)
 */
export const DEFAULT_ASSUMPTIONS = {
  /** Typical floor-to-floor height in meters */
  TYP_FLOOR_TO_FLOOR_M: 3.5,
  /** Building efficiency ratio (NLA/GFA) */
  EFFICIENCY_RATIO: 0.82,
  /** Default construction cost per sqm (SGD) */
  CONSTRUCTION_COST_PSM: 3500,
  /** Default land cost premium factor */
  LAND_COST_PREMIUM: 1.15,
  /** Default parking ratio (lots per 1000 sqm GFA) */
  PARKING_RATIO: 3.5,
  /** Default development timeline in months */
  DEVELOPMENT_TIMELINE_MONTHS: 36,
  /** Default capitalization rate */
  CAP_RATE: 0.045,
  /** Default discount rate */
  DISCOUNT_RATE: 0.08,
  /** Default rental escalation per annum */
  RENTAL_ESCALATION: 0.025,
  /** Default vacancy rate */
  VACANCY_RATE: 0.05,
} as const

// =============================================================================
// SCENARIO OPTIONS
// =============================================================================

export const SCENARIO_OPTIONS = [
  {
    id: 'residential_high_density',
    label: 'Residential - High Density',
    type: PROPERTY_TYPES.RESIDENTIAL,
    developmentType: DEVELOPMENT_TYPES.NEW_DEVELOPMENT,
    description: 'High-rise residential development',
  },
  {
    id: 'residential_medium_density',
    label: 'Residential - Medium Density',
    type: PROPERTY_TYPES.RESIDENTIAL,
    developmentType: DEVELOPMENT_TYPES.NEW_DEVELOPMENT,
    description: 'Mid-rise residential development',
  },
  {
    id: 'mixed_use_retail_residential',
    label: 'Mixed Use - Retail/Residential',
    type: PROPERTY_TYPES.MIXED_USE,
    developmentType: DEVELOPMENT_TYPES.NEW_DEVELOPMENT,
    description: 'Ground floor retail with residential above',
  },
  {
    id: 'office_grade_a',
    label: 'Office - Grade A',
    type: PROPERTY_TYPES.OFFICE,
    developmentType: DEVELOPMENT_TYPES.NEW_DEVELOPMENT,
    description: 'Premium office development',
  },
  {
    id: 'industrial_light',
    label: 'Industrial - Light',
    type: PROPERTY_TYPES.INDUSTRIAL,
    developmentType: DEVELOPMENT_TYPES.NEW_DEVELOPMENT,
    description: 'Light industrial/business park',
  },
  {
    id: 'redevelopment_existing',
    label: 'Redevelopment',
    type: PROPERTY_TYPES.MIXED_USE,
    developmentType: DEVELOPMENT_TYPES.REDEVELOPMENT,
    description: 'Demolish and rebuild existing structure',
  },
  {
    id: 'renovation_upgrade',
    label: 'Renovation/Upgrade',
    type: PROPERTY_TYPES.OFFICE,
    developmentType: DEVELOPMENT_TYPES.RENOVATION,
    description: 'Upgrade existing building systems',
  },
] as const

// =============================================================================
// GENERATIVE DESIGN OPTIONS
// =============================================================================

export const GENERATIVE_OPTIONS = [
  { id: 'maximize_gfa', label: 'Maximize GFA', priority: 'area' },
  { id: 'maximize_yield', label: 'Maximize Yield', priority: 'financial' },
  { id: 'optimize_views', label: 'Optimize Views', priority: 'amenity' },
  { id: 'minimize_cost', label: 'Minimize Cost', priority: 'cost' },
  { id: 'balanced', label: 'Balanced Approach', priority: 'balanced' },
] as const

// =============================================================================
// FINANCIAL SCENARIO TYPES
// =============================================================================

export const CAPITAL_STACK_TYPES = {
  EQUITY: 'equity',
  SENIOR_DEBT: 'senior_debt',
  MEZZANINE: 'mezzanine',
  PREFERRED_EQUITY: 'preferred_equity',
} as const

export const FINANCING_SOURCES = [
  { id: 'developer_equity', label: 'Developer Equity', type: 'equity' },
  { id: 'investor_equity', label: 'Investor Equity', type: 'equity' },
  { id: 'bank_loan', label: 'Bank Loan', type: 'senior_debt' },
  { id: 'mezzanine_loan', label: 'Mezzanine Loan', type: 'mezzanine' },
  { id: 'construction_loan', label: 'Construction Loan', type: 'senior_debt' },
] as const

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Get scenario option by ID
 */
export function getScenarioOption(id: string) {
  return SCENARIO_OPTIONS.find((s) => s.id === id)
}

/**
 * Get property type label
 */
export function getPropertyTypeLabel(type: PropertyType): string {
  const labels: Record<PropertyType, string> = {
    office: 'Office',
    retail: 'Retail',
    industrial: 'Industrial',
    residential: 'Residential',
    mixed_use: 'Mixed Use',
    hotel: 'Hotel',
    warehouse: 'Warehouse',
    land: 'Land',
    special_purpose: 'Special Purpose',
  }
  return labels[type] || type
}

/**
 * Get status color for UI display
 */
export function getStatusColor(
  status: string,
): 'success' | 'warning' | 'error' | 'info' | 'default' {
  const colorMap: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
    completed: 'success',
    approved: 'success',
    acquired: 'success',
    compliant: 'success',
    in_progress: 'info',
    under_construction: 'info',
    negotiating: 'info',
    pending_review: 'warning',
    due_diligence: 'warning',
    on_hold: 'warning',
    rejected: 'error',
    non_compliant: 'error',
    cancelled: 'error',
    passed: 'error',
  }
  return colorMap[status] || 'default'
}
