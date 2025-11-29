/**
 * Feasibility signal builders
 *
 * Pure functions for analyzing scenario metrics and generating
 * opportunities/risks signals. These are used to provide quick
 * insights based on scenario type and property data.
 */

import type { QuickAnalysisEntry, FeasibilitySignals } from '../types'
import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import { safeNumber } from './formatters'
import type { NumberFormatter } from './cardBuilders'

// ============================================================================
// Types
// ============================================================================

export interface FeasibilitySignalsContext {
  /** The quick analysis entry to evaluate */
  entry: QuickAnalysisEntry
  /** Captured property data (optional, provides envelope/optimization context) */
  capturedProperty?: SiteAcquisitionResult | null
  /** Number formatter function */
  formatNumber: NumberFormatter
}

// ============================================================================
// Per-Scenario Signal Builders
// ============================================================================

function buildRawLandSignals(
  entry: QuickAnalysisEntry,
  capturedProperty: SiteAcquisitionResult | null | undefined,
  formatNumber: NumberFormatter,
): FeasibilitySignals {
  const opportunities: string[] = []
  const risks: string[] = []
  const metrics = entry.metrics ?? {}

  const potentialGfa = safeNumber(metrics['potential_gfa_sqm'])
  const siteArea = safeNumber(metrics['site_area_sqm'])
  const plotRatio = safeNumber(metrics['plot_ratio'])

  if (potentialGfa && siteArea) {
    opportunities.push(
      `Potential GFA of ${formatNumber(potentialGfa, {
        maximumFractionDigits: 0,
      })} sqm`,
    )
  }
  if (!plotRatio) {
    risks.push('Plot ratio unavailable — confirm URA control parameters.')
  }
  if (!siteArea) {
    risks.push('Site area missing — gather survey or title data.')
  }

  if (capturedProperty?.buildEnvelope) {
    const { maxBuildableGfaSqm, additionalPotentialGfaSqm, allowablePlotRatio } =
      capturedProperty.buildEnvelope
    if (maxBuildableGfaSqm) {
      opportunities.push(
        `Zoning envelope supports ≈ ${formatNumber(maxBuildableGfaSqm, {
          maximumFractionDigits: 0,
        })} sqm of GFA.`,
      )
    }
    if (additionalPotentialGfaSqm && additionalPotentialGfaSqm > 0) {
      opportunities.push(
        `Estimated uplift of ${formatNumber(additionalPotentialGfaSqm, {
          maximumFractionDigits: 0,
        })} sqm available under current controls.`,
      )
    } else if (additionalPotentialGfaSqm !== null && additionalPotentialGfaSqm !== undefined) {
      risks.push('No additional GFA headroom — optimisation required before submission.')
    }
    if (!plotRatio && allowablePlotRatio) {
      opportunities.push(
        `Plot ratio cap ${formatNumber(allowablePlotRatio, {
          maximumFractionDigits: 2,
        })} still allows refinement.`,
      )
    }
  }

  return { opportunities, risks }
}

function buildExistingBuildingSignals(
  entry: QuickAnalysisEntry,
  formatNumber: NumberFormatter,
): FeasibilitySignals {
  const opportunities: string[] = []
  const risks: string[] = []
  const metrics = entry.metrics ?? {}

  const uplift = safeNumber(metrics['gfa_uplift_sqm'])
  const averagePsf = safeNumber(metrics['average_psf_price'])

  if (uplift && uplift > 0) {
    opportunities.push(
      `Unlock ≈ ${formatNumber(uplift, {
        maximumFractionDigits: 0,
      })} sqm of additional GFA.`,
    )
  } else {
    risks.push('Limited GFA uplift — focus on retrofit efficiency.')
  }
  if (!averagePsf) {
    risks.push('No recent transaction comps — check market data sources.')
  }

  return { opportunities, risks }
}

function buildHeritagePropertySignals(entry: QuickAnalysisEntry): FeasibilitySignals {
  const opportunities: string[] = []
  const risks: string[] = []
  const metrics = entry.metrics ?? {}

  const heritageRisk = (metrics['heritage_risk'] ?? '').toString().toLowerCase()
  if (heritageRisk === 'high') {
    risks.push('High heritage risk — expect conservation dialogue.')
  } else if (heritageRisk === 'medium') {
    risks.push('Moderate heritage constraints — document mitigation plan.')
  } else {
    opportunities.push('Heritage considerations manageable based on current data.')
  }

  return { opportunities, risks }
}

