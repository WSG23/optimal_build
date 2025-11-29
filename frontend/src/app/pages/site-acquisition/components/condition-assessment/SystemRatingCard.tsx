/**
 * System Rating Card Component
 *
 * Displays a single system's condition rating with score, delta badge, notes, and actions.
 * Pure presentational component - receives display-ready props.
 */

import type { SeverityVisuals, DeltaVisuals } from '../../utils/insights'

// ============================================================================
// Types
// ============================================================================

export interface SystemRatingCardProps {
  /** System name (e.g., "Structural", "M&E") */
  systemName: string
  /** Current rating letter (e.g., "A", "B", "C") */
  rating: string
  /** Current score out of 100 */
  score: number
  /** System notes/description */
  notes: string
  /** Recommended actions for this system */
  recommendedActions: string[]
  /** Previous rating letter, if available */
  previousRating: string | null
  /** Previous score, if available */
  previousScore: number | null
  /** Score delta from previous assessment */
  delta: number | null
  /** Pre-computed formatted delta string (e.g., "+5", "-3") */
  formattedDelta: string
  /** Pre-computed badge visuals from getSeverityVisuals */
  badgeVisuals: SeverityVisuals
  /** Pre-computed delta visuals from getDeltaVisuals */
  deltaVisuals: DeltaVisuals
}

// ============================================================================
// Component
// ============================================================================

export function SystemRatingCard({
  systemName,
  rating,
  score,
  notes,
  recommendedActions,
  previousRating,
  previousScore,
  delta,
  formattedDelta,
  badgeVisuals,
  deltaVisuals,
}: SystemRatingCardProps) {
  return (
    <div
      style={{
        border: '1px solid #e5e5e7',
        borderRadius: '12px',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '0.6rem',
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
          }}
        >
          <h3
            style={{
              margin: 0,
              fontSize: '1.0625rem',
              fontWeight: 600,
            }}
          >
            {systemName}
          </h3>
          {previousRating && previousScore !== null && (
            <span style={{ fontSize: '0.8rem', color: '#6e6e73' }}>
              Previous {previousRating} · {previousScore}/100
            </span>
          )}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.45rem',
          }}
        >
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.3rem 0.65rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              border: `1px solid ${badgeVisuals.border}`,
              background: badgeVisuals.background,
              color: badgeVisuals.text,
            }}
          >
            <span
              style={{
                width: '0.35rem',
                height: '0.35rem',
                borderRadius: '9999px',
                background: badgeVisuals.indicator,
              }}
            />
            {rating} · {score}/100
          </span>
          {delta !== null && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
                padding: '0.25rem 0.55rem',
                borderRadius: '9999px',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: deltaVisuals.background,
                color: deltaVisuals.text,
                border: `1px solid ${deltaVisuals.border}`,
              }}
            >
              {delta > 0 ? '▲' : delta < 0 ? '▼' : '■'} {formattedDelta}
            </span>
          )}
        </div>
      </div>
      <p
        style={{
          margin: 0,
          fontSize: '0.9rem',
          color: '#3a3a3c',
          lineHeight: 1.5,
        }}
      >
        {notes}
      </p>
      <ul
        style={{
          margin: 0,
          paddingLeft: '1.1rem',
          fontSize: '0.875rem',
          color: '#3a3a3c',
          lineHeight: 1.4,
        }}
      >
        {recommendedActions.map((action) => (
          <li key={action}>{action}</li>
        ))}
      </ul>
    </div>
  )
}
