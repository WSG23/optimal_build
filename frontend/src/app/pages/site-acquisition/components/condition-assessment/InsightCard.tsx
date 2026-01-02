/**
 * Insight Card Component
 *
 * Displays a single condition insight with severity badge, title, detail, and optional chips.
 * Pure presentational component - receives display-ready props.
 */

import type { CSSProperties } from 'react'
import type { SeverityVisuals } from '../../utils/insights'

// ============================================================================
// Types
// ============================================================================

export interface InsightCardProps {
  /** Unique identifier for the insight */
  id: string
  /** Pre-computed severity visuals (from getSeverityVisuals) */
  visuals: SeverityVisuals
  /** Insight title */
  title: string
  /** Detailed description */
  detail: string
  /** Whether this is a checklist-derived insight */
  isChecklistInsight: boolean
  /** Optional specialist recommendation */
  specialist: string | null
}

// ============================================================================
// Component
// ============================================================================

export function InsightCard({
  id,
  visuals,
  title,
  detail,
  isChecklistInsight,
  specialist,
}: InsightCardProps) {
  const chipStyle: CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 'var(--ob-space-035)',
    padding: 'var(--ob-space-025) var(--ob-space-065)',
    borderRadius: 'var(--ob-radius-pill)',
    fontSize: 'var(--ob-font-size-xs)',
    fontWeight: 600,
    background: 'var(--ob-color-bg-muted)',
    color: 'var(--ob-color-text-primary)',
    border: '1px solid var(--ob-color-border-subtle)',
  }

  return (
    <div
      key={id}
      style={{
        border: `1px solid ${visuals.border}`,
        background: visuals.background,
        color: visuals.text,
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-120)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-065)',
      }}
    >
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 'var(--ob-space-035)',
          fontSize: 'var(--ob-font-size-xs)',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: 'var(--ob-letter-spacing-widest)',
        }}
      >
        <span
          style={{
            width: 'var(--ob-space-035)',
            height: 'var(--ob-space-035)',
            borderRadius: 'var(--ob-radius-pill)',
            background: visuals.indicator,
          }}
        />
        {visuals.label}
      </span>
      <strong
        style={{
          fontSize: 'var(--ob-font-size-md)',
          lineHeight: 'var(--ob-line-height-snug)',
        }}
      >
        {title}
      </strong>
      <p
        style={{
          margin: 0,
          fontSize: 'var(--ob-font-size-sm)',
          lineHeight: 'var(--ob-line-height-snug)',
        }}
      >
        {detail}
      </p>
      {(specialist || isChecklistInsight) && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 'var(--ob-space-050)',
          }}
        >
          {isChecklistInsight && (
            <span
              style={{
                ...chipStyle,
                background: 'var(--ob-color-brand-muted)',
                color: 'var(--ob-brand-700)',
                border: '1px solid var(--ob-color-brand-soft)',
              }}
            >
              Checklist follow-up
            </span>
          )}
          {specialist && (
            <span style={chipStyle}>
              Specialist · <strong>{specialist}</strong>
            </span>
          )}
        </div>
      )}
    </div>
  )
}
