import { describe, expect, it } from 'vitest'

import type {
  PreviewJob,
  SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
import {
  buildScenarioRecommendation,
  deriveCurrentVsCodeStatus,
  deriveGrandfatheredLikelihood,
  mapSiteAcquisitionResultToCaptureResultV2,
} from './captureResultV2'

function buildCapturedProperty(): SiteAcquisitionResult {
  return {
    propertyId: 'prop-1',
    currencySymbol: 'S$',
    timestamp: '2026-04-07T09:34:05Z',
    jurisdictionCode: 'SG',
    existingUse: 'Office',
    address: {
      fullAddress: '1 Example Street, Singapore 048616',
      district: 'Downtown Core',
    },
    coordinates: {
      latitude: 1.284,
      longitude: 103.851,
    },
    propertyInfo: {
      propertyName: 'Example Tower',
      tenure: '99-year leasehold',
      siteAreaSqm: 5000,
      gfaApproved: 18000,
      buildingHeight: 36,
      completionYear: 2005,
      lastTransactionDate: null,
      lastTransactionPrice: null,
    },
    buildEnvelope: {
      zoneCode: 'C',
      zoneDescription: 'Commercial',
      siteAreaSqm: 5000,
      allowablePlotRatio: 4.2,
      grossPlotRatio: 4.2,
      maxBuildableGfaSqm: 21000,
      currentGfaSqm: 18000,
      additionalPotentialGfaSqm: 3000,
      buildingHeightLimitM: 36,
      siteCoveragePct: 50,
      setbackFrontM: null,
      setbackRearM: null,
      setbackSideM: null,
      stepBacks: [],
      airRightsNote: null,
      assumptions: [],
      sourceReference: 'URA Mock',
      ruleCorpusStatus: null,
    },
    visualization: {
      status: 'placeholder',
      previewAvailable: false,
      notes: ['Instant capture only'],
      conceptMeshUrl: null,
      previewMetadataUrl: null,
      thumbnailUrl: null,
      cameraOrbitHint: null,
      previewSeed: null,
      previewJobId: null,
      massingLayers: [],
      colorLegend: [],
    },
    optimizations: [],
    financialSummary: {
      totalEstimatedRevenueSgd: null,
      totalEstimatedCapexSgd: null,
      dominantRiskProfile: null,
      notes: [],
      financeBlueprint: null,
    },
    heritageContext: null,
    previewJobs: [],
    uraZoning: {
      zoneCode: 'C',
      zoneDescription: 'Commercial',
      plotRatio: 4.2,
      buildingHeightLimit: 36,
      siteCoverage: 50,
      useGroups: ['Office'],
      specialConditions: 'Minimum unit size applies',
    },
    nearbyAmenities: null,
    quickAnalysis: {
      generatedAt: '2026-04-07T09:34:05Z',
      scenarios: [],
    },
  } as SiteAcquisitionResult
}

describe('captureResultV2', () => {
  it('marks above-code existing bulk as likely grandfathered and recommends existing-building path', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.currentGfaSqm = 25000
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 14000
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = 0

    expect(deriveCurrentVsCodeStatus(capturedProperty)).toBe('above')
    expect(deriveGrandfatheredLikelihood('above', capturedProperty)).toBe(
      'high',
    )

    const recommendation = buildScenarioRecommendation(capturedProperty)
    expect(recommendation.recommended).toBe('existing_building')
    expect(recommendation.defaultRecommended).toBe('existing_building')
    expect(recommendation.userOverride).toBe(false)
    expect(recommendation.reasonCodes).toEqual(
      expect.arrayContaining([
        'CURRENT_GFA_EXCEEDS_CURRENT_CODE',
        'LIKELY_GRANDFATHERED_CONDITION',
      ]),
    )
  })

  it('recommends underused asset when an existing building remains below today’s envelope', () => {
    const recommendation = buildScenarioRecommendation(buildCapturedProperty())

    expect(recommendation.recommended).toBe('underused_asset')
    expect(recommendation.defaultRecommended).toBe('underused_asset')
    expect(recommendation.reasonCodes).toEqual(
      expect.arrayContaining([
        'CODE_HEADROOM_AVAILABLE',
        'REUSE_OR_EXPANSION_POSSIBLE',
      ]),
    )
  })

  it('keeps missing existing GFA as pending instead of assuming raw land or renovation', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.confidence).toBe('low')
    expect(recommendation.reasonCodes).toEqual(
      expect.arrayContaining([
        'EXISTING_GFA_UNAVAILABLE',
        'CURRENT_CODE_COMPARISON_PENDING',
      ]),
    )
  })

  it('biases heritage path before other scenario rules', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.optimizations = [
      {
        assetType: 'retail',
        allocationPct: 55,
        allocatedGfaSqm: 7700,
        niaEfficiency: 0.74,
        targetFloorHeightM: 4.8,
        parkingRatioPer1000Sqm: null,
        rentPsmMonth: null,
        stabilisedVacancyPct: null,
        opexPctOfRent: null,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        fitoutCostPsm: null,
        absorptionMonths: null,
        riskLevel: null,
        heritagePremiumPct: null,
        notes: [],
      },
      {
        assetType: 'amenities',
        allocationPct: 20,
        allocatedGfaSqm: 2800,
        niaEfficiency: 0.78,
        targetFloorHeightM: 3.6,
        parkingRatioPer1000Sqm: null,
        rentPsmMonth: null,
        stabilisedVacancyPct: null,
        opexPctOfRent: null,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        fitoutCostPsm: null,
        absorptionMonths: null,
        riskLevel: null,
        heritagePremiumPct: null,
        notes: [],
      },
    ]
    capturedProperty.heritageContext = {
      flag: true,
      risk: 'medium',
      notes: [],
      constraints: ['Conservation dialogue required'],
      assumption: null,
      overlay: {
        name: 'Conservation Area',
        source: 'URA',
        heritagePremiumPct: null,
      },
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('heritage_property')
    expect(recommendation.defaultRecommended).toBe('heritage_property')
    expect(recommendation.confidence).toBe('high')
    expect(recommendation.reasonCodes).toContain('HERITAGE_OVERLAY_DETECTED')
    expect(recommendation.programDirectionLabel).toBe('Retail-led heritage mix')
    expect(recommendation.programDrivers).toEqual(['Retail', 'Amenities'])
  })

  it('honours an explicit override even when code logic would prefer renovation', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.currentGfaSqm = 25000
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 14000

    const recommendation = buildScenarioRecommendation(capturedProperty, {
      overrideScenario: 'raw_land',
      selectedScenarios: ['raw_land', 'existing_building'],
    })

    expect(recommendation.recommended).toBe('raw_land')
    expect(recommendation.defaultRecommended).toBe('existing_building')
    expect(recommendation.userOverride).toBe(true)
    expect(recommendation.overrideIntent).toBe('exploratory')
    expect(recommendation.reasonCodes[0]).toBe('EXPLORATORY_OVERRIDE')
    expect(recommendation.explanation).toBe(
      'Exploratory new construction override is active for this session.',
    )
    expect(recommendation.alternatives).toContain('existing_building')
  })

  it('does not let a single requested scenario replace the rule-based recommendation', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.currentGfaSqm = 25000
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 14000
    capturedProperty.heritageContext = {
      flag: true,
      risk: 'medium',
      notes: ['Source: NHB Historic Site'],
      constraints: ['Heritage record.'],
      assumption: 'Heritage overlay detected.',
      overlay: {
        name: 'Central Sikh Temple',
        source: 'NHB Historic Site',
        heritagePremiumPct: null,
      },
    }

    const recommendation = buildScenarioRecommendation(capturedProperty, {
      selectedScenarios: ['existing_building'],
    })

    expect(recommendation.recommended).toBe('heritage_property')
    expect(recommendation.defaultRecommended).toBe('heritage_property')
    expect(recommendation.userOverride).toBe(false)
    expect(recommendation.reasonCodes).toContain('HERITAGE_OVERLAY_DETECTED')
    expect(recommendation.explanation).toBe(
      'Heritage context detected: Central Sikh Temple. Capture prioritises a conservation-compatible starting path.',
    )
  })

  it('uses industrial zoning signals before office defaults for renovation program direction', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.zoneCode = 'B1'
    capturedProperty.buildEnvelope.zoneDescription = 'Business 1'
    capturedProperty.buildEnvelope.currentGfaSqm = 25000
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 12500
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = 0
    capturedProperty.existingUse = 'Office'
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'B1',
      zoneDescription: 'Business 1',
      useGroups: ['Office'],
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('existing_building')
    expect(recommendation.programDirectionLabel).toBe(
      'Industrial-led renovation mix',
    )
    expect(recommendation.programDrivers).toEqual(['Industrial', 'Office'])
    expect(recommendation.programDirectionSummary).toBe(
      'Capture is shaping the starter model around industrial-led program with office support for renovation within the current-code envelope.',
    )
  })

  it('uses Sim Lim commercial address signals before stale residential defaults', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress =
      '10 Jln Besar, #11-06 Sim Lim Tower, Singapore 208787'
    capturedProperty.address.district = 'Rochor'
    capturedProperty.propertyInfo.propertyName = 'Sim Lim Tower'
    capturedProperty.buildEnvelope.zoneCode = 'R'
    capturedProperty.buildEnvelope.zoneDescription = 'Residential'
    capturedProperty.buildEnvelope.currentGfaSqm = 25000
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 14000
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = 0
    capturedProperty.existingUse = 'Residential'
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'R',
      zoneDescription: 'Residential',
      useGroups: ['Residential'],
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('existing_building')
    expect(recommendation.programDirectionLabel).toBe(
      'Office-led renovation mix',
    )
    expect(recommendation.programDrivers).toEqual(['Office', 'Retail'])
    expect(recommendation.programDirectionSummary).toBe(
      'Capture is shaping the starter model around office-led program with retail support for renovation within the current-code envelope.',
    )
  })

  it('does not let generic commercial hotel allowances drive an Orchard site to hospitality', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress = '2 Orchard Turn, Singapore 238801'
    capturedProperty.address.district = 'Orchard'
    capturedProperty.propertyInfo.propertyName = 'ION Orchard'
    capturedProperty.buildEnvelope.zoneCode = 'C'
    capturedProperty.buildEnvelope.zoneDescription = 'Commercial'
    capturedProperty.buildEnvelope.currentGfaSqm = 25000
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 60000
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = 35000
    capturedProperty.existingUse = 'Commercial Building'
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'C',
      zoneDescription: 'Commercial',
      plotRatio: 12,
      useGroups: ['Office', 'Retail', 'Hotel', 'Restaurant'],
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('underused_asset')
    expect(recommendation.programDirectionLabel).toBe(
      'Retail-led adaptive reuse mix',
    )
    expect(recommendation.programDrivers).toEqual(['Retail', 'Office'])
    expect(recommendation.programDirectionSummary).toBe(
      'Capture is steering the starter model toward retail-led program with office support while preserving reusable existing bulk.',
    )
  })

  it('keeps mixed-use Marina zoning from becoming residential-only', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress =
      '10 Marina Boulevard, Singapore 018983'
    capturedProperty.address.district = 'Marina Bay'
    capturedProperty.propertyInfo.propertyName = null
    capturedProperty.buildEnvelope.zoneCode = 'SG:mixed_use'
    capturedProperty.buildEnvelope.zoneDescription = null
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = null
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.existingUse = 'Unknown'
    capturedProperty.optimizations = []
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'SG:mixed_use',
      zoneDescription: null,
      plotRatio: null,
      useGroups: ['Commercial', 'Residential', 'Office'],
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.programDirectionLabel).toBe(
      'Mixed-use-led program pending',
    )
    expect(recommendation.programDrivers).toEqual(['Mixed-use', 'Retail'])
    expect(recommendation.programDirectionSummary).toBe(
      "Based on today's zoning, Capture can identify mixed-use-led program with retail support. Scenario selection is pending until current GFA evidence is available.",
    )
    expect(recommendation.explanation).toBe(
      'Capture needs current GFA or existing-asset evidence before recommending renovation, redevelopment, or ground-up.',
    )
  })

  it('recommends ground-up when building footprints indicate a vacant parcel', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 18000
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.buildEnvelope.ruleCorpusStatus = {
      site_development_status: 'vacant',
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('raw_land')
    expect(recommendation.reasonCodes).toContain(
      'NO_BUILDING_FOOTPRINT_DETECTED',
    )
    expect(recommendation.confidence).toBe('medium')
  })

  it('keeps scenario pending when a developed parcel lacks current GFA', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 18000
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.buildEnvelope.ruleCorpusStatus = {
      site_development_status: 'developed',
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.reasonCodes).toContain(
      'EXISTING_BUILDING_FOOTPRINT_DETECTED',
    )
    expect(recommendation.explanation).toBe(
      'Capture detected an existing building footprint, but needs current GFA before recommending renovation or redevelopment.',
    )
  })

  it('labels address-based existing asset evidence without claiming footprint evidence', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = null
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.buildEnvelope.ruleCorpusStatus = {
      site_development_status: 'developed',
      site_development_lookup_source: {
        kind: 'capture_address_evidence',
        status: 'developed',
        reason: 'resolved_building_address_without_footprint_coverage',
      },
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.reasonCodes).toContain(
      'EXISTING_ASSET_EVIDENCE_DETECTED',
    )
    expect(recommendation.reasonCodes).not.toContain(
      'EXISTING_BUILDING_FOOTPRINT_DETECTED',
    )
    expect(recommendation.explanation).toBe(
      'Capture detected existing-asset evidence, but needs current GFA before recommending renovation or redevelopment.',
    )
  })

  it('maps hotel zoning to a hotel-led pending program', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress = '10 Scotts Rd, Singapore'
    capturedProperty.propertyInfo.propertyName = null
    capturedProperty.buildEnvelope.zoneCode = 'SG:hotel'
    capturedProperty.buildEnvelope.zoneDescription = 'Hotel'
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 40790
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.existingUse = 'Unknown'
    capturedProperty.optimizations = []
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'SG:hotel',
      zoneDescription: 'Hotel',
      plotRatio: 4.2,
      useGroups: ['Hotel', 'Retail'],
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.programDirectionLabel).toBe(
      'Hotel-led program pending',
    )
    expect(recommendation.programDrivers).toEqual(['Hotel', 'Retail'])
    expect(recommendation.programDirectionSummary).toBe(
      "Based on today's zoning, Capture can identify hotel-led program with retail support. Scenario selection is pending until current GFA evidence is available.",
    )
  })

  it('uses hotel zoning code even when zoning use groups are empty', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.zoneCode = 'SG:hotel'
    capturedProperty.buildEnvelope.zoneDescription = null
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 40790
    capturedProperty.existingUse = 'Unknown'
    capturedProperty.optimizations = []
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'SG:hotel',
      zoneDescription: null,
      useGroups: [],
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.programDirectionLabel).toBe(
      'Hotel-led program pending',
    )
    expect(recommendation.programDrivers).toEqual(['Hotel', 'Retail'])
  })

  it('maps health and medical care zoning to a specialized operator-led pending program', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress =
      '5 Lower Kent Ridge Rd, Singapore 119074'
    capturedProperty.propertyInfo.propertyName = null
    capturedProperty.buildEnvelope.zoneCode = 'SG:health_medical_care'
    capturedProperty.buildEnvelope.zoneDescription = 'Health & Medical Care'
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = null
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.existingUse = 'Unknown'
    capturedProperty.optimizations = []
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'SG:health_medical_care',
      zoneDescription: 'Health & Medical Care',
      plotRatio: null,
      useGroups: ['Health & Medical Care'],
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.reasonCodes).toEqual([
      'SPECIALIZED_OPERATOR_LED_ZONE',
      'CURRENT_CODE_COMPARISON_PENDING',
    ])
    expect(recommendation.programDirectionLabel).toBe(
      'Specialized operator-led program',
    )
    expect(recommendation.programDrivers).toEqual([
      'Healthcare',
      'Institutional',
      'Operator-led use',
    ])
    expect(recommendation.programDirectionSummary).toBe(
      'Capture matched health/medical-care zoning. Scenario selection stays pending because this is a specialized operator-led use; Capture needs current GFA and site-specific controls before recommending renovation or redevelopment.',
    )
    expect(recommendation.explanation).toBe(
      recommendation.programDirectionSummary,
    )
  })

  it('maps sports and recreation zoning to a specialized operator-led pending program', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress = '39A Soon Lee Rd, Singapore'
    capturedProperty.propertyInfo.propertyName = null
    capturedProperty.buildEnvelope.zoneCode = 'SG:sports_recreation'
    capturedProperty.buildEnvelope.zoneDescription = 'Sports & Recreation'
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = null
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.existingUse = 'Unknown'
    capturedProperty.optimizations = []
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'SG:sports_recreation',
      zoneDescription: 'Sports & Recreation',
      plotRatio: null,
      useGroups: ['Sports & Recreation'],
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.programDirectionLabel).toBe(
      'Specialized operator-led program',
    )
    expect(recommendation.programDrivers).toEqual([
      'Recreation',
      'Amenities',
      'Operator-led use',
    ])
    expect(recommendation.programDirectionSummary).toBe(
      'Capture matched sports/recreation zoning. Scenario selection stays pending because this is a specialized operator-led use; Capture needs current GFA and site-specific controls before recommending renovation or redevelopment.',
    )
    expect(recommendation.explanation).toBe(
      recommendation.programDirectionSummary,
    )
  })

  it('maps business park white zoning to a business park program', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress =
      '1 Fusionopolis Way, Singapore 138632'
    capturedProperty.address.district = 'one-north'
    capturedProperty.propertyInfo.propertyName = null
    capturedProperty.buildEnvelope.zoneCode = 'SG:business_park_white'
    capturedProperty.buildEnvelope.zoneDescription = 'Business Park - White'
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 120738
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.existingUse = 'Unknown'
    capturedProperty.optimizations = []
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'SG:business_park_white',
      zoneDescription: 'Business Park - White',
      plotRatio: 3.5,
      useGroups: ['Business park', 'Office-lab'],
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.programDirectionLabel).toBe(
      'Business park-led program pending',
    )
    expect(recommendation.programDrivers).toEqual([
      'Business park',
      'Office-lab',
    ])
    expect(recommendation.programDirectionSummary).toBe(
      "Based on today's zoning, Capture can identify business park-led program with office-lab support. Scenario selection is pending until current GFA evidence is available.",
    )
  })

  it('keeps transport facilities zoning in control review instead of a standard program', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress = '28 Soon Lee Rd, Singapore 628083'
    capturedProperty.propertyInfo.propertyName = null
    capturedProperty.buildEnvelope.zoneCode = 'SG:transport_facilities'
    capturedProperty.buildEnvelope.zoneDescription = null
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = null
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.existingUse = 'Unknown'
    capturedProperty.optimizations = []
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'SG:transport_facilities',
      zoneDescription: null,
      plotRatio: null,
      useGroups: ['Transport', 'Logistics'],
      specialConditions: 'non_standard_or_non_developable_control',
      developmentControlStatus: 'non_standard_or_non_developable',
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.programDirectionLabel).toBe(
      'No standard private program',
    )
    expect(recommendation.programDrivers).toEqual([
      'Transport facilities',
      'Control review',
    ])
    expect(recommendation.programDirectionSummary).toBe(
      'Capture matched transport-facilities zoning. Scenario selection stays pending because this control is not a standard private development program; site-specific approval, rezoning, or public-use review may be required before a building scenario is studied.',
    )
    expect(recommendation.explanation).toBe(
      recommendation.programDirectionSummary,
    )
  })

  it('keeps road zoning in control review instead of a standard program', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress = '25 Soon Lee Rd, Singapore 628083'
    capturedProperty.propertyInfo.propertyName = null
    capturedProperty.buildEnvelope.zoneCode = 'SG:road'
    capturedProperty.buildEnvelope.zoneDescription = null
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = null
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.existingUse = 'Unknown'
    capturedProperty.optimizations = []
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'SG:road',
      zoneDescription: null,
      plotRatio: null,
      useGroups: ['Transport', 'Logistics'],
      specialConditions: 'non_standard_or_non_developable_control',
      developmentControlStatus: 'non_standard_or_non_developable',
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.reasonCodes).toEqual([
      'NON_STANDARD_OR_NON_DEVELOPABLE_ZONE',
      'MAP_POINT_OR_CONTROL_REVIEW_REQUIRED',
    ])
    expect(recommendation.programDirectionLabel).toBe(
      'No standard private program',
    )
    expect(recommendation.programDrivers).toEqual([
      'Road reserve',
      'Control review',
    ])
    expect(recommendation.explanation).toBe(
      'Capture matched road zoning. Scenario selection stays pending because this control is not a standard private development program; site-specific approval, rezoning, or public-use review may be required before a building scenario is studied.',
    )
  })

  it('keeps open-space zoning in control review instead of a standard program', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress =
      '11 Marina Boulevard, Singapore 018983'
    capturedProperty.propertyInfo.propertyName = null
    capturedProperty.buildEnvelope.zoneCode = 'SG:open_space'
    capturedProperty.buildEnvelope.zoneDescription = 'Open Space'
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = null
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.existingUse = 'Unknown'
    capturedProperty.optimizations = []
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'SG:open_space',
      zoneDescription: 'Open Space',
      plotRatio: null,
      useGroups: [],
      specialConditions: 'non_standard_or_non_developable_control',
      developmentControlStatus: 'non_standard_or_non_developable',
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.programDirectionLabel).toBe(
      'No standard private program',
    )
    expect(recommendation.programDrivers).toEqual([
      'Park / open space',
      'Control review',
    ])
    expect(recommendation.explanation).toBe(
      'Capture matched park/open-space zoning. Scenario selection stays pending because this control is not a standard private development program; site-specific approval, rezoning, or public-use review may be required before a building scenario is studied.',
    )
    expect(recommendation.programDirectionSummary).toBe(
      recommendation.explanation,
    )
  })

  it('keeps park zoning in non-standard program review instead of private development copy', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress = '1 Nassim Rd, Singapore'
    capturedProperty.propertyInfo.propertyName = null
    capturedProperty.buildEnvelope.zoneCode = 'SG:park'
    capturedProperty.buildEnvelope.zoneDescription = 'Park'
    capturedProperty.buildEnvelope.currentGfaSqm = null
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = null
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
    capturedProperty.existingUse = 'Unknown'
    capturedProperty.optimizations = []
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'SG:park',
      zoneDescription: 'Park',
      plotRatio: null,
      useGroups: [],
      specialConditions: 'non_standard_or_non_developable_control',
      developmentControlStatus: 'non_standard_or_non_developable',
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('scenario_pending')
    expect(recommendation.programDirectionLabel).toBe(
      'No standard private program',
    )
    expect(recommendation.programDrivers).toEqual([
      'Park / open space',
      'Control review',
    ])
    expect(recommendation.explanation).toBe(
      'Capture matched park/open-space zoning. Scenario selection stays pending because this control is not a standard private development program; site-specific approval, rezoning, or public-use review may be required before a building scenario is studied.',
    )
    expect(recommendation.programDirectionSummary).toBe(
      recommendation.explanation,
    )
  })

  it.each([
    {
      code: 'SG:educational_institution',
      description: 'Educational Institution',
      driver: 'Education',
      control: 'education',
    },
    {
      code: 'SG:special_use',
      description: 'Special Use',
      driver: 'Special use',
      control: 'special-use',
    },
    {
      code: 'SG:reserve_site',
      description: 'Reserve Site',
      driver: 'Reserve site',
      control: 'reserve-site',
    },
    {
      code: 'SG:civic_community_institution',
      description: 'Civic & Community Institution',
      driver: 'Civic/community institution',
      control: 'civic/community institution',
    },
  ])(
    'keeps $description zoning out of standard private scenario selection',
    ({ code, description, driver, control }) => {
      const capturedProperty = buildCapturedProperty()
      capturedProperty.address.fullAddress = `${description}, Singapore`
      capturedProperty.propertyInfo.propertyName = null
      capturedProperty.buildEnvelope.zoneCode = code
      capturedProperty.buildEnvelope.zoneDescription = description
      capturedProperty.buildEnvelope.currentGfaSqm = null
      capturedProperty.buildEnvelope.maxBuildableGfaSqm = null
      capturedProperty.buildEnvelope.additionalPotentialGfaSqm = null
      capturedProperty.existingUse = 'Unknown'
      capturedProperty.optimizations = []
      capturedProperty.uraZoning = {
        ...capturedProperty.uraZoning,
        zoneCode: code,
        zoneDescription: description,
        plotRatio: null,
        useGroups: [description],
        specialConditions: null,
        developmentControlStatus: null,
      }

      const recommendation = buildScenarioRecommendation(capturedProperty)

      expect(recommendation.recommended).toBe('scenario_pending')
      expect(recommendation.programDirectionLabel).toBe(
        'No standard private program',
      )
      expect(recommendation.programDrivers).toEqual([driver, 'Control review'])
      expect(recommendation.explanation).toBe(
        `Capture matched ${control} zoning. Scenario selection stays pending because this control is not a standard private development program; site-specific approval, rezoning, or public-use review may be required before a building scenario is studied.`,
      )
      expect(recommendation.programDirectionSummary).toBe(
        recommendation.explanation,
      )
    },
  )

  it('uses residential zoning before generic commercial and home-office fallbacks', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.address.fullAddress = '45 Burghley Dr, Singapore 559022'
    capturedProperty.address.district = 'Serangoon'
    capturedProperty.propertyInfo.propertyName = '45 Burghley Drive'
    capturedProperty.buildEnvelope.zoneCode = 'R'
    capturedProperty.buildEnvelope.zoneDescription = 'Residential'
    capturedProperty.buildEnvelope.currentGfaSqm = 25000
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 14000
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = 0
    capturedProperty.existingUse = 'Commercial Building'
    capturedProperty.uraZoning = {
      ...capturedProperty.uraZoning,
      zoneCode: 'R',
      zoneDescription: 'Residential',
      useGroups: ['Residential', 'Home Office'],
    }

    const recommendation = buildScenarioRecommendation(capturedProperty)

    expect(recommendation.recommended).toBe('existing_building')
    expect(recommendation.programDirectionLabel).toBe(
      'Residential-led renovation mix',
    )
    expect(recommendation.programDrivers).toEqual(['Residential', 'Amenities'])
    expect(recommendation.programDirectionSummary).toBe(
      'Capture is shaping the starter model around residential-led program with amenities support for renovation within the current-code envelope.',
    )
  })

  it('maps starter-model and analysis fields into CaptureResultV2', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.optimizations = [
      {
        assetType: 'office',
        allocationPct: 60,
        allocatedGfaSqm: 12600,
        niaEfficiency: 0.81,
        targetFloorHeightM: 4,
        parkingRatioPer1000Sqm: null,
        rentPsmMonth: null,
        stabilisedVacancyPct: null,
        opexPctOfRent: null,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        fitoutCostPsm: null,
        absorptionMonths: null,
        riskLevel: null,
        heritagePremiumPct: null,
        notes: [],
      },
      {
        assetType: 'retail',
        allocationPct: 25,
        allocatedGfaSqm: 5250,
        niaEfficiency: 0.79,
        targetFloorHeightM: 4.8,
        parkingRatioPer1000Sqm: null,
        rentPsmMonth: null,
        stabilisedVacancyPct: null,
        opexPctOfRent: null,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        fitoutCostPsm: null,
        absorptionMonths: null,
        riskLevel: null,
        heritagePremiumPct: null,
        notes: [],
      },
    ]
    const previewJob: PreviewJob = {
      id: 'preview-job-1',
      propertyId: capturedProperty.propertyId,
      scenario: 'underused_asset',
      status: 'ready',
      requestedAt: '2026-04-07T09:34:05Z',
      startedAt: '2026-04-07T09:34:07Z',
      finishedAt: '2026-04-07T09:34:12Z',
      previewUrl: '/static/dev-previews/example/preview.gltf',
      metadataUrl: '/static/dev-previews/example/preview.json',
      thumbnailUrl: '/static/dev-previews/example/thumb.png',
      assetVersion: '20260407093405',
      message: null,
      geometryDetailLevel: 'medium',
      starterModelAssumptions: {
        wallThicknessMm: 230,
        coreRatioPct: 17,
        commonAreaRatioPct: 13,
        floorToFloorM: 4,
        clearCeilingM: 2.9,
        hvacSpaceRatioPct: 7,
        electricalSpaceRatioPct: 4,
        structuralGridNote: 'selective repositioning',
        source: 'hybrid',
        retentionStrategy: 'selective_repositioning',
        efficiencyFactor: 0.99,
        provenance: {
          summary: 'rules_with_property_adjustments',
          fields: {
            floor_to_floor_m: 'property_specific',
            efficiency_factor: 'property_specific',
          },
          adjustments: ['older_building_age'],
        },
        assetProfiles: [
          {
            assetType: 'office',
            floorToFloorM: 4,
            clearCeilingM: 2.9,
            niaEfficiency: 0.81,
            source: 'hybrid',
          },
          {
            assetType: 'retail',
            floorToFloorM: 4.8,
            clearCeilingM: 3.7,
            niaEfficiency: 0.81,
            source: 'hybrid',
          },
        ],
      },
    }

    capturedProperty.previewJobs = [previewJob]
    capturedProperty.buildEnvelope = {
      ...capturedProperty.buildEnvelope,
      setbackFrontM: 7.5,
      setbackRearM: null,
      setbackSideM: 3,
      stepBacks: [{ level: 6, depthM: 4 }],
      airRightsNote: 'Subject to aviation height review.',
    }
    capturedProperty.visualization = {
      ...capturedProperty.visualization,
      status: 'ready',
      previewAvailable: true,
      conceptMeshUrl: '/static/dev-previews/example/preview.gltf',
      previewMetadataUrl: '/static/dev-previews/example/preview.json',
      thumbnailUrl: '/static/dev-previews/example/thumb.png',
      massingLayers: [
        {
          assetType: 'office',
          allocationPct: 100,
          gfaSqm: 21000,
          niaSqm: 17850,
          estimatedHeightM: 24,
          color: '#3366ff',
        },
      ],
      colorLegend: [],
    }

    const resultV2 = mapSiteAcquisitionResultToCaptureResultV2(capturedProperty)

    expect(resultV2.address.jurisdictionCode).toBe('SG')
    expect(resultV2.codeConstraints.currentVsCodeStatus).toBe('below')
    expect(resultV2.codeConstraints.grossPlotRatio).toBe(4.2)
    expect(resultV2.codeConstraints.sourceReference).toBe('URA Mock')
    expect(resultV2.codeConstraints.setbacks).toEqual({
      frontM: 7.5,
      rearM: null,
      sideM: 3,
    })
    expect(resultV2.codeConstraints.stepBacks).toEqual([
      { level: 6, depthM: 4 },
    ])
    expect(resultV2.codeConstraints.airRightsNote).toBe(
      'Subject to aviation height review.',
    )
    expect(resultV2.analysisStatus.missingInputs).not.toContain('setbacks')
    expect(resultV2.analysisStatus.missingInputs).not.toContain('step-backs')
    expect(resultV2.analysisStatus.missingInputs).not.toContain(
      'air-rights review',
    )
    expect(resultV2.analysisStatus.supportsFullCompliance).toBe(false)
    expect(resultV2.starterModel.status).toBe('ready')
    expect(resultV2.starterModel.modelUrl).toBe(
      '/static/dev-previews/example/preview.gltf',
    )
    expect(resultV2.starterModel.geometryScope).toBe('massing_stack')
    expect(resultV2.starterModel.generatedFrom).toEqual(
      expect.arrayContaining([
        'preview_job',
        'visualization_summary',
        'massing_layers',
      ]),
    )
    expect(resultV2.engineeringAssumptions.source).toBe('hybrid')
    expect(resultV2.engineeringAssumptions.floorToFloorM).toBe(4)
    expect(resultV2.engineeringAssumptions.retentionStrategy).toBe(
      'selective_repositioning',
    )
    expect(resultV2.engineeringAssumptions.provenance).toEqual(
      expect.objectContaining({
        summary: 'rules_with_property_adjustments',
        adjustments: ['older_building_age'],
      }),
    )
    expect(resultV2.engineeringAssumptions.assetProfiles).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          assetType: 'office',
          floorToFloorM: 4,
        }),
        expect.objectContaining({
          assetType: 'retail',
          floorToFloorM: 4.8,
        }),
      ]),
    )
    expect(resultV2.scenarioRecommendation.programDirectionLabel).toBe(
      'Office-led adaptive reuse mix',
    )
    expect(resultV2.scenarioRecommendation.programDrivers).toEqual([
      'Office',
      'Retail',
    ])
  })

  it('binds the starter model to the recommended or overridden scenario instead of the first preview job', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.previewJobs = [
      {
        id: 'preview-job-raw-land',
        propertyId: capturedProperty.propertyId,
        scenario: 'raw_land',
        status: 'ready',
        requestedAt: '2026-04-07T09:34:05Z',
        startedAt: '2026-04-07T09:34:07Z',
        finishedAt: '2026-04-07T09:34:12Z',
        previewUrl: '/static/dev-previews/example/raw-land.gltf',
        metadataUrl: '/static/dev-previews/example/raw-land.json',
        thumbnailUrl: '/static/dev-previews/example/raw-land.png',
        assetVersion: '20260407093405',
        message: null,
        geometryDetailLevel: 'medium',
      },
      {
        id: 'preview-job-renovation',
        propertyId: capturedProperty.propertyId,
        scenario: 'existing_building',
        status: 'ready',
        requestedAt: '2026-04-07T09:35:05Z',
        startedAt: '2026-04-07T09:35:07Z',
        finishedAt: '2026-04-07T09:35:12Z',
        previewUrl: '/static/dev-previews/example/renovation.gltf',
        metadataUrl: '/static/dev-previews/example/renovation.json',
        thumbnailUrl: '/static/dev-previews/example/renovation.png',
        assetVersion: '20260407093505',
        message: null,
        geometryDetailLevel: 'medium',
      },
    ]
    capturedProperty.buildEnvelope.currentGfaSqm = 25000
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 14000
    capturedProperty.visualization = {
      ...capturedProperty.visualization,
      status: 'ready',
      previewAvailable: true,
      conceptMeshUrl: '/static/dev-previews/example/fallback.gltf',
      previewMetadataUrl: '/static/dev-previews/example/fallback.json',
      thumbnailUrl: '/static/dev-previews/example/fallback.png',
      massingLayers: [
        {
          assetType: 'office',
          allocationPct: 100,
          gfaSqm: 21000,
          niaSqm: 17850,
          estimatedHeightM: 24,
          color: '#3366ff',
        },
      ],
      colorLegend: [],
    }

    const defaultResult =
      mapSiteAcquisitionResultToCaptureResultV2(capturedProperty)
    expect(defaultResult.scenarioRecommendation.recommended).toBe(
      'existing_building',
    )
    expect(defaultResult.scenarioRecommendation.defaultRecommended).toBe(
      'existing_building',
    )
    expect(defaultResult.starterModel.modelUrl).toBe(
      '/static/dev-previews/example/renovation.gltf',
    )

    const overriddenResult = mapSiteAcquisitionResultToCaptureResultV2(
      capturedProperty,
      {
        overrideScenario: 'raw_land',
        selectedScenarios: ['raw_land', 'existing_building'],
      },
    )
    expect(overriddenResult.scenarioRecommendation.recommended).toBe('raw_land')
    expect(overriddenResult.scenarioRecommendation.defaultRecommended).toBe(
      'existing_building',
    )
    expect(overriddenResult.starterModel.modelUrl).toBe(
      '/static/dev-previews/example/raw-land.gltf',
    )
  })
})
