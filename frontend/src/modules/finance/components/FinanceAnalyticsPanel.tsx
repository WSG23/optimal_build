import type { FinanceAnalyticsBucket, FinanceAnalyticsMetadata } from '../../../api/finance'

interface FinanceAnalyticsPanelProps {
  analytics: FinanceAnalyticsMetadata
  currency: string
}

function formatCurrencyValue(
  value: string | null | undefined,
  currency: string,
): string {
  if (value === null || value === undefined || value === '') {
    return '—'
  }
  const amount = Number(value)
  if (!Number.isFinite(amount)) {
    return value
  }
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(amount)
  } catch {
    return `${value} ${currency}`
  }
}

function formatRatio(value: string | null | undefined): string {
  if (!value) {
    return '—'
  }
  return `${value}x`
}

function renderBucketBar(
  bucket: FinanceAnalyticsBucket,
  total: number,
): JSX.Element {
  const percentage = total > 0 ? Math.round((bucket.count / total) * 100) : 0
  return (
    <div
      key={bucket.key}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        marginBottom: '0.35rem',
      }}
    >
      <div style={{ width: '120px', fontWeight: 600, color: '#1f2937' }}>
        {bucket.label}
      </div>
      <div
        style={{
          flex: 1,
          background: '#e5e7eb',
          borderRadius: '9999px',
          height: '8px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${Math.max(percentage, 2)}%`,
            background: bucket.key === 'lt_1' ? '#f97316' : '#2563eb',
            height: '100%',
          }}
        />
      </div>
      <div style={{ width: '40px', textAlign: 'right', fontWeight: 600 }}>
        {bucket.count}
      </div>
    </div>
  )
}

export function FinanceAnalyticsPanel({
  analytics,
  currency,
}: FinanceAnalyticsPanelProps) {
  const cashSummary = analytics.cash_flow_summary ?? {}
  const buckets = analytics.dscr_heatmap?.buckets ?? []
  const totalPeriods = buckets.reduce((sum, bucket) => sum + bucket.count, 0)

  return (
    <section
      style={{
        marginTop: '1.5rem',
        borderRadius: '20px',
        border: '1px solid #d1d5db',
        padding: '1.5rem',
        background: '#f9fafb',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#111827' }}>
            Advanced analytics
          </h3>
          <p style={{ margin: 0, color: '#4b5563', fontSize: '0.95rem' }}>
            MOIC, equity multiples, and DSCR health derived from the current scenario.
          </p>
        </div>
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem',
        }}
      >
        <article
          style={{
            borderRadius: '16px',
            border: '1px solid #d1d5db',
            padding: '1rem',
            background: '#fff',
          }}
        >
          <p style={{ margin: 0, fontSize: '0.8rem', color: '#6b7280' }}>MOIC</p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '1.5rem', fontWeight: 700 }}>
            {formatRatio(analytics.moic)}
          </p>
        </article>
        <article
          style={{
            borderRadius: '16px',
            border: '1px solid #d1d5db',
            padding: '1rem',
            background: '#fff',
          }}
        >
          <p style={{ margin: 0, fontSize: '0.8rem', color: '#6b7280' }}>
            Equity multiple
          </p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '1.5rem', fontWeight: 700 }}>
            {formatRatio(analytics.equity_multiple)}
          </p>
        </article>
        <article
          style={{
            borderRadius: '16px',
            border: '1px solid #d1d5db',
            padding: '1rem',
            background: '#fff',
          }}
        >
          <p style={{ margin: 0, fontSize: '0.8rem', color: '#6b7280' }}>
            Equity invested
          </p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '1.2rem', fontWeight: 700 }}>
            {formatCurrencyValue(cashSummary.invested_equity, currency)}
          </p>
          <p style={{ margin: 0, fontSize: '0.8rem', color: '#6b7280' }}>
            Net cash: {formatCurrencyValue(cashSummary.net_cash, currency)}
          </p>
        </article>
      </div>
      <div>
        <h4 style={{ margin: '0 0 0.5rem', fontSize: '1rem', color: '#111827' }}>
          DSCR heat map ({totalPeriods} periods)
        </h4>
        {buckets.length === 0 ? (
          <p style={{ margin: 0, color: '#6b7280' }}>DSCR data not available.</p>
        ) : (
          <div>
            {buckets.map((bucket) => renderBucketBar(bucket, totalPeriods))}
          </div>
        )}
      </div>
    </section>
  )
}
