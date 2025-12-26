import type {
  FinanceAnalyticsBucket,
  FinanceAnalyticsMetadata,
} from '../../../api/finance'

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
        gap: 'var(--ob-space-100)',
        marginBottom: 'var(--ob-space-050)',
      }}
    >
      <div
        style={{
          width: '120px',
          fontWeight: 600,
          color: 'var(--ob-color-text-secondary)',
        }}
      >
        {bucket.label}
      </div>
      <div
        style={{
          flex: 1,
          background: 'var(--ob-color-border-subtle)',
          borderRadius: 'var(--ob-radius-pill)',
          height: '8px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${Math.max(percentage, 2)}%`,
            background:
              bucket.key === 'lt_1'
                ? 'var(--ob-color-status-warning-text)'
                : 'var(--ob-color-brand-primary)',
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
        marginTop: 'var(--ob-space-200)',
        borderRadius: 'var(--ob-radius-sm)',
        border: '1px solid var(--ob-color-border-subtle)',
        padding: 'var(--ob-space-200)',
        background: 'var(--ob-color-bg-surface-elevated)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-150)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-100)',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-lg)',
              color: 'var(--ob-color-text-primary)',
            }}
          >
            Advanced analytics
          </h3>
          <p
            style={{
              margin: 0,
              color: 'var(--ob-color-text-secondary)',
              fontSize: 'var(--ob-font-size-md)',
            }}
          >
            MOIC, equity multiples, and DSCR health derived from the current
            scenario.
          </p>
        </div>
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 'var(--ob-space-150)',
        }}
      >
        <article
          style={{
            borderRadius: 'var(--ob-radius-sm)',
            border: '1px solid var(--ob-color-border-subtle)',
            padding: 'var(--ob-space-150)',
            background: 'var(--ob-color-bg-surface)',
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-muted)',
            }}
          >
            MOIC
          </p>
          <p
            style={{
              margin: 'var(--ob-space-075) 0 0',
              fontSize: 'var(--ob-font-size-2xl)',
              fontWeight: 700,
            }}
          >
            {formatRatio(analytics.moic)}
          </p>
        </article>
        <article
          style={{
            borderRadius: 'var(--ob-radius-sm)',
            border: '1px solid var(--ob-color-border-subtle)',
            padding: 'var(--ob-space-150)',
            background: 'var(--ob-color-bg-surface)',
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-muted)',
            }}
          >
            Equity multiple
          </p>
          <p
            style={{
              margin: 'var(--ob-space-075) 0 0',
              fontSize: 'var(--ob-font-size-2xl)',
              fontWeight: 700,
            }}
          >
            {formatRatio(analytics.equity_multiple)}
          </p>
        </article>
        <article
          style={{
            borderRadius: 'var(--ob-radius-sm)',
            border: '1px solid var(--ob-color-border-subtle)',
            padding: 'var(--ob-space-150)',
            background: 'var(--ob-color-bg-surface)',
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-muted)',
            }}
          >
            Equity invested
          </p>
          <p
            style={{
              margin: 'var(--ob-space-075) 0 0',
              fontSize: 'var(--ob-font-size-xl)',
              fontWeight: 700,
            }}
          >
            {formatCurrencyValue(cashSummary.invested_equity, currency)}
          </p>
          <p
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-muted)',
            }}
          >
            Net cash: {formatCurrencyValue(cashSummary.net_cash, currency)}
          </p>
        </article>
      </div>
      <div>
        <h4
          style={{
            margin: '0 0 var(--ob-space-075)',
            fontSize: 'var(--ob-font-size-md)',
            color: 'var(--ob-color-text-primary)',
          }}
        >
          DSCR heat map ({totalPeriods} periods)
        </h4>
        {buckets.length === 0 ? (
          <p style={{ margin: 0, color: 'var(--ob-color-text-muted)' }}>
            DSCR data not available.
          </p>
        ) : (
          <div>
            {buckets.map((bucket) => renderBucketBar(bucket, totalPeriods))}
          </div>
        )}
      </div>
    </section>
  )
}
