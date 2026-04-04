import { render, screen } from '@testing-library/react'
import React from 'react'
import { describe, expect, it } from 'vitest'

import type { SiteAcquisitionResult } from '../../../api/siteAcquisition'
import { FeasibilityOutputPanel } from '../components/FeasibilityOutputPanel'

function buildCaptureResult(): SiteAcquisitionResult {
  return {
    propertyId: 'prop-1',
    currencySymbol: 'S$',
    address: {
      fullAddress: '1 Example Street',
      district: 'Downtown Core',
    },
    coordinates: {
      latitude: 1.3,
      longitude: 103.85,
    },
    propertyInfo: {
      propertyName: 'Example Tower',
      tenure: '99-year leasehold',
      completionYear: 2005,
      lastTransactionDate: '2025-01-15',
      lastTransactionPrice: 185000000,
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
    existingUse: 'Commercial office tower',
    nearbyAmenities: {
      mrtStations: [{ name: 'Raffles Place', distanceM: 180 }],
      busStops: [{ name: 'One Raffles Quay', distanceM: 120 }],
      schools: [],
      shoppingMalls: [{ name: 'Marina Bay Link Mall', distanceM: 320 }],
      parks: [],
    },
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
    timestamp: '2026-01-06T10:00:00Z',
    jurisdictionCode: 'SG',
  } as SiteAcquisitionResult
}

describe('FeasibilityOutputPanel', () => {
  it('renders market and connectivity context from the captured property', () => {
    render(
      <FeasibilityOutputPanel
        status="success"
        assessment={null}
        result={null}
        captureResult={buildCaptureResult()}
        activeSiteLabel="1 Example Street"
        numberFormatter={new Intl.NumberFormat('en-SG', {
          maximumFractionDigits: 0,
        })}
        oneDecimalFormatter={new Intl.NumberFormat('en-SG', {
          minimumFractionDigits: 1,
          maximumFractionDigits: 1,
        })}
      />,
    )

    expect(screen.getByText('Market & Connectivity')).toBeInTheDocument()
    expect(screen.getByText('Commercial office tower')).toBeInTheDocument()
    expect(screen.getByText(/Raffles Place \(180 m\)/)).toBeInTheDocument()
    expect(screen.getByText(/One Raffles Quay \(120 m\)/)).toBeInTheDocument()
    expect(screen.getByText(/S\$185,000,000 · 15 Jan 2025/)).toBeInTheDocument()
    expect(screen.getByText('3 traced')).toBeInTheDocument()
  })
})
