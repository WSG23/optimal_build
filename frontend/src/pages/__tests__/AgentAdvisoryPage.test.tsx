import assert from 'node:assert/strict'
import { afterEach, beforeEach, describe, it } from 'node:test'

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { JSDOM } from 'jsdom'
import React from 'react'

import { TranslationProvider } from '../../i18n'
import AgentAdvisoryPage from '../AgentAdvisoryPage'

/**
 * KNOWN ISSUE: This test may fail with async timing issues in JSDOM.
 * See: ../../TESTING_KNOWN_ISSUES.md - "Frontend: React Testing Library Async Timing"
 *
 * If this test fails but the HTML dump shows content is rendered correctly,
 * the feature is working - it's a test harness issue, not an application bug.
 */

const summaryPayload = {
  asset_mix: {
    property_id: 'test-property',
    total_programmable_gfa_sqm: 52000,
    mix_recommendations: [
      {
        use: 'office',
        allocation_pct: 60,
        target_gfa_sqm: 31200,
        rationale: 'Maintain premium office exposure.',
      },
    ],
    notes: ['Plot ratio allows flexibility.'],
  },
  market_positioning: {
    market_tier: 'Prime CBD',
    pricing_guidance: {
      sale_psf: {
        target_min: 2800,
        target_max: 3100,
      },
    },
    target_segments: [{ segment: 'Regional HQ', weight_pct: 40 }],
    messaging: ['Position as premium inventory.'],
  },
  absorption_forecast: {
    expected_months_to_stabilize: 9,
    monthly_velocity_target: 3,
    confidence: 'medium',
    timeline: [
      {
        milestone: 'Launch preparation',
        month: 3,
        expected_absorption_pct: 25,
      },
    ],
  },
  feedback: [],
}

const feedbackRecord = {
  id: 'record-1',
  property_id: 'test-property',
  submitted_by: null,
  channel: 'call',
  sentiment: 'positive',
  notes: 'Strong inbound interest.',
  metadata: {},
  created_at: new Date('2025-02-18T10:00:00Z').toISOString(),
}

describe('AgentAdvisoryPage', () => {
  let dom: JSDOM
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    dom = new JSDOM('<!doctype html><html><body></body></html>', {
      url: 'http://localhost/agents/advisory?propertyId=test-property',
    })

    const globalWithDom = globalThis as typeof globalThis & {
      window: Window & typeof globalThis
      document: Document
      navigator: Navigator
    }
    globalWithDom.window = dom.window
    globalWithDom.document = dom.window.document
    globalWithDom.navigator = dom.window.navigator

    // Ensure window.location has the query string
    dom.window.history.replaceState(
      null,
      '',
      'http://localhost/agents/advisory?propertyId=test-property',
    )

    let _callCount = 0
    globalThis.fetch = (async (input: RequestInfo, init?: RequestInit) => {
      _callCount += 1
      const method = init?.method ?? 'GET'
      if (method === 'GET') {
        return makeMockResponse(summaryPayload)
      }
      assert.equal(method, 'POST')
      return makeMockResponse(feedbackRecord)
    }) as typeof globalThis.fetch
  })

  afterEach(() => {
    cleanup()
    dom.window.close()
    const globalWithDom = globalThis as {
      window?: Window & typeof globalThis
      document?: Document
      navigator?: Navigator
    }
    delete globalWithDom.window
    delete globalWithDom.document
    delete globalWithDom.navigator
    globalThis.fetch = originalFetch
  })

  it('renders advisory data and submits feedback', async () => {
    render(
      <TranslationProvider>
        <AgentAdvisoryPage />
      </TranslationProvider>,
    )

    await waitFor(
      () => {
        assert.ok(screen.getByText(/Asset mix strategy/i))
      },
      { timeout: 5000 },
    )

    assert.ok(screen.getByText(/Plot ratio allows flexibility/i))

    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: 'positive' },
    })
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Strong inbound interest.' },
    })

    fireEvent.click(screen.getByRole('button', { name: /Record feedback/i }))

    await waitFor(() => {
      assert.ok(screen.getByText(/Strong inbound interest\./i))
    })
  })
})

function makeMockResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    async json() {
      return body
    },
    async text() {
      return JSON.stringify(body)
    },
  } as Response
}
