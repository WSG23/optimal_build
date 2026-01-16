/**
 * AgentPerformancePage Analytics Unit Test
 *
 * This test validates the UI rendering with mocked hooks and Recharts.
 *
 * Why we mock hooks and Recharts:
 * 1. Recharts relies on ResizeObserver/DOM measurements that don't work in JSDOM
 * 2. Real hooks make async fetch calls that cause timing issues and flaky tests
 * 3. The component tree has complex provider nesting that's hard to replicate in tests
 *
 * Trade-off: We lose integration confidence but gain:
 * - Fast, reliable tests (~1s vs 30s+)
 * - Stable CI pipeline
 * - Clear validation that UI renders expected content
 *
 * For true integration testing, use manual browser testing or E2E tests.
 */
import { afterEach, assert, beforeEach, describe, it, vi } from 'vitest'
import { ThemeModeProvider } from '../../theme/ThemeContext'

import React from 'react'
import { cleanup, render, screen } from '@testing-library/react'

import { TranslationProvider } from '../../i18n'

// Stub Recharts to avoid JSDOM layout/ResizeObserver issues
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

// Stub hooks to return static data - avoids async fetch timing issues
vi.mock('../../modules/agent-performance/hooks', () => {
  const deal = {
    id: 'deal-1',
    agentId: 'agent-123',
    title: 'Flagship Office Sale',
    description: null,
    assetType: 'office',
    dealType: 'sell_side',
    pipelineStage: 'lead_captured',
    status: 'open',
    leadSource: 'referral',
    estimatedValueAmount: 1000000,
    estimatedValueCurrency: 'SGD',
    expectedCloseDate: null,
    actualCloseDate: null,
    confidence: 0.6,
    metadata: {},
    createdAt: '2025-02-01T00:00:00Z',
    updatedAt: '2025-02-02T00:00:00Z',
  }

  return {
    useDeals: () => ({
      deals: [deal],
      loadingDeals: false,
      dealError: null,
      selectedDealId: deal.id,
      selectedDeal: deal,
      groupedDeals: { lead_captured: [deal] },
      stageOrder: ['lead_captured'],
      setSelectedDealId: () => {},
    }),
    useTimeline: () => ({
      timeline: [
        {
          id: 'timeline-1',
          dealId: deal.id,
          fromStage: null,
          toStage: 'lead_captured',
          changedBy: 'agent-123',
          note: 'Initial qualification',
          recordedAt: '2025-02-02T08:00:00Z',
          metadata: {},
          durationSeconds: 3600,
          auditLog: null,
        },
      ],
      timelineLoading: false,
      timelineError: null,
    }),
    useAnalytics: () => ({
      latestSnapshot: {
        id: 'snap-latest',
        agentId: 'agent-123',
        asOfDate: '2025-02-10',
        dealsOpen: 3,
        dealsClosedWon: 2,
        dealsClosedLost: 0,
        grossPipelineValue: 1800000,
        weightedPipelineValue: 950000,
        confirmedCommissionAmount: 32000,
        disputedCommissionAmount: 0,
        avgCycleDays: 78,
        conversionRate: 0.42,
        roiMetrics: {},
        snapshotContext: {},
      },
      snapshotHistory: [],
      analyticsLoading: false,
      analyticsError: null,
      trendData: [
        {
          label: 'Feb 8',
          gross: 1500000,
          weighted: 870000,
          conversion: 38,
          cycle: 82,
        },
        {
          label: 'Feb 9',
          gross: 1750000,
          weighted: 900000,
          conversion: 40,
          cycle: 80,
        },
      ],
    }),
    useBenchmarks: () => ({
      benchmarks: {
        conversion: null,
        cycle: null,
        pipeline: null,
      },
      benchmarksLoading: false,
      benchmarksError: null,
      benchmarkComparisons: [
        {
          key: 'conversion',
          label: 'Conversion rate',
          actual: '42.0%',
          benchmark: '35.0%',
          cohort: 'industry avg',
          deltaText: '+7.0 pts',
          deltaPositive: true,
        },
      ],
      benchmarksHasContent: true,
    }),
  }
})

// Import after mocks are set up
import AgentPerformancePage from '../AgentPerformancePage'

describe('AgentPerformancePage analytics (unit)', () => {
  const originalResizeObserver = (globalThis as { ResizeObserver?: unknown })
    .ResizeObserver

  beforeEach(() => {
    cleanup()
    window.history.replaceState(null, '', '/agents/performance')

    // Mock ResizeObserver for Recharts compatibility
    class MockResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }

    ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver =
      MockResizeObserver
  })

  afterEach(() => {
    cleanup()
    if (originalResizeObserver) {
      ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver =
        originalResizeObserver
    } else {
      delete (globalThis as { ResizeObserver?: unknown }).ResizeObserver
    }
  })

  it('renders analytics dashboard with metrics and charts', async () => {
    render(
      <ThemeModeProvider>
        <TranslationProvider>
          <AgentPerformancePage />
        </TranslationProvider>
      </ThemeModeProvider>,
    )

    // Verify key metrics are displayed
    assert.ok(await screen.findByText(/Open deals/i))
    assert.ok(await screen.findByText(/SGD\s*1,800,000/i))
    const conversionMatches = await screen.findAllByText(/42\.0%/)
    assert.ok(conversionMatches.length >= 1)

    // Verify benchmark comparison section
    assert.ok(await screen.findByText(/Benchmark comparison/i))
    assert.ok(await screen.findByText(/industry avg 35\.0%/i))
    assert.ok(await screen.findByText(/\+7\.0 pts/))
  })
})