function buildUnderusedAssetSignals(
  entry: QuickAnalysisEntry,
  formatNumber: NumberFormatter,
): FeasibilitySignals {
  const opportunities: string[] = []
  const risks: string[] = []
  const metrics = entry.metrics ?? {}

  const mrtCount = safeNumber(metrics['nearby_mrt_count'])
  const averageRent = safeNumber(metrics['average_monthly_rent'])
  const buildingHeight = safeNumber(metrics['building_height_m'])

  if (mrtCount && mrtCount > 0) {
    opportunities.push(`${mrtCount} MRT stations support reuse potential.`)
  } else {
    risks.push('Limited transit access — budget for last-mile improvements.')
  }
  if (buildingHeight && buildingHeight < 20) {
    opportunities.push('Low-rise profile — vertical expansion is feasible.')
  }
  if (!averageRent) {
    risks.push('Missing rental comps — collect updated leasing benchmarks.')
  }

  // formatNumber is available for future use but not currently needed
  void formatNumber

  return { opportunities, risks }
}

function buildMixedUseSignals(
  entry: QuickAnalysisEntry,
  formatNumber: NumberFormatter,
): FeasibilitySignals {
  const opportunities: string[] = []
  const risks: string[] = []
  const metrics = entry.metrics ?? {}

  const plotRatio = safeNumber(metrics['plot_ratio'])
  const useGroups = Array.isArray(metrics['use_groups'])
    ? (metrics['use_groups'] as string[])
    : []

  if (plotRatio && plotRatio > 0) {
    opportunities.push(`Zoning plot ratio ${plotRatio} supports higher density.`)
  }
  if (useGroups.length) {
    opportunities.push(`Permitted uses include: ${useGroups.join(', ')}.`)
  }
  if (!plotRatio) {
    risks.push('Plot ratio not defined — confirm with URA before design.')
  }

  // formatNumber is available for future use but not currently needed
  void formatNumber

  return { opportunities, risks }
}

function buildDefaultSignals(entry: QuickAnalysisEntry): FeasibilitySignals {
  const opportunities: string[] = []
  const risks: string[] = []

  if (entry.notes.length) {
    opportunities.push(...entry.notes)
  }

  return { opportunities, risks }
}

// ============================================================================
// Main Builder Function
// ============================================================================

/**
 * Build feasibility signals (opportunities and risks) for a quick analysis entry.
 *
 * This is a pure function that analyzes the scenario type and metrics to generate
 * actionable insights. It does not modify any state.
 *
 * @param context - The analysis entry, optional captured property, and formatter
 * @returns Object containing opportunities and risks arrays
 */
export function buildFeasibilitySignals(context: FeasibilitySignalsContext): FeasibilitySignals {
  const { entry, capturedProperty, formatNumber } = context

  let signals: FeasibilitySignals

  switch (entry.scenario) {
    case 'raw_land':
      signals = buildRawLandSignals(entry, capturedProperty, formatNumber)
      break
    case 'existing_building':
      signals = buildExistingBuildingSignals(entry, formatNumber)
      break
    case 'heritage_property':
      signals = buildHeritagePropertySignals(entry)
      break
    case 'underused_asset':
      signals = buildUnderusedAssetSignals(entry, formatNumber)
      break
    case 'mixed_use_redevelopment':
      signals = buildMixedUseSignals(entry, formatNumber)
      break
    default:
      signals = buildDefaultSignals(entry)
  }

  // Append optimization insight if available
  if (capturedProperty?.optimizations?.length) {
    const lead = capturedProperty.optimizations[0]
    const mixLabel = lead.assetType.replace(/_/g, ' ')
    signals.opportunities.push(
      `${mixLabel.charAt(0).toUpperCase()}${mixLabel.slice(1)} holds ${formatNumber(lead.allocationPct, {
        maximumFractionDigits: 0,
      })}% of the suggested programme, aligning with the current envelope.`,
    )
  }

  return signals
}
