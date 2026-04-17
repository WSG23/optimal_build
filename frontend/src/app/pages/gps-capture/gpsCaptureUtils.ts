/**
 * GPS Capture Page Utilities
 *
 * Formatting helpers extracted from GpsCapturePage for component size management.
 */

import type {
  DevelopmentScenario,
  ProfessionalPackType,
} from '../../../api/agents'

// Dark mode map style for Google Maps
export const DARK_MAP_STYLE = [
  { elementType: 'geometry', stylers: [{ color: '#242f3e' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#242f3e' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#746855' }] },
  {
    featureType: 'administrative.locality',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#d59563' }],
  },
  {
    featureType: 'poi',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#d59563' }],
  },
  {
    featureType: 'poi.park',
    elementType: 'geometry',
    stylers: [{ color: '#263c3f' }],
  },
  {
    featureType: 'road',
    elementType: 'geometry',
    stylers: [{ color: '#38414e' }],
  },
  {
    featureType: 'road',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#9ca5b3' }],
  },
  {
    featureType: 'road.highway',
    elementType: 'geometry',
    stylers: [{ color: '#746855' }],
  },
  {
    featureType: 'water',
    elementType: 'geometry',
    stylers: [{ color: '#17263c' }],
  },
  {
    featureType: 'water',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#515c6d' }],
  },
]

export const PACK_TYPES: ProfessionalPackType[] = [
  'universal',
  'investment',
  'sales',
  'lease',
]

export function formatScenarioLabel(value: DevelopmentScenario) {
  switch (value) {
    case 'raw_land':
      return 'Raw land'
    case 'existing_building':
      return 'Existing building'
    case 'heritage_property':
      return 'Heritage property'
    case 'underused_asset':
      return 'Underused asset'
    case 'mixed_use_redevelopment':
      return 'Mixed-use redevelopment'
    default:
      return value
  }
}

export function formatPackLabel(value: ProfessionalPackType) {
  switch (value) {
    case 'universal':
      return 'Universal pack'
    case 'investment':
      return 'Investment memo'
    case 'sales':
      return 'Sales brief'
    case 'lease':
      return 'Lease brochure'
    default:
      return value
  }
}

export function humanizeMetricKey(key: string) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

export function formatMetricValue(
  value: unknown,
  metricKey?: string,
  currencySymbol?: string,
) {
  if (value === null || value === undefined) {
    return '—'
  }
  if (typeof value === 'number') {
    const formattedNumber = Number.isInteger(value)
      ? value.toLocaleString()
      : value.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })

    const isCountField =
      metricKey &&
      (metricKey.includes('count') ||
        metricKey.includes('number') ||
        metricKey.includes('quantity') ||
        metricKey.includes('units'))

    const hasFinancialKeyword =
      metricKey &&
      !isCountField &&
      (metricKey.includes('price') ||
        metricKey.includes('noi') ||
        metricKey.includes('valuation') ||
        metricKey.includes('capex') ||
        metricKey.includes('rent') ||
        metricKey.includes('cost') ||
        metricKey.includes('value') ||
        metricKey.includes('revenue') ||
        metricKey.includes('income'))

    if (currencySymbol && hasFinancialKeyword) {
      return `${currencySymbol}${formattedNumber}`
    }
    return formattedNumber
  }
  return String(value)
}

export function extractReportValue(
  report: Record<string, unknown>,
  key: string,
) {
  const value = report[key]
  return typeof value === 'string' && value.trim() !== '' ? value : '—'
}

export function extractTransactions(report: Record<string, unknown>) {
  const comparables = report.comparables_analysis
  if (
    comparables &&
    typeof comparables === 'object' &&
    'transaction_count' in comparables
  ) {
    const value = (comparables as Record<string, unknown>).transaction_count
    if (typeof value === 'number') {
      return value.toLocaleString()
    }
  }
  return '—'
}
