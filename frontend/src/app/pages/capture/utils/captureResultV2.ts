import type {
  CaptureAnalysisStatusV2,
  CaptureCodeConstraintsV2,
  CaptureCurrentVsCodeStatus,
  CaptureEngineeringAssumptionsV2,
  CaptureGrandfatheredLikelihood,
  CaptureOverrideIntent,
  CaptureResultV2,
  CaptureScenarioRecommendationV2,
  CaptureStarterModelV2,
  SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
import { DEFAULT_SCENARIO_ORDER } from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'
import { selectPreviewJobForScenario } from '../../site-acquisition/utils/previewJobSelection'

export interface BuildCaptureResultV2Options {
  selectedScenarios?: DevelopmentScenario[]
  overrideScenario?: DevelopmentScenario | null
  overrideIntent?: CaptureOverrideIntent | null
}

function formatScenarioProductLabel(scenario: DevelopmentScenario): string {
  switch (scenario) {
    case 'raw_land':
      return 'new construction'
    case 'existing_building':
      return 'renovation'
    case 'heritage_property':
      return 'heritage integration'
    case 'underused_asset':
      return 'adaptive reuse'
    case 'mixed_use_redevelopment':
      return 'mixed-use redevelopment'
    default:
      return String(scenario).replace(/_/g, ' ')
  }
}

function uniqueScenarios(
  scenarios: readonly DevelopmentScenario[],
): DevelopmentScenario[] {
  return Array.from(new Set(scenarios))
}

export function deriveCurrentVsCodeStatus(
  capturedProperty: SiteAcquisitionResult,
): CaptureCurrentVsCodeStatus {
  const current = capturedProperty.buildEnvelope.currentGfaSqm
  const max = capturedProperty.buildEnvelope.maxBuildableGfaSqm
  if (current == null || max == null) {
    return 'unknown'
  }
  if (current > max) {
    return 'above'
  }
  if (current < max) {
    return 'below'
  }
  return 'at_limit'
}

export function deriveGrandfatheredLikelihood(
  status: CaptureCurrentVsCodeStatus,
  capturedProperty: SiteAcquisitionResult,
): CaptureGrandfatheredLikelihood {
  if (status === 'above') {
    return 'high'
  }
  if (status === 'unknown') {
    return 'unknown'
  }
  if (
    capturedProperty.buildEnvelope.currentGfaSqm != null &&
    capturedProperty.buildEnvelope.currentGfaSqm > 0
  ) {
    return 'low'
  }
  return 'unknown'
}

function chooseRecommendedScenario(capturedProperty: SiteAcquisitionResult): {
  scenario: DevelopmentScenario
  reasonCodes: string[]
  confidence: CaptureScenarioRecommendationV2['confidence']
} {
  const status = deriveCurrentVsCodeStatus(capturedProperty)
  const heritageDetected =
    Boolean(capturedProperty.heritageContext?.flag) ||
    Boolean(capturedProperty.heritageContext?.overlay?.name)

  if (heritageDetected) {
    return {
      scenario: 'heritage_property',
      reasonCodes: [
        'HERITAGE_OVERLAY_DETECTED',
        'CONSERVATION_REVIEW_REQUIRED',
      ],
      confidence: 'high',
    }
  }

  if (status === 'above') {
    return {
      scenario: 'existing_building',
      reasonCodes: [
        'CURRENT_GFA_EXCEEDS_CURRENT_CODE',
        'LIKELY_GRANDFATHERED_CONDITION',
      ],
      confidence: 'high',
    }
  }

  const currentGfa = capturedProperty.buildEnvelope.currentGfaSqm ?? 0
  const additionalPotential =
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm ?? null

  if (currentGfa <= 0) {
    return {
      scenario: 'raw_land',
      reasonCodes: ['NO_EXISTING_GFA_DETECTED', 'GROUND_UP_BASELINE'],
      confidence: 'medium',
    }
  }

  if (additionalPotential != null && additionalPotential > 0) {
    return {
      scenario: 'underused_asset',
      reasonCodes: ['CODE_HEADROOM_AVAILABLE', 'REUSE_OR_EXPANSION_POSSIBLE'],
      confidence: 'medium',
    }
  }

  return {
    scenario: 'existing_building',
    reasonCodes: ['EXISTING_BUILDING_BASELINE', 'LIMITED_INCREMENTAL_HEADROOM'],
    confidence: 'medium',
  }
}

export function buildScenarioRecommendation(
  capturedProperty: SiteAcquisitionResult,
  options: BuildCaptureResultV2Options = {},
): CaptureScenarioRecommendationV2 {
  const availableScenarios = uniqueScenarios(
    options.selectedScenarios?.length
      ? options.selectedScenarios
      : DEFAULT_SCENARIO_ORDER,
  )
  const ruleChoice = chooseRecommendedScenario(capturedProperty)

  const explicitOverride =
    options.overrideScenario ??
    (availableScenarios.length === 1 ? availableScenarios[0] : null)

  const recommended = explicitOverride ?? ruleChoice.scenario
  const userOverride =
    explicitOverride !== null && explicitOverride !== ruleChoice.scenario
  const explicitScenarioOverride = options.overrideScenario != null
  const overrideIntent =
    userOverride && explicitScenarioOverride
      ? (options.overrideIntent ?? 'exploratory')
      : null

  const reasonCodes = userOverride
    ? [
        overrideIntent === 'exploratory'
          ? 'EXPLORATORY_OVERRIDE'
          : overrideIntent === 'saved'
            ? 'SAVED_PROJECT_OVERRIDE'
            : overrideIntent === 'learnable'
              ? 'LEARNABLE_OVERRIDE'
              : 'USER_OVERRIDE',
        ...ruleChoice.reasonCodes,
      ]
    : ruleChoice.reasonCodes

  const explanation = userOverride
    ? overrideIntent === 'exploratory'
      ? `Exploratory ${formatScenarioProductLabel(recommended)} override is active for this session.`
      : overrideIntent === 'saved'
        ? `${formatScenarioProductLabel(recommended)} is applied as the saved project override.`
        : overrideIntent === 'learnable'
          ? `${formatScenarioProductLabel(recommended)} is applied as a learnable preference candidate.`
          : `User-selected ${formatScenarioProductLabel(recommended)} overrides the default capture recommendation.`
    : recommended === 'heritage_property'
      ? 'Heritage context is present, so Capture prioritises a conservation-compatible starting path.'
      : recommended === 'existing_building'
        ? 'Existing bulk and current-code conditions favour a renovation-first starting point.'
        : recommended === 'underused_asset'
          ? 'Existing conditions appear reusable and current controls still leave headroom for uplift.'
          : 'No existing bulk was detected, so Capture starts from a ground-up massing path.'

  const alternatives = availableScenarios.filter(
    (scenario) => scenario !== recommended,
  )

  return {
    recommended,
    defaultRecommended: ruleChoice.scenario,
    alternatives,
    reasonCodes,
    explanation,
    userOverride,
    overrideIntent,
    confidence: userOverride ? 'medium' : ruleChoice.confidence,
  }
}

function buildFallbackEngineeringAssumptions(
  recommendedScenario: DevelopmentScenario,
): CaptureEngineeringAssumptionsV2 {
  const rulesOnlyProvenance = {
    summary: 'frontend_fallback_defaults',
    fields: {
      wall_thickness_mm: 'heuristic_fallback',
      core_ratio_pct: 'heuristic_fallback',
      common_area_ratio_pct: 'heuristic_fallback',
      floor_to_floor_m: 'heuristic_fallback',
      clear_ceiling_m: 'heuristic_fallback',
      hvac_space_ratio_pct: 'heuristic_fallback',
      electrical_space_ratio_pct: 'heuristic_fallback',
      retention_strategy: 'heuristic_fallback',
    },
    adjustments: [],
  }
  switch (recommendedScenario) {
    case 'raw_land':
    case 'mixed_use_redevelopment':
      return {
        wallThicknessMm: 250,
        coreRatioPct: 18,
        commonAreaRatioPct: 15,
        floorToFloorM: 4.2,
        clearCeilingM: 3.2,
        hvacSpaceRatioPct: 6,
        electricalSpaceRatioPct: 3,
        structuralGridNote: 'Preliminary new-build defaults',
        source: 'heuristic_fallback',
        provenance: rulesOnlyProvenance,
      }
    case 'heritage_property':
      return {
        wallThicknessMm: 220,
        coreRatioPct: 14,
        commonAreaRatioPct: 12,
        floorToFloorM: 4,
        clearCeilingM: 3,
        hvacSpaceRatioPct: 8,
        electricalSpaceRatioPct: 4,
        structuralGridNote: 'Preliminary conservation retrofit defaults',
        source: 'heuristic_fallback',
        provenance: rulesOnlyProvenance,
      }
    case 'existing_building':
    case 'underused_asset':
    default:
      return {
        wallThicknessMm: 200,
        coreRatioPct: 16,
        commonAreaRatioPct: 12,
        floorToFloorM: 3.9,
        clearCeilingM: 2.8,
        hvacSpaceRatioPct: 8,
        electricalSpaceRatioPct: 4,
        structuralGridNote: 'Preliminary renovation defaults',
        source: 'heuristic_fallback',
        provenance: rulesOnlyProvenance,
      }
  }
}

function buildEngineeringAssumptions(
  capturedProperty: SiteAcquisitionResult,
  recommendedScenario: DevelopmentScenario,
): CaptureEngineeringAssumptionsV2 {
  const previewJob = selectPreviewJobForScenario(
    capturedProperty.previewJobs,
    recommendedScenario,
  )

  if (previewJob?.starterModelAssumptions) {
    return previewJob.starterModelAssumptions
  }

  return buildFallbackEngineeringAssumptions(recommendedScenario)
}

function buildStarterModel(
  capturedProperty: SiteAcquisitionResult,
  preferredScenario?: DevelopmentScenario | null,
): CaptureStarterModelV2 {
  const previewJob = selectPreviewJobForScenario(
    capturedProperty.previewJobs,
    preferredScenario,
  )
  const visualization = capturedProperty.visualization
  const modelUrl =
    previewJob?.previewUrl ?? visualization?.conceptMeshUrl ?? null
  const metadataUrl =
    previewJob?.metadataUrl ?? visualization?.previewMetadataUrl ?? null
  const thumbnailUrl =
    previewJob?.thumbnailUrl ?? visualization?.thumbnailUrl ?? null
  const rawStatus = (
    previewJob?.status ??
    visualization?.status ??
    'placeholder'
  ).toLowerCase()
  const status: CaptureStarterModelV2['status'] =
    rawStatus === 'ready' ||
    rawStatus === 'failed' ||
    rawStatus === 'queued' ||
    rawStatus === 'processing' ||
    rawStatus === 'placeholder'
      ? rawStatus
      : 'placeholder'
  const floorsEstimate =
    visualization?.massingLayers?.reduce<number | null>((max, layer) => {
      const floors =
        layer.estimatedHeightM != null && layer.estimatedHeightM > 0
          ? Math.max(1, Math.round(layer.estimatedHeightM / 4))
          : null
      if (floors == null) {
        return max
      }
      return max == null ? floors : Math.max(max, floors)
    }, null) ?? null

  const generatedFrom = [
    previewJob ? 'preview_job' : null,
    visualization?.conceptMeshUrl ? 'visualization_summary' : null,
    visualization?.massingLayers?.length ? 'massing_layers' : null,
  ].filter((entry): entry is string => Boolean(entry))

  const geometryScope =
    modelUrl && visualization?.massingLayers?.length
      ? 'massing_stack'
      : 'scalar_envelope'

  return {
    status,
    modelUrl,
    metadataUrl,
    thumbnailUrl,
    floorsEstimate,
    generatedFrom,
    geometryScope,
  }
}

function buildCodeConstraints(
  capturedProperty: SiteAcquisitionResult,
): CaptureCodeConstraintsV2 {
  const envelope = capturedProperty.buildEnvelope
  const zoning = capturedProperty.uraZoning
  const currentVsCodeStatus = deriveCurrentVsCodeStatus(capturedProperty)
  const constraintFlags = [
    zoning?.specialConditions?.trim() || null,
    ...(capturedProperty.heritageContext?.constraints ?? []).slice(0, 2),
  ].filter((entry): entry is string => Boolean(entry))

  return {
    zoningCode: envelope.zoneCode ?? zoning?.zoneCode ?? null,
    zoningDescription:
      envelope.zoneDescription ?? zoning?.zoneDescription ?? null,
    allowablePlotRatio:
      envelope.allowablePlotRatio ?? zoning?.plotRatio ?? null,
    maxBuildableGfaSqm: envelope.maxBuildableGfaSqm,
    currentGfaSqm: envelope.currentGfaSqm,
    currentVsCodeStatus,
    grandfatheredLikelihood: deriveGrandfatheredLikelihood(
      currentVsCodeStatus,
      capturedProperty,
    ),
    setbacks: {
      frontM: null,
      rearM: null,
      sideM: null,
    },
    stepBacks: [],
    buildingHeightLimitM:
      envelope.buildingHeightLimitM ?? zoning?.buildingHeightLimit ?? null,
    siteCoveragePct: envelope.siteCoveragePct ?? zoning?.siteCoverage ?? null,
    airRightsNote: null,
    constraintFlags,
  }
}

function buildAnalysisStatus(
  capturedProperty: SiteAcquisitionResult,
): CaptureAnalysisStatusV2 {
  const codeConstraints = buildCodeConstraints(capturedProperty)
  const resolvedSignals = [
    codeConstraints.zoningCode,
    codeConstraints.allowablePlotRatio,
    codeConstraints.maxBuildableGfaSqm,
    codeConstraints.buildingHeightLimitM,
    codeConstraints.siteCoveragePct,
  ].filter((value) => value !== null && value !== undefined).length

  const missingInputs: string[] = []
  if (codeConstraints.setbacks.frontM == null) {
    missingInputs.push('setbacks')
  }
  if (codeConstraints.stepBacks.length === 0) {
    missingInputs.push('step-backs')
  }
  missingInputs.push('floor-by-floor compliance')
  missingInputs.push('air-rights review')
  missingInputs.push('solar orientation')
  missingInputs.push('terrain profile')

  return {
    completenessPct: Math.round((resolvedSignals / 5) * 100),
    missingInputs: Array.from(new Set(missingInputs)),
    supportsFullCompliance: false,
  }
}

export function mapSiteAcquisitionResultToCaptureResultV2(
  capturedProperty: SiteAcquisitionResult,
  options: BuildCaptureResultV2Options = {},
): CaptureResultV2 {
  const scenarioRecommendation = buildScenarioRecommendation(
    capturedProperty,
    options,
  )
  const codeConstraints = buildCodeConstraints(capturedProperty)
  const heritageOverlay =
    capturedProperty.heritageContext?.overlay?.name ??
    (capturedProperty.heritageContext?.flag
      ? 'Heritage overlay detected'
      : null)

  return {
    propertyId: capturedProperty.propertyId,
    address: {
      fullAddress: capturedProperty.address.fullAddress,
      district: capturedProperty.address.district ?? null,
      coordinates: capturedProperty.coordinates,
      jurisdictionCode: capturedProperty.jurisdictionCode,
    },
    siteContext: {
      siteAreaSqm:
        capturedProperty.buildEnvelope.siteAreaSqm ??
        capturedProperty.propertyInfo?.siteAreaSqm ??
        null,
      frontageM: null,
      depthM: null,
      slopeClass: 'unknown',
      solarOrientation: 'unknown',
      heritageOverlay,
      environmentalFlags: heritageOverlay ? ['heritage_overlay_detected'] : [],
    },
    codeConstraints,
    engineeringAssumptions: buildEngineeringAssumptions(
      capturedProperty,
      scenarioRecommendation.recommended,
    ),
    starterModel: buildStarterModel(
      capturedProperty,
      scenarioRecommendation.recommended,
    ),
    scenarioRecommendation,
    analysisStatus: buildAnalysisStatus(capturedProperty),
    sourceCapture: capturedProperty,
  }
}
