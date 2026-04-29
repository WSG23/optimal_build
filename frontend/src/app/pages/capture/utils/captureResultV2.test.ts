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
