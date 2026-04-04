import { renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import { useCaptureScenarioComparison } from './useCaptureScenarioComparison'

function buildCapturedProperty(): SiteAcquisitionResult {
  return {
    propertyId: 'prop-1',
    currencySymbol: 'S$',
    address: {
      fullAddress: '1 Example Street',
      district: 'Downtown',
    },
    coordinates: {
      latitude: 1.3,
      longitude: 103.85,
    },
    existingUse: 'Commercial office tower',
    propertyInfo: {
      propertyName: 'Example Tower',
      tenure: '99-year leasehold',
      completionYear: 2005,
    },
    nearbyAmenities: null,
    uraZoning: {
      zoneCode: 'C',
      zoneDescription: 'Commercial',
      plotRatio: 4.2,
      buildingHeightLimit: 120,
      siteCoverage: 80,
      useGroups: ['Office'],
      specialConditions: null,
    },
    buildEnvelope: {
      zoneCode: 'C',
      zoneDescription: 'Commercial',
      siteAreaSqm: 5000,
      allowablePlotRatio: 4.2,
      maxBuildableGfaSqm: 21000,
      currentGfaSqm: 18000,
      additionalPotentialGfaSqm: 3000,
      buildingHeightLimitM: 120,
      siteCoveragePct: 80,
      assumptions: [],
      sourceReference: null,
    },
    visualization: {
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
    quickAnalysis: {
      generatedAt: '2026-01-06T10:00:00Z',
      scenarios: [
        {
          scenario: 'raw_land',
          headline: 'Revenue upside and NOI expansion look attractive.',
          metrics: {
            potential_gfa_sqm: 21000,
            annual_noi: 9000000,
            estimated_capex: 40000000,
          },
          notes: [],
        },
      ],
    },
    timestamp: '2026-01-06T10:00:00Z',
    jurisdictionCode: 'SG',
  } as SiteAcquisitionResult
}

describe('useCaptureScenarioComparison', () => {
  it('keeps capture scenario data code-focused and sanitizes finance headlines', () => {
    const { result } = renderHook(() =>
      useCaptureScenarioComparison({
        capturedProperty: buildCapturedProperty(),
        activeScenario: 'raw_land',
        currencySymbol: 'S$',
      }),
    )

    const rawLand = result.current.scenarioComparisonData.find(
      (entry) => entry.key === 'raw_land',
    )

    expect(rawLand).toBeTruthy()
    expect(rawLand?.quickHeadline).toBe(
      'New Construction instant zoning and envelope scan available.',
    )
    expect(rawLand?.quickMetrics.map((metric) => metric.key)).toEqual([
      'potential_gfa_sqm',
    ])
    expect(rawLand?.quickMetrics.map((metric) => metric.key)).not.toContain(
      'annual_noi',
    )
    expect(rawLand?.quickMetrics.map((metric) => metric.key)).not.toContain(
      'estimated_capex',
    )
  })
})
