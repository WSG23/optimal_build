import { useCallback, useMemo } from 'react'

import { AppLayout } from '../../App'
import {
  type CrossCorrelationIntelligenceState,
  type GraphIntelligenceState,
  type InvestigationAnalyticsServices,
  type PredictiveIntelligenceState,
  useInvestigationAnalytics,
} from '../../hooks/useInvestigationAnalytics'

export interface AdvancedIntelligencePageProps {
  workspaceId?: string
  services?: Partial<InvestigationAnalyticsServices>
}

const DEFAULT_WORKSPACE_ID = 'default-investigation'

function formatPercent(value: number | null | undefined, fractionDigits = 0) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '–'
  }
  return `${value.toFixed(fractionDigits)}%`
}

function renderGraphSection(state: GraphIntelligenceState) {
  if (state.status === 'loading') {
    return <p>Loading relationship intelligence…</p>
  }

  if (state.status === 'error') {
    return (
      <p role="alert" className="advanced-intelligence__error">
        Unable to load relationship intelligence: {state.error}
      </p>
    )
  }

  if (state.status === 'empty') {
    return (
      <p className="advanced-intelligence__empty">
        No relationship intelligence is available for this workspace yet.
      </p>
    )
  }

  const nodeCount = state.graph.nodes.length
  const edgeCount = state.graph.edges.length
  const topNodes = [...state.graph.nodes]
    .sort((a, b) => b.score - a.score)
    .slice(0, 4)

  return (
    <div className="advanced-intelligence__panel">
      <p>{state.summary}</p>
      <p>
        Graph density:{' '}
        <strong>
          {nodeCount} nodes / {edgeCount} edges
        </strong>
      </p>
      <ul className="advanced-intelligence__list">
        {topNodes.map((node) => (
          <li key={node.id}>
            <strong>{node.label}</strong> — {node.category} ({Math.round(node.score * 100) / 100})
          </li>
        ))}
      </ul>
      <p className="advanced-intelligence__meta">Generated at {state.generatedAt}</p>
    </div>
  )
}

function deriveAdoptionRate(state: PredictiveIntelligenceState): number | null {
  if (state.status !== 'ok') {
    return null
  }
  if (state.segments.length === 0) {
    return 0
  }
  const sumProbability = state.segments.reduce(
    (sum, segment) => sum + segment.probability,
    0,
  )
  return (sumProbability / state.segments.length) * 100
}

function deriveAverageUplift(state: PredictiveIntelligenceState): number | null {
  if (state.status !== 'ok') {
    return null
  }
  let contributingSegments = 0
  const cumulativeUplift = state.segments.reduce((sum, segment) => {
    if (segment.baseline === 0) {
      return sum
    }
    contributingSegments += 1
    return sum + ((segment.projection - segment.baseline) / segment.baseline) * 100
  }, 0)

  if (contributingSegments === 0) {
    return 0
  }

  return cumulativeUplift / contributingSegments
}

function renderPredictiveSection(state: PredictiveIntelligenceState) {
  if (state.status === 'loading') {
    return <p>Running predictive models…</p>
  }

  if (state.status === 'error') {
    return (
      <p role="alert" className="advanced-intelligence__error">
        Unable to load predictive intelligence: {state.error}
      </p>
    )
  }

  if (state.status === 'empty') {
    return (
      <p className="advanced-intelligence__empty">
        Predictive models have not produced any actionable signals for this workspace.
      </p>
    )
  }

  const adoptionRate = deriveAdoptionRate(state)
  const averageUplift = deriveAverageUplift(state)
  const momentumSegments = state.segments
    .filter((segment) => segment.projection > segment.baseline)
    .sort((a, b) => b.probability - a.probability)
    .slice(0, 3)

  return (
    <div className="advanced-intelligence__panel">
      <p>{state.summary}</p>
      <p>
        Average adoption likelihood:{' '}
        <strong>{formatPercent(adoptionRate)}</strong>
      </p>
      <p>
        Average projected uplift:{' '}
        <strong>{formatPercent(averageUplift, 1)}</strong>
      </p>
      <p>
        Forecast horizon:{' '}
        <strong>{state.horizonMonths} months</strong>
      </p>
      <ul className="advanced-intelligence__list">
        {momentumSegments.map((segment) => (
          <li key={segment.segmentId}>
            <strong>{segment.segmentName}</strong> —
            {` ${(segment.probability * 100).toFixed(0)}% likelihood, projection ${segment.projection.toLocaleString()}`}
          </li>
        ))}
      </ul>
      <p className="advanced-intelligence__meta">Generated at {state.generatedAt}</p>
    </div>
  )
}

