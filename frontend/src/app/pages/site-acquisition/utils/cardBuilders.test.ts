import { describe, expect, it } from 'vitest'

import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import { buildPropertyOverviewCards } from './cardBuilders'

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
    propertyInfo: {
      propertyName: 'Example Tower',
      tenure: '99-year leasehold',
      completionYear: 2005,
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
    heritageContext: null,
    visualization: {
      status: 'queued',
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
    optimizations: [
      {
        assetType: 'office',
        allocationPct: 100,
        allocatedGfaSqm: 21000,
        niaEfficiency: 0.85,
        targetFloorHeightM: 3.8,
        parkingRatioPer1000Sqm: 1.2,
        rentPsmMonth: 12,
        stabilisedVacancyPct: 0.05,
        opexPctOfRent: 0.1,
        estimatedRevenueSgd: 1000000,
        estimatedCapexSgd: 500000,
        fitoutCostPsm: 120,
        absorptionMonths: 12,
        riskLevel: 'moderate',
        heritagePremiumPct: null,
        notes: ['Should not appear on capture overview cards'],
      },
    ],
    financialSummary: {
      totalEstimatedRevenueSgd: 1000000,
      totalEstimatedCapexSgd: 500000,
      dominantRiskProfile: 'moderate',
      notes: ['Should not appear on capture overview cards'],
      financeBlueprint: null,
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
    quickAnalysis: {
      generatedAt: '2026-01-06T10:00:00Z',
      scenarios: [],
    },
    previewJobs: [],
  } as SiteAcquisitionResult
}

describe('buildPropertyOverviewCards', () => {
  it('keeps capture overview focused on instant code/envelope status', () => {
    const cards = buildPropertyOverviewCards({
      capturedProperty: buildCapturedProperty(),
      previewJob: null,
      colorLegendEntries: [],
      formatters: {
        formatNumber: (value, options) =>
          new Intl.NumberFormat('en-SG', options).format(value),
        formatCurrency: (value) =>
          `S$${new Intl.NumberFormat('en-SG', {
            maximumFractionDigits: 0,
          }).format(value)}`,
        formatTimestamp: (value) => value,
      },
      currencySymbol: 'S$',
    })

    expect(cards.map((card) => card.title)).toContain('Analysis status')
    expect(cards.map((card) => card.title)).not.toContain('Financial snapshot')
    expect(cards.map((card) => card.title)).not.toContain(
      'Market & connectivity',
    )
    expect(cards.map((card) => card.title)).not.toContain(
      'Recommended asset mix',
    )
  })
})
