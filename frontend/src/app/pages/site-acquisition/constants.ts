/**
 * Constants for SiteAcquisitionPage
 *
 * Pure data - no runtime dependencies.
 */

import type {
  DevelopmentScenario,
  GeometryDetailLevel,
} from '../../../api/siteAcquisition'
import type { InsightSeverity } from './types'

// ============================================================================
// Scenario Options
// ============================================================================

export type ScenarioOption = {
  value: DevelopmentScenario
  label: string
  description: string
  icon: string
}

export const SCENARIO_OPTIONS: ScenarioOption[] = [
  {
    value: 'raw_land',
    label: 'New Construction',
    description: 'Raw land development with ground-up construction',
    icon: '🏗️',
  },
  {
    value: 'existing_building',
    label: 'Renovation',
    description: 'Existing building renovation and modernization',
    icon: '🔨',
  },
  {
    value: 'heritage_property',
    label: 'Heritage Integration',
    description: 'Heritage-protected property with conservation requirements',
    icon: '🏛️',
  },
  {
    value: 'underused_asset',
    label: 'Adaptive Reuse',
    description: 'Underutilized asset repositioning and value-add',
    icon: '♻️',
  },
  {
    value: 'mixed_use_redevelopment',
    label: 'Mixed-Use Redevelopment',
    description:
      'Complex mixed-use project with residential, commercial, and retail components',
    icon: '🏙️',
  },
]

// ============================================================================
// Jurisdiction Options
// ============================================================================

export type JurisdictionOption = {
  code: string
  label: string
  defaultLat: string
  defaultLon: string
}

export const JURISDICTION_OPTIONS: readonly JurisdictionOption[] = [
  {
    code: 'SG',
    label: 'Singapore',
    defaultLat: '1.3000',
    defaultLon: '103.8500',
  },
  {
    code: 'HK',
    label: 'Hong Kong',
    defaultLat: '22.3193',
    defaultLon: '114.1694',
  },
  {
    code: 'NZ',
    label: 'New Zealand',
    defaultLat: '-36.8485',
    defaultLon: '174.7633',
  },
  {
    code: 'SEA',
    label: 'Seattle',
    defaultLat: '47.6062',
    defaultLon: '-122.3321',
  },
  {
    code: 'TOR',
    label: 'Toronto',
    defaultLat: '43.6532',
    defaultLon: '-79.3832',
  },
] as const

// ============================================================================
// Condition Assessment Constants
// ============================================================================

export const CONDITION_RATINGS = ['A', 'B', 'C', 'D', 'E'] as const
export const CONDITION_RISK_LEVELS = [
  'low',
  'moderate',
  'elevated',
  'high',
  'critical',
] as const

export const DEFAULT_CONDITION_SYSTEMS = [
  'Structural frame & envelope',
  'Mechanical & electrical systems',
  'Compliance & envelope maintenance',
] as const

// ============================================================================
// History & Limits
// ============================================================================

export const HISTORY_FETCH_LIMIT = 10
export const QUICK_ANALYSIS_HISTORY_LIMIT = 5

// ============================================================================
// Preview Options
// ============================================================================

export const PREVIEW_DETAIL_OPTIONS: GeometryDetailLevel[] = [
  'medium',
  'simple',
]

export const PREVIEW_DETAIL_LABELS: Record<GeometryDetailLevel, string> = {
  medium: 'Medium (octagonal, setbacks, floor lines)',
  simple: 'Simple (fast box geometry)',
}

// ============================================================================
// Scenario Metric Configuration
// ============================================================================

export const SCENARIO_METRIC_PRIORITY: readonly string[] = [
  'plot_ratio',
  'potential_gfa_sqm',
  'gfa_uplift_sqm',
  'occupancy_pct',
  'annual_noi',
  'valuation_cap_rate',
  'potential_rent_uplift_pct',
  'target_lease_term_years',
  'estimated_capex',
  'conservation_status',
]

export const SCENARIO_METRIC_LABELS: Record<string, string> = {
  plot_ratio: 'Plot ratio',
  potential_gfa_sqm: 'Potential GFA (sqm)',
  gfa_uplift_sqm: 'GFA uplift (sqm)',
  occupancy_pct: 'Occupancy',
  annual_noi: 'Annual NOI',
  valuation_cap_rate: 'Cap rate',
  potential_rent_uplift_pct: 'Rent uplift',
  target_lease_term_years: 'Lease term (yrs)',
  estimated_capex: 'Estimated CAPEX',
  conservation_status: 'Conservation status',
}

// ============================================================================
// Insight Severity Order (for sorting)
// ============================================================================

export const INSIGHT_SEVERITY_ORDER: Record<InsightSeverity, number> = {
  critical: 0,
  warning: 1,
  positive: 2,
  info: 3,
}
