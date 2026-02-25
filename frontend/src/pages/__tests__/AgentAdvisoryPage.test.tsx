import { afterEach, assert, beforeEach, describe, it, vi } from 'vitest'

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'

import React from 'react'

import { TranslationProvider } from '../../i18n'
import { ThemeModeProvider } from '../../theme/ThemeContext'
import AgentAdvisoryPage from '../AgentAdvisoryPage'

type ResponsiveContainerChild =
  | React.ReactNode
  | ((size: { width: number; height: number }) => React.ReactNode)

vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof import('recharts')>()
  return {
    ...actual,
    ResponsiveContainer: ({
      children,
    }: {
      children?: ResponsiveContainerChild
    }) => (
      <div style={{ width: 800, height: 400 }}>
        {typeof children === 'function'
          ? children({ width: 800, height: 400 })
          : children}
      </div>
    ),
  }
})

/**
 * ⚠️ KNOWN ISSUE: This test may fail with async timing issues in JSDOM.
 *
 * See: docs/all_steps_to_product_completion.md#-known-testing-issues
 * Section: "Frontend: React Testing Library Async Timing"
 *
 * If this test fails but the HTML dump shows content is rendered correctly,
 * the feature is working - it's a test harness issue, not an application bug.
 *
 * When this is fixed, update the Known Testing Issues section per the maintenance checklist.
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
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    cleanup()
    window.history.replaceState(
      null,
      '',
      '/agents/advisory?propertyId=test-property',
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
    globalThis.fetch = originalFetch
  })

  it('renders advisory data and submits feedback', async () => {
    render(
      <ThemeModeProvider>
        <TranslationProvider>
          <AgentAdvisoryPage />
        </TranslationProvider>
      </ThemeModeProvider>,
    )

    await waitFor(
      () => {
        assert.ok(screen.getByText(/Asset mix strategy/i))
      },
      { timeout: 5000 },
    )

    assert.ok(screen.getByText(/Plot ratio allows flexibility/i))

    // Sentiment defaults to "positive"; submitting notes is sufficient here.
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
