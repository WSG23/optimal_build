import assert from 'node:assert/strict'
import { describe, it } from 'node:test'

import { type DevelopmentScenario, logPropertyByGps } from '../agents'

describe('agents API mapping', () => {
  it('maps the GPS capture payload into camelCase structures', async () => {
    const transport = async () => ({
      property_id: '123e4567-e89b-12d3-a456-426614174000',
      address: {
        full_address: '1 Example Street, Singapore',
        street_name: 'Example Street',
        building_name: 'Example Tower',
        block_number: '01',
        postal_code: '123456',
        district: 'D01 - Raffles Place',
        country: 'Singapore',
      },
      coordinates: { latitude: 1.3, longitude: 103.85 },
      ura_zoning: {
        zone_code: 'C',
        zone_description: 'Commercial',
        plot_ratio: 4.0,
        building_height_limit: 160,
        site_coverage: 80,
        use_groups: ['Office', 'Retail'],
        special_conditions: 'Subject to urban design guidelines',
      },
      existing_use: 'Office Building',
      property_info: {
        property_name: 'Example Tower',
        tenure: '99-year leasehold',
        site_area_sqm: 5000,
        gfa_approved: 18000,
        building_height: 18,
        completion_year: 1965,
        last_transaction_date: '2023-06-15',
        last_transaction_price: 150_000_000,
      },
      nearby_amenities: {
        mrt_stations: [{ name: 'Raffles MRT', distance_m: 180 }],
        bus_stops: [{ name: 'Bus Stop', distance_m: 90 }],
        schools: [],
        shopping_malls: [],
        parks: [],
      },
      quick_analysis: {
        generated_at: '2025-01-01T00:00:00Z',
        scenarios: [
          {
            scenario: 'raw_land',
            headline: 'Est. max GFA ≈ 20,000 sqm',
            metrics: {
              site_area_sqm: 5000,
              plot_ratio: 4,
              potential_gfa_sqm: 20000,
            },
            notes: ['Commercial'],
          },
        ],
      },
      timestamp: '2025-01-01T00:00:10Z',
    })

    const result = await logPropertyByGps(
      { latitude: 1.3, longitude: 103.85 },
      transport,
    )

    assert.equal(result.propertyId, '123e4567-e89b-12d3-a456-426614174000')
    assert.equal(result.address.fullAddress, '1 Example Street, Singapore')
    assert.equal(result.uraZoning.zoneCode, 'C')
    assert.equal(result.propertyInfo?.gfaApproved, 18000)
    assert.equal(result.nearbyAmenities?.mrtStations[0]?.name, 'Raffles MRT')
    assert.equal(result.quickAnalysis.generatedAt, '2025-01-01T00:00:00Z')
    assert.equal(result.quickAnalysis.scenarios.length, 1)
    assert.equal(
      result.quickAnalysis.scenarios[0]?.metrics.potential_gfa_sqm,
      20000,
    )
  })

  it('forwards explicit scenario selections to the transport layer', async () => {
    const captured: DevelopmentScenario[][] = []
    const transport = async (
      baseUrl: string,
      payload: { developmentScenarios?: DevelopmentScenario[] },
      _options?: { signal?: AbortSignal },
    ) => {
      if (payload.developmentScenarios) {
        captured.push(payload.developmentScenarios)
      }
      return {
        property_id: 'id',
        address: { full_address: 'Mock', country: 'Singapore' },
        coordinates: { latitude: 1.0, longitude: 103.0 },
        ura_zoning: null,
        existing_use: 'Unknown',
        property_info: null,
        nearby_amenities: null,
        quick_analysis: { generated_at: '2025-01-01T00:00:00Z', scenarios: [] },
        timestamp: '2025-01-01T00:00:00Z',
      }
    }

    const selection: DevelopmentScenario[] = ['raw_land', 'heritage_property']
    await logPropertyByGps(
      { latitude: 1.0, longitude: 103.0, developmentScenarios: selection },
      transport,
    )

    assert.deepEqual(captured[0], selection)
  })
})
