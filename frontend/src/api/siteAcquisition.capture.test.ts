import { afterEach, describe, expect, it, vi } from 'vitest'

import { capturePropertyForDevelopment } from './siteAcquisition'

describe('capturePropertyForDevelopment', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('maps deeper envelope controls from the developer capture response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          property_id: 'prop-456',
          address: {
            full_address: '28 Soon Lee Rd, Singapore 628083',
            district: 'D22',
          },
          coordinates: { latitude: 1.331096, longitude: 103.6977849 },
          ura_zoning: {
            zone_code: 'B2',
            zone_description: 'Industrial',
            plot_ratio: 2.5,
          },
          existing_use: 'industrial',
          property_info: {
            site_area_sqm: 5600,
            gross_floor_area_sqm: 12000,
          },
          nearby_amenities: {
            mrt_stations: [],
            bus_stops: [],
            schools: [],
            shopping_malls: [],
            parks: [],
          },
          quick_analysis: {
            generated_at: '2026-04-26T01:00:00Z',
            scenarios: [],
          },
          timestamp: '2026-04-26T01:00:00Z',
          jurisdiction_code: 'SG',
          currency_symbol: 'S$',
          build_envelope: {
            zone_code: 'B2',
            zone_description: 'Industrial',
            site_area_sqm: 5600,
            allowable_plot_ratio: 2.5,
            max_buildable_gfa_sqm: 14000,
            current_gfa_sqm: 12000,
            additional_potential_gfa_sqm: 2000,
            building_height_limit_m: 50,
            site_coverage_pct: 70,
            setback_front_m: 7.5,
            setback_rear_m: 5,
            setback_side_m: 3,
            step_backs: [{ level: 6, depth_m: 4 }],
            air_rights_note: 'Subject to aviation height review.',
            assumptions: ['Resolved deeper controls: setbacks, step-backs.'],
            source_reference: 'URA Zoning Rules (SG RefRule Database)',
          },
          visualization: {
            status: 'placeholder',
            preview_available: false,
            notes: [],
            concept_mesh_url: null,
            preview_metadata_url: null,
            thumbnail_url: null,
            camera_orbit_hint: null,
            preview_seed: null,
            preview_job_id: null,
            massing_layers: [],
            color_legend: [],
          },
          optimizations: [],
          financial_summary: {
            total_estimated_revenue_sgd: null,
            total_estimated_capex_sgd: null,
            dominant_risk_profile: null,
            notes: [],
            finance_blueprint: null,
          },
          heritage_context: null,
          preview_jobs: [],
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )

    const result = await capturePropertyForDevelopment({
      latitude: 1.331096,
      longitude: 103.6977849,
      developmentScenarios: ['existing_building'],
      jurisdictionCode: 'SG',
    })

    expect(result.buildEnvelope).toMatchObject({
      zoneCode: 'B2',
      allowablePlotRatio: 2.5,
      setbackFrontM: 7.5,
      setbackRearM: 5,
      setbackSideM: 3,
      stepBacks: [{ level: 6, depthM: 4 }],
      airRightsNote: 'Subject to aviation height review.',
      sourceReference: 'URA Zoning Rules (SG RefRule Database)',
    })
  })
})
