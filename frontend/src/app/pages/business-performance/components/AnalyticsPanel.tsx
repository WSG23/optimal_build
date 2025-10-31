import type { AnalyticsMetric, BenchmarkEntry, TrendPoint } from '../types'

interface AnalyticsPanelProps {
  metrics: AnalyticsMetric[]
  trend: TrendPoint[]
  benchmarks: BenchmarkEntry[]
}

export function AnalyticsPanel({
  metrics,
  trend,
  benchmarks,
}: AnalyticsPanelProps) {
  return (
    <div className="bp-analytics">
      <section className="bp-analytics__metrics">
        {metrics.map((metric) => (
          <article className="bp-metric-card" key={metric.key}>
            <h4>{metric.label}</h4>
            <span className="bp-metric-card__value">{metric.value}</span>
            {metric.helperText && (
              <p className="bp-metric-card__hint">{metric.helperText}</p>
            )}
          </article>
        ))}
      </section>

      <section className="bp-analytics__trend">
        <h3>30-day trend</h3>
        <div className="bp-trend-placeholder">
          <p>
            Trend visualisation will display weighted pipeline vs. gross value,
            plus conversion rate vs. cycle time.
          </p>
          <ul>
            {trend.map((point) => (
              <li key={point.label}>
                <strong>{point.label}</strong> — Gross:{' '}
                {formatNumber(point.gross)}, Weighted:{' '}
                {formatNumber(point.weighted)}, Conversion:{' '}
                {formatPercent(point.conversion)}, Cycle:{' '}
                {formatNumber(point.cycle)} days
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="bp-analytics__benchmarks">
        <h3>Benchmark comparison</h3>
        <ul className="bp-benchmark-list">
          {benchmarks.map((entry) => (
            <li key={entry.key}>
              <div className="bp-benchmark-list__header">
                <span>{entry.label}</span>
                <strong>{entry.actual}</strong>
              </div>
              <p>
                {entry.benchmark && entry.cohort && (
                  <span>
                    vs {entry.cohort}: {entry.benchmark}
                  </span>
                )}
                {entry.deltaText && (
                  <span
                    className={[
                      'bp-benchmark-list__delta',
                      entry.deltaPositive
                        ? 'bp-benchmark-list__delta--positive'
                        : 'bp-benchmark-list__delta--negative',
                    ].join(' ')}
                  >
                    {entry.deltaText}
                  </span>
                )}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

function formatNumber(value: number | null) {
  if (value === null || Number.isNaN(value)) return '—'
  return value.toLocaleString(undefined, { maximumFractionDigits: 1 })
}

function formatPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) return '—'
  return `${(value * 100).toFixed(1)}%`
}
