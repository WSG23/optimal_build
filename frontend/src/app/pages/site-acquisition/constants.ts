/**
 * Constants for SiteAcquisitionPage
 *
 * Pure data - no runtime dependencies.
 */

import type {
  DevelopmentScenario,
  GeometryDetailLevel,
} from '../../../api/siteAcquisition'
import type { InsightSeverity, OfflineChecklistTemplate } from './types'

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
  medium: 'Medium (layered massing, optional floor bands)',
  simple: 'Simple (fast box geometry)',
}

// ============================================================================
// Scenario Metric Configuration
// ============================================================================

export const SCENARIO_METRIC_PRIORITY: readonly string[] = [
  'plot_ratio',
  'potential_gfa_sqm',
  'gfa_uplift_sqm',
  'site_area_sqm',
  'building_height_limit_m',
  'site_coverage_pct',
  'conservation_status',
  'heritage_risk',
]

export const SCENARIO_METRIC_LABELS: Record<string, string> = {
  plot_ratio: 'Plot ratio',
  potential_gfa_sqm: 'Potential GFA (sqm)',
  gfa_uplift_sqm: 'GFA uplift (sqm)',
  site_area_sqm: 'Site area (sqm)',
  building_height_limit_m: 'Height limit (m)',
  site_coverage_pct: 'Site coverage',
  conservation_status: 'Conservation status',
  heritage_risk: 'Heritage risk',
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

// ============================================================================
// Offline Checklist Templates
// ============================================================================

export const OFFLINE_CHECKLIST_TEMPLATES: OfflineChecklistTemplate[] = [
  // Raw Land
  {
    developmentScenario: 'raw_land',
    category: 'title_verification',
    itemTitle: 'Confirm land ownership and title status',
    itemDescription:
      'Retrieve SLA title extracts and confirm that there are no caveats or encumbrances on the parcel.',
    priority: 'critical',
    requiresProfessional: true,
    professionalType: 'Conveyancing lawyer',
    typicalDurationDays: 5,
    displayOrder: 10,
  },
  {
    developmentScenario: 'raw_land',
    category: 'zoning_compliance',
    itemTitle: 'Validate URA master plan parameters',
    itemDescription:
      'Cross-check zoning, plot ratio, and allowable uses against intended development outcomes.',
    priority: 'critical',
    requiresProfessional: false,
    typicalDurationDays: 4,
    displayOrder: 20,
  },
  {
    developmentScenario: 'raw_land',
    category: 'environmental_assessment',
    itemTitle: 'Screen for environmental and soil constraints',
    itemDescription:
      'Review PUB drainage, flood susceptibility, soil conditions, and adjacent environmental protections.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Geotechnical engineer',
    typicalDurationDays: 7,
    displayOrder: 30,
  },
  {
    developmentScenario: 'raw_land',
    category: 'access_rights',
    itemTitle: 'Confirm legal site access and right-of-way',
    itemDescription:
      'Validate ingress/egress arrangements with LTA and adjacent land owners for temporary works.',
    priority: 'medium',
    requiresProfessional: true,
    professionalType: 'Traffic consultant',
    typicalDurationDays: 6,
    displayOrder: 40,
  },
  // Existing Building
  {
    developmentScenario: 'existing_building',
    category: 'structural_survey',
    itemTitle: 'Commission structural integrity assessment',
    itemDescription:
      'Carry out intrusive and non-intrusive inspections to determine retrofitting effort.',
    priority: 'critical',
    requiresProfessional: true,
    professionalType: 'Structural engineer',
    typicalDurationDays: 14,
    displayOrder: 10,
  },
  {
    developmentScenario: 'existing_building',
    category: 'utility_capacity',
    itemTitle: 'Benchmark utility upgrade requirements',
    itemDescription:
      'Review existing electrical, water, and gas supply against target load profiles.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'M&E engineer',
    typicalDurationDays: 5,
    displayOrder: 20,
  },
  {
    developmentScenario: 'existing_building',
    category: 'zoning_compliance',
    itemTitle: 'Validate change-of-use requirements',
    itemDescription:
      'Confirm URA and BCA approvals required for intended repositioning program.',
    priority: 'high',
    requiresProfessional: false,
    typicalDurationDays: 3,
    displayOrder: 30,
  },
  {
    developmentScenario: 'existing_building',
    category: 'environmental_assessment',
    itemTitle: 'Assess asbestos and hazardous material presence',
    itemDescription:
      'Undertake sampling programme before any strip-out or demolition work proceeds.',
    priority: 'medium',
    requiresProfessional: true,
    professionalType: 'Environmental consultant',
    typicalDurationDays: 10,
    displayOrder: 40,
  },
  // Heritage Property
  {
    developmentScenario: 'heritage_property',
    category: 'heritage_constraints',
    itemTitle: 'Confirm conservation requirements with URA',
    itemDescription:
      'Document façade retention, material preservation, and permissible alteration scope.',
    priority: 'critical',
    requiresProfessional: true,
    professionalType: 'Heritage architect',
    typicalDurationDays: 7,
    displayOrder: 10,
  },
  {
    developmentScenario: 'heritage_property',
    category: 'structural_survey',
    itemTitle: 'Heritage structural reinforcement study',
    itemDescription:
      'Evaluate load paths and necessary strengthening to achieve code compliance without damaging heritage elements.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Structural engineer',
    typicalDurationDays: 12,
    displayOrder: 20,
  },
  {
    developmentScenario: 'heritage_property',
    category: 'zoning_compliance',
    itemTitle: 'Assess conservation overlay with planning parameters',
    itemDescription:
      'Check whether conservation overlays restrict development intensity or allowable uses.',
    priority: 'high',
    requiresProfessional: false,
    typicalDurationDays: 5,
    displayOrder: 30,
  },
  {
    developmentScenario: 'heritage_property',
    category: 'access_rights',
    itemTitle: 'Coordinate logistics with surrounding stakeholders',
    itemDescription:
      'Identify staging areas, hoarding approvals, and historic streetscape protection measures.',
    priority: 'medium',
    requiresProfessional: false,
    typicalDurationDays: 4,
    displayOrder: 40,
  },
  // Underused Asset
  {
    developmentScenario: 'underused_asset',
    category: 'utility_capacity',
    itemTitle: 'Determine retrofit M&E upgrade scope',
    itemDescription:
      'Right-size mechanical plant, vertical transportation, and ICT backbone for the new programme.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Building services engineer',
    typicalDurationDays: 8,
    displayOrder: 10,
  },
  {
    developmentScenario: 'underused_asset',
    category: 'environmental_assessment',
    itemTitle: 'Perform indoor environmental quality audit',
    itemDescription:
      'Quantify remediation required for mould, humidity, and ventilation gaps from prolonged underuse.',
    priority: 'medium',
    requiresProfessional: true,
    professionalType: 'Environmental specialist',
    typicalDurationDays: 6,
    displayOrder: 20,
  },
  {
    developmentScenario: 'underused_asset',
    category: 'access_rights',
    itemTitle: 'Validate access control and fire egress updates',
    itemDescription:
      'Ensure adaptive reuse complies with SCDF requirements and workplace safety codes.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Fire engineer',
    typicalDurationDays: 5,
    displayOrder: 30,
  },
  // Mixed-Use Redevelopment
  {
    developmentScenario: 'mixed_use_redevelopment',
    category: 'zoning_compliance',
    itemTitle: 'Confirm mixed-use allowable combination',
    itemDescription:
      'Reconcile residential, commercial, and retail programme with masterplan mix and strata limitations.',
    priority: 'critical',
    requiresProfessional: false,
    typicalDurationDays: 6,
    displayOrder: 10,
  },
  {
    developmentScenario: 'mixed_use_redevelopment',
    category: 'utility_capacity',
    itemTitle: 'Integrate district cooling and energy sharing options',
    itemDescription:
      "Assess utility providers' capacity and incentives for precinct-scale systems.",
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Energy consultant',
    typicalDurationDays: 9,
    displayOrder: 20,
  },
  {
    developmentScenario: 'mixed_use_redevelopment',
    category: 'structural_survey',
    itemTitle: 'Phase-by-phase structural staging plan',
    itemDescription:
      'Evaluate demolition, retention, and staging needed to keep operations running during redevelopment.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Structural engineer',
    typicalDurationDays: 15,
    displayOrder: 30,
  },
  {
    developmentScenario: 'mixed_use_redevelopment',
    category: 'heritage_constraints',
    itemTitle: 'Coordinate heritage façade integration',
    itemDescription:
      'Identify conserved elements that must be retained and methods to blend with new podium.',
    priority: 'medium',
    requiresProfessional: true,
    professionalType: 'Conservation architect',
    typicalDurationDays: 10,
    displayOrder: 40,
  },
]
