/**
 * useStarterModelMemos - Extracted useMemo computations for starter model
 * display values, assumption lines, override notices, and recommendation labels.
 *
 * Extracted from DeveloperResults to reduce file size.
 */

import { useMemo } from 'react'

import type {
  CaptureResultV2,
  CaptureStarterModelV2,
} from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'

export type CaptureResultV2StarterModel = CaptureStarterModelV2 & {
  generatedFrom: string[]
}

export interface StarterModelAssumptionLine {
  label: string
  value: string
  sourceDetail: string | null
}

export interface StarterModelAssetProfileLine {
  label: string
  value: string
  sourceDetail: string | null
}

export interface StarterModelAssumptionBuckets {
  pinned: string[]
  tunable: string[]
}

export interface CaptureDataBasisItem {
  label: string
  value: string
  tone: 'success' | 'warning' | 'default'
}

interface PreviewJobLike {
  status: string
  previewUrl?: string | null
  metadataUrl?: string | null
  thumbnailUrl?: string | null
  starterModelAssumptions?: CaptureResultV2['engineeringAssumptions'] | null
}

interface UseStarterModelMemosOptions {
  captureResultV2: CaptureResultV2
  previewJob: PreviewJobLike | null
  isGeneratingStarterModel: boolean
  isRefreshingPreview: boolean
  hasPreferredScenarioPreview: boolean
  previewJobs: PreviewJobLike[] | undefined
  formatScenarioLabel: (scenario: DevelopmentScenario | 'all' | null) => string
  formatNumber: (value: number, options?: Intl.NumberFormatOptions) => string
}

const ASSUMPTION_FIELD_LABELS = new Map<string, string>([
  ['floor_to_floor_m', 'floor-to-floor'],
  ['clear_ceiling_m', 'clear ceiling'],
  ['wall_thickness_mm', 'wall thickness'],
  ['core_ratio_pct', 'core ratio'],
  ['common_area_ratio_pct', 'common area'],
  ['hvac_space_ratio_pct', 'HVAC'],
  ['electrical_space_ratio_pct', 'electrical'],
  ['retention_strategy', 'retention strategy'],
  ['efficiency_factor', 'efficiency factor'],
])

