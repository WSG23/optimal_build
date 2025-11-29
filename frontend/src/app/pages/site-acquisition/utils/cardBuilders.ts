/**
 * Pure functions for building property overview card data
 *
 * These functions have no side effects and return structured data for display.
 */

import type {
  SiteAcquisitionResult,
  DeveloperAssetOptimization,
  PreviewJob,
  DeveloperColorLegendEntry,
} from '../../../../api/siteAcquisition'
import type { PropertyOverviewCard } from '../types'

// ============================================================================
// Types
// ============================================================================

export type NumberFormatter = (
  value: number,
  options?: Intl.NumberFormatOptions,
) => string

export type CurrencyFormatter = (value: number) => string

export type TimestampFormatter = (value: string) => string

export interface CardBuilderFormatters {
  formatNumber: NumberFormatter
  formatCurrency: CurrencyFormatter
  formatTimestamp: TimestampFormatter
}

export interface CardBuilderContext {
  capturedProperty: SiteAcquisitionResult
  /** Pre-extracted propertyInfo summary (optional, will be derived from capturedProperty if not provided) */
  propertyInfoSummary?: SiteAcquisitionResult['propertyInfo'] | null
  /** Pre-extracted uraZoning summary (optional, will be derived from capturedProperty if not provided) */
  zoningSummary?: SiteAcquisitionResult['uraZoning'] | null
  /** Pre-extracted nearest MRT station (optional, will be derived from capturedProperty if not provided) */
  nearestMrtStation?: { name: string; distanceM: number | null } | null
  /** Pre-extracted nearest bus stop (optional, will be derived from capturedProperty if not provided) */
  nearestBusStop?: { name: string; distanceM: number | null } | null
  previewJob: PreviewJob | null
  colorLegendEntries: DeveloperColorLegendEntry[]
  formatters: CardBuilderFormatters
  /** Currency symbol for display (e.g. 'S$', 'HK$', '$') - defaults to 'S$' */
  currencySymbol?: string
}

// ============================================================================
// Internal Formatters (derived from formatNumber)
// ============================================================================

function createAreaFormatter(formatNumber: NumberFormatter) {
  return (value: number | null | undefined): string => {
    if (value === null || value === undefined) {
      return '—'
    }
    const precision = value >= 1000 ? 0 : 2
    return `${formatNumber(value, { maximumFractionDigits: precision })} sqm`
  }
}

function createHeightFormatter(formatNumber: NumberFormatter) {
  return (value: number | null | undefined): string => {
    if (value === null || value === undefined) {
      return '—'
    }
    return `${formatNumber(value, { maximumFractionDigits: 1 })} m`
  }
}

function createPlotRatioFormatter(formatNumber: NumberFormatter) {
  return (value: number | null | undefined): string => {
    if (value === null || value === undefined) {
      return '—'
    }
    return formatNumber(value, { maximumFractionDigits: 2 })
  }
}

function createSiteCoverageFormatter(formatNumber: NumberFormatter) {
  return (value: number | null | undefined): string => {
    if (value === null || value === undefined) {
      return '—'
    }
    let percent = value
    if (percent <= 1) {
      percent = percent * 100
    }
    return `${formatNumber(percent, {
      maximumFractionDigits: percent >= 100 ? 0 : 1,
    })}%`
  }
}