function renderCorrelationSection(state: CrossCorrelationIntelligenceState) {
  if (state.status === 'loading') {
    return <p>Analysing cross correlations…</p>
  }

  if (state.status === 'error') {
    return (
      <p role="alert" className="advanced-intelligence__error">
        Unable to load cross-correlation intelligence: {state.error}
      </p>
    )
  }

  if (state.status === 'empty') {
    return (
      <p className="advanced-intelligence__empty">
        There are no significant cross correlations detected for this workspace.
      </p>
    )
  }

  const rankedRelationships = [...state.relationships]
    .sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient))
    .slice(0, 4)

  return (
    <div className="advanced-intelligence__panel">
      <p>{state.summary}</p>
      <ul className="advanced-intelligence__list">
        {rankedRelationships.map((relationship) => (
          <li key={relationship.pairId}>
            <strong>{relationship.driver}</strong> → {relationship.outcome}{' '}
            ({relationship.coefficient.toFixed(2)} ρ, p={relationship.pValue.toFixed(3)})
          </li>
        ))}
      </ul>
      <p className="advanced-intelligence__meta">Updated at {state.updatedAt}</p>
    </div>
  )
}

export function AdvancedIntelligencePage({
  workspaceId = DEFAULT_WORKSPACE_ID,
  services,
}: AdvancedIntelligencePageProps) {
  const { graph, predictive, correlation, isLoading, refetch } =
    useInvestigationAnalytics(workspaceId, services)

  const handleRefresh = useCallback(() => {
    return refetch()
  }, [refetch])

  const derivedAdoptionRate = useMemo(() => deriveAdoptionRate(predictive), [predictive])
  const derivedAverageUplift = useMemo(
    () => deriveAverageUplift(predictive),
    [predictive],
  )

  return (
    <AppLayout
      title="Advanced Intelligence"
      subtitle="Investigation analytics workspace"
      actions={
        <button
          type="button"
          className="advanced-intelligence__refresh"
          onClick={handleRefresh}
          disabled={isLoading}
        >
          {isLoading ? 'Refreshing…' : 'Refresh analytics'}
        </button>
      }
    >
      <div className="page">{/* Standard page container */}
        <section className="advanced-intelligence__section" aria-labelledby="advanced-intelligence-overview">
          <h3 id="advanced-intelligence-overview">Workspace signals</h3>
          {isLoading && (
            <p data-testid="analytics-loading">Loading analytics for workspace {workspaceId}…</p>
          )}
          {!isLoading && predictive.status === 'ok' && (
            <div className="advanced-intelligence__summary">
              <p>
                Current adoption likelihood across cohorts:{' '}
                <strong>{formatPercent(derivedAdoptionRate)}</strong>
              </p>
              <p>
                Average projected uplift across active cohorts:{' '}
                <strong>{formatPercent(derivedAverageUplift, 1)}</strong>
              </p>
            </div>
          )}
        </section>

        <section className="advanced-intelligence__section" aria-labelledby="graph-intelligence">
          <h3 id="graph-intelligence">Relationship intelligence</h3>
          {renderGraphSection(graph)}
        </section>

        <section className="advanced-intelligence__section" aria-labelledby="predictive-intelligence">
          <h3 id="predictive-intelligence">Predictive intelligence</h3>
          {renderPredictiveSection(predictive)}
        </section>

        <section className="advanced-intelligence__section" aria-labelledby="correlation-intelligence">
          <h3 id="correlation-intelligence">Cross-correlation intelligence</h3>
          {renderCorrelationSection(correlation)}
        </section>
      </div>
    </AppLayout>
  )
}

export default AdvancedIntelligencePage
