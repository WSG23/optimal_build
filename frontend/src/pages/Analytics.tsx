import { useCallback, useEffect, useMemo, useState } from 'react'

import { AppLayout } from '../App'

export interface QueryMetric {
  id: string
  statement: string
  averageDurationMs: number
  executionCount: number
  lastRunAt: string
}

export interface NormalizedQueryMetrics {
  byId: Record<string, QueryMetric>
  allIds: string[]
}

export type QueryMetricsSource = 'local' | 'remote'

type QueryMetricsStatus = 'idle' | 'loading' | 'ready'

export interface QueryMetricsSnapshot {
  source: QueryMetricsSource
  data: NormalizedQueryMetrics
}

export interface QueryMetricsErrorState {
  message: string
}

export interface AnalyticsServices {
  fetchQueryMetrics: () => Promise<NormalizedQueryMetrics>
}

const EMPTY_NORMALIZED_METRICS: NormalizedQueryMetrics = {
  byId: {},
  allIds: [],
}

const defaultSnapshot: QueryMetricsSnapshot = {
  source: 'local',
  data: EMPTY_NORMALIZED_METRICS,
}

async function defaultFetchQueryMetrics(): Promise<NormalizedQueryMetrics> {
  // Placeholder implementation; real implementation should call API service.
  return EMPTY_NORMALIZED_METRICS
}

const defaultServices: AnalyticsServices = {
  fetchQueryMetrics: defaultFetchQueryMetrics,
}

function renderQueryList(snapshot: QueryMetricsSnapshot) {
  if (snapshot.data.allIds.length === 0) {
    return (
      <p className="analytics__empty" data-testid="query-metrics-empty">
        No recent queries have been recorded yet.
      </p>
    )
  }

  return (
    <ul className="analytics__queries" data-testid="query-metrics-list">
      {snapshot.data.allIds.map((id) => {
        const metric = snapshot.data.byId[id]
        return (
          <li key={id} className="analytics__query">
            <pre className="analytics__query-sql">{metric.statement}</pre>
            <dl className="analytics__query-meta">
              <div>
                <dt>Average duration</dt>
                <dd>{metric.averageDurationMs.toLocaleString()} ms</dd>
              </div>
              <div>
                <dt>Execution count</dt>
                <dd>{metric.executionCount.toLocaleString()}</dd>
              </div>
              <div>
                <dt>Last run</dt>
                <dd>{metric.lastRunAt}</dd>
              </div>
            </dl>
          </li>
        )
      })}
    </ul>
  )
}

export interface AnalyticsPageProps {
  services?: Partial<AnalyticsServices>
}

export function AnalyticsPage({ services }: AnalyticsPageProps) {
  const mergedServices = useMemo<AnalyticsServices>(() => {
    if (!services) {
      return defaultServices
    }
    return {
      ...defaultServices,
      ...services,
    }
  }, [services])

  const [metrics, setMetrics] = useState<QueryMetricsSnapshot>(defaultSnapshot)
  const [status, setStatus] = useState<QueryMetricsStatus>('idle')
  const [error, setError] = useState<QueryMetricsErrorState | null>(null)

  const loadQueryMetrics = useCallback(async () => {
    setStatus('loading')
    setError(null)
    try {
      const normalized = await mergedServices.fetchQueryMetrics()
      setMetrics({
        source: 'remote',
        data: normalized,
      })
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Unable to load query metrics'
      setError({ message })
    } finally {
      setStatus('ready')
    }
  }, [mergedServices])

  useEffect(() => {
    loadQueryMetrics().catch(() => {
      // Errors handled in loadQueryMetrics
    })
  }, [loadQueryMetrics])

  return (
    <AppLayout title="Analytics" subtitle="Query performance overview">
      <section className="analytics">
        <header className="analytics__header">
          <h3>Recent query activity</h3>
          <button
            type="button"
            className="analytics__refresh"
            onClick={() => {
              loadQueryMetrics().catch(() => {
                // Errors handled in loadQueryMetrics
              })
            }}
            disabled={status === 'loading'}
          >
            {status === 'loading' ? 'Refreshing…' : 'Refresh'}
          </button>
        </header>
        {error ? (
          <p role="alert" className="analytics__error">
            {error.message}
          </p>
        ) : null}
        {renderQueryList(metrics)}
      </section>
    </AppLayout>
  )
}

export default AnalyticsPage
