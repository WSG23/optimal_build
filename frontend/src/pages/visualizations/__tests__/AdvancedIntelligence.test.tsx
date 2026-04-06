import type { ReactNode } from 'react'

import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

import AdvancedIntelligencePage from '../AdvancedIntelligence'
import type {
  CrossCorrelationIntelligenceResponse,
  GraphIntelligenceResponse,
  PredictiveIntelligenceResponse,
} from '../../../services/analytics/advancedAnalytics'

vi.mock('../../../App', () => ({
  AppLayout: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))

vi.mock('../components/KPITickerCard', () => ({
  KPITickerCard: ({ label, value }: { label: string; value: string }) => (
    <div>
      {label}: {value}
    </div>
  ),
}))

vi.mock('../components/RelationshipGraph', () => ({
  RelationshipGraph: () => <div>relationship-graph</div>,
}))

vi.mock('../components/ConfidenceGauge', () => ({
  ConfidenceGauge: ({ label, value }: { label: string; value: number }) => (
    <div>
      {label}: {value}
    </div>
  ),
}))

vi.mock('../components/CorrelationHeatmap', () => ({
  CorrelationHeatmap: () => <div>correlation-heatmap</div>,
}))

function renderPage(services: {
  fetchGraphIntelligence: () => Promise<GraphIntelligenceResponse>
  fetchPredictiveIntelligence: () => Promise<PredictiveIntelligenceResponse>
  fetchCrossCorrelationIntelligence: () => Promise<CrossCorrelationIntelligenceResponse>
}) {
  return render(
    <AdvancedIntelligencePage
      workspaceId="workspace-test"
      services={services}
    />,
  )
}

describe('AdvancedIntelligencePage', () => {
  it('renders explicit loading states before analytics resolve', () => {
    const pending = new Promise<never>(() => undefined)

    renderPage({
      fetchGraphIntelligence: () => pending,
      fetchPredictiveIntelligence: () => pending,
      fetchCrossCorrelationIntelligence: () => pending,
    })

    expect(
      screen.getByText('Mapping organization network...'),
    ).toBeInTheDocument()
    expect(screen.getByText('Running predictive models...')).toBeInTheDocument()
    expect(screen.getByText('Analyzing correlations...')).toBeInTheDocument()
  })

  it('renders narrative empty states when analytics payloads are empty', async () => {
    renderPage({
      fetchGraphIntelligence: async () => ({
        kind: 'graph',
        status: 'empty',
        summary: 'No graph signals.',
      }),
      fetchPredictiveIntelligence: async () => ({
        kind: 'predictive',
        status: 'empty',
        summary: 'No predictive signals.',
      }),
      fetchCrossCorrelationIntelligence: async () => ({
        kind: 'correlation',
        status: 'empty',
        summary: 'No correlation signals.',
      }),
    })

    expect(
      await screen.findByText(
        'Awaiting investigation metadata to construct intelligence graph',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('No graph signals.')).toBeInTheDocument()
    expect(
      screen.getByText(
        'No predictive signals available for this workspace yet',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('No predictive signals.')).toBeInTheDocument()
    expect(
      screen.getByText('No significant cross-correlations detected yet'),
    ).toBeInTheDocument()
    expect(screen.getByText('No correlation signals.')).toBeInTheDocument()
    expect(screen.getByText('Adoption Likelihood: N/A')).toBeInTheDocument()
    expect(screen.getByText('Projected Uplift: N/A')).toBeInTheDocument()
    expect(screen.getByText('Active Experiments: N/A')).toBeInTheDocument()
    expect(screen.getByText('Intelligence Score: N/A')).toBeInTheDocument()
  })

  it('renders explicit graph error copy without collapsing other panels', async () => {
    renderPage({
      fetchGraphIntelligence: async () => {
        throw new Error('graph service unavailable')
      },
      fetchPredictiveIntelligence: async () => ({
        kind: 'predictive',
        status: 'empty',
        summary: 'No predictive signals.',
      }),
      fetchCrossCorrelationIntelligence: async () => ({
        kind: 'correlation',
        status: 'empty',
        summary: 'No correlation signals.',
      }),
    })

    expect(
      await screen.findByText('Unable to load intelligence graph'),
    ).toBeInTheDocument()
    expect(screen.getByText('graph service unavailable')).toBeInTheDocument()
    expect(
      screen.getByText(
        'No predictive signals available for this workspace yet',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText('No significant cross-correlations detected yet'),
    ).toBeInTheDocument()
  })
})
