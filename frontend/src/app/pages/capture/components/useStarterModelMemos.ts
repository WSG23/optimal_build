/**
 * useStarterModelMemos - Extracted useMemo computations for starter model
 * display values, assumption lines, override notices, and recommendation labels.
 *
 * Extracted from DeveloperResults to reduce file size.
 */

import { useMemo } from 'react'

import type {
  CaptureRecommendationScenario,
  CaptureResultV2,
  CaptureStarterModelV2,
} from '../../../../api/siteAcquisition'

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
  statusLabel: string
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
  formatScenarioLabel: (
    scenario: CaptureRecommendationScenario | 'all' | null,
  ) => string
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

const RULE_FIELD_LABELS = new Map<string, string>([
  ['site_area', 'site area'],
  ['land_use', 'land use'],
  ['plot_ratio', 'plot ratio'],
  ['building_height_limit_m', 'height limit'],
  ['site_coverage_pct', 'site coverage'],
  ['setbacks', 'setbacks'],
  ['step_backs', 'step-backs'],
  ['air_rights_note', 'air-rights clearance'],
])

function getObjectRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object'
    ? (value as Record<string, unknown>)
    : null
}

function formatRuleFieldLabel(field: string): string {
  return RULE_FIELD_LABELS.get(field) ?? field.replace(/_/g, ' ')
}

function getRuleFieldIds(value: unknown): string[] {
  return Array.isArray(value)
    ? value
        .map((entry) =>
          typeof entry === 'string' && entry.trim() ? entry.trim() : null,
        )
        .filter((entry): entry is string => Boolean(entry))
    : []
}

function getRuleFieldSources(
  value: Record<string, unknown> | null,
): Record<string, string> {
  if (!value) {
    return {}
  }
  return Object.fromEntries(
    Object.entries(value)
      .map(([field, source]) => [
        formatRuleFieldLabel(field),
        typeof source === 'string' ? source : '',
      ])
      .filter((entry): entry is [string, string] => entry[1].length > 0),
  )
}

function isGfaEnvelopeAvailable(
  codeConstraints: CaptureResultV2['codeConstraints'],
): boolean {
  return Boolean(
    codeConstraints.maxBuildableGfaSqm != null &&
    codeConstraints.currentGfaSqm != null,
  )
}

function formatZoningSummary(
  codeConstraints: CaptureResultV2['codeConstraints'],
): string {
  const description = codeConstraints.zoningDescription?.trim()
  const code = codeConstraints.zoningCode?.trim()

  if (description && code && description.toLowerCase() !== code.toLowerCase()) {
    return `${description} (${code})`
  }

  return description || code || 'Zoning unresolved'
}

function formatUnresolvedRuleFieldLabel(
  field: string,
  codeConstraints: CaptureResultV2['codeConstraints'],
): string {
  if (
    field === 'building_height_limit_m' &&
    isGfaEnvelopeAvailable(codeConstraints)
  ) {
    return 'height limit - separate official control'
  }
  return formatRuleFieldLabel(field)
}

function getUnresolvedRuleFieldSummary(
  value: unknown,
  codeConstraints: CaptureResultV2['codeConstraints'],
  excludedFields: Set<string> = new Set(),
): string[] {
  return getRuleFieldIds(value)
    .filter((entry) => !excludedFields.has(entry))
    .map((entry) => formatUnresolvedRuleFieldLabel(entry, codeConstraints))
}

interface OfficialSourceGapSummary {
  field: string
  label: string
  workflow: string | null
  reason: string | null
  sourceValue: string | null
  reviewNote: string | null
}

function getOfficialSourceGapSummaries(
  value: unknown,
  codeConstraints: CaptureResultV2['codeConstraints'],
): OfficialSourceGapSummary[] {
  if (!Array.isArray(value)) {
    return []
  }

  return value
    .map((entry): OfficialSourceGapSummary | null => {
      const record = getObjectRecord(entry)
      const rawField = typeof record?.field === 'string' ? record.field : null
      if (!rawField) {
        return null
      }

      const sources = Array.isArray(record?.candidate_sources)
        ? record.candidate_sources
        : []
      const authorities = Array.from(
        new Set(
          sources
            .map((source) => {
              const sourceRecord = getObjectRecord(source)
              return typeof sourceRecord?.authority === 'string'
                ? sourceRecord.authority
                : null
            })
            .filter((authority): authority is string => Boolean(authority)),
        ),
      )
      const workflows = Array.from(
        new Set(
          sources
            .map((source) => {
              const sourceRecord = getObjectRecord(source)
              return typeof sourceRecord?.resolution_workflow === 'string'
                ? sourceRecord.resolution_workflow
                : null
            })
            .filter((workflow): workflow is string => Boolean(workflow)),
        ),
      )

      const label = formatUnresolvedRuleFieldLabel(rawField, codeConstraints)
      return {
        field: rawField,
        label: authorities.length
          ? `${label} (${authorities.join(', ')})`
          : label,
        workflow: workflows[0] ?? null,
        reason: typeof record.reason === 'string' ? record.reason : null,
        sourceValue:
          typeof record.source_value === 'string' ? record.source_value : null,
        reviewNote:
          typeof record.review_note === 'string' ? record.review_note : null,
      }
    })
    .filter((entry): entry is OfficialSourceGapSummary => Boolean(entry))
}

