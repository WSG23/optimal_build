import { assert, describe, expect, it } from 'vitest'

import {
  type DevelopmentScenario,
  logPropertyByGps,
  fetchPropertyMarketIntelligence,
  generateProfessionalPack,
} from '../agents'

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

  it('fetches market intelligence and returns the report payload', async () => {
    const originalFetch = globalThis.fetch

    let requestedUrl: string | null = null
    globalThis.fetch = (async (input: RequestInfo, _init?: RequestInit) => {
      requestedUrl = typeof input === 'string' ? input : String(input)
      return {
        ok: true,
        status: 200,
        headers: {
          get: () => 'application/json',
        },
        async json() {
          return {
            property_id: 'abc123',
            report: { comparables_analysis: { transaction_count: 5 } },
          }
        },
      }
    }) as typeof globalThis.fetch

    try {
      const summary = await fetchPropertyMarketIntelligence('abc123', 6)
      assert.ok(
        requestedUrl?.includes('/market-intelligence?months=6'),
        'request url includes months filter',
      )
      assert.equal(summary.report.comparables_analysis.transaction_count, 5)
      assert.equal(summary.isFallback, false)
    } finally {
      globalThis.fetch = originalFetch
    }
  })

  it('throws when the market intelligence endpoint fails', async () => {
    const originalFetch = globalThis.fetch
    globalThis.fetch = (async () => ({
      ok: false,
      status: 503,
      headers: {
        get: () => 'text/plain',
      },
      async text() {
        return 'service unavailable'
      },
    })) as typeof globalThis.fetch

    try {
      await expect(fetchPropertyMarketIntelligence('abc123')).rejects.toThrow(
        /service unavailable/,
      )
    } finally {
      globalThis.fetch = originalFetch
    }
  })

  it('requests professional pack generation and maps the response payload', async () => {
    const originalFetch = globalThis.fetch

    let requestedUrl: string | null = null
    let requestedMethod: string | undefined

    globalThis.fetch = (async (input: RequestInfo, init?: RequestInit) => {
      requestedUrl = typeof input === 'string' ? input : String(input)
      requestedMethod = init?.method
      return {
        ok: true,
        status: 200,
        headers: {
          get: () => 'application/json',
        },
        async json() {
          return {
            pack_type: 'sales',
            property_id: 'abc123',
            filename: 'sales_brochure.pdf',
            download_url: 'https://example.com/sales.pdf',
            generated_at: '2025-07-01T00:00:00Z',
            size_bytes: 42_000,
          }
        },
      }
    }) as typeof globalThis.fetch

    try {
      const summary = await generateProfessionalPack('abc123', 'sales')
      assert.ok(
        requestedUrl?.endsWith(
          '/api/v1/agents/commercial-property/properties/abc123/generate-pack/sales',
        ),
      )
      assert.equal(requestedMethod, 'POST')
      assert.equal(summary.packType, 'sales')
      assert.equal(summary.propertyId, 'abc123')
      assert.equal(summary.filename, 'sales_brochure.pdf')
      assert.equal(summary.downloadUrl, 'https://example.com/sales.pdf')
      assert.equal(summary.sizeBytes, 42_000)
      assert.equal(summary.isFallback, false)
    } finally {
      globalThis.fetch = originalFetch
    }
  })

  it('throws when professional pack generation fails', async () => {
    const originalFetch = globalThis.fetch

    globalThis.fetch = (async () => ({
      ok: false,
      status: 429,
      statusText: 'Too Many Requests',
      headers: {
        get: () => 'text/plain',
      },
      async text() {
        return 'generation throttled'
      },
    })) as typeof globalThis.fetch

    try {
      await expect(
        generateProfessionalPack('abc123', 'investment'),
      ).rejects.toThrow(/generation throttled/)
    } finally {
      globalThis.fetch = originalFetch
    }
  })

  it('throws when the GPS capture request fails', async () => {
    const request = { latitude: 1.301, longitude: 103.832 }
    await expect(
      logPropertyByGps(request, async () => {
        throw new TypeError('Network timeout')
      }),
    ).rejects.toThrow(/Network timeout/)
  })
})
