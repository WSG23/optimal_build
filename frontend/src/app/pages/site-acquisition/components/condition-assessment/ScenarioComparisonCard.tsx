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
      ? '#15803d'
      : scoreDelta < 0
        ? '#c53030'
        : 'var(--ob-color-text-secondary)'

  const formattedDelta =
    scoreDelta === 0 ? 'Δ 0' : `Δ ${scoreDelta > 0 ? '+' : ''}${scoreDelta}`

  return (
    <div
      key={scenarioKey}
      style={{
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-200)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
        background: 'var(--ob-color-bg-default)',
      }}
    >
      <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
        {scenarioLabel}
      </strong>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-100)',
          fontSize: '0.9rem',
          color: 'var(--ob-color-bg-elevated)',
        }}
      >
        <span>
          Score {score}/100{' '}
          <span
            style={{
              color: scoreDeltaColor,
              fontWeight: 600,
            }}
          >
            {formattedDelta}
          </span>
        </span>
        <span
          style={{
            color: toneColorMap[ratingChange.tone],
            fontWeight: 600,
          }}
        >
          {ratingChange.text}
        </span>
        <span
          style={{
            color: toneColorMap[riskChange.tone],
            fontWeight: 600,
          }}
        >
          {riskChange.text}
        </span>
      </div>
      <p
        style={{
          margin: 0,
          fontSize: '0.9rem',
          color: 'var(--ob-color-bg-elevated)',
          lineHeight: 1.5,
        }}
      >
        {summary}
      </p>
      {scenarioContext && (
        <p
          style={{
            margin: 0,
            fontSize: '0.85rem',
            color: '#0071e3',
          }}
        >
          {scenarioContext}
        </p>
      )}
      {recommendedActions.length > 0 && (
        <div style={{ display: 'grid', gap: 'var(--ob-space-100)' }}>
          <strong style={{ fontSize: '0.85rem' }}>Actions</strong>
          <ul
            style={{
              margin: 0,
              paddingLeft: 'var(--ob-space-200)',
              fontSize: '0.85rem',
              color: 'var(--ob-color-bg-elevated)',
              lineHeight: 1.4,
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
