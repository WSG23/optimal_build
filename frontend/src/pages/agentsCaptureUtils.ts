/**
 * Agent GPS Capture Utilities
 *
 * Formatting helpers and constants extracted from AgentsGpsCapturePage
 * for component size management.
 */

import type {
  DevelopmentScenario,
  MetricValue,
  ProfessionalPackType,
} from '../api/agents'

export interface ScenarioOption {
  value: DevelopmentScenario
  labelKey: string
  descriptionKey: string
}

export const SCENARIO_OPTIONS: readonly ScenarioOption[] = [
  {
    value: 'raw_land',
    labelKey: 'agentsCapture.scenarios.rawLand.title',
    descriptionKey: 'agentsCapture.scenarios.rawLand.description',
  },
  {
    value: 'existing_building',
    labelKey: 'agentsCapture.scenarios.existingBuilding.title',
    descriptionKey: 'agentsCapture.scenarios.existingBuilding.description',
  },
  {
    value: 'heritage_property',
    labelKey: 'agentsCapture.scenarios.heritageProperty.title',
    descriptionKey: 'agentsCapture.scenarios.heritageProperty.description',
  },
  {
    value: 'underused_asset',
    labelKey: 'agentsCapture.scenarios.underusedAsset.title',
    descriptionKey: 'agentsCapture.scenarios.underusedAsset.description',
  },
] as const

export interface PackOption {
  value: ProfessionalPackType
  labelKey: string
  descriptionKey: string
}

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

export const DEFAULT_LATITUDE = '1.3000'
export const DEFAULT_LONGITUDE = '103.8500'

export function formatDateDisplay(
  value: unknown,
  locale: string,
): string | null {
  if (typeof value !== 'string' || value.trim() === '') {
    return null
  }
  const timestamp = Date.parse(value)
  if (Number.isNaN(timestamp)) {
    return value
  }
  return new Date(timestamp).toLocaleDateString(locale)
}

export function formatMetricLabel(
  key: string,
  translate: (key: string) => string,
): string {
  const lookup: Record<string, string> = {
    site_area_sqm: translate('agentsCapture.metrics.siteArea'),
    plot_ratio: translate('agentsCapture.metrics.plotRatio'),
    potential_gfa_sqm: translate('agentsCapture.metrics.potentialGfa'),
    approved_gfa_sqm: translate('agentsCapture.metrics.approvedGfa'),
    scenario_gfa_sqm: translate('agentsCapture.metrics.scenarioGfa'),
    gfa_uplift_sqm: translate('agentsCapture.metrics.gfaUplift'),
    near_by_mrt_count: translate('agentsCapture.metrics.nearbyMrtCount'),
    nearby_mrt_count: translate('agentsCapture.metrics.nearbyMrtCount'),
    current_use: translate('agentsCapture.metrics.currentUse'),
    building_height_m: translate('agentsCapture.metrics.buildingHeight'),
    nearby_development_count: translate(
      'agentsCapture.metrics.nearbyDevelopmentCount',
    ),
    nearest_completion: translate('agentsCapture.metrics.nearestCompletion'),
    recent_transaction_count: translate(
      'agentsCapture.metrics.recentTransactionCount',
    ),
    average_psf_price: translate('agentsCapture.metrics.averagePsfPrice'),
    average_monthly_rent: translate('agentsCapture.metrics.averageMonthlyRent'),
    rental_comparable_count: translate(
      'agentsCapture.metrics.rentalComparableCount',
    ),
    property_type: translate('agentsCapture.metrics.propertyType'),
    completion_year: translate('agentsCapture.metrics.completionYear'),
    heritage_risk: translate('agentsCapture.metrics.heritageRisk'),
  }

  if (lookup[key]) {
    return lookup[key]
  }
  const cleaned = key.replace(/_/g, ' ')
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
}

export function formatMetricValue(
  value: MetricValue | undefined,
  locale: string,
): string {
  if (value === null || value === undefined) {
    return '—'
  }
  if (typeof value === 'number') {
    return new Intl.NumberFormat(locale, {
      maximumFractionDigits: Number.isInteger(value) ? 0 : 2,
    }).format(value)
  }
  return value
}

export function formatFileSize(bytes: number | null, locale: string): string {
  if (bytes == null || Number.isNaN(bytes)) {
    return '—'
  }
  if (bytes < 1024) {
    return `${new Intl.NumberFormat(locale).format(bytes)} B`
  }
  const units = ['KB', 'MB', 'GB'] as const
  let value = bytes / 1024
  let index = 0
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(value)} ${units[index]}`
}

export function scenarioTitle(
  scenario: DevelopmentScenario,
  translate: (key: string) => string,
): string {
  switch (scenario) {
    case 'raw_land':
      return translate('agentsCapture.scenarios.rawLand.title')
    case 'existing_building':
      return translate('agentsCapture.scenarios.existingBuilding.title')
    case 'heritage_property':
      return translate('agentsCapture.scenarios.heritageProperty.title')
    case 'underused_asset':
      return translate('agentsCapture.scenarios.underusedAsset.title')
    default:
      return scenario
  }
}

export function scenarioDescription(
  scenario: DevelopmentScenario,
  translate: (key: string) => string,
): string {
  switch (scenario) {
    case 'raw_land':
      return translate('agentsCapture.scenarios.rawLand.description')
    case 'existing_building':
      return translate('agentsCapture.scenarios.existingBuilding.description')
    case 'heritage_property':
      return translate('agentsCapture.scenarios.heritageProperty.description')
    case 'underused_asset':
      return translate('agentsCapture.scenarios.underusedAsset.description')
    default:
      return ''
  }
}