function getEnvelopeSourceStatusLabel(
  sourceReference: string,
  resolvedSourcesByField: Record<string, string>,
): string {
  const landUseSource = resolvedSourcesByField['land use']
  const plotRatioSource = resolvedSourcesByField['plot ratio']
  const siteAreaSource = resolvedSourcesByField['site area']
  if (
    landUseSource === 'ref_zoning_layer' &&
    plotRatioSource === 'ref_zoning_layer' &&
    siteAreaSource === 'ref_parcel'
  ) {
    return 'Official zoning + parcel area'
  }
  if (
    landUseSource === 'ref_zoning_layer' &&
    plotRatioSource === 'ref_zoning_layer'
  ) {
    return 'Official land use + plot ratio'
  }
  if (/zoning layers/i.test(sourceReference)) {
    return 'Official zoning layer'
  }
  return 'Rule-backed controls'
}

function getProjectClearanceFieldIds(
  explicitValue: unknown,
  sourceGapSummaries: OfficialSourceGapSummary[],
): Set<string> {
  const explicitFields = Array.isArray(explicitValue)
    ? explicitValue
        .map((entry) => {
          const record = getObjectRecord(entry)
          return typeof record?.field === 'string' && record.field.trim()
            ? record.field.trim()
            : null
        })
        .filter((field): field is string => Boolean(field))
    : []
  const inferredFields = sourceGapSummaries
    .filter((gap) => gap.workflow === 'project_specific_clearance')
    .map((gap) => gap.field)

  return new Set([...explicitFields, ...inferredFields])
}

function getProjectClearanceGapSummaries(
  explicitValue: unknown,
  sourceGapSummaries: OfficialSourceGapSummary[],
  codeConstraints: CaptureResultV2['codeConstraints'],
): string[] {
  const explicitSummaries = getOfficialSourceGapSummaries(
    explicitValue,
    codeConstraints,
  ).map((gap) => gap.label)
  const inferredSummaries = sourceGapSummaries
    .filter((gap) => gap.workflow === 'project_specific_clearance')
    .map((gap) => gap.label)
  return Array.from(new Set([...explicitSummaries, ...inferredSummaries]))
}

interface LiveSourceScanSummary {
  value: string
  tone: CaptureDataBasisItem['tone']
  statusLabel: string
}

function getLiveSourceScanSummary(
  value: unknown,
): LiveSourceScanSummary | null {
  const record = getObjectRecord(value)
  if (!record) {
    return null
  }
  const resolved =
    typeof record.resolved_count === 'number' ? record.resolved_count : 0
  const staged =
    typeof record.staged_count === 'number' ? record.staged_count : 0
  const existing =
    typeof record.existing_count === 'number' ? record.existing_count : 0
  const failed =
    typeof record.failed_count === 'number' ? record.failed_count : 0
  if (!resolved && !staged && !existing && !failed) {
    return null
  }
  const parts = []
  if (resolved) {
    parts.push(`${resolved} normalized into approved rules`)
  }
  if (staged) {
    parts.push(`${staged} staged for review`)
  }
  if (existing) {
    parts.push(`${existing} already staged`)
  }
  if (failed) {
    parts.push(`${failed} fetch failed`)
  }
  const hasPendingWork = Boolean(staged || existing || failed)
  return {
    value: `${parts.join(' / ')}. ${
      hasPendingWork
        ? 'Pending source candidates still require review before Capture treats those controls as resolved.'
        : 'Normalized source values are now available to the rule resolver.'
    }`,
    tone: hasPendingWork || failed ? 'warning' : 'success',
    statusLabel: hasPendingWork || failed ? 'Review required' : 'Resolved',
  }
}

