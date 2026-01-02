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
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-075)',
        background: 'var(--ob-color-bg-surface)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-065)',
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-035)',
          }}
        >
          <h3
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-lg)',
              fontWeight: 600,
            }}
          >
            {systemName}
          </h3>
          {previousRating && previousScore !== null && (
            <span
              style={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'var(--ob-color-text-muted)',
              }}
            >
              Previous {previousRating} · {previousScore}/100
            </span>
          )}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 'var(--ob-space-050)',
          }}
        >
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 'var(--ob-space-035)',
              padding: 'var(--ob-space-025) var(--ob-space-065)',
              borderRadius: 'var(--ob-radius-pill)',
              fontSize: 'var(--ob-font-size-xs)',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: 'var(--ob-letter-spacing-widest)',
              border: `1px solid ${badgeVisuals.border}`,
              background: badgeVisuals.background,
              color: badgeVisuals.text,
            }}
          >
            <span
              style={{
                width: 'var(--ob-space-035)',
                height: 'var(--ob-space-035)',
                borderRadius: 'var(--ob-radius-pill)',
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
                gap: 'var(--ob-space-025)',
                padding: 'var(--ob-space-025) var(--ob-space-050)',
                borderRadius: 'var(--ob-radius-pill)',
                fontSize: 'var(--ob-font-size-xs)',
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
          fontSize: 'var(--ob-font-size-sm)',
          color: 'var(--ob-color-text-secondary)',
          lineHeight: 'var(--ob-line-height-normal)',
        }}
      >
        {notes}
      </p>
      <ul
        style={{
          margin: 0,
          paddingLeft: 'var(--ob-space-100)',
          fontSize: 'var(--ob-font-size-sm)',
          color: 'var(--ob-color-text-secondary)',
          lineHeight: 'var(--ob-line-height-snug)',
        }}
      >
        {recommendedActions.map((action) => (
          <li key={action}>{action}</li>
        ))}
      </ul>
    </div>
  )
}
