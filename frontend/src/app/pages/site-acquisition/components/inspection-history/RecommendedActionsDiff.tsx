/**
 * Recommended Actions Diff
 *
 * Shows new and cleared recommended actions between two inspection cycles.
 * Extracted from HistoryCompareView for component size management.
 */

import type { HistoryRecommendedActionDiff as RecommendedActionDiff } from '../../utils/historyComparisons'

export interface RecommendedActionsDiffProps {
  recommendedActionDiff: RecommendedActionDiff
}

export function RecommendedActionsDiffPanel({
  recommendedActionDiff,
}: RecommendedActionsDiffProps) {
  return (
    <div
      style={{
        border: '1px solid var(--ob-color-border-primary)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}
    >
      <h4
        style={{
          margin: 0,
          fontSize: 'var(--ob-font-size-sm)',
          fontWeight: 600,
        }}
      >
        Recommended actions diff
      </h4>
      <div
        style={{
          display: 'grid',
          gap: '0.75rem',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        }}
      >
        {/* New actions */}
        <div>
          <strong
            style={{
              fontSize: 'var(--ob-font-size-sm)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              color: 'var(--ob-success-700)',
            }}
          >
            New this cycle
          </strong>
          {recommendedActionDiff.newActions.length > 0 ? (
            <ul
              style={{
                margin: '0.4rem 0 0',
                paddingLeft: '1.1rem',
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-primary)',
                lineHeight: 1.4,
              }}
            >
              {recommendedActionDiff.newActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          ) : (
            <p
              style={{
                margin: '0.35rem 0 0',
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-secondary)',
              }}
            >
              No new actions added.
            </p>
          )}
        </div>

        {/* Cleared actions */}
        <div>
          <strong
            style={{
              fontSize: 'var(--ob-font-size-sm)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              color: 'var(--ob-color-brand-500)',
            }}
          >
            Completed / Cleared
          </strong>
          {recommendedActionDiff.clearedActions.length > 0 ? (
            <ul
              style={{
                margin: '0.4rem 0 0',
                paddingLeft: '1.1rem',
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-primary)',
                lineHeight: 1.4,
              }}
            >
              {recommendedActionDiff.clearedActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          ) : (
            <p
              style={{
                margin: '0.35rem 0 0',
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-secondary)',
              }}
            >
              No actions cleared.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
