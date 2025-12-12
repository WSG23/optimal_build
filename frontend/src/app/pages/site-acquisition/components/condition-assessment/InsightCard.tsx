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
    gap: '0.35rem',
    padding: '0.3rem 0.6rem',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: 600,
    background: 'rgba(15, 23, 42, 0.08)',
    color: '#0f172a',
    border: '1px solid rgba(15, 23, 42, 0.12)',
  }

  return (
    <div
      key={id}
      style={{
        border: `1px solid ${visuals.border}`,
        background: visuals.background,
        color: visuals.text,
        borderRadius: '4px',
        padding: '1.2rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.65rem',
      }}
    >
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4rem',
          fontSize: '0.75rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        }}
      >
        <span
          style={{
            width: '0.35rem',
            height: '0.35rem',
            borderRadius: '9999px',
            background: visuals.indicator,
          }}
        />
        {visuals.label}
      </span>
      <strong style={{ fontSize: '0.95rem', lineHeight: 1.4 }}>{title}</strong>
      <p
        style={{
          margin: 0,
          fontSize: '0.85rem',
          lineHeight: 1.4,
        }}
      >
        {detail}
      </p>
      {(specialist || isChecklistInsight) && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.5rem',
          }}
        >
          {isChecklistInsight && (
            <span
              style={{
                ...chipStyle,
                background: 'rgba(29, 78, 216, 0.08)',
                color: '#1d4ed8',
                border: '1px solid rgba(29, 78, 216, 0.15)',
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
