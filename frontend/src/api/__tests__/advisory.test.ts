import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  fetchAdvisoryFeedback,
  fetchAdvisorySummary,
  submitAdvisoryFeedback,
} from '../advisory'

describe('advisory API client', () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('fetches advisory summaries with the expected URL', async () => {
    const payload = {
      asset_mix: {
        property_id: 'prop-1',
        total_programmable_gfa_sqm: 4200,
        mix_recommendations: [],
        notes: [],
      },
      market_positioning: {
        market_tier: 'Tier 1',
        pricing_guidance: {},
        target_segments: [],
        messaging: [],
      },
      absorption_forecast: {
        expected_months_to_stabilize: 6,
        monthly_velocity_target: 2,
        confidence: 'high',
        timeline: [],
      },
      feedback: [],
    }

    globalThis.fetch = vi.fn(async (input) => {
      const url = typeof input === 'string' ? input : input.url
      expect(url).toBe(
        '/api/v1/agents/commercial-property/properties/prop-1/advisory',
      )
      return {
        ok: true,
        status: 200,
        async json() {
          return payload
        },
      } as Response
    })

    const summary = await fetchAdvisorySummary('prop-1')
    expect(summary.asset_mix.property_id).toBe('prop-1')
    expect(summary.absorption_forecast.monthly_velocity_target).toBe(2)
    expect(globalThis.fetch).toHaveBeenCalledTimes(1)
  })

  it('submits advisory feedback and returns created record', async () => {
    const createdRecord = {
      id: 'record-1',
      property_id: 'prop-1',
      sentiment: 'positive',
      notes: 'Pipeline partner confirmed pricing.',
      channel: 'call',
      metadata: {},
      created_at: '2025-03-12T10:30:00.000Z',
    }

    globalThis.fetch = vi.fn(async (input, init) => {
      expect(init?.method).toBe('POST')
      expect(init?.headers).toMatchObject({ 'content-type': 'application/json' })
      const body = init?.body ? JSON.parse(String(init.body)) : null
      expect(body).toMatchObject({
        sentiment: 'positive',
        notes: 'Pipeline partner confirmed pricing.',
      })

      return {
        ok: true,
        status: 200,
        async json() {
          return createdRecord
        },
      } as Response
    })

    const record = await submitAdvisoryFeedback('prop-1', {
      sentiment: 'positive',
      notes: 'Pipeline partner confirmed pricing.',
    })

    expect(record.id).toBe('record-1')
    expect(globalThis.fetch).toHaveBeenCalledTimes(1)
  })

  it('throws a helpful error when feedback retrieval fails', async () => {
    globalThis.fetch = vi.fn(async () => ({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      async json() {
        return []
      },
      async text() {
        return 'Backend unavailable'
      },
    }))

    await expect(fetchAdvisoryFeedback('prop-1')).rejects.toThrow(
      'Failed to load advisory feedback',
    )
  })
})