interface ControlAutomationDependencySummary {
  label: string
  status: string
  action: string
}

function getControlAutomationDependencies(
  value: unknown,
): ControlAutomationDependencySummary[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value
    .map((entry): ControlAutomationDependencySummary | null => {
      const record = getObjectRecord(entry)
      const label = typeof record?.label === 'string' ? record.label : null
      const status = typeof record?.status === 'string' ? record.status : null
      const action = typeof record?.action === 'string' ? record.action : null
      if (!label || !status || !action) {
        return null
      }
      return { label, status, action }
    })
    .filter((entry): entry is ControlAutomationDependencySummary =>
      Boolean(entry),
    )
}

function formatControlAutomationStatus(status: string): string {
  return status
    .replace(/^source_mapping_required$/, 'source mapping required')
    .replace(
      /^site_specific_control_required$/,
      'site-specific control required',
    )
    .replace(/^project_clearance_required$/, 'project clearance required')
    .replace(/_/g, ' ')
}

function formatControlAutomationDependencies(
  dependencies: ControlAutomationDependencySummary[],
): string {
  return `${dependencies
    .slice(0, 4)
    .map(
      (dependency) =>
        `${dependency.label}: ${formatControlAutomationStatus(dependency.status)}`,
    )
    .join('; ')}${dependencies.length > 4 ? '; ...' : ''}.`
}

function getSiteSpecificGprSummary(
  gaps: OfficialSourceGapSummary[],
): string | null {
  const gap = gaps.find(
    (entry) =>
      entry.field === 'plot_ratio' &&
      entry.reason === 'envelope_control_area_requires_site_specific_controls',
  )
  if (!gap) {
    return null
  }
  return gap.sourceValue
    ? `Site-specific envelope control required (${gap.sourceValue})`
    : 'Site-specific envelope control required'
}

function formatRuleFieldSummary(fields: string[]): string {
  const uniqueFields = Array.from(new Set(fields))
  return `${uniqueFields.slice(0, 5).join(', ')}${uniqueFields.length > 5 ? ', ...' : ''}.`
}

interface ResolvedRuleSourceGroup {
  label: string
  statusLabel: string
  fields: string[]
}

