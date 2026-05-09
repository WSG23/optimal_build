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
        padding: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-075)',
      }}
    >
      <h4
        style={{
          margin: 0,
          fontSize: 'var(--ob-font-size-sm)',
          fontWeight: 'var(--ob-font-weight-semibold)',
        }}
      >
        Recommended actions diff
      </h4>
      <div
        style={{
          display: 'grid',
          gap: 'var(--ob-space-075)',
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
                margin: 'var(--ob-space-035) 0 0',
                paddingLeft: 'var(--ob-space-120)',
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-primary)',
                lineHeight: 'var(--ob-line-height-snug)',
              }}
            >
              {recommendedActionDiff.newActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          ) : (
            <p
              style={{
                margin: 'var(--ob-space-035) 0 0',
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
                margin: 'var(--ob-space-035) 0 0',
                paddingLeft: 'var(--ob-space-120)',
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-primary)',
                lineHeight: 'var(--ob-line-height-snug)',
              }}
            >
              {recommendedActionDiff.clearedActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          ) : (
            <p
              style={{
                margin: 'var(--ob-space-035) 0 0',
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
