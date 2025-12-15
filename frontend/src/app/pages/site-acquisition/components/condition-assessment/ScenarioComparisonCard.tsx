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
    scoreDelta > 0 ? '#15803d' : scoreDelta < 0 ? '#c53030' : '#6e6e73'

  const formattedDelta =
    scoreDelta === 0 ? 'Δ 0' : `Δ ${scoreDelta > 0 ? '+' : ''}${scoreDelta}`

  return (
    <div
      key={scenarioKey}
      style={{
        border: '1px solid #e5e5e7',
        borderRadius: '4px',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.6rem',
        background: '#ffffff',
      }}
    >
      <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
        {scenarioLabel}
      </strong>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '0.4rem',
          fontSize: '0.9rem',
          color: '#3a3a3c',
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
          color: '#3a3a3c',
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
        <div style={{ display: 'grid', gap: '0.4rem' }}>
          <strong style={{ fontSize: '0.85rem' }}>Actions</strong>
          <ul
            style={{
              margin: 0,
              paddingLeft: '1.1rem',
              fontSize: '0.85rem',
              color: '#3a3a3c',
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