function getResolvedRuleSourceGroups(
  sourcesByField: Record<string, string>,
): ResolvedRuleSourceGroup[] {
  const siteCaptured: string[] = []
  const ruleBacked: string[] = []
  const otherResolved: string[] = []

  for (const [field, source] of Object.entries(sourcesByField)) {
    if (source.startsWith('captured_')) {
      siteCaptured.push(field)
    } else if (/rule|registry|ref_rule/i.test(source)) {
      ruleBacked.push(field)
    } else {
      otherResolved.push(field)
    }
  }

  return [
    {
      label: 'Site captured controls',
      statusLabel: 'Site / captured',
      fields: siteCaptured,
    },
    {
      label: 'Rule-backed controls',
      statusLabel: 'Rule-backed',
      fields: ruleBacked,
    },
    {
      label: 'Other resolved controls',
      statusLabel: 'Resolved',
      fields: otherResolved,
    },
  ].filter((group) => group.fields.length > 0)
}

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

  const starterModelScenarioLabel = useMemo(() => {
    return captureResultV2.scenarioRecommendation.recommended ===
      'scenario_pending'
      ? 'envelope'
      : formatScenarioLabel(captureResultV2.scenarioRecommendation.recommended)
  }, [captureResultV2.scenarioRecommendation.recommended, formatScenarioLabel])

  const starterModelStatusSummary = useMemo(() => {
    const isScenarioPending =
      captureResultV2.scenarioRecommendation.recommended === 'scenario_pending'
    const scenarioLabel = starterModelScenarioLabel
    switch (effectiveStarterModel.status) {
      case 'queued':
        return isScenarioPending
          ? 'An envelope-based starter model has been queued. Capture will replace the fallback preview when the render is ready.'
          : `A ${scenarioLabel.toLowerCase()} starter model has been queued. Capture will replace the fallback preview when the render is ready.`
      case 'processing':
        return isScenarioPending
          ? 'Capture is generating an envelope-based starter model now.'
          : `Capture is generating the ${scenarioLabel.toLowerCase()} starter model now.`
      case 'ready':
        return isScenarioPending
          ? 'The envelope-based starter model is ready for review; scenario selection remains pending until existing GFA is available.'
          : hasPreferredScenarioPreview
            ? `The ${scenarioLabel.toLowerCase()} starter model is ready for review.`
            : `The ${scenarioLabel.toLowerCase()} starter model is not ready yet. Capture is still showing the ${fallbackPreviewScenarioLabel.toLowerCase()} preview until a scenario-specific model is available.`
      case 'failed':
        return isScenarioPending
          ? 'Capture could not generate the envelope-based starter model yet. Retry generation from this panel.'
          : `Capture could not generate the ${scenarioLabel.toLowerCase()} starter model yet. Retry generation from this panel.`
      case 'placeholder':
      default:
        return isScenarioPending
          ? 'No envelope-based starter model is available yet. Capture is currently showing the best available fallback preview.'
          : 'No scenario-specific starter model is available yet. Capture is currently showing the best available fallback preview.'
    }
  }, [
    captureResultV2.scenarioRecommendation.recommended,
    effectiveStarterModel.status,
    fallbackPreviewScenarioLabel,
    hasPreferredScenarioPreview,
    starterModelScenarioLabel,
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
    const ruleCorpusStatus = getObjectRecord(
      captureResultV2.sourceCapture.buildEnvelope.ruleCorpusStatus,
    )
    const officialSourceGapSummaries = getOfficialSourceGapSummaries(
      ruleCorpusStatus?.official_source_gaps,
      codeConstraints,
    )
    const comparisonSummary =
      codeConstraints.currentVsCodeStatus === 'above'
        ? 'Current GFA exceeds today\u2019s code envelope and may reflect a grandfathered condition.'
        : codeConstraints.currentVsCodeStatus === 'below'
          ? 'Current GFA remains below today\u2019s code envelope, leaving compliant headroom to study.'
          : codeConstraints.currentVsCodeStatus === 'at_limit'
            ? 'Current GFA appears to match today\u2019s code envelope.'
            : codeConstraints.currentGfaSqm == null
              ? 'Current GFA is unavailable, so current-versus-code fit is pending.'
              : codeConstraints.maxBuildableGfaSqm == null
                ? 'Current-code envelope is incomplete, so code fit is pending.'
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
        : codeConstraints.maxBuildableGfaSqm != null
          ? `Current GFA unavailable for comparison with ${formatNumber(
              codeConstraints.maxBuildableGfaSqm,
              {
                maximumFractionDigits: 0,
              },
            )} sqm current-code max.`
          : codeConstraints.currentGfaSqm != null
            ? 'Max GFA cannot be calculated until site area and official envelope controls are resolved.'
            : captureResultV2.siteContext.siteAreaSqm != null
              ? 'Max GFA cannot be calculated until plot ratio or envelope controls are resolved; current GFA is unavailable.'
              : 'Max GFA cannot be calculated until site area is resolved; current GFA is unavailable.'

    const gprSummary =
      codeConstraints.grossPlotRatio != null
        ? formatNumber(codeConstraints.grossPlotRatio, {
            maximumFractionDigits: 2,
          })
        : (getSiteSpecificGprSummary(officialSourceGapSummaries) ??
          'GPR unresolved')

    const heritageSummary = captureResultV2.siteContext.heritageOverlay
      ? `Context: ${captureResultV2.siteContext.heritageOverlay}.`
      : 'No heritage overlay is currently driving the starter model.'

    return {
      comparisonSummary,
      gprSummary,
      headroomSummary,
      heritageSummary,
      zoningSummary: formatZoningSummary(codeConstraints),
    }
  }, [
    captureResultV2.codeConstraints,
    captureResultV2.sourceCapture.buildEnvelope.ruleCorpusStatus,
    captureResultV2.siteContext,
    formatNumber,
  ])

  const captureDataBasis = useMemo((): CaptureDataBasisItem[] => {
    const ruleCorpusStatus = getObjectRecord(
      captureResultV2.sourceCapture.buildEnvelope.ruleCorpusStatus,
    )
    const resolvedBy = getObjectRecord(ruleCorpusStatus?.resolved_by)
    const resolvedSourcesByField = getRuleFieldSources(resolvedBy)
    const resolvedRuleGroups = getResolvedRuleSourceGroups(
      resolvedSourcesByField,
    )
    const officialSourceGapSummaries = getOfficialSourceGapSummaries(
      ruleCorpusStatus?.official_source_gaps,
      captureResultV2.codeConstraints,
    )
    const projectClearanceGaps = getProjectClearanceGapSummaries(
      ruleCorpusStatus?.project_clearance_required,
      officialSourceGapSummaries,
      captureResultV2.codeConstraints,
    )
    const projectClearanceFieldIds = getProjectClearanceFieldIds(
      ruleCorpusStatus?.project_clearance_required,
      officialSourceGapSummaries,
    )
    const unresolvedRuleFields = getUnresolvedRuleFieldSummary(
      ruleCorpusStatus?.unresolved_fields,
      captureResultV2.codeConstraints,
      projectClearanceFieldIds,
    )
    const sourceIngestionGaps = officialSourceGapSummaries
      .filter((gap) => gap.workflow !== 'project_specific_clearance')
      .map((gap) => gap.label)
    const liveSourceScanSummary = getLiveSourceScanSummary(
      ruleCorpusStatus?.official_source_ingestion,
    )
    const controlAutomationDependencies = getControlAutomationDependencies(
      ruleCorpusStatus?.automation_dependencies,
    )

    const items: CaptureDataBasisItem[] = [
      {
        label: 'Site input',
        value: 'Address and coordinates are site-specific.',
        tone: 'success',
        statusLabel: 'Site-specific',
      },
    ]
    const currentUseEvidence =
      captureResultV2.sourceCapture.propertyInfo?.currentUseEvidence?.[0]
    if (currentUseEvidence) {
      const evidenceSource = currentUseEvidence.source
        .replace(/^google_places_details$/i, 'Google Places details')
        .replace(/^google_places_autocomplete$/i, 'Google Places autocomplete')
        .replace(/^ura_existing_use$/i, 'URA existing-use service')
        .replace(/_/g, ' ')
      const placeName = currentUseEvidence.placeName
        ? ` (${currentUseEvidence.placeName})`
        : ''
      items.push({
        label: 'Current use evidence',
        value: `${currentUseEvidence.use}${placeName}. Source: ${evidenceSource}; ${currentUseEvidence.basis}`,
        tone:
          currentUseEvidence.confidence.toLowerCase() === 'high'
            ? 'success'
            : 'warning',
        statusLabel:
          currentUseEvidence.confidence.toLowerCase() === 'high'
            ? 'Current use verified'
            : 'Current use signal',
      })
    }

    const sourceReference = captureResultV2.codeConstraints.sourceReference
    if (!sourceReference) {
      items.push({
        label: 'Envelope source',
        value: 'Zoning envelope source is unresolved.',
        tone: 'warning',
        statusLabel: 'Source unresolved',
      })
    } else if (/mock data|fallback|no refrule/i.test(sourceReference)) {
      items.push({
        label: 'Envelope source',
        value: sourceReference,
        tone: 'warning',
        statusLabel: 'Partial source',
      })
    } else {
      items.push({
        label: 'Envelope source',
        value: sourceReference,
        tone: 'success',
        statusLabel: getEnvelopeSourceStatusLabel(
          sourceReference,
          resolvedSourcesByField,
        ),
      })
    }

    const hasUnresolvedRuleFieldStatus = Array.isArray(
      ruleCorpusStatus?.unresolved_fields,
    )
    const captureCompletenessFields = hasUnresolvedRuleFieldStatus
      ? unresolvedRuleFields
      : captureResultV2.analysisStatus.missingInputs
    const unresolvedCount = captureCompletenessFields.length
    const unresolvedSummary = `${captureCompletenessFields.slice(0, 3).join(', ')}${unresolvedCount > 3 ? ', …' : ''}`
    const unresolvedSubject = hasUnresolvedRuleFieldStatus
      ? `official ${unresolvedCount === 1 ? 'control' : 'controls'}`
      : `capture ${unresolvedCount === 1 ? 'input' : 'inputs'}`
    const unresolvedAction = hasUnresolvedRuleFieldStatus
      ? unresolvedCount === 1
        ? 'still needs source review'
        : 'still need source review'
      : unresolvedCount === 1
        ? 'is still unresolved'
        : 'are still unresolved'
    const projectClearanceSummary = `${projectClearanceGaps.slice(0, 3).join(', ')}${projectClearanceGaps.length > 3 ? ', …' : ''}`
    const isPartialCapture =
      unresolvedCount > 0 || projectClearanceGaps.length > 0
    const completenessValue =
      unresolvedCount > 0
        ? `${unresolvedCount} ${unresolvedSubject} ${unresolvedAction} (${unresolvedSummary}).`
        : projectClearanceGaps.length > 0
          ? `${projectClearanceGaps.length} project ${projectClearanceGaps.length === 1 ? 'clearance is' : 'clearances are'} still required (${projectClearanceSummary}).`
          : 'Core rule controls resolved for this capture.'
    items.push({
      label: 'Capture completeness',
      value: completenessValue,
      tone: isPartialCapture ? 'warning' : 'success',
      statusLabel: isPartialCapture
        ? 'Partial capture'
        : 'Core controls resolved',
    })

    for (const group of resolvedRuleGroups) {
      items.push({
        label: group.label,
        value: formatRuleFieldSummary(group.fields),
        tone: 'success',
        statusLabel: group.statusLabel,
      })
    }

    if (unresolvedRuleFields.length > 0) {
      items.push({
        label: 'Official controls pending',
        value: formatRuleFieldSummary(unresolvedRuleFields),
        tone: 'warning',
        statusLabel: 'Source review needed',
      })
    }

    if (projectClearanceGaps.length > 0) {
      const clearanceList = `${projectClearanceGaps.slice(0, 4).join(', ')}${projectClearanceGaps.length > 4 ? ', ...' : ''}`
      items.push({
        label: 'Project clearance required',
        value: `${clearanceList} ${projectClearanceGaps.length === 1 ? 'requires' : 'require'} site-specific aviation and height-clearance review. Capture does not resolve ${projectClearanceGaps.length === 1 ? 'this clearance' : 'these clearances'}.`,
        tone: 'warning',
        statusLabel: 'Project clearance required',
      })
    }

    if (sourceIngestionGaps.length > 0) {
      const sourceList = `${sourceIngestionGaps.slice(0, 4).join(', ')}${sourceIngestionGaps.length > 4 ? ', ...' : ''}`
      items.push({
        label: 'Control automation path',
        value: `${sourceList} ${sourceIngestionGaps.length === 1 ? 'has' : 'have'} official source categories identified, but Capture has not mapped reviewed values for this zone yet.`,
        tone: 'warning',
        statusLabel: 'Control source not mapped',
      })
    }

    if (controlAutomationDependencies.length > 0) {
      items.push({
        label: 'Next automation dependencies',
        value: formatControlAutomationDependencies(
          controlAutomationDependencies,
        ),
        tone: 'warning',
        statusLabel: 'Automation dependencies',
      })
    }

    if (liveSourceScanSummary) {
      items.push({
        label: 'Live source scan',
        value: liveSourceScanSummary.value,
        tone: liveSourceScanSummary.tone,
        statusLabel: liveSourceScanSummary.statusLabel,
      })
    }

    items.push({
      label: 'Geometry',
      value:
        effectiveStarterModel.status === 'ready' &&
        effectiveStarterModel.generatedFrom.includes('preview_job')
          ? captureResultV2.scenarioRecommendation.recommended ===
            'scenario_pending'
            ? 'Envelope-based starter model is generated from the preview pipeline while scenario selection remains pending.'
            : 'Scenario-specific starter model is generated from the preview pipeline.'
          : 'Geometry is still preliminary and may rely on fallback or placeholder massing.',
      tone:
        effectiveStarterModel.status === 'ready' &&
        effectiveStarterModel.generatedFrom.includes('preview_job')
          ? 'success'
          : 'warning',
      statusLabel:
        effectiveStarterModel.status === 'ready' &&
        effectiveStarterModel.generatedFrom.includes('preview_job')
          ? captureResultV2.scenarioRecommendation.recommended ===
            'scenario_pending'
            ? 'Envelope starter model'
            : 'Starter model pipeline'
          : 'Preliminary geometry',
    })

    return items
  }, [
    captureResultV2.analysisStatus.missingInputs,
    captureResultV2.codeConstraints,
    captureResultV2.scenarioRecommendation.recommended,
    captureResultV2.sourceCapture.buildEnvelope.ruleCorpusStatus,
    captureResultV2.sourceCapture.propertyInfo?.currentUseEvidence,
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
          ? 'Starter model defaults'
          : summary === 'common_practice_assumptions_with_property_adjustments'
            ? 'Common-practice assumptions with property-specific adjustments'
            : summary === 'common_practice_assumptions'
              ? 'Common-practice assumptions'
              : summary === 'frontend_fallback_defaults'
                ? 'Frontend fallback defaults'
                : assumptions.source === 'hybrid'
                  ? 'Mixed-source assumptions'
                  : assumptions.source === 'heuristic_fallback'
                    ? 'Common-practice assumptions'
                    : assumptions.source === 'rules'
                      ? 'Starter model defaults'
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

    const scenarioLabel = starterModelScenarioLabel

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
    previewJob,
    previewJobs,
    starterModelScenarioLabel,
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
