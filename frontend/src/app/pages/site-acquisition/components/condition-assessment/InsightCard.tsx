/**
 * Insight Card Component
 *
 * Displays a single condition insight with severity badge, title, detail, and optional chips.
 * Pure presentational component - receives display-ready props.
 *
 * Design Pattern: Left-border accent with glass surface
 * - Glass background (--ob-surface-glass-1)
 * - Colored left border indicates severity (3px accent)
 * - Severity badge with subtle semantic colors
 *
 * @see frontend/UI_STANDARDS.md - Card Interaction States
 * @see frontend/UX_ARCHITECTURE.md - Insight/Callout Box Pattern
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
      className="condition-insight-card"
      style={{
        // Glass surface with left-border accent pattern
        background: 'var(--ob-surface-glass-1)',
        backdropFilter: 'blur(var(--ob-blur-md))',
        WebkitBackdropFilter: 'blur(var(--ob-blur-md))',
        border: '1px solid var(--ob-color-border-subtle)',
        borderLeft: `3px solid ${visuals.indicator}`,
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-120)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-065)',
        color: 'var(--ob-color-text-primary)',
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
      }}
    >
      {/* Severity badge with semantic colors */}
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          alignSelf: 'flex-start',
          gap: 'var(--ob-space-035)',
          padding: 'var(--ob-space-025) var(--ob-space-065)',
          borderRadius: 'var(--ob-radius-xs)',
          fontSize: 'var(--ob-font-size-xs)',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: 'var(--ob-letter-spacing-widest)',
          background: visuals.badgeBg,
          color: visuals.badgeText,
          border: `1px solid ${visuals.badgeBorder}`,
        }}
      >
        <span
          style={{
            width: '6px',
            height: '6px',
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
