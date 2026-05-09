import { afterEach, describe, expect, it, vi } from 'vitest'

import { requestStarterModelForScenario } from './siteAcquisition'

describe('requestStarterModelForScenario', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('posts a scenario-specific starter-model request and maps the created preview job', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 'preview-job-1',
          property_id: 'prop-123',
          scenario: 'existing_building',
          status: 'queued',
          preview_url: null,
          metadata_url: null,
          thumbnail_url: null,
          asset_version: null,
          requested_at: '2026-04-07T09:34:05Z',
          started_at: null,
          finished_at: null,
          message: null,
          geometry_detail_level: 'medium',
          starter_model_assumptions: {
            wall_thickness_mm: 210,
            core_ratio_pct: 15,
            common_area_ratio_pct: 11,
            floor_to_floor_m: 3.7,
            clear_ceiling_m: 2.7,
            hvac_space_ratio_pct: 7,
            electrical_space_ratio_pct: 4,
            retention_strategy: 'preserve_existing_bulk',
            efficiency_factor: 0.96,
            source: 'hybrid',
            provenance: {
              summary: 'rules_with_property_adjustments',
              fields: {
                floor_to_floor_m: 'property_specific',
                efficiency_factor: 'property_specific',
                wall_thickness_mm: 'rules',
              },
              adjustments: ['older_building_age'],
            },
            asset_profiles: [
              {
                asset_type: 'office',
                floor_to_floor_m: 3.7,
                clear_ceiling_m: 2.7,
                nia_efficiency: 0.82,
                source: 'hybrid',
              },
              {
                asset_type: 'retail',
                floor_to_floor_m: 4.8,
                clear_ceiling_m: 3.8,
                nia_efficiency: 0.82,
                source: 'hybrid',
              },
            ],
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )

    const result = await requestStarterModelForScenario({
      propertyId: 'prop-123',
      scenario: 'existing_building',
      detailLevel: 'medium',
      colorLegend: [
        {
          assetType: 'office',
          label: 'Office',
          color: '#3366ff',
          description: 'Primary use',
        },
      ],
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        '/api/v1/developers/properties/prop-123/preview-jobs',
      ),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario: 'existing_building',
          geometry_detail_level: 'medium',
          color_legend: [
            {
              asset_type: 'office',
              label: 'Office',
              color: '#3366ff',
              description: 'Primary use',
            },
          ],
        }),
      }),
    )
    expect(result.outcome).toBe('created')
    expect(result.job).toMatchObject({
      scenario: 'existing_building',
      status: 'queued',
      geometryDetailLevel: 'medium',
      starterModelAssumptions: {
        floorToFloorM: 3.7,
        source: 'hybrid',
        retentionStrategy: 'preserve_existing_bulk',
        efficiencyFactor: 0.96,
        provenance: {
          summary: 'rules_with_property_adjustments',
          fields: expect.objectContaining({
            floor_to_floor_m: 'property_specific',
          }),
          adjustments: ['older_building_age'],
        },
        assetProfiles: [
          expect.objectContaining({
            assetType: 'office',
            floorToFloorM: 3.7,
          }),
          expect.objectContaining({
            assetType: 'retail',
            floorToFloorM: 4.8,
          }),
        ],
      },
    })
  })

  it('returns unsupported for endpoints that are not available yet', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(null, { status: 405 }),
    )

    const result = await requestStarterModelForScenario({
      propertyId: 'prop-123',
      scenario: 'raw_land',
    })

    expect(result).toEqual({ job: null, outcome: 'unsupported' })
  })
})
