/**
 * Pure functions for building property overview card data
 *
 * These functions have no side effects and return structured data for display.
 */

import type {
  SiteAcquisitionResult,
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

// ============================================================================
// Card Builders
// ============================================================================

function buildLocationCard(
  capturedProperty: SiteAcquisitionResult,
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
        value: info?.completionYear ? String(info.completionYear) : '—',
      },
    ],
  }
}

function buildEnvelopeCard(
  capturedProperty: SiteAcquisitionResult,
  formatNumber: NumberFormatter,
): PropertyOverviewCard {
  const envelope = capturedProperty.buildEnvelope
  const info = capturedProperty.propertyInfo
  const formatArea = createAreaFormatter(formatNumber)
  const formatPlotRatio = createPlotRatioFormatter(formatNumber)
  const formatHeight = createHeightFormatter(formatNumber)
  const formatSiteCoverage = createSiteCoverageFormatter(formatNumber)

  // Use envelope height limit if available, otherwise fall back to property info
  const heightValue =
    envelope.buildingHeightLimitM ?? info?.buildingHeight ?? null

  // Build note: prefer source reference, then first assumption
  let noteText: string | null = null
  if (envelope.sourceReference) {
    noteText = `Source: ${envelope.sourceReference}`
  } else if (envelope.assumptions?.length) {
    noteText = envelope.assumptions[0]
  }

  const currentGfa = envelope.currentGfaSqm
  const maxGfa = envelope.maxBuildableGfaSqm
  const hasCurrentAndMax =
    currentGfa !== null &&
    currentGfa !== undefined &&
    maxGfa !== null &&
    maxGfa !== undefined

  let gfaRelationshipValue = '—'
  let gfaReadingValue = '—'
  let additionalPotentialValue = formatArea(envelope.additionalPotentialGfaSqm)

  if (hasCurrentAndMax) {
    const comparisonSymbol =
      currentGfa > maxGfa ? '>' : currentGfa < maxGfa ? '<' : '='
    gfaRelationshipValue = `${formatArea(currentGfa)} ${comparisonSymbol} ${formatArea(maxGfa)}`

    if (currentGfa > maxGfa) {
      gfaReadingValue = 'Likely grandfathered from a former code baseline'
      additionalPotentialValue = 'No current code-compliant uplift'
    } else if (currentGfa < maxGfa) {
      gfaReadingValue = 'Existing bulk remains below today’s envelope'
    } else {
      gfaReadingValue = 'Existing bulk matches today’s envelope'
    }
  }

  return {
    title: 'Build envelope',
    subtitle:
      envelope.zoneDescription ??
      envelope.zoneCode ??
      'Zoning envelope preview',
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
        label: 'Current vs max GFA',
        value: gfaRelationshipValue,
      },
      {
        label: 'Envelope reading',
        value: gfaReadingValue,
      },
      {
        label: 'Additional potential',
        value: additionalPotentialValue,
      },
      {
        label: 'Building height limit',
        value: formatHeight(heightValue),
      },
      {
        label: 'Site coverage',
        value: formatSiteCoverage(envelope.siteCoveragePct),
      },
    ],
    note: noteText,
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
  const previewItems: Array<{ label: string; value: string }> = []
  previewItems.push({ label: 'Status', value: statusLabel })
  previewItems.push({ label: 'Scenario', value: previewJob.scenario })
  previewItems.push({
    label: 'Requested',
    value: previewJob.requestedAt
      ? formatTimestamp(previewJob.requestedAt)
      : '—',
  })
  if (previewJob.finishedAt) {
    previewItems.push({
      label: 'Completed',
      value: formatTimestamp(previewJob.finishedAt),
    })
  }
  const assetLabels = [
    previewJob.previewUrl ? 'mesh' : null,
    previewJob.metadataUrl ? 'metadata' : null,
    previewJob.thumbnailUrl ? 'thumbnail' : null,
  ].filter(Boolean)
  if (assetLabels.length > 0) {
    previewItems.push({
      label: 'Assets returned',
      value: assetLabels.join(', '),
    })
  }
  if (previewJob.assetVersion) {
    previewItems.push({
      label: 'Asset version',
      value: previewJob.assetVersion,
    })
  }
  if (previewJob.message) {
    previewItems.push({ label: 'Notes', value: previewJob.message })
  }

  let previewNote: string | null = previewJob.message ?? null
  if (!previewNote) {
    if (statusLower === 'ready') {
      previewNote = 'Concept mesh ready for review.'
    } else if (statusLower === 'failed') {
      previewNote = 'Preview request failed — try refreshing status.'
    } else if (statusLower === 'expired') {
      previewNote = 'Preview expired — refresh to regenerate assets.'
    } else {
      previewNote = 'Preview job processing — status updates every few seconds.'
    }
  }

  return {
    title: 'Preview Job Status',
    subtitle:
      statusLower === 'ready' ? 'Preview job completed' : 'Preview job summary',
    items: previewItems,
    tags: [statusLabel],
    note: previewNote,
    layout: 'status',
  }
}

