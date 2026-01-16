/**
 * AgentPerformancePage Analytics Integration Test
 *
 * This test uses REAL hooks with mocked fetch calls to verify the full
 * data flow from API responses through hooks to UI rendering.
 *
 * What's mocked:
 * - Recharts components (JSDOM doesn't support SVG layout)
 * - HeaderUtilityCluster (avoids context sync issues with vi.resetModules)
 * - fetch() responses (returns predefined API data)
 *
 * What's NOT mocked (real integration):
 * - useDeals, useTimeline, useAnalytics, useBenchmarks hooks
 * - Data transformation and state management
 * - Component rendering based on hook state
 *
 * Run time: ~25-30s (slower due to real async operations)
 */
import { afterEach, assert, beforeEach, describe, it, vi } from 'vitest'
import React from 'react'
import { cleanup, screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'

// Stub Recharts - charts don't render properly in JSDOM
vi.mock('recharts', () => ({
  ResponsiveContainer: () => <div data-testid="recharts-responsive" />,
  AreaChart: () => <div data-testid="recharts-area-chart" />,
  LineChart: () => <div data-testid="recharts-line-chart" />,
  CartesianGrid: () => null,
  Line: () => null,
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
}))

// Stub HeaderUtilityCluster to avoid provider context issues
// This component uses useThemeMode which requires ThemeModeProvider,
// but due to module caching with vi.resetModules(), the context instances
// can get out of sync. Stubbing it keeps the rest of the component tree intact.
vi.mock('../../components/layout/HeaderUtilityCluster', () => ({
  HeaderUtilityCluster: () => <div data-testid="header-utility-cluster-stub" />,
}))

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

describe('AgentPerformancePage analytics (integration)', () => {
  let AgentPerformancePage: typeof import('../AgentPerformancePage').default

  const originalFetch = globalThis.fetch
  const originalResizeObserver = (globalThis as { ResizeObserver?: unknown })
    .ResizeObserver

  beforeEach(async () => {
    cleanup()
    vi.resetModules() // Reset module cache to ensure fresh hook instances
    window.history.replaceState(null, '', '/agents/performance')

    // Mock ResizeObserver for Recharts compatibility
    class MockResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }

    ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver =
      MockResizeObserver

    // API response data
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

    // Mock fetch to return API responses
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

      // Return empty response for unexpected URLs instead of throwing
      console.warn(`Unexpected fetch: ${url.href}`)
      return makeMockResponse([])
    }) as typeof globalThis.fetch

    AgentPerformancePage = (await import('../AgentPerformancePage')).default
  }, 30_000)

  afterEach(() => {
    cleanup()
    globalThis.fetch = originalFetch
    if (originalResizeObserver) {
      ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver =
        originalResizeObserver
    } else {
      delete (globalThis as { ResizeObserver?: unknown }).ResizeObserver
    }
  })

  it('renders analytics dashboard with data from API', async () => {
    // Use renderWithProviders with inBaseLayout: true (default)
    // This skips HeaderUtilityCluster while keeping the rest intact
    renderWithProviders(<AgentPerformancePage />)

    // Wait for async data to load and render
    await waitFor(
      async () => {
        // Verify key metrics from API response are displayed
        assert.ok(await screen.findByText(/Open deals/i))
        assert.ok(await screen.findByText(/SGD\s*1,800,000/i))
      },
      { timeout: 10_000 },
    )

    // Verify conversion rate is displayed
    const conversionMatches = await screen.findAllByText(/42\.0%/)
    assert.ok(conversionMatches.length >= 1)

    // Verify benchmark comparison section
    assert.ok(await screen.findByText(/Benchmark comparison/i))
  }, 60_000)

  it('displays deal information from API', async () => {
    renderWithProviders(<AgentPerformancePage />)

    // Wait for deals to load
    await waitFor(
      async () => {
        // Verify deal title appears
        assert.ok(await screen.findByText(/Flagship Office Sale/i))
      },
      { timeout: 10_000 },
    )
  }, 60_000)
})
