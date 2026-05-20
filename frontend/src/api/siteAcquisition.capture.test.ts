import { afterEach, describe, expect, it, vi } from 'vitest'

import { capturePropertyForDevelopment } from './siteAcquisition'

describe('capturePropertyForDevelopment', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
  })

  it('maps deeper envelope controls from the developer capture response', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
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
            special_conditions: 'non_standard_or_non_developable_control',
            development_control_status: 'non_standard_or_non_developable',
            source: 'ref_zoning_layer',
            source_reason: 'parcel_dominant_zoning',
          },
          existing_use: 'industrial',
          property_info: {
            site_area_sqm: 5600,
            gross_floor_area_sqm: 12000,
            current_use: 'Hotel / lodging',
            current_use_evidence: [
              {
                use: 'Hotel / lodging',
                source: 'google_places_autocomplete',
                confidence: 'medium',
                basis: 'Selected place is tagged as lodging.',
                place_name: 'lyf one-north Singapore',
                place_types: ['lodging', 'point_of_interest'],
              },
            ],
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
            gross_plot_ratio: 2.5,
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
            source_reference: 'SG Rule Registry (RefRule + zoning layers)',
            rule_corpus_status: {
              coverage_state: 'partial',
              resolved_by: {
                plot_ratio: 'ref_rule',
                setbacks: 'ref_rule',
              },
              unresolved_fields: ['air_rights_note'],
            },
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
            massing_layers: [
              {
                asset_type: 'industrial',
                allocation_pct: 70,
                gfa_sqm: 9800,
                footprint_area_sqm: 3920,
                estimated_height_m: 25,
                color: '#2563eb',
              },
            ],
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
    localStorage.setItem('app:api-role', 'developer')

    const result = await capturePropertyForDevelopment({
      latitude: 1.331096,
      longitude: 103.6977849,
      submittedAddress: '28 Soon Lee Rd, Singapore 628083',
      placeId: 'google-place-123',
      placeName: 'lyf one-north Singapore',
      placeTypes: ['lodging', 'point_of_interest'],
      developmentScenarios: ['existing_building'],
      jurisdictionCode: 'SG',
      currentGfaSqm: 12000,
      currentGfaSource: 'approved plans',
    })

    const [, requestInit] = fetchMock.mock.calls[0] as [
      RequestInfo | URL,
      RequestInit,
    ]
    expect(requestInit.headers).toMatchObject({
      'X-Role': 'reviewer',
      'X-User-Email': 'demo-owner@example.com',
      'X-User-Id': '00000000-0000-0000-0000-000000000001',
    })
    expect(JSON.parse(String(requestInit.body))).toMatchObject({
      latitude: 1.331096,
      longitude: 103.6977849,
      submitted_address: '28 Soon Lee Rd, Singapore 628083',
      place_id: 'google-place-123',
      place_name: 'lyf one-north Singapore',
      place_types: ['lodging', 'point_of_interest'],
      development_scenarios: ['existing_building'],
      jurisdiction_code: 'SG',
      current_gfa_sqm: 12000,
      current_gfa_source: 'approved plans',
    })
    expect(result.buildEnvelope).toMatchObject({
      zoneCode: 'B2',
      allowablePlotRatio: 2.5,
      grossPlotRatio: 2.5,
      setbackFrontM: 7.5,
      setbackRearM: 5,
      setbackSideM: 3,
      stepBacks: [{ level: 6, depthM: 4 }],
      airRightsNote: 'Subject to aviation height review.',
      sourceReference: 'SG Rule Registry (RefRule + zoning layers)',
      ruleCorpusStatus: {
        coverage_state: 'partial',
        resolved_by: {
          plot_ratio: 'ref_rule',
          setbacks: 'ref_rule',
        },
        unresolved_fields: ['air_rights_note'],
      },
    })
    expect(result.uraZoning).toMatchObject({
      zoneCode: 'B2',
      specialConditions: 'non_standard_or_non_developable_control',
      developmentControlStatus: 'non_standard_or_non_developable',
      source: 'ref_zoning_layer',
      sourceReason: 'parcel_dominant_zoning',
    })
    expect(result.visualization.massingLayers[0]).toMatchObject({
      assetType: 'industrial',
      footprintAreaSqm: 3920,
    })
    expect(result.propertyInfo?.currentUse).toBe('Hotel / lodging')
    expect(result.propertyInfo?.currentUseEvidence?.[0]).toMatchObject({
      use: 'Hotel / lodging',
      source: 'google_places_autocomplete',
      confidence: 'medium',
      placeName: 'lyf one-north Singapore',
      placeTypes: ['lodging', 'point_of_interest'],
    })
  })

  it('surfaces structured developer capture errors as readable messages', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          detail:
            'Submitted address does not match the resolved map point. Please re-geocode.',
        }),
        {
          status: 409,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )

    await expect(
      capturePropertyForDevelopment({
        latitude: 1.3286413,
        longitude: 103.698443,
        submittedAddress: '25 Soon Lee Rd, Singapore 628083',
        developmentScenarios: [],
      }),
    ).rejects.toThrow(
      'Submitted address does not match the resolved map point. Please re-geocode.',
    )
  })
})