function buildAnalysisStatusCard(
  capturedProperty: SiteAcquisitionResult,
  previewJob: PreviewJob | null,
): PropertyOverviewCard {
  const envelope = capturedProperty.buildEnvelope
  const visualization = capturedProperty.visualization
  const envelopeResolved = [
    envelope.zoneCode,
    envelope.allowablePlotRatio,
    envelope.maxBuildableGfaSqm,
    envelope.buildingHeightLimitM,
    envelope.siteCoveragePct,
  ].filter((value) => value !== null && value !== undefined).length
  const geometryStatus = previewJob?.status?.toLowerCase()
  const isPlaceholderGeometry =
    visualization.status.toLowerCase() === 'placeholder' ||
    (!visualization.previewAvailable &&
      !visualization.conceptMeshUrl &&
      !previewJob?.previewUrl)
  const envelopeMode =
    envelope.sourceReference || envelopeResolved >= 4
      ? 'Resolved scalar controls'
      : 'Derived scalar controls'

  return {
    title: 'Analysis status',
    subtitle: isPlaceholderGeometry
      ? 'Instant capture only'
      : 'Capture with preview job',
    items: [
      {
        label: 'Envelope completeness',
        value: `${envelopeResolved}/5 scalar controls`,
      },
      {
        label: 'Envelope mode',
        value: envelopeMode,
      },
      {
        label: 'Geometry status',
        value: isPlaceholderGeometry
          ? 'Placeholder only'
          : geometryStatus
            ? geometryStatus.replace(/_/g, ' ')
            : 'Pending',
      },
      {
        label: 'Compliance scope',
        value: 'No setbacks or floor-by-floor compliance',
      },
    ],
    note: 'Capture currently reports parcel-level zoning and build-envelope signals. Setbacks, step-backs, and floor-by-floor compliance remain out of scope here.',
    layout: 'status',
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
        ? 'Mesh ready'
        : visualization.status.toLowerCase() === 'placeholder'
          ? 'Placeholder only'
          : 'Queued / pending',
    },
    {
      label: 'Status flag',
      value: visualization.status
        ? visualization.status.replace(/_/g, ' ')
        : 'Pending',
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

  const assetBundle = [
    visualization.conceptMeshUrl ? 'Mesh' : null,
    visualization.previewMetadataUrl ? 'Metadata' : null,
    visualization.thumbnailUrl ? 'Thumbnail' : null,
  ].filter(Boolean)
  visualizationItems.push({
    label: 'Asset bundle',
    value:
      assetBundle.length > 0 ? assetBundle.join(' • ') : 'No preview assets',
  })

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
      label: 'Preview layer',
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
    title: 'Preview Availability',
    subtitle: visualization.previewAvailable
      ? 'Preview ready'
      : visualization.status.toLowerCase() === 'placeholder'
        ? 'Instant capture only'
        : 'Preview pending',
    items: visualizationItems,
    note: visualization.notes?.length ? visualization.notes[0] : null,
    tags: [visualization.status.toUpperCase()],
    layout: 'status',
  }
}

// buildSiteMetricsCard removed - data consolidated into buildEnvelopeCard
// Site area, GFA, plot ratio, and building height are now shown in Build Envelope card

function buildZoningCard(
  capturedProperty: SiteAcquisitionResult,
  formatNumber: NumberFormatter,
): PropertyOverviewCard {
  const zoning = capturedProperty.uraZoning
  const envelope = capturedProperty.buildEnvelope
  const planningItems: Array<{ label: string; value: string }> = []

  if (zoning?.plotRatio != null && envelope.allowablePlotRatio == null) {
    planningItems.push({
      label: 'Plot ratio',
      value: formatNumber(zoning.plotRatio, { maximumFractionDigits: 2 }),
    })
  }
  if (
    zoning?.buildingHeightLimit != null &&
    envelope.buildingHeightLimitM == null
  ) {
    planningItems.push({
      label: 'Building height limit',
      value: `${formatNumber(zoning.buildingHeightLimit, {
        maximumFractionDigits: 1,
      })} m`,
    })
  }
  if (zoning?.siteCoverage != null && envelope.siteCoveragePct == null) {
    planningItems.push({
      label: 'Site coverage',
      value: `${formatNumber(zoning.siteCoverage, {
        maximumFractionDigits: zoning.siteCoverage >= 100 ? 0 : 1,
      })}%`,
    })
  }
  planningItems.push({
    label: 'Special conditions',
    value: zoning?.specialConditions ?? '—',
  })

  return {
    title: 'Zoning & planning',
    subtitle:
      zoning?.zoneDescription ??
      zoning?.zoneCode ??
      'Zoning details unavailable',
    items: planningItems,
    tags: zoning?.useGroups ?? [],
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
  const { capturedProperty, previewJob, colorLegendEntries, formatters } =
    context
  const { formatNumber, formatTimestamp } = formatters

  const cards: PropertyOverviewCard[] = []

  // Location & tenure
  cards.push(buildLocationCard(capturedProperty))

  // Build envelope
  cards.push(buildEnvelopeCard(capturedProperty, formatNumber))

  // Heritage context (optional)
  const heritageCard = buildHeritageCard(capturedProperty, formatNumber)
  if (heritageCard) {
    cards.push(heritageCard)
  }

  cards.push(buildAnalysisStatusCard(capturedProperty, previewJob))

  // Visualization readiness
  const visualizationCard = buildVisualizationCard(
    capturedProperty,
    colorLegendEntries,
    formatNumber,
  )
  if (visualizationCard) {
    cards.push(visualizationCard)
  }

  // Preview job details (optional)
  if (previewJob) {
    cards.push(buildPreviewJobCard(previewJob, formatTimestamp))
  }

  // Site metrics card removed - data is now consolidated in Build Envelope card
  // (site area, GFA, plot ratio, building height)

  // Zoning & planning
  cards.push(buildZoningCard(capturedProperty, formatNumber))

  return cards
}
