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
