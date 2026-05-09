import type {
  CaptureAnalysisStatusV2,
  CaptureCodeConstraintsV2,
  CaptureCurrentVsCodeStatus,
  CaptureEngineeringAssumptionsV2,
  CaptureGrandfatheredLikelihood,
  CaptureOverrideIntent,
  CaptureRecommendationScenario,
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

function formatScenarioProductLabel(
  scenario: CaptureRecommendationScenario,
): string {
  switch (scenario) {
    case 'scenario_pending':
      return 'scenario pending'
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

function getPreviewScenarioForRecommendation(
  scenario: CaptureRecommendationScenario,
): DevelopmentScenario {
  return scenario === 'scenario_pending' ? 'existing_building' : scenario
}

function formatAssetTypeLabel(assetType: string): string {
  switch (assetType.toLowerCase()) {
    case 'hotel':
      return 'Hotel'
    case 'retail':
      return 'Retail'
    case 'office':
      return 'Office'
    case 'commercial':
      return 'Commercial'
    case 'residential':
      return 'Residential'
    case 'hospitality':
      return 'Hospitality'
    case 'healthcare':
      return 'Healthcare'
    case 'medical':
    case 'medical_care':
      return 'Medical care'
    case 'institutional':
      return 'Institutional'
    case 'amenities':
      return 'Amenities'
    case 'industrial':
      return 'Industrial'
    case 'mixed_use':
    case 'mixed_use_redevelopment':
      return 'Mixed-use'
    default:
      return assetType
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (char) => char.toUpperCase())
  }
}

function normalizeUseSignal(value: string | null | undefined): string {
  return value?.trim().toLowerCase().replace(/[_-]+/g, ' ') ?? ''
}

function ruleCorpusString(
  ruleCorpusStatus: Record<string, unknown> | null | undefined,
  key: string,
): string | null {
  const value = ruleCorpusStatus?.[key]
  return typeof value === 'string' ? value : null
}

function deriveSiteDevelopmentStatus(
  capturedProperty: SiteAcquisitionResult,
): 'developed' | 'vacant' | 'uncertain' {
  const status = ruleCorpusString(
    capturedProperty.buildEnvelope?.ruleCorpusStatus,
    'site_development_status',
  )
  return status === 'developed' || status === 'vacant' ? status : 'uncertain'
}

function deriveSiteDevelopmentSourceKind(
  capturedProperty: SiteAcquisitionResult,
): string | null {
  const lookupSource =
    capturedProperty.buildEnvelope?.ruleCorpusStatus?.[
      'site_development_lookup_source'
    ]
  if (!lookupSource || typeof lookupSource !== 'object') {
    return null
  }
  const kind = (lookupSource as Record<string, unknown>).kind
  return typeof kind === 'string' ? kind : null
}

type SpecialZoningControl = {
  kind:
    | 'road'
    | 'open_space'
    | 'transport_facilities'
    | 'specialized_operator'
    | 'non_standard'
  label: string
  drivers: string[]
  summary: string
  explanation: string
}

function buildNonStandardPrivateProgramControl(
  kind: SpecialZoningControl['kind'],
  planningControlLabel: string,
  driverLabel: string,
): SpecialZoningControl {
  const explanation = `Capture matched ${planningControlLabel} zoning. Scenario selection stays pending because this control is not a standard private development program; site-specific approval, rezoning, or public-use review may be required before a building scenario is studied.`
  return {
    kind,
    label: 'No standard private program',
    drivers: [driverLabel, 'Control review'],
    summary: explanation,
    explanation,
  }
}

function buildSpecializedOperatorProgramControl(
  planningControlLabel: string,
  primaryDriver: string,
  supportDriver: string,
): SpecialZoningControl {
  const explanation = `Capture matched ${planningControlLabel} zoning. Scenario selection stays pending because this is a specialized operator-led use; Capture needs current GFA and site-specific controls before recommending renovation or redevelopment.`
  return {
    kind: 'specialized_operator',
    label: 'Specialized operator-led program',
    drivers: [primaryDriver, supportDriver, 'Operator-led use'],
    summary: explanation,
    explanation,
  }
}

function deriveSpecialZoningControl(
  capturedProperty: SiteAcquisitionResult,
): SpecialZoningControl | null {
  const rawZoning = capturedProperty.uraZoning as
    | (typeof capturedProperty.uraZoning & {
        developmentControlStatus?: string | null
      })
    | null
    | undefined
  const status = normalizeUseSignal(rawZoning?.developmentControlStatus)
  const specialConditions = normalizeUseSignal(rawZoning?.specialConditions)
  const zoningSignals = [
    capturedProperty.buildEnvelope?.zoneCode,
    capturedProperty.buildEnvelope?.zoneDescription,
    ruleCorpusString(
      capturedProperty.buildEnvelope?.ruleCorpusStatus,
      'zone_code',
    ),
    ruleCorpusString(
      capturedProperty.buildEnvelope?.ruleCorpusStatus,
      'zone_description',
    ),
    rawZoning?.zoneCode,
    rawZoning?.zoneDescription,
  ]
    .map(normalizeUseSignal)
    .filter(Boolean)
  const compactSignals = zoningSignals.map((signal) =>
    signal.replace(/[^a-z0-9]/g, ''),
  )
  const hasNonStandardFlag =
    status === 'non standard or non developable' ||
    status === 'non_standard_or_non_developable' ||
    specialConditions === 'non standard or non developable control' ||
    specialConditions === 'non_standard_or_non_developable_control'

  const hasRoad = zoningSignals.some((signal, index) => {
    const compact = compactSignals[index]
    return signal === 'road' || compact === 'sgroad'
  })
  const hasParkOrOpenSpace = zoningSignals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      signal === 'park' ||
      signal === 'open space' ||
      signal === 'open-space' ||
      compact === 'sgpark' ||
      compact === 'sgopenspace'
    )
  })
  const hasTransportFacilities = zoningSignals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      signal === 'transport facilities' ||
      signal === 'transport-facilities' ||
      compact === 'sgtransportfacilities'
    )
  })
  const hasEducation = zoningSignals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      signal === 'education' ||
      signal === 'educational institution' ||
      signal === 'school' ||
      signal.includes('educational institution') ||
      compact === 'sgeducation' ||
      compact === 'sgeducationalinstitution' ||
      compact.includes('educationalinstitution')
    )
  })
  const hasSpecialUse = zoningSignals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      signal === 'special use' ||
      signal === 'special-use' ||
      signal.includes('special use') ||
      compact === 'sgspecialuse' ||
      compact === 'specialuse'
    )
  })
  const hasReserveSite = zoningSignals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      signal === 'reserve site' ||
      signal === 'reserve' ||
      signal.includes('reserve site') ||
      compact === 'sgreservesite' ||
      compact === 'reservesite'
    )
  })
  const hasCivicCommunityInstitution = zoningSignals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      signal === 'civic & community institution' ||
      signal === 'civic and community institution' ||
      signal === 'community institution' ||
      signal.includes('civic') ||
      signal.includes('community institution') ||
      compact === 'sgciviccommunityinstitution' ||
      compact === 'civiccommunityinstitution' ||
      compact.includes('civiccommunityinstitution')
    )
  })
  const hasHealthcare = zoningSignals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      signal === 'health & medical care' ||
      signal === 'health and medical care' ||
      signal === 'hospital' ||
      signal.includes('health') ||
      signal.includes('medical') ||
      signal.includes('hospital') ||
      compact === 'sghealthmedicalcare' ||
      compact.includes('healthmedicalcare')
    )
  })
  const hasSportsRecreation = zoningSignals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      signal === 'sports & recreation' ||
      signal === 'sports and recreation' ||
      signal.includes('sports') ||
      signal.includes('recreation') ||
      compact === 'sgsportsrecreation' ||
      compact.includes('sportsrecreation')
    )
  })

  if (hasRoad) {
    return buildNonStandardPrivateProgramControl('road', 'road', 'Road reserve')
  }
  if (hasParkOrOpenSpace) {
    return buildNonStandardPrivateProgramControl(
      'open_space',
      'park/open-space',
      'Park / open space',
    )
  }
  if (hasTransportFacilities) {
    return buildNonStandardPrivateProgramControl(
      'transport_facilities',
      'transport-facilities',
      'Transport facilities',
    )
  }
  if (hasEducation) {
    return buildNonStandardPrivateProgramControl(
      'non_standard',
      'education',
      'Education',
    )
  }
  if (hasSpecialUse) {
    return buildNonStandardPrivateProgramControl(
      'non_standard',
      'special-use',
      'Special use',
    )
  }
  if (hasReserveSite) {
    return buildNonStandardPrivateProgramControl(
      'non_standard',
      'reserve-site',
      'Reserve site',
    )
  }
  if (hasCivicCommunityInstitution) {
    return buildNonStandardPrivateProgramControl(
      'non_standard',
      'civic/community institution',
      'Civic/community institution',
    )
  }
  if (hasHealthcare) {
    return buildSpecializedOperatorProgramControl(
      'health/medical-care',
      'Healthcare',
      'Institutional',
    )
  }
  if (hasSportsRecreation) {
    return buildSpecializedOperatorProgramControl(
      'sports/recreation',
      'Recreation',
      'Amenities',
    )
  }
  if (hasNonStandardFlag) {
    const explanation =
      'Capture matched a non-standard planning control. Scenario selection stays pending until the official control is reviewed.'
    return {
      kind: 'non_standard',
      label: 'No standard private program',
      drivers: ['Non-standard control', 'Control review'],
      summary: explanation,
      explanation,
    }
  }

  return null
}

