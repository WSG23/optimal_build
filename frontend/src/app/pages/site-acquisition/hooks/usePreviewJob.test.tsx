import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type {
  DeveloperPreviewJob,
  SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
import { usePreviewJob } from './usePreviewJob'

const mockListPreviewJobs = vi.fn()
const mockRequestStarterModelForScenario = vi.fn()

vi.mock('../../../../api/siteAcquisition', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('../../../../api/siteAcquisition')>()
  return {
    ...actual,
    listPreviewJobs: (...args: unknown[]) => mockListPreviewJobs(...args),
    requestStarterModelForScenario: (...args: unknown[]) =>
      mockRequestStarterModelForScenario(...args),
    refreshPreviewJob: vi.fn(),
    fetchPreviewJob: vi.fn(),
  }
})

function buildCapturedProperty(): SiteAcquisitionResult {
  return {
    propertyId: 'prop-123',
    currencySymbol: 'S$',
    address: {
      fullAddress: '1 Example Street',
      district: 'Downtown',
    },
    coordinates: {
      latitude: 1.3,
      longitude: 103.85,
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
    heritageContext: {
      flag: true,
      risk: 'medium',
      notes: [],
      constraints: ['Conservation review required'],
      assumption: null,
      overlay: {
        name: 'Heritage overlay detected',
        source: 'URA',
        heritagePremiumPct: null,
      },
    },
    previewJobs: [],
    quickAnalysis: {
      generatedAt: '2026-04-13T12:57:00Z',
      scenarios: [],
    },
    timestamp: '2026-04-13T12:57:00Z',
    jurisdictionCode: 'SG',
  } as SiteAcquisitionResult
}

function buildPreviewJob(scenario: string, id: string): DeveloperPreviewJob {
  return {
    id,
    propertyId: 'prop-123',
    scenario,
    status: 'ready',
    previewUrl: `/static/${scenario}.gltf`,
    metadataUrl: `/static/${scenario}.json`,
    thumbnailUrl: `/static/${scenario}.png`,
    assetVersion: '20260413125700',
    requestedAt: '2026-04-13T12:57:00Z',
    startedAt: '2026-04-13T12:57:02Z',
    finishedAt: '2026-04-13T12:57:05Z',
    message: null,
    geometryDetailLevel: 'medium',
    starterModelAssumptions: {
      wallThicknessMm: 240,
      coreRatioPct: 14,
      commonAreaRatioPct: 14,
      floorToFloorM: 3.6,
      clearCeilingM: 2.7,
      hvacSpaceRatioPct: 9,
      electricalSpaceRatioPct: 5,
      structuralGridNote: 'conservation retention',
      source: 'rules',
      retentionStrategy: 'conservation_retention',
      efficiencyFactor: 0.92,
      provenance: {
        summary: 'rules_with_property_adjustments',
        fields: {
          retention_strategy: 'property_specific',
          efficiency_factor: 'property_specific',
        },
        adjustments: ['heritage_context'],
      },
    },
  }
}

describe('usePreviewJob', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ layers: [], color_legend: [] }),
      }),
    )
    mockListPreviewJobs.mockResolvedValue([])
    mockRequestStarterModelForScenario.mockResolvedValue({
      outcome: 'created',
      job: buildPreviewJob('heritage_property', 'preview-heritage'),
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('preserves a live generated preview job when switching away from and back to the recommended scenario', async () => {
    const capturedProperty = buildCapturedProperty()
    const { result, rerender } = renderHook(
      ({ preferredScenario }) =>
        usePreviewJob({
          capturedProperty,
          preferredScenario,
        }),
      {
        initialProps: {
          preferredScenario: 'heritage_property' as const,
        },
      },
    )

    await act(async () => {
      await result.current.handleEnsureStarterModel()
    })

    await waitFor(() => {
      expect(result.current.previewJob?.scenario).toBe('heritage_property')
    })

    rerender({ preferredScenario: 'raw_land' as const })

    await waitFor(() => {
      expect(result.current.previewJob).toBeNull()
    })

    rerender({ preferredScenario: 'heritage_property' as const })

    await waitFor(() => {
      expect(result.current.previewJob?.scenario).toBe('heritage_property')
      expect(
        result.current.previewJob?.starterModelAssumptions?.retentionStrategy,
      ).toBe('conservation_retention')
    })

    expect(mockRequestStarterModelForScenario).toHaveBeenCalledTimes(1)
  })
})
