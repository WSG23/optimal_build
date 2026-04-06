import type { ReactNode } from 'react'

import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

import AdvancedIntelligencePage from '../AdvancedIntelligence'
import type {
  CrossCorrelationIntelligenceResponse,
  GraphIntelligenceResponse,
  PredictiveIntelligenceResponse,
  WorkspaceSignalsResponse,
} from '../../../services/analytics/advancedAnalytics'

vi.mock('../../../App', () => ({
  AppLayout: ({
    children,
    actions,
  }: {
    children: ReactNode
    actions?: ReactNode
  }) => (
    <div>
      {actions}
      {children}
    </div>
  ),
}))

vi.mock('../../../router', () => ({
  useRouterParams: () => ({}),
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
  fetchWorkspaceSignals: () => Promise<WorkspaceSignalsResponse>
  fetchGraphIntelligence: () => Promise<GraphIntelligenceResponse>
  fetchPredictiveIntelligence: () => Promise<PredictiveIntelligenceResponse>
  fetchCrossCorrelationIntelligence: () => Promise<CrossCorrelationIntelligenceResponse>
}) {
  return render(
    <AdvancedIntelligencePage projectId="project-test" services={services} />,
  )
}

describe('AdvancedIntelligencePage', () => {
  it('renders explicit loading states before analytics resolve', () => {
    const pending = new Promise<never>(() => undefined)

    renderPage({
      fetchWorkspaceSignals: () => pending,
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
      fetchWorkspaceSignals: async () => ({
        kind: 'signals',
        status: 'empty',
        summary: 'No workspace signals.',
      }),
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
      screen.getByText('No predictive signals available for this project yet'),
    ).toBeInTheDocument()
    expect(screen.getByText('No predictive signals.')).toBeInTheDocument()
    expect(
      screen.getByText('No significant cross-correlations detected yet'),
    ).toBeInTheDocument()
    expect(screen.getByText('No correlation signals.')).toBeInTheDocument()
    expect(screen.getByText('Approval Readiness: N/A')).toBeInTheDocument()
    expect(screen.getByText('Finance Coverage: N/A')).toBeInTheDocument()
    expect(screen.getByText('Active Workflows: N/A')).toBeInTheDocument()
    expect(screen.getByText('Intelligence Score: N/A')).toBeInTheDocument()
  })

  it('renders explicit graph error copy without collapsing other panels', async () => {
    renderPage({
      fetchWorkspaceSignals: async () => ({
        kind: 'signals',
        status: 'ok',
        summary: 'Signal snapshot ready.',
        generatedAt: '2026-04-06T00:00:00Z',
        signals: [
          {
            signalId: 'approval-readiness',
            label: 'Approval Readiness',
            value: 67.5,
            unit: '%',
            trend: [],
          },
          {
            signalId: 'finance-coverage',
            label: 'Finance Coverage',
            value: 81.4,
            unit: '%',
            trend: [],
          },
          {
            signalId: 'active-workflows',
            label: 'Active Workflows',
            value: 2,
            unit: 'count',
            trend: [],
          },
          {
            signalId: 'intelligence-score',
            label: 'Intelligence Score',
            value: 74,
            unit: 'score',
            trend: [],
          },
        ],
      }),
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
      screen.getByText('No predictive signals available for this project yet'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('No significant cross-correlations detected yet'),
    ).toBeInTheDocument()
    expect(screen.getByText('Approval Readiness: 67.5%')).toBeInTheDocument()
  })

  it('renders a strict select-project empty state when no project is scoped', () => {
    render(<AdvancedIntelligencePage services={undefined} />)

    expect(
      screen.getByText('Select a project to load intelligence graph'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Advanced Intelligence now runs against a real project scope. Pick a project from the selector or open a project route first.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('SELECT PROJECT')).toBeInTheDocument()
  })
})
