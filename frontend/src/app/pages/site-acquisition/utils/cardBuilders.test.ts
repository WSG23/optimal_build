import { describe, expect, it } from 'vitest'

import type {
  PreviewJob,
  SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
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

  it('surfaces explicit GFA relationship and avoids raw preview URLs', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.propertyInfo!.completionYear = 2015
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 14000
    capturedProperty.buildEnvelope.currentGfaSqm = 25000
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = 0
    capturedProperty.uraZoning!.specialConditions = 'Minimum unit size applies'
    capturedProperty.visualization = {
      ...capturedProperty.visualization,
      status: 'ready',
      previewAvailable: true,
      conceptMeshUrl: '/static/dev-previews/example/preview.gltf',
      previewMetadataUrl: '/static/dev-previews/example/preview.json',
      thumbnailUrl: '/static/dev-previews/example/thumb.png',
      cameraOrbitHint: { theta: 48, phi: 32 },
      massingLayers: [
        {
          assetType: 'office',
          allocationPct: 100,
          gfaSqm: 14000,
          estimatedHeightM: 36,
        },
      ],
    } as SiteAcquisitionResult['visualization']

    const previewJob: PreviewJob = {
      id: 'preview-job-1',
      scenario: 'base',
      status: 'ready',
      requestedAt: '2026-04-07T09:34:05Z',
      startedAt: '2026-04-07T09:34:05Z',
      finishedAt: '2026-04-07T09:34:12Z',
      previewUrl: '/static/dev-previews/example/preview.gltf',
      metadataUrl: '/static/dev-previews/example/preview.json',
      thumbnailUrl: '/static/dev-previews/example/thumb.png',
      assetVersion: '20260407093405',
      message: null,
      geometryDetailLevel: 'medium',
    }

    const cards = buildPropertyOverviewCards({
      capturedProperty,
      previewJob,
      colorLegendEntries: [
        {
          assetType: 'office',
          label: 'Office',
          color: '#3366ff',
          description: 'Office layer',
        },
      ],
      formatters: {
        formatNumber: (value, options) =>
          new Intl.NumberFormat('en-SG', options).format(value),
        formatCurrency: (value) =>
          `S$${new Intl.NumberFormat('en-SG', {
            maximumFractionDigits: 0,
          }).format(value)}`,
        formatTimestamp: (value) =>
          new Intl.DateTimeFormat('en-SG', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
          }).format(new Date(value)),
      },
      currencySymbol: 'S$',
    })

    const locationCard = cards.find(
      (card) => card.title === 'Location & tenure',
    )
    const buildEnvelopeCard = cards.find(
      (card) => card.title === 'Build envelope',
    )
    const previewCard = cards.find(
      (card) => card.title === 'Preview Availability',
    )
    const previewJobCard = cards.find(
      (card) => card.title === 'Preview Job Status',
    )
    const zoningCard = cards.find((card) => card.title === 'Zoning & planning')

    expect(
      locationCard?.items.find((item) => item.label === 'Completion year')
        ?.value,
    ).toBe('2015')
    expect(
      buildEnvelopeCard?.items.find(
        (item) => item.label === 'Current vs max GFA',
      )?.value,
    ).toBe('25,000 sqm > 14,000 sqm')
    expect(
      buildEnvelopeCard?.items.find((item) => item.label === 'Envelope reading')
        ?.value,
    ).toBe('Likely grandfathered from a former code baseline')
    expect(
      buildEnvelopeCard?.items.find(
        (item) => item.label === 'Additional potential',
      )?.value,
    ).toBe('No current code-compliant uplift')
    expect(previewCard?.layout).toBe('status')
    expect(previewJobCard?.layout).toBe('status')
    expect(
      previewCard?.items.find((item) => item.label === 'Asset bundle')?.value,
    ).toBe('Mesh • Metadata • Thumbnail')
    expect(
      previewJobCard?.items.find((item) => item.label === 'Assets returned')
        ?.value,
    ).toBe('mesh, metadata, thumbnail')
    expect(
      previewCard?.items.some((item) =>
        item.value.includes('/static/dev-previews'),
      ),
    ).toBe(false)
    expect(
      previewJobCard?.items.some((item) =>
        item.value.includes('/static/dev-previews'),
      ),
    ).toBe(false)
    expect(zoningCard?.items.map((item) => item.label)).toEqual([
      'Special conditions',
    ])
  })

  it('shows remaining code-compliant capacity when current GFA is below the envelope', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 21000
    capturedProperty.buildEnvelope.currentGfaSqm = 18000
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = 3000

    const cards = buildPropertyOverviewCards({
      capturedProperty,
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

    const buildEnvelopeCard = cards.find(
      (card) => card.title === 'Build envelope',
    )
    expect(
      buildEnvelopeCard?.items.find(
        (item) => item.label === 'Current vs max GFA',
      )?.value,
    ).toBe('18,000 sqm < 21,000 sqm')
    expect(
      buildEnvelopeCard?.items.find((item) => item.label === 'Envelope reading')
        ?.value,
    ).toBe('Existing bulk remains below today’s envelope')
    expect(
      buildEnvelopeCard?.items.find(
        (item) => item.label === 'Additional potential',
      )?.value,
    ).toBe('3,000 sqm')
  })

  it('shows no uplift when current GFA matches the envelope exactly', () => {
    const capturedProperty = buildCapturedProperty()
    capturedProperty.buildEnvelope.maxBuildableGfaSqm = 21000
    capturedProperty.buildEnvelope.currentGfaSqm = 21000
    capturedProperty.buildEnvelope.additionalPotentialGfaSqm = 0

    const cards = buildPropertyOverviewCards({
      capturedProperty,
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

    const buildEnvelopeCard = cards.find(
      (card) => card.title === 'Build envelope',
    )
    expect(
      buildEnvelopeCard?.items.find(
        (item) => item.label === 'Current vs max GFA',
      )?.value,
    ).toBe('21,000 sqm = 21,000 sqm')
    expect(
      buildEnvelopeCard?.items.find((item) => item.label === 'Envelope reading')
        ?.value,
    ).toBe('Existing bulk matches today’s envelope')
    expect(
      buildEnvelopeCard?.items.find(
        (item) => item.label === 'Additional potential',
      )?.value,
    ).toBe('0 sqm')
  })
})