export function useStarterModelMemos({
  captureResultV2,
  previewJob,
  isGeneratingStarterModel,
  isRefreshingPreview,
  hasPreferredScenarioPreview,
  previewJobs,
  formatScenarioLabel,
  formatNumber,
}: UseStarterModelMemosOptions) {
  const effectiveStarterModel = useMemo(() => {
    const baseModel = captureResultV2.starterModel
    if (previewJob) {
      const rawStatus = previewJob.status.toLowerCase()
      const status =
        rawStatus === 'ready' ||
        rawStatus === 'failed' ||
        rawStatus === 'queued' ||
        rawStatus === 'processing' ||
        rawStatus === 'placeholder'
          ? rawStatus
          : baseModel.status
      return {
        ...baseModel,
        status,
        modelUrl: previewJob.previewUrl ?? baseModel.modelUrl,
        metadataUrl: previewJob.metadataUrl ?? baseModel.metadataUrl,
        thumbnailUrl: previewJob.thumbnailUrl ?? baseModel.thumbnailUrl,
        generatedFrom: Array.from(
          new Set(['preview_job', ...baseModel.generatedFrom]),
        ),
      }
    }

    if (isGeneratingStarterModel) {
      return {
        ...baseModel,
        status: 'processing' as const,
      }
    }

    return baseModel
  }, [captureResultV2.starterModel, isGeneratingStarterModel, previewJob])

  const defaultRecommendationLabel = useMemo(
    () =>
      formatScenarioLabel(
        captureResultV2.scenarioRecommendation.defaultRecommended,
      ),
    [
      captureResultV2.scenarioRecommendation.defaultRecommended,
      formatScenarioLabel,
    ],
  )

  const fallbackPreviewScenarioLabel = useMemo(() => {
    if (
      captureResultV2.scenarioRecommendation.userOverride &&
      !hasPreferredScenarioPreview
    ) {
      return defaultRecommendationLabel
    }
    return formatScenarioLabel(
      captureResultV2.scenarioRecommendation.recommended,
    )
  }, [
    captureResultV2.scenarioRecommendation.recommended,
    captureResultV2.scenarioRecommendation.userOverride,
    defaultRecommendationLabel,
    formatScenarioLabel,
    hasPreferredScenarioPreview,
  ])

  const starterModelStatusSummary = useMemo(() => {
    const scenarioLabel = formatScenarioLabel(
      captureResultV2.scenarioRecommendation.recommended,
    )
    switch (effectiveStarterModel.status) {
      case 'queued':
        return `A ${scenarioLabel.toLowerCase()} starter model has been queued. Capture will replace the fallback preview when the render is ready.`
      case 'processing':
        return `Capture is generating the ${scenarioLabel.toLowerCase()} starter model now.`
      case 'ready':
        return hasPreferredScenarioPreview
          ? `The ${scenarioLabel.toLowerCase()} starter model is ready for review.`
          : `The ${scenarioLabel.toLowerCase()} starter model is not ready yet. Capture is still showing the ${fallbackPreviewScenarioLabel.toLowerCase()} preview until a scenario-specific model is available.`
      case 'failed':
        return `Capture could not generate the ${scenarioLabel.toLowerCase()} starter model yet. Retry generation from this panel.`
      case 'placeholder':
      default:
        return 'No scenario-specific starter model is available yet. Capture is currently showing the best available fallback preview.'
    }
  }, [
    captureResultV2.scenarioRecommendation.recommended,
    effectiveStarterModel.status,
    fallbackPreviewScenarioLabel,
    formatScenarioLabel,
    hasPreferredScenarioPreview,
  ])

  const effectiveEngineeringAssumptions = useMemo(
    () =>
      previewJob?.starterModelAssumptions ??
      captureResultV2.engineeringAssumptions,
    [
      captureResultV2.engineeringAssumptions,
      previewJob?.starterModelAssumptions,
    ],
  )

  const scenarioFitSummary = useMemo(() => {
    const codeConstraints = captureResultV2.codeConstraints
    const comparisonSummary =
      codeConstraints.currentVsCodeStatus === 'above'
        ? 'Current GFA exceeds today\u2019s code envelope and may reflect a grandfathered condition.'
        : codeConstraints.currentVsCodeStatus === 'below'
          ? 'Current GFA remains below today\u2019s code envelope, leaving compliant headroom to study.'
          : codeConstraints.currentVsCodeStatus === 'at_limit'
            ? 'Current GFA appears to match today\u2019s code envelope.'
            : 'Current-versus-code envelope relationship is still unresolved.'

    const headroomSummary =
      codeConstraints.maxBuildableGfaSqm != null &&
      codeConstraints.currentGfaSqm != null
        ? `${formatNumber(codeConstraints.currentGfaSqm, {
            maximumFractionDigits: 0,
          })} sqm current vs ${formatNumber(
            codeConstraints.maxBuildableGfaSqm,
            {
              maximumFractionDigits: 0,
            },
          )} sqm current-code max.`
        : 'Current and maximum GFA comparison is still pending.'

    const heritageSummary = captureResultV2.siteContext.heritageOverlay
      ? `Context: ${captureResultV2.siteContext.heritageOverlay}.`
      : 'No heritage overlay is currently driving the starter model.'

    return {
      comparisonSummary,
      headroomSummary,
      heritageSummary,
    }
  }, [
    captureResultV2.codeConstraints,
    captureResultV2.siteContext,
    formatNumber,
  ])

  const captureDataBasis = useMemo((): CaptureDataBasisItem[] => {
    const items: CaptureDataBasisItem[] = [
      {
        label: 'Site input',
        value: 'Address and coordinates are site-specific.',
        tone: 'success',
      },
    ]

    const sourceReference = captureResultV2.codeConstraints.sourceReference
    if (!sourceReference) {
      items.push({
        label: 'Envelope source',
        value: 'Zoning envelope source is unresolved.',
        tone: 'warning',
      })
    } else if (/mock data|fallback|no refrule/i.test(sourceReference)) {
      items.push({
        label: 'Envelope source',
        value: sourceReference,
        tone: 'warning',
      })
    } else {
      items.push({
        label: 'Envelope source',
        value: sourceReference,
        tone: 'success',
      })
    }

    const unresolvedCount = captureResultV2.analysisStatus.missingInputs.length
    items.push({
      label: 'Rule coverage',
      value:
        unresolvedCount > 0
          ? `${unresolvedCount} control areas still unresolved (${captureResultV2.analysisStatus.missingInputs.slice(0, 3).join(', ')}${unresolvedCount > 3 ? ', …' : ''}).`
          : 'Core rule controls resolved for this capture.',
      tone: unresolvedCount > 0 ? 'warning' : 'success',
    })

    items.push({
      label: 'Geometry',
      value:
        effectiveStarterModel.status === 'ready' &&
        effectiveStarterModel.generatedFrom.includes('preview_job')
          ? 'Scenario-specific starter model is generated from the preview pipeline.'
          : 'Geometry is still preliminary and may rely on fallback or placeholder massing.',
      tone:
        effectiveStarterModel.status === 'ready' &&
        effectiveStarterModel.generatedFrom.includes('preview_job')
          ? 'success'
          : 'warning',
    })

    return items
  }, [
    captureResultV2.analysisStatus.missingInputs,
    captureResultV2.codeConstraints.sourceReference,
    effectiveStarterModel.generatedFrom,
    effectiveStarterModel.status,
  ])

  const starterModelAssumptionLines = useMemo(() => {
    const assumptions = effectiveEngineeringAssumptions
    const provenanceFields = assumptions.provenance?.fields ?? {}

    const formatSourceLabel = (source: string): string =>
      source === 'property_specific'
        ? 'property-specific'
        : source === 'heuristic_fallback'
          ? 'heuristic fallback'
          : source.replace(/_/g, ' ')

    const describeFieldSources = (fields: string[]): string | null => {
      const mapped = fields
        .map((field) => ({
          field,
          source: provenanceFields[field],
        }))
        .filter(
          (
            entry,
          ): entry is {
            field: string
            source: string
          } => Boolean(entry.source),
        )

      if (!mapped.length) {
        return null
      }

      const uniqueSources = Array.from(
        new Set(mapped.map((entry) => entry.source)),
      )
      if (uniqueSources.length === 1) {
        return formatSourceLabel(uniqueSources[0]!)
      }

      const propertySpecificFields = mapped
        .filter((entry) => entry.source === 'property_specific')
        .map(
          (entry) =>
            ASSUMPTION_FIELD_LABELS.get(entry.field) ??
            entry.field.replace(/_/g, ' '),
        )

      if (propertySpecificFields.length) {
        return `${propertySpecificFields.join(', ')} property-specific`
      }

      return 'mixed sources'
    }

    const lines = [
      assumptions.floorToFloorM != null && assumptions.clearCeilingM != null
        ? {
            label: 'Vertical profile',
            value: `${formatNumber(assumptions.floorToFloorM, {
              maximumFractionDigits: 1,
            })} m floor-to-floor / ${formatNumber(assumptions.clearCeilingM, {
              maximumFractionDigits: 1,
            })} m clear`,
            sourceDetail: describeFieldSources([
              'floor_to_floor_m',
              'clear_ceiling_m',
            ]),
          }
        : null,
      assumptions.wallThicknessMm != null && assumptions.coreRatioPct != null
        ? {
            label: 'Structure + core',
            value: `${formatNumber(assumptions.wallThicknessMm, {
              maximumFractionDigits: 0,
            })} mm walls / ${formatNumber(assumptions.coreRatioPct, {
              maximumFractionDigits: 0,
            })}% core`,
            sourceDetail: describeFieldSources([
              'wall_thickness_mm',
              'core_ratio_pct',
            ]),
          }
        : null,
      assumptions.commonAreaRatioPct != null &&
      assumptions.hvacSpaceRatioPct != null &&
      assumptions.electricalSpaceRatioPct != null
        ? {
            label: 'Shared systems',
            value: `${formatNumber(assumptions.commonAreaRatioPct, {
              maximumFractionDigits: 0,
            })}% common / ${formatNumber(assumptions.hvacSpaceRatioPct, {
              maximumFractionDigits: 0,
            })}% HVAC / ${formatNumber(assumptions.electricalSpaceRatioPct, {
              maximumFractionDigits: 0,
            })}% electrical`,
            sourceDetail: describeFieldSources([
              'common_area_ratio_pct',
              'hvac_space_ratio_pct',
              'electrical_space_ratio_pct',
            ]),
          }
        : null,
      assumptions.retentionStrategy
        ? {
            label: 'Retention + yield',
            value: `${assumptions.retentionStrategy.replace(/_/g, ' ')}${
              assumptions.efficiencyFactor != null
                ? ` / ${formatNumber(assumptions.efficiencyFactor, {
                    maximumFractionDigits: 2,
                  })} efficiency`
                : ''
            }`,
            sourceDetail: describeFieldSources([
              'retention_strategy',
              'efficiency_factor',
            ]),
          }
        : assumptions.efficiencyFactor != null
          ? {
              label: 'Yield factor',
              value: `${formatNumber(assumptions.efficiencyFactor, {
                maximumFractionDigits: 2,
              })} efficiency`,
              sourceDetail: describeFieldSources(['efficiency_factor']),
            }
          : null,
    ].filter(
      (
        line,
      ): line is {
        label: string
        value: string
        sourceDetail: string | null
      } => Boolean(line),
    )

    return lines
  }, [effectiveEngineeringAssumptions, formatNumber])

  const starterModelAssetProfileLines = useMemo(() => {
    const profiles = effectiveEngineeringAssumptions.assetProfiles ?? []
    const formatAssetLabel = (assetType: string) =>
      assetType
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (char) => char.toUpperCase())

    const formatSourceLabel = (source: string): string =>
      source === 'property_specific'
        ? 'property-specific'
        : source === 'heuristic_fallback'
          ? 'heuristic fallback'
          : source.replace(/_/g, ' ')

    return profiles.map((profile) => {
      const parts: string[] = []
      if (profile.floorToFloorM != null) {
        parts.push(
          `${formatNumber(profile.floorToFloorM, {
            maximumFractionDigits: 1,
          })} m floor-to-floor`,
        )
      }
      if (profile.clearCeilingM != null) {
        parts.push(
          `${formatNumber(profile.clearCeilingM, {
            maximumFractionDigits: 1,
          })} m clear`,
        )
      }
      if (profile.niaEfficiency != null) {
        parts.push(
          `${formatNumber(profile.niaEfficiency, {
            maximumFractionDigits: 2,
          })} efficiency`,
        )
      }

      return {
        label: formatAssetLabel(profile.assetType),
        value: parts.join(' / '),
        sourceDetail: formatSourceLabel(profile.source),
      }
    })
  }, [effectiveEngineeringAssumptions.assetProfiles, formatNumber])

  const starterModelAssumptionSourceLine = useMemo(() => {
    const assumptions = effectiveEngineeringAssumptions
    const summary = assumptions.provenance?.summary ?? null
    const adjustments = assumptions.provenance?.adjustments ?? []

    const summaryLabel =
      summary === 'rules_with_property_adjustments'
        ? 'Rule defaults with property-specific adjustments'
        : summary === 'rules_only'
          ? 'Rule defaults only'
          : summary === 'frontend_fallback_defaults'
            ? 'Frontend fallback defaults'
            : assumptions.source === 'hybrid'
              ? 'Mixed-source assumptions'
              : assumptions.source === 'heuristic_fallback'
                ? 'Heuristic fallback defaults'
                : assumptions.source === 'rules'
                  ? 'Rule defaults'
                  : assumptions.source.replace(/_/g, ' ')

    if (!adjustments.length) {
      return `Assumption source: ${summaryLabel}.`
    }

    const adjustmentLabel = adjustments
      .map((adjustment) => adjustment.replace(/_/g, ' '))
      .join(', ')

    return `Assumption source: ${summaryLabel} (${adjustmentLabel}).`
  }, [effectiveEngineeringAssumptions])

  const starterModelAssumptionFallbackReason = useMemo(() => {
    const assumptions = effectiveEngineeringAssumptions
    if (assumptions.provenance?.summary !== 'frontend_fallback_defaults') {
      return null
    }

    const scenarioLabel = formatScenarioLabel(
      captureResultV2.scenarioRecommendation.recommended,
    )

    if (!previewJobs?.length) {
      return `Capture is using fallback assumptions because no scenario-specific preview jobs are attached to this property yet.`
    }

    if (!previewJob) {
      return `Capture is using fallback assumptions because no ${scenarioLabel.toLowerCase()} preview job is available yet.`
    }

    if (!previewJob.starterModelAssumptions) {
      return `Capture is using fallback assumptions because the current ${scenarioLabel.toLowerCase()} preview was generated without stored starter-model assumptions.`
    }

    return `Capture is using fallback assumptions because backend starter-model assumptions are not available for this scenario yet.`
  }, [
    effectiveEngineeringAssumptions,
    captureResultV2.scenarioRecommendation.recommended,
    formatScenarioLabel,
    previewJob,
    previewJobs,
  ])

  const starterModelOverridePreviewNotice = useMemo(() => {
    if (
      !captureResultV2.scenarioRecommendation.userOverride ||
      hasPreferredScenarioPreview
    ) {
      return null
    }

    const requestedScenarioLabel = formatScenarioLabel(
      captureResultV2.scenarioRecommendation.recommended,
    )

    return `Requested scenario: ${requestedScenarioLabel}. The preview above still reflects ${fallbackPreviewScenarioLabel} until a scenario-specific starter model is ready.`
  }, [
    captureResultV2.scenarioRecommendation.recommended,
    captureResultV2.scenarioRecommendation.userOverride,
    fallbackPreviewScenarioLabel,
    formatScenarioLabel,
    hasPreferredScenarioPreview,
  ])

  const starterModelAssumptionBuckets = useMemo(() => {
    const provenanceFields =
      effectiveEngineeringAssumptions.provenance?.fields ?? {}
    const fieldPriority = [
      'retention_strategy',
      'efficiency_factor',
      'floor_to_floor_m',
      'clear_ceiling_m',
      'wall_thickness_mm',
      'core_ratio_pct',
      'common_area_ratio_pct',
      'hvac_space_ratio_pct',
      'electrical_space_ratio_pct',
    ]

    const uniqueBySource = (source: string) =>
      Array.from(
        new Set(
          fieldPriority
            .filter((field) => provenanceFields[field] === source)
            .map(
              (field) =>
                ASSUMPTION_FIELD_LABELS.get(field) ?? field.replace(/_/g, ' '),
            ),
        ),
      )

    return {
      pinned: uniqueBySource('property_specific'),
      tunable: Array.from(
        new Set([
          ...uniqueBySource('rules'),
          ...uniqueBySource('heuristic_fallback'),
          ...uniqueBySource('jurisdiction_default'),
          ...uniqueBySource('learned'),
        ]),
      ),
    }
  }, [effectiveEngineeringAssumptions.provenance])

  const overrideModeLine = useMemo(() => {
    const recommendation = captureResultV2.scenarioRecommendation
    if (!recommendation.userOverride) {
      return 'Rule-based default'
    }
    if (recommendation.overrideIntent === 'exploratory') {
      return 'Exploratory override'
    }
    if (recommendation.overrideIntent === 'saved') {
      return 'Saved project override'
    }
    if (recommendation.overrideIntent === 'learnable') {
      return 'Learnable preference candidate'
    }
    return 'User override'
  }, [captureResultV2.scenarioRecommendation])

  const overrideIntentGuidance = useMemo(() => {
    const recommendation = captureResultV2.scenarioRecommendation
    if (recommendation.overrideIntent === 'exploratory') {
      return 'This scenario selection is temporary for the current session and does not update learned defaults.'
    }
    if (recommendation.overrideIntent === 'saved') {
      return 'This override is saved for the project and will continue to guide downstream work.'
    }
    if (recommendation.overrideIntent === 'learnable') {
      return 'This override may be considered as a future learning signal, but stronger site and rule inputs still take precedence.'
    }
    return null
  }, [captureResultV2.scenarioRecommendation])

  const recommendationCardTitle = useMemo(() => {
    const recommendation = captureResultV2.scenarioRecommendation
    if (!recommendation.overrideIntent) {
      return 'Capture Recommendation'
    }
    if (recommendation.overrideIntent === 'saved') {
      return 'Saved Scenario Override'
    }
    if (recommendation.overrideIntent === 'exploratory') {
      return 'Current Scenario Override'
    }
    return 'Current Scenario'
  }, [captureResultV2.scenarioRecommendation])

  const starterModelActionLabel = isGeneratingStarterModel
    ? 'Generating Starter Model...'
    : isRefreshingPreview
      ? 'Refreshing Starter Model...'
      : hasPreferredScenarioPreview
        ? 'Refresh Starter Model'
        : 'Generate Starter Model'

  return {
    effectiveStarterModel,
    defaultRecommendationLabel,
    fallbackPreviewScenarioLabel,
    starterModelStatusSummary,
    effectiveEngineeringAssumptions,
    scenarioFitSummary,
    captureDataBasis,
    starterModelAssumptionLines,
    starterModelAssetProfileLines,
    starterModelAssumptionSourceLine,
    starterModelAssumptionFallbackReason,
    starterModelOverridePreviewNotice,
    starterModelAssumptionBuckets,
    overrideModeLine,
    overrideIntentGuidance,
    recommendationCardTitle,
    starterModelActionLabel,
  }
}
