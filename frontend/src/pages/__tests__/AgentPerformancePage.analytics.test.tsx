import assert from 'node:assert/strict'
import { afterEach, beforeEach, describe, it } from 'node:test'

import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { JSDOM } from 'jsdom'
import React from 'react'

import { TranslationProvider } from '../../i18n'
import AgentPerformancePage from '../AgentPerformancePage'

function makeMockResponse(body: unknown, status = 200): Response {
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

describe('AgentPerformancePage analytics', () => {
  let dom: JSDOM
  const originalFetch = globalThis.fetch
  const originalResizeObserver = (globalThis as { ResizeObserver?: unknown })
    .ResizeObserver

  beforeEach(() => {
    dom = new JSDOM('<!doctype html><html><body></body></html>', {
      url: 'http://localhost/agents/performance',
    })

    const globalWithDom = globalThis as typeof globalThis & {
      window: Window & typeof globalThis
      document: Document
      navigator: Navigator
    }
    globalWithDom.window = dom.window
    globalWithDom.document = dom.window.document
    globalWithDom.navigator = dom.window.navigator

    class MockResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }

    ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver =
      MockResizeObserver

    const dealsResponse = [
      {
        id: 'deal-1',
        agent_id: 'agent-123',
        title: 'Flagship Office Sale',
        asset_type: 'office',
        deal_type: 'sell_side',
        pipeline_stage: 'lead_captured',
        status: 'open',
        lead_source: 'referral',
        estimated_value_amount: 1000000,
        estimated_value_currency: 'SGD',
        confidence: 0.6,
        metadata: {},
        created_at: '2025-02-01T00:00:00Z',
        updated_at: '2025-02-02T00:00:00Z',
      },
    ]

    const timelineResponse = [
      {
        id: 'timeline-1',
        deal_id: 'deal-1',
        from_stage: null,
        to_stage: 'lead_captured',
        changed_by: 'agent-123',
        note: 'Initial qualification',
        recorded_at: '2025-02-02T08:00:00Z',
        duration_seconds: 3600,
        audit_log: null,
      },
    ]

    const snapshotLatest = [
      {
        id: 'snap-latest',
        agent_id: 'agent-123',
        as_of_date: '2025-02-10',
        deals_open: 3,
        deals_closed_won: 2,
        deals_closed_lost: 0,
        gross_pipeline_value: 1800000,
        weighted_pipeline_value: 950000,
        confirmed_commission_amount: 32000,
        disputed_commission_amount: 0,
        avg_cycle_days: 78,
        conversion_rate: 0.42,
        roi_metrics: {},
        snapshot_context: {},
      },
    ]

    const snapshotHistory = [
      {
        id: 'snap-1',
        agent_id: 'agent-123',
        as_of_date: '2025-02-08',
        deals_open: 2,
        deals_closed_won: 2,
        deals_closed_lost: 0,
        gross_pipeline_value: 1500000,
        weighted_pipeline_value: 870000,
        confirmed_commission_amount: 29000,
        disputed_commission_amount: 0,
        avg_cycle_days: 82,
        conversion_rate: 0.38,
        roi_metrics: {},
        snapshot_context: {},
      },
      {
        id: 'snap-2',
        agent_id: 'agent-123',
        as_of_date: '2025-02-09',
        deals_open: 3,
        deals_closed_won: 2,
        deals_closed_lost: 0,
        gross_pipeline_value: 1750000,
        weighted_pipeline_value: 900000,
        confirmed_commission_amount: 31000,
        disputed_commission_amount: 0,
        avg_cycle_days: 80,
        conversion_rate: 0.4,
        roi_metrics: {},
        snapshot_context: {},
      },
    ]

    const benchmarksByKey: Record<string, unknown[]> = {
      conversion_rate: [
        {
          id: 'bench-conversion',
          metric_key: 'conversion_rate',
          asset_type: 'office',
          deal_type: 'sell_side',
          cohort: 'industry_avg',
          value_numeric: 0.35,
          value_text: null,
          source: 'seed',
          effective_date: '2024-01-01',
        },
      ],
      avg_cycle_days: [
        {
          id: 'bench-cycle',
          metric_key: 'avg_cycle_days',
          asset_type: 'office',
          deal_type: 'sell_side',
          cohort: 'industry_avg',
          value_numeric: 90,
          value_text: null,
          source: 'seed',
          effective_date: '2024-01-01',
        },
      ],
      pipeline_weighted_value: [
        {
          id: 'bench-pipeline',
          metric_key: 'pipeline_weighted_value',
          asset_type: null,
          deal_type: null,
          cohort: 'top_quartile',
          value_numeric: 1200000,
          value_text: null,
          source: 'seed',
          effective_date: '2024-01-01',
        },
      ],
    }

    globalThis.fetch = (async (input: RequestInfo, init?: RequestInit) => {
      const href =
        typeof input === 'string'
          ? input
          : 'url' in input
          ? input.url
          : String(input)
      const url = new URL(href, 'http://localhost')
      const { pathname, searchParams } = url
      const method = init?.method ?? 'GET'

      if (pathname === '/api/v1/deals' && method === 'GET') {
        return makeMockResponse(dealsResponse)
      }
      if (pathname === '/api/v1/deals/deal-1/timeline') {
        return makeMockResponse(timelineResponse)
      }
      if (pathname === '/api/v1/performance/snapshots') {
        if (searchParams.get('limit') === '1') {
          return makeMockResponse(snapshotLatest)
        }
        return makeMockResponse(snapshotHistory)
      }
      if (pathname === '/api/v1/performance/benchmarks') {
        const metricKey = searchParams.get('metric_key') ?? ''
        const payload = benchmarksByKey[metricKey] ?? []
        return makeMockResponse(payload)
      }

      throw new Error(`Unexpected fetch: ${url.href}`)
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
    if (originalResizeObserver) {
      ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver =
        originalResizeObserver
    } else {
      delete (globalThis as { ResizeObserver?: unknown }).ResizeObserver
    }
  })

  it('renders analytics metrics, charts, and benchmarks', async () => {
    render(
      <TranslationProvider>
        <AgentPerformancePage />
      </TranslationProvider>,
    )

    await waitFor(() => {
      assert.ok(screen.getByText(/Deals won/i))
    })

    assert.ok(screen.getByText(/Weighted pipeline/i))
    assert.ok(screen.getByText(/Conversion rate/i))

    await waitFor(() => {
      assert.ok(screen.getByText(/Benchmark comparison/i))
    })

    assert.ok(screen.getByText(/industry avg/i))
    assert.ok(screen.getByText(/\+7\.0 pts/))
  })
})