function deriveZoningProgramDrivers(
  capturedProperty: SiteAcquisitionResult,
): string[] | null {
  if (deriveSpecialZoningControl(capturedProperty)) {
    return null
  }

  const useGroups = Array.isArray(capturedProperty.uraZoning?.useGroups)
    ? capturedProperty.uraZoning.useGroups
    : []

  const signals = [
    capturedProperty.address?.fullAddress,
    capturedProperty.address?.district,
    capturedProperty.propertyInfo?.propertyName,
    capturedProperty.buildEnvelope?.zoneCode,
    capturedProperty.buildEnvelope?.zoneDescription,
    ruleCorpusString(
      capturedProperty.buildEnvelope?.ruleCorpusStatus,
      'zone_code',
    ),
    ruleCorpusString(
      capturedProperty.buildEnvelope?.ruleCorpusStatus,
      'zone_description',
    ),
    capturedProperty.uraZoning?.zoneCode,
    capturedProperty.uraZoning?.zoneDescription,
    ...useGroups,
    capturedProperty.existingUse,
  ]
    .map(normalizeUseSignal)
    .filter(Boolean)

  const compactSignals = signals.map((signal) =>
    signal.replace(/[^a-z0-9]/g, ''),
  )
  const zoningSignals = [
    capturedProperty.buildEnvelope?.zoneCode,
    capturedProperty.buildEnvelope?.zoneDescription,
    ruleCorpusString(
      capturedProperty.buildEnvelope?.ruleCorpusStatus,
      'zone_code',
    ),
    ruleCorpusString(
      capturedProperty.buildEnvelope?.ruleCorpusStatus,
      'zone_description',
    ),
    capturedProperty.uraZoning?.zoneCode,
    capturedProperty.uraZoning?.zoneDescription,
  ]
    .map(normalizeUseSignal)
    .filter(Boolean)
  const compactZoningSignals = zoningSignals.map((signal) =>
    signal.replace(/[^a-z0-9]/g, ''),
  )
  const propertyUseSignals = [
    capturedProperty.address?.fullAddress,
    capturedProperty.address?.district,
    capturedProperty.propertyInfo?.propertyName,
    capturedProperty.existingUse,
  ]
    .map(normalizeUseSignal)
    .filter(Boolean)

  const hasIndustrialSignal = signals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      /\bb[12]\b/.test(signal) ||
      signal.includes('business 1') ||
      signal.includes('business 2') ||
      signal.includes('industrial') ||
      compact === 'sgindustrial' ||
      compact === 'b1' ||
      compact === 'b2'
    )
  })

  if (hasIndustrialSignal) {
    return ['Industrial', 'Office']
  }

  const hasBusinessParkZoningSignal = zoningSignals.some((signal) => {
    const compact = signal.replace(/[^a-z0-9]/g, '')
    return (
      signal.includes('business park') ||
      compact.includes('businesspark') ||
      compact.startsWith('sgbusinesspark')
    )
  })

  if (hasBusinessParkZoningSignal) {
    return ['Business park', 'Office-lab']
  }

  const hasHospitalitySignal = [...zoningSignals, ...propertyUseSignals].some(
    (signal) => {
      const compact = signal.replace(/[^a-z0-9]/g, '')
      return (
        signal.includes('hotel') ||
        signal.includes('hospitality') ||
        compact === 'sghotel'
      )
    },
  )

  if (hasHospitalitySignal) {
    return ['Hotel', 'Retail']
  }

  const hasHealthcareZoningSignal = zoningSignals.some((signal, index) => {
    const compact = compactZoningSignals[index]
    return (
      signal.includes('health') ||
      signal.includes('medical') ||
      signal.includes('hospital') ||
      compact.includes('healthmedicalcare') ||
      compact === 'sghealthmedicalcare'
    )
  })

  if (hasHealthcareZoningSignal) {
    return ['Healthcare', 'Institutional']
  }

  const hasSportsRecreationZoningSignal = zoningSignals.some(
    (signal, index) => {
      const compact = compactZoningSignals[index]
      return (
        signal.includes('sports') ||
        signal.includes('recreation') ||
        compact.includes('sportsrecreation') ||
        compact === 'sgsportsrecreation'
      )
    },
  )

  if (hasSportsRecreationZoningSignal) {
    return ['Recreation', 'Amenities']
  }

  const hasInstitutionalZoningSignal = zoningSignals.some((signal, index) => {
    const compact = compactZoningSignals[index]
    return (
      signal.includes('civic') ||
      signal.includes('community institution') ||
      signal.includes('educational institution') ||
      signal.includes('institution') ||
      signal.includes('university') ||
      signal.includes('school') ||
      compact.includes('civicinstitution') ||
      compact.includes('educationalinstitution') ||
      compact === 'sgcivicinstitutional'
    )
  })

  if (hasInstitutionalZoningSignal) {
    return ['Institutional', 'Amenities']
  }

  const hasSimLimSignal = signals.some((signal, index) => {
    const compact = compactSignals[index]
    return signal.includes('sim lim') || compact === 'simlimtower'
  })

  if (hasSimLimSignal) {
    return ['Office', 'Retail']
  }

  const hasMixedUseZoningSignal = zoningSignals.some((signal, index) => {
    const compact = compactZoningSignals[index]
    return (
      signal.includes('mixed use') ||
      signal.includes('mixed-use') ||
      compact === 'mu' ||
      compact === 'mixeduse' ||
      compact === 'sgmixeduse'
    )
  })

  if (hasMixedUseZoningSignal) {
    return ['Mixed-use', 'Retail', 'Residential']
  }

  const hasResidentialZoningSignal = zoningSignals.some((signal, index) => {
    const compact = compactZoningSignals[index]
    return (
      signal.includes('residential') ||
      signal.includes('housing') ||
      compact === 'r'
    )
  })

  if (hasResidentialZoningSignal) {
    return ['Residential', 'Amenities']
  }

  const hasRetailSpecificSignal = signals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      signal.includes('orchard') ||
      signal.includes('retail') ||
      signal.includes('shopping') ||
      signal.includes('mall') ||
      signal.includes('restaurant') ||
      compact.includes('shoppingcentre') ||
      compact.includes('shoppingmall')
    )
  })

  if (hasRetailSpecificSignal) {
    return ['Retail', 'Office']
  }

  const hasResidentialSignal = signals.some((signal, index) => {
    const compact = compactSignals[index]
    return (
      signal.includes('residential') ||
      signal.includes('housing') ||
      compact === 'r'
    )
  })

  if (hasResidentialSignal) {
    return ['Residential', 'Amenities']
  }

  return null
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
  scenario: CaptureRecommendationScenario
  reasonCodes: string[]
  confidence: CaptureScenarioRecommendationV2['confidence']
} {
  const status = deriveCurrentVsCodeStatus(capturedProperty)
  const specialZoningControl = deriveSpecialZoningControl(capturedProperty)
  const heritageDetected =
    Boolean(capturedProperty.heritageContext?.flag) ||
    Boolean(capturedProperty.heritageContext?.overlay?.name)

  if (specialZoningControl) {
    const reasonCodes =
      specialZoningControl.kind === 'specialized_operator'
        ? ['SPECIALIZED_OPERATOR_LED_ZONE', 'CURRENT_CODE_COMPARISON_PENDING']
        : [
            'NON_STANDARD_OR_NON_DEVELOPABLE_ZONE',
            'MAP_POINT_OR_CONTROL_REVIEW_REQUIRED',
          ]
    return {
      scenario: 'scenario_pending',
      reasonCodes,
      confidence: 'low',
    }
  }

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

  const currentGfa = capturedProperty.buildEnvelope.currentGfaSqm
  const additionalPotential =
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm ?? null
  const siteDevelopmentStatus = deriveSiteDevelopmentStatus(capturedProperty)
  const siteDevelopmentSourceKind =
    deriveSiteDevelopmentSourceKind(capturedProperty)

  if (currentGfa == null) {
    if (siteDevelopmentStatus === 'vacant') {
      return {
        scenario: 'raw_land',
        reasonCodes: [
          'NO_BUILDING_FOOTPRINT_DETECTED',
          'GROUND_UP_STUDY_BASELINE',
        ],
        confidence: 'medium',
      }
    }
    return {
      scenario: 'scenario_pending',
      reasonCodes: [
        'EXISTING_GFA_UNAVAILABLE',
        siteDevelopmentStatus === 'developed'
          ? siteDevelopmentSourceKind === 'capture_address_evidence'
            ? 'EXISTING_ASSET_EVIDENCE_DETECTED'
            : 'EXISTING_BUILDING_FOOTPRINT_DETECTED'
          : 'EXISTING_ASSET_STATUS_UNRESOLVED',
        'CURRENT_CODE_COMPARISON_PENDING',
      ],
      confidence: 'low',
    }
  }

  if (currentGfa <= 0) {
    return {
      scenario: 'raw_land',
      reasonCodes: [
        'CURRENT_GFA_ZERO_OR_UNAVAILABLE',
        'GROUND_UP_STUDY_BASELINE',
      ],
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

function buildProgramDirection(
  capturedProperty: SiteAcquisitionResult,
  recommendedScenario: CaptureRecommendationScenario,
): Pick<
  CaptureScenarioRecommendationV2,
  'programDirectionLabel' | 'programDirectionSummary' | 'programDrivers'
> {
  const specialZoningControl = deriveSpecialZoningControl(capturedProperty)
  if (specialZoningControl) {
    return {
      programDirectionLabel: specialZoningControl.label,
      programDirectionSummary: specialZoningControl.summary,
      programDrivers: specialZoningControl.drivers,
    }
  }

  const optimizationCandidates = capturedProperty.optimizations
    .map((entry) => ({
      assetType: entry.assetType,
      label: formatAssetTypeLabel(entry.assetType),
      weight:
        entry.allocationPct ??
        entry.allocatedGfaSqm ??
        entry.niaEfficiency ??
        0,
    }))
    .filter((entry) => entry.assetType && entry.weight > 0)
    .sort((left, right) => right.weight - left.weight)

  const existingUseFallback =
    capturedProperty.existingUse &&
    !/^unknown$/i.test(capturedProperty.existingUse.trim())
      ? capturedProperty.existingUse.trim()
      : null
  const fallbackAssetType =
    existingUseFallback ||
    capturedProperty.buildEnvelope.zoneDescription?.trim() ||
    capturedProperty.uraZoning?.zoneDescription?.trim() ||
    capturedProperty.uraZoning?.useGroups?.[0]?.trim() ||
    'mixed_use'

  const zoningProgramDrivers = deriveZoningProgramDrivers(capturedProperty)
  const primary =
    zoningProgramDrivers?.[0] ??
    optimizationCandidates[0]?.label ??
    formatAssetTypeLabel(fallbackAssetType)
  const secondaryCandidate = optimizationCandidates[1]
  const secondary =
    zoningProgramDrivers?.find((driver) => driver !== primary) ??
    (secondaryCandidate &&
    secondaryCandidate.weight >= 15 &&
    secondaryCandidate.label !== primary
      ? secondaryCandidate.label
      : null)

  const programSummaryLabel = secondary
    ? `${primary.toLowerCase()}-led program with ${secondary.toLowerCase()} support`
    : `${primary.toLowerCase()}-focused program`
  const programDrivers = secondary ? [primary, secondary] : [primary]

  switch (recommendedScenario) {
    case 'scenario_pending':
      return {
        programDirectionLabel: secondary
          ? `${primary}-led program pending`
          : `${primary}-focused program pending`,
        programDirectionSummary: `Based on today's zoning, Capture can identify ${programSummaryLabel}. Scenario selection is pending until current GFA evidence is available.`,
        programDrivers,
      }
    case 'heritage_property':
      return {
        programDirectionLabel: secondary
          ? `${primary}-led heritage mix`
          : `${primary}-led heritage program`,
        programDirectionSummary: `Capture is favouring a conservation-compatible ${programSummaryLabel} under the current heritage controls.`,
        programDrivers,
      }
    case 'existing_building':
      return {
        programDirectionLabel: secondary
          ? `${primary}-led renovation mix`
          : `${primary}-led renovation`,
        programDirectionSummary: `Capture is shaping the starter model around ${programSummaryLabel} for renovation within the current-code envelope.`,
        programDrivers,
      }
    case 'underused_asset':
      return {
        programDirectionLabel: secondary
          ? `${primary}-led adaptive reuse mix`
          : `${primary}-led adaptive reuse`,
        programDirectionSummary: `Capture is steering the starter model toward ${programSummaryLabel} while preserving reusable existing bulk.`,
        programDrivers,
      }
    case 'mixed_use_redevelopment':
      return {
        programDirectionLabel: secondary
          ? `${primary}-led mixed-use redevelopment`
          : `${primary}-led redevelopment`,
        programDirectionSummary: `Capture is treating the site as a redevelopment play with ${programSummaryLabel}.`,
        programDrivers,
      }
    case 'raw_land':
    default:
      return {
        programDirectionLabel: secondary
          ? `${primary}-led mixed-use development`
          : `${primary}-led ground-up development`,
        programDirectionSummary: `Capture is shaping the first massing around ${programSummaryLabel} under the current zoning envelope.`,
        programDrivers,
      }
  }
}

function buildHeritageExplanation(
  capturedProperty: SiteAcquisitionResult,
): string {
  const heritageName = capturedProperty.heritageContext?.overlay?.name?.trim()
  if (heritageName) {
    return `Heritage context detected: ${heritageName}. Capture prioritises a conservation-compatible starting path.`
  }
  return 'Heritage context is present, so Capture prioritises a conservation-compatible starting path.'
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

  const explicitOverride = options.overrideScenario ?? null

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
      ? buildHeritageExplanation(capturedProperty)
      : recommended === 'scenario_pending'
        ? (deriveSpecialZoningControl(capturedProperty)?.explanation ??
          (deriveSiteDevelopmentStatus(capturedProperty) === 'developed'
            ? deriveSiteDevelopmentSourceKind(capturedProperty) ===
              'capture_address_evidence'
              ? 'Capture detected existing-asset evidence, but needs current GFA before recommending renovation or redevelopment.'
              : 'Capture detected an existing building footprint, but needs current GFA before recommending renovation or redevelopment.'
            : 'Capture needs current GFA or existing-asset evidence before recommending renovation, redevelopment, or ground-up.'))
        : recommended === 'existing_building'
          ? 'Existing bulk and current-code conditions favour a renovation-first starting point.'
          : recommended === 'underused_asset'
            ? 'Existing conditions appear reusable and current controls still leave headroom for uplift.'
            : 'No existing bulk was detected, so Capture starts from a ground-up massing path.'

  const alternatives = availableScenarios.filter(
    (scenario) => scenario !== recommended,
  )
  const programDirection = buildProgramDirection(capturedProperty, recommended)

  return {
    recommended,
    defaultRecommended: ruleChoice.scenario,
    alternatives,
    reasonCodes,
    explanation,
    programDirectionLabel: programDirection.programDirectionLabel,
    programDirectionSummary: programDirection.programDirectionSummary,
    programDrivers: programDirection.programDrivers,
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
        assetProfiles: [],
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
        assetProfiles: [],
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
        assetProfiles: [],
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
    grossPlotRatio:
      envelope.grossPlotRatio ??
      envelope.allowablePlotRatio ??
      zoning?.plotRatio ??
      null,
    maxBuildableGfaSqm: envelope.maxBuildableGfaSqm,
    currentGfaSqm: envelope.currentGfaSqm,
    sourceReference: envelope.sourceReference ?? null,
    currentVsCodeStatus,
    grandfatheredLikelihood: deriveGrandfatheredLikelihood(
      currentVsCodeStatus,
      capturedProperty,
    ),
    setbacks: {
      frontM: envelope.setbackFrontM,
      rearM: envelope.setbackRearM,
      sideM: envelope.setbackSideM,
    },
    stepBacks: envelope.stepBacks,
    buildingHeightLimitM:
      envelope.buildingHeightLimitM ?? zoning?.buildingHeightLimit ?? null,
    siteCoveragePct: envelope.siteCoveragePct ?? zoning?.siteCoverage ?? null,
    airRightsNote: envelope.airRightsNote,
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
    codeConstraints.setbacks.frontM,
    codeConstraints.setbacks.rearM,
    codeConstraints.setbacks.sideM,
    codeConstraints.stepBacks.length ? codeConstraints.stepBacks.length : null,
    codeConstraints.airRightsNote,
  ].filter((value) => value !== null && value !== undefined).length

  const missingInputs: string[] = []
  if (
    codeConstraints.setbacks.frontM == null &&
    codeConstraints.setbacks.rearM == null &&
    codeConstraints.setbacks.sideM == null
  ) {
    missingInputs.push('setbacks')
  }
  if (codeConstraints.stepBacks.length === 0) {
    missingInputs.push('step-backs')
  }
  missingInputs.push('floor-by-floor compliance')
  if (!codeConstraints.airRightsNote) {
    missingInputs.push('air-rights review')
  }
  missingInputs.push('solar orientation')
  missingInputs.push('terrain profile')

  return {
    completenessPct: Math.round((resolvedSignals / 10) * 100),
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
      getPreviewScenarioForRecommendation(scenarioRecommendation.recommended),
    ),
    starterModel: buildStarterModel(
      capturedProperty,
      getPreviewScenarioForRecommendation(scenarioRecommendation.recommended),
    ),
    scenarioRecommendation,
    analysisStatus: buildAnalysisStatus(capturedProperty),
    sourceCapture: capturedProperty,
  }
}
