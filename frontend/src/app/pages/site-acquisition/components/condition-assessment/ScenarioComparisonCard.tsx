/**
 * Scenario Comparison Card Component
 *
 * Displays a scenario assessment compared against a baseline, showing deltas
 * for score, rating, and risk level.
 * Pure presentational component - receives display-ready props.
 */

import { toneColorMap, type ToneType } from '../../utils/insights'

// ============================================================================
// Types
// ============================================================================

export interface ScenarioComparisonCardProps {
  /** Unique scenario key */
  scenarioKey: string
  /** Display label for the scenario */
  scenarioLabel: string
  /** Score out of 100 */
  score: number
  /** Score delta from baseline */
  scoreDelta: number
  /** Pre-computed rating change info */
  ratingChange: { text: string; tone: ToneType }
  /** Pre-computed risk change info */
  riskChange: { text: string; tone: ToneType }
  /** Assessment summary text */
  summary: string
  /** Optional scenario context */
  scenarioContext: string | null
  /** Recommended actions for this scenario */
  recommendedActions: string[]
}

// ============================================================================
// Component
// ============================================================================

export function ScenarioComparisonCard({
  scenarioKey,
  scenarioLabel,
  score,
  scoreDelta,
  ratingChange,
  riskChange,
  summary,
  scenarioContext,
  recommendedActions,
}: ScenarioComparisonCardProps) {
  const scoreDeltaColor =
    scoreDelta > 0
      ? 'var(--ob-color-status-success)'
      : scoreDelta < 0
        ? 'var(--ob-color-status-error)'
        : 'var(--ob-color-text-muted)'

  const formattedDelta =
    scoreDelta === 0 ? 'Δ 0' : `Δ ${scoreDelta > 0 ? '+' : ''}${scoreDelta}`

  return (
    <div
      key={scenarioKey}
      style={{
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-065)',
        background: 'var(--ob-color-bg-surface)',
      }}
    >
      <strong
        style={{
          fontSize: 'var(--ob-font-size-base)',
          fontWeight: 'var(--ob-font-weight-semibold)',
        }}
      >
        {scenarioLabel}
      </strong>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-035)',
          fontSize: 'var(--ob-font-size-sm)',
          color: 'var(--ob-color-text-primary)',
        }}
      >
        <span>
          Score {score}/100{' '}
          <span
            style={{
              color: scoreDeltaColor,
              fontWeight: 'var(--ob-font-weight-semibold)',
            }}
          >
            {formattedDelta}
          </span>
        </span>
        <span
          style={{
            color: toneColorMap[ratingChange.tone],
            fontWeight: 'var(--ob-font-weight-semibold)',
          }}
        >
          {ratingChange.text}
        </span>
        <span
          style={{
            color: toneColorMap[riskChange.tone],
            fontWeight: 'var(--ob-font-weight-semibold)',
          }}
        >
          {riskChange.text}
        </span>
      </div>
      <p
        style={{
          margin: 0,
          fontSize: 'var(--ob-font-size-sm)',
          color: 'var(--ob-color-text-primary)',
          lineHeight: 'var(--ob-line-height-normal)',
        }}
      >
        {summary}
      </p>
      {scenarioContext && (
        <p
          style={{
            margin: 0,
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-color-brand-primary)',
          }}
        >
          {scenarioContext}
        </p>
      )}
      {recommendedActions.length > 0 && (
        <div style={{ display: 'grid', gap: 'var(--ob-space-035)' }}>
          <strong style={{ fontSize: 'var(--ob-font-size-sm)' }}>
            Actions
          </strong>
          <ul
            style={{
              margin: 0,
              paddingLeft: 'var(--ob-space-120)',
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-primary)',
              lineHeight: 'var(--ob-line-height-snug)',
            }}
          >
            {recommendedActions.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
