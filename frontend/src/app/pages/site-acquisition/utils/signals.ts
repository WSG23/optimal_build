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
    const {
      maxBuildableGfaSqm,
      additionalPotentialGfaSqm,
      allowablePlotRatio,
      buildingHeightLimitM,
      siteCoveragePct,
    } = capturedProperty.buildEnvelope
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
    } else if (
      additionalPotentialGfaSqm !== null &&
      additionalPotentialGfaSqm !== undefined
    ) {
      risks.push(
        'No additional GFA headroom — optimisation required before submission.',
      )
    }
    if (!plotRatio && allowablePlotRatio) {
      opportunities.push(
        `Plot ratio cap ${formatNumber(allowablePlotRatio, {
          maximumFractionDigits: 2,
        })} still allows refinement.`,
      )
    }
    if (buildingHeightLimitM == null) {
      risks.push(
        'Height limit unresolved — capture currently reflects scalar envelope only.',
      )
    }
    if (siteCoveragePct == null) {
      risks.push(
        'Site coverage unresolved — confirm planning controls before massing.',
      )
    }
  }

  return { opportunities, risks }
}

function buildExistingBuildingSignals(
  entry: QuickAnalysisEntry,
  capturedProperty: SiteAcquisitionResult | null | undefined,
  formatNumber: NumberFormatter,
): FeasibilitySignals {
  const opportunities: string[] = []
  const risks: string[] = []
  const metrics = entry.metrics ?? {}

  const uplift =
    safeNumber(metrics['gfa_uplift_sqm']) ??
    capturedProperty?.buildEnvelope?.additionalPotentialGfaSqm
  const currentGfa = capturedProperty?.buildEnvelope?.currentGfaSqm

  if (uplift && uplift > 0) {
    opportunities.push(
      `Unlock ≈ ${formatNumber(uplift, {
        maximumFractionDigits: 0,
      })} sqm of additional GFA.`,
    )
  } else {
    risks.push(
      'Limited code headroom detected — validate retrofit scope against current approvals.',
    )
  }
  if (currentGfa && currentGfa > 0) {
    opportunities.push(
      `Existing approvals already cover ≈ ${formatNumber(currentGfa, {
        maximumFractionDigits: 0,
      })} sqm of GFA.`,
    )
  }
  if (capturedProperty?.buildEnvelope?.buildingHeightLimitM == null) {
    risks.push('Height limit unresolved — confirm current control envelope.')
  }
  if (capturedProperty?.buildEnvelope?.siteCoveragePct == null) {
    risks.push('Site coverage unresolved — scalar code controls still partial.')
  }

  return { opportunities, risks }
}

function buildHeritagePropertySignals(
  entry: QuickAnalysisEntry,
  capturedProperty: SiteAcquisitionResult | null | undefined,
): FeasibilitySignals {
  const opportunities: string[] = []
  const risks: string[] = []
  const metrics = entry.metrics ?? {}

  const heritageRisk = (metrics['heritage_risk'] ?? '').toString().toLowerCase()
  if (heritageRisk === 'high') {
    risks.push('High heritage risk — expect conservation dialogue.')
  } else if (heritageRisk === 'medium') {
    risks.push('Moderate heritage constraints — document mitigation plan.')
  } else {
    opportunities.push(
      'Heritage considerations manageable based on current data.',
    )
  }
  const overlayName = capturedProperty?.heritageContext?.overlay?.name
  if (overlayName) {
    opportunities.push(`Heritage overlay identified: ${overlayName}.`)
  }
  if (!capturedProperty?.heritageContext?.constraints?.length) {
    risks.push('Detailed conservation controls are not yet itemized in Capture.')
  }

  return { opportunities, risks }
}

function buildUnderusedAssetSignals(
  entry: QuickAnalysisEntry,
  capturedProperty: SiteAcquisitionResult | null | undefined,
  formatNumber: NumberFormatter,
): FeasibilitySignals {
  const opportunities: string[] = []
  const risks: string[] = []
  const metrics = entry.metrics ?? {}

  const uplift =
    safeNumber(metrics['gfa_uplift_sqm']) ??
    capturedProperty?.buildEnvelope?.additionalPotentialGfaSqm
  const buildingHeightLimit =
    safeNumber(metrics['building_height_limit_m']) ??
    capturedProperty?.buildEnvelope?.buildingHeightLimitM
  const siteCoverage =
    safeNumber(metrics['site_coverage_pct']) ??
    capturedProperty?.buildEnvelope?.siteCoveragePct

  if (uplift && uplift > 0) {
    opportunities.push(
      `Reuse path retains ≈ ${formatNumber(uplift, {
        maximumFractionDigits: 0,
      })} sqm of code headroom.`,
    )
  }
  if (buildingHeightLimit != null) {
    opportunities.push(
      `Height control currently resolves to ${formatNumber(buildingHeightLimit, {
        maximumFractionDigits: 0,
      })} m.`,
    )
  } else {
    risks.push('Height control unresolved — adaptive reuse massing is preliminary.')
  }
  if (siteCoverage != null) {
    opportunities.push(
      `Site coverage control at ${formatNumber(siteCoverage, {
        maximumFractionDigits: 0,
      })}% frames the reuse envelope.`,
    )
  } else {
    risks.push('Site coverage unavailable — confirm scalar controls before reuse studies.')
  }

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
    opportunities.push(
      `Zoning plot ratio ${formatNumber(plotRatio, {
        maximumFractionDigits: 2,
      })} supports higher density.`,
    )
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
export function buildFeasibilitySignals(
  context: FeasibilitySignalsContext,
): FeasibilitySignals {
  const { entry, capturedProperty, formatNumber } = context

  let signals: FeasibilitySignals

  switch (entry.scenario) {
    case 'raw_land':
      signals = buildRawLandSignals(entry, capturedProperty, formatNumber)
      break
    case 'existing_building':
      signals = buildExistingBuildingSignals(
        entry,
        capturedProperty,
        formatNumber,
      )
      break
    case 'heritage_property':
      signals = buildHeritagePropertySignals(entry, capturedProperty)
      break
    case 'underused_asset':
      signals = buildUnderusedAssetSignals(
        entry,
        capturedProperty,
        formatNumber,
      )
      break
    case 'mixed_use_redevelopment':
      signals = buildMixedUseSignals(entry, formatNumber)
      break
    default:
      signals = buildDefaultSignals(entry)
  }

  return signals
}