function createDistanceFormatter(formatNumber: NumberFormatter) {
  return (value: number | null | undefined): string => {
    if (value === null || value === undefined) {
      return '—'
    }
    if (value >= 1000) {
      return `${formatNumber(value / 1000, {
        maximumFractionDigits: 1,
      })} km`
    }
    return `${formatNumber(value, { maximumFractionDigits: 0 })} m`
  }
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return '—'
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat('en-SG', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(parsed)
}

// ============================================================================
// Card Builders
// ============================================================================

function buildLocationCard(
  capturedProperty: SiteAcquisitionResult,
  formatNumber: NumberFormatter,
): PropertyOverviewCard {
  const info = capturedProperty.propertyInfo
  return {
    title: 'Location & tenure',
    items: [
      {
        label: 'Address',
        value: capturedProperty.address.fullAddress || '—',
      },
      {
        label: 'District',
        value: capturedProperty.address.district || '—',
      },
      {
        label: 'Tenure',
        value: info?.tenure ?? '—',
      },
      {
        label: 'Completion year',
        value: info?.completionYear
          ? formatNumber(info.completionYear, { maximumFractionDigits: 0 })
          : '—',
      },
    ],
  }
}

function buildEnvelopeCard(
  capturedProperty: SiteAcquisitionResult,
  formatNumber: NumberFormatter,
): PropertyOverviewCard {
  const envelope = capturedProperty.buildEnvelope
  const formatArea = createAreaFormatter(formatNumber)
  const formatPlotRatio = createPlotRatioFormatter(formatNumber)

  return {
    title: 'Build envelope',
    subtitle: envelope.zoneDescription ?? envelope.zoneCode ?? 'Zoning envelope preview',
    items: [
      { label: 'Zone code', value: envelope.zoneCode ?? '—' },
      {
        label: 'Allowable plot ratio',
        value: formatPlotRatio(envelope.allowablePlotRatio),
      },
      { label: 'Site area', value: formatArea(envelope.siteAreaSqm) },
      {
        label: 'Max buildable GFA',
        value: formatArea(envelope.maxBuildableGfaSqm),
      },
      {
        label: 'Current GFA',
        value: formatArea(envelope.currentGfaSqm),
      },
      {
        label: 'Additional potential',
        value: formatArea(envelope.additionalPotentialGfaSqm),
      },
    ],
    note: envelope.assumptions?.length ? envelope.assumptions[0] : null,
  }
}

function buildHeritageCard(
  capturedProperty: SiteAcquisitionResult,
  formatNumber: NumberFormatter,
): PropertyOverviewCard | null {
  const heritageContext = capturedProperty.heritageContext
  if (!heritageContext) {
    return null
  }

  const riskLabel = heritageContext.risk
    ? heritageContext.risk.toUpperCase()
    : 'UNKNOWN'
  const overlay = heritageContext.overlay

  const heritageItems: Array<{ label: string; value: string }> = [
    {
      label: 'Risk level',
      value: riskLabel,
    },
  ]

  if (overlay?.name) {
    heritageItems.push({ label: 'Overlay name', value: overlay.name })
  }
  if (overlay?.source) {
    heritageItems.push({ label: 'Source', value: overlay.source })
  }
  if (overlay?.heritagePremiumPct != null) {
    heritageItems.push({
      label: 'Premium (optimiser)',
      value: `${formatNumber(overlay.heritagePremiumPct, {
        maximumFractionDigits: overlay.heritagePremiumPct >= 100 ? 0 : 1,
      })}%`,
    })
  }
  if (heritageContext.constraints.length) {
    heritageItems.push({
      label: 'Key constraints',
      value: heritageContext.constraints.slice(0, 2).join(' • '),
    })
  }

  return {
    title: 'Heritage context',
    subtitle: overlay?.name ?? 'Heritage assessment',
    items: heritageItems,
    tags: heritageContext.flag ? [riskLabel] : undefined,
    note: heritageContext.assumption ?? heritageContext.notes[0] ?? null,
  }
}

function buildPreviewJobCard(
  previewJob: PreviewJob,
  formatTimestamp: TimestampFormatter,
): PropertyOverviewCard {
  const statusLabel = previewJob.status.toUpperCase()
  const statusLower = previewJob.status.toLowerCase()
  const previewItems: Array<{ label: string; value: string }> = [
    { label: 'Status', value: statusLabel },
    { label: 'Scenario', value: previewJob.scenario },
    {
      label: 'Requested',
      value: previewJob.requestedAt ? formatTimestamp(previewJob.requestedAt) : '—',
    },
  ]
  if (previewJob.startedAt) {
    previewItems.push({
      label: 'Started',
      value: formatTimestamp(previewJob.startedAt),
    })
  }
  if (previewJob.finishedAt) {
    previewItems.push({
      label: 'Finished',
      value: formatTimestamp(previewJob.finishedAt),
    })
  }
  if (previewJob.previewUrl) {
    previewItems.push({ label: 'Preview URL', value: previewJob.previewUrl })
  }
  if (previewJob.metadataUrl) {
    previewItems.push({ label: 'Metadata', value: previewJob.metadataUrl })
  }
  if (previewJob.thumbnailUrl) {
    previewItems.push({ label: 'Thumbnail', value: previewJob.thumbnailUrl })
  }
  if (previewJob.assetVersion) {
    previewItems.push({ label: 'Asset version', value: previewJob.assetVersion })
  }
  if (previewJob.message) {
    previewItems.push({ label: 'Notes', value: previewJob.message })
  }

  let previewNote: string | null = previewJob.message ?? null
  if (!previewNote) {
    if (statusLower === 'ready') {
      previewNote = 'Concept mesh ready for review.'
    } else if (statusLower === 'failed') {
      previewNote = 'Preview generation failed — try refreshing.'
    } else if (statusLower === 'expired') {
      previewNote = 'Preview expired — refresh to regenerate assets.'
    } else {
      previewNote = 'Preview job processing — status updates every few seconds.'
    }
  }

  return {
    title: 'Preview generation',
    subtitle: `Job ${previewJob.id.slice(0, 8)}…`,
    items: previewItems,
    tags: [statusLabel],
    note: previewNote,
  }
}

function buildAssetMixCard(
  optimizations: DeveloperAssetOptimization[],
  formatNumber: NumberFormatter,
  currencySymbol: string = 'S$',
): PropertyOverviewCard | null {
  if (optimizations.length === 0) {
    return null
  }

  const formatAllocation = (plan: DeveloperAssetOptimization) => {
    const segments: string[] = [
      `${formatNumber(plan.allocationPct, { maximumFractionDigits: 0 })}%`,
    ]
    if (plan.allocatedGfaSqm != null) {
      segments.push(
        `${formatNumber(
          plan.allocatedGfaSqm >= 1000
            ? plan.allocatedGfaSqm / 1000
            : plan.allocatedGfaSqm,
          {
            maximumFractionDigits: plan.allocatedGfaSqm >= 1000 ? 1 : 0,
          },
        )}${plan.allocatedGfaSqm >= 1000 ? 'k' : ''} sqm`,
      )
    }
    if (plan.niaEfficiency != null) {
      segments.push(
        `NIA ${formatNumber(plan.niaEfficiency * 100, {
          maximumFractionDigits: plan.niaEfficiency * 100 >= 100 ? 0 : 1,
        })}%`,
      )
    }
    if (plan.targetFloorHeightM != null) {
      segments.push(
        `${formatNumber(plan.targetFloorHeightM, {
          maximumFractionDigits: 1,
        })} m floor height`,
      )
    }
    if (plan.parkingRatioPer1000Sqm != null) {
      segments.push(
        `${formatNumber(plan.parkingRatioPer1000Sqm, {
          maximumFractionDigits: 1,
        })} lots / 1,000 sqm`,
      )
    }
    if (plan.estimatedRevenueSgd != null && plan.estimatedRevenueSgd > 0) {
      segments.push(
        `Rev ≈ ${currencySymbol}${formatNumber(plan.estimatedRevenueSgd / 1_000_000, {
          maximumFractionDigits: 1,
        })}M`,
      )
    }
    if (plan.estimatedCapexSgd != null && plan.estimatedCapexSgd > 0) {
      segments.push(
        `CAPEX ≈ ${currencySymbol}${formatNumber(plan.estimatedCapexSgd / 1_000_000, {
          maximumFractionDigits: 1,
        })}M`,
      )
    }
    if (plan.riskLevel) {
      const riskLabel = `${plan.riskLevel.charAt(0).toUpperCase()}${plan.riskLevel.slice(1)}`
      segments.push(
        `${riskLabel} risk${
          plan.absorptionMonths
            ? ` · ~${formatNumber(plan.absorptionMonths, { maximumFractionDigits: 0 })}m absorption`
            : ''
        }`,
      )
    }
    return segments.join(' • ')
  }

  return {
    title: 'Recommended asset mix',
    subtitle: 'Initial allocation guidance',
    items: optimizations.map((plan) => ({
      label: plan.assetType,
      value: formatAllocation(plan),
    })),
    note:
      optimizations.find((plan) => plan.notes.length)?.notes[0] ??
      'Adjust allocations as feasibility modelling matures.',
  }
}

function buildFinancialCard(
  capturedProperty: SiteAcquisitionResult,
  formatNumber: NumberFormatter,
  currencySymbol: string = 'S$',
): PropertyOverviewCard {
  const financialSummary = capturedProperty.financialSummary
  const financeNote =
    financialSummary.notes.length > 0
      ? financialSummary.notes[0]
      : 'Sync with finance modelling to validate programme-level cash flows.'

  const financialItems: Array<{ label: string; value: string }> = [
    {
      label: 'Total estimated revenue',
      value:
        financialSummary.totalEstimatedRevenueSgd != null
          ? `${currencySymbol}${formatNumber(
              financialSummary.totalEstimatedRevenueSgd / 1_000_000,
              { maximumFractionDigits: 1 },
            )}M`
          : '—',
    },
    {
      label: 'Total estimated capex',
      value:
        financialSummary.totalEstimatedCapexSgd != null
          ? `${currencySymbol}${formatNumber(
              financialSummary.totalEstimatedCapexSgd / 1_000_000,
              { maximumFractionDigits: 1 },
            )}M`
          : '—',
    },
    {
      label: 'Dominant risk',
      value:
        financialSummary.dominantRiskProfile
          ? financialSummary.dominantRiskProfile.replace('_', ' ')
          : '—',
    },
  ]

  const financeBlueprint = financialSummary.financeBlueprint
  if (financeBlueprint?.capitalStructure.length) {
    const baseScenario =
      financeBlueprint.capitalStructure.find((entry) => entry.scenario === 'Base Case') ??
      financeBlueprint.capitalStructure[0]
    financialItems.push({
      label: 'Capital stack (base)',
      value: `${formatNumber(baseScenario.debtPct, {
        maximumFractionDigits: 0,
      })}% debt / ${formatNumber(baseScenario.equityPct, {
        maximumFractionDigits: 0,
      })}% equity`,
    })
  }
  if (financeBlueprint?.debtFacilities.length) {
    const constructionLoan = financeBlueprint.debtFacilities.find(
      (facility) => facility.facilityType.toLowerCase().includes('construction'),
    )
    if (constructionLoan) {
      financialItems.push({
        label: 'Construction loan rate',
        value: constructionLoan.interestRate,
      })
    }
  }

  return {
    title: 'Financial snapshot',
    subtitle: 'Optimisation-derived rollup',
    items: financialItems,
    note: financeNote,
  }
}

function buildVisualizationCard(
  capturedProperty: SiteAcquisitionResult,
  colorLegendEntries: DeveloperColorLegendEntry[],
  formatNumber: NumberFormatter,
): PropertyOverviewCard | null {
  const visualization = capturedProperty.visualization ?? {
    status: 'placeholder',
    previewAvailable: false,
    notes: [],
    conceptMeshUrl: null,
    previewMetadataUrl: null,
    thumbnailUrl: null,
    cameraOrbitHint: null,
    previewSeed: null,
    previewJobId: null,
    massingLayers: [],
    colorLegend: [],
  }

  const visualizationItems: Array<{ label: string; value: string }> = [
    {
      label: 'Preview status',
      value: visualization.previewAvailable
        ? 'High-fidelity preview ready'
        : 'Waiting on Phase 2B visuals',
    },
    {
      label: 'Status flag',
      value: visualization.status ? visualization.status.replace(/_/g, ' ') : 'Pending',
    },
    {
      label: 'Concept mesh',
      value: visualization.conceptMeshUrl ?? 'Stub not generated yet',
    },
    {
      label: 'Camera orbit hint',
      value: visualization.cameraOrbitHint
        ? `${formatNumber(visualization.cameraOrbitHint.theta ?? 0, {
            maximumFractionDigits: 0,
          })}° / ${formatNumber(visualization.cameraOrbitHint.phi ?? 0, {
            maximumFractionDigits: 0,
          })}°`
        : '—',
    },
  ]

  if (visualization.massingLayers?.length > 0) {
    const primaryLayer = visualization.massingLayers[0]
    const layerLabel = primaryLayer.assetType
      .replace(/[_-]/g, ' ')
      .replace(/\b\w/g, (match) => match.toUpperCase())
    const heightValue =
      primaryLayer.estimatedHeightM != null
        ? `${formatNumber(primaryLayer.estimatedHeightM, {
            maximumFractionDigits: 0,
          })} m`
        : '—'
    visualizationItems.push({
      label: 'Primary massing',
      value: `${layerLabel} · ${heightValue}`,
    })
  }

  if (colorLegendEntries.length > 0) {
    const legendPreview = colorLegendEntries
      .slice(0, 3)
      .map((entry) => entry.label)
      .join(', ')
    visualizationItems.push({
      label: 'Colour legend',
      value: legendPreview || '—',
    })
  }

  return {
    title: 'Visualization readiness',
    subtitle: visualization.previewAvailable ? 'Preview ready' : 'Preview in progress',
    items: visualizationItems,
    note: visualization.notes?.length ? visualization.notes[0] : null,
  }
}

function buildSiteMetricsCard(
  capturedProperty: SiteAcquisitionResult,
  formatNumber: NumberFormatter,
): PropertyOverviewCard {
  const info = capturedProperty.propertyInfo
  const zoning = capturedProperty.uraZoning
  const formatArea = createAreaFormatter(formatNumber)
  const formatHeight = createHeightFormatter(formatNumber)
  const formatPlotRatio = createPlotRatioFormatter(formatNumber)

  return {
    title: 'Site metrics',
    items: [
      { label: 'Site area', value: formatArea(info?.siteAreaSqm) },
      { label: 'Approved GFA', value: formatArea(info?.gfaApproved) },
      { label: 'Building height', value: formatHeight(info?.buildingHeight) },
      {
        label: 'Plot ratio',
        value: formatPlotRatio(zoning?.plotRatio),
      },
    ],
  }
}

function buildZoningCard(
  capturedProperty: SiteAcquisitionResult,
  formatNumber: NumberFormatter,
): PropertyOverviewCard {
  const zoning = capturedProperty.uraZoning
  const formatHeight = createHeightFormatter(formatNumber)
  const formatSiteCoverage = createSiteCoverageFormatter(formatNumber)

  return {
    title: 'Zoning & planning',
    subtitle:
      zoning?.zoneDescription ?? zoning?.zoneCode ?? 'Zoning details unavailable',
    items: [
      {
        label: 'Building height limit',
        value: formatHeight(zoning?.buildingHeightLimit),
      },
      {
        label: 'Site coverage',
        value:
          zoning?.siteCoverage !== null && zoning?.siteCoverage !== undefined
            ? formatSiteCoverage(zoning.siteCoverage)
            : '—',
      },
      {
        label: 'Special conditions',
        value: zoning?.specialConditions ?? '—',
      },
    ],
    tags: zoning?.useGroups ?? [],
  }
}

function buildMarketCard(
  capturedProperty: SiteAcquisitionResult,
  formatNumber: NumberFormatter,
  formatCurrency: CurrencyFormatter,
): PropertyOverviewCard {
  const info = capturedProperty.propertyInfo
  const formatDistance = createDistanceFormatter(formatNumber)
  const nearestMrtStation = capturedProperty.nearbyAmenities?.mrtStations?.[0] ?? null
  const nearestBusStop = capturedProperty.nearbyAmenities?.busStops?.[0] ?? null

  return {
    title: 'Market & connectivity',
    items: [
      {
        label: 'Existing use',
        value:
          capturedProperty.existingUse && capturedProperty.existingUse.trim()
            ? capturedProperty.existingUse
            : '—',
      },
      {
        label: 'Last transaction',
        value:
          info?.lastTransactionDate || info?.lastTransactionPrice
            ? [
                formatDate(info?.lastTransactionDate),
                info?.lastTransactionPrice
                  ? formatCurrency(info.lastTransactionPrice)
                  : null,
              ]
                .filter(Boolean)
                .join(' · ')
            : '—',
      },
      {
        label: 'Nearest MRT',
        value: nearestMrtStation
          ? `${nearestMrtStation.name} (${formatDistance(nearestMrtStation.distanceM)})`
          : '—',
      },
      {
        label: 'Nearest bus stop',
        value: nearestBusStop
          ? `${nearestBusStop.name} (${formatDistance(nearestBusStop.distanceM)})`
          : '—',
      },
    ],
    note: `Lat ${formatNumber(capturedProperty.coordinates.latitude, {
      maximumFractionDigits: 6,
    })}, Lon ${formatNumber(capturedProperty.coordinates.longitude, {
      maximumFractionDigits: 6,
    })}`,
  }
}

// ============================================================================
// Main Export
// ============================================================================

/**
 * Build all property overview cards from captured property data
 *
 * This is a pure function that takes property data and formatters,
 * returning an array of card data structures for display.
 */
export function buildPropertyOverviewCards(
  context: CardBuilderContext,
): PropertyOverviewCard[] {
  const {
    capturedProperty,
    // These can be passed for optimization or derived from capturedProperty
    propertyInfoSummary: _propertyInfoSummary,
    zoningSummary: _zoningSummary,
    nearestMrtStation: _nearestMrtStation,
    nearestBusStop: _nearestBusStop,
    previewJob,
    colorLegendEntries,
    formatters,
    currencySymbol: contextCurrencySymbol,
  } = context
  const { formatNumber, formatCurrency, formatTimestamp } = formatters
  // Get currency symbol from context or capturedProperty, defaulting to S$
  const currencySymbol =
    contextCurrencySymbol ?? capturedProperty.currencySymbol ?? 'S$'

  const cards: PropertyOverviewCard[] = []

  // Location & tenure
  cards.push(buildLocationCard(capturedProperty, formatNumber))

  // Build envelope
  cards.push(buildEnvelopeCard(capturedProperty, formatNumber))

  // Heritage context (optional)
  const heritageCard = buildHeritageCard(capturedProperty, formatNumber)
  if (heritageCard) {
    cards.push(heritageCard)
  }

  // Preview job (optional)
  if (previewJob) {
    cards.push(buildPreviewJobCard(previewJob, formatTimestamp))
  }

  // Asset mix (optional)
  const assetMixCard = buildAssetMixCard(
    capturedProperty.optimizations ?? [],
    formatNumber,
    currencySymbol,
  )
  if (assetMixCard) {
    cards.push(assetMixCard)
  }

  // Financial snapshot
  cards.push(buildFinancialCard(capturedProperty, formatNumber, currencySymbol))

  // Visualization readiness
  const visualizationCard = buildVisualizationCard(
    capturedProperty,
    colorLegendEntries,
    formatNumber,
  )
  if (visualizationCard) {
    cards.push(visualizationCard)
  }

  // Site metrics
  cards.push(buildSiteMetricsCard(capturedProperty, formatNumber))

  // Zoning & planning
  cards.push(buildZoningCard(capturedProperty, formatNumber))

  // Market & connectivity
  cards.push(buildMarketCard(capturedProperty, formatNumber, formatCurrency))

  return cards
}
