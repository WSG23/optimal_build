/**
 * Inspection History Summary Component
 *
 * Displays a summary of developer inspections for a property,
 * with actions to view timeline or log new inspections.
 */

import type { ConditionAssessmentEntry } from '../../../../api/siteAcquisition'

// ============================================================================
// Types
// ============================================================================

export interface InspectionHistorySummaryProps {
  /** Whether a property is captured (enables log inspection button) */
  hasProperty: boolean
  /** Loading state for assessment history */
  isLoading: boolean
  /** Error message if history failed to load */
  error: string | null
  /** Most recent assessment entry */
  latestEntry: ConditionAssessmentEntry | null
  /** Previous assessment entry for comparison */
  previousEntry: ConditionAssessmentEntry | null
  /** Format scenario key to display label - accepts various scenario type unions */
  formatScenario: (scenario: string | null | undefined) => string
  /** Format timestamp for display */
  formatTimestamp: (timestamp: string | null | undefined) => string
  /** Handler to open history modal */
  onViewTimeline: () => void
  /** Handler to open assessment editor */
  onLogInspection: () => void
}

// ============================================================================
// Component
// ============================================================================

export function InspectionHistorySummary({
  hasProperty,
  isLoading,
  error,
  latestEntry,
  previousEntry,
  formatScenario,
  formatTimestamp,
  onViewTimeline,
  onLogInspection,
}: InspectionHistorySummaryProps) {
  return (
    <div
      style={{
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '0.75rem',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: '1.0625rem',
              fontWeight: 600,
            }}
          >
            Inspection History
          </h3>
          <p
            style={{
              margin: '0.2rem 0 0',
              fontSize: '0.85rem',
              color: 'var(--ob-color-text-muted)',
            }}
          >
            Track developer inspections saved for this property.
          </p>
        </div>
        <button
          type="button"
          onClick={onViewTimeline}
          style={{
            borderRadius: 'var(--ob-radius-pill)',
            border: '1px solid var(--ob-color-text-primary)',
            background: 'var(--ob-color-text-primary)',
            color: 'white',
            padding: '0.45rem 1rem',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          View timeline
        </button>
        <button
          type="button"
          onClick={onLogInspection}
          disabled={!hasProperty}
          style={{
            borderRadius: 'var(--ob-radius-pill)',
            border: '1px solid var(--ob-color-text-primary)',
            background: 'white',
            color: 'var(--ob-color-text-primary)',
            padding: '0.45rem 1rem',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: hasProperty ? 'pointer' : 'not-allowed',
            opacity: hasProperty ? 1 : 0.6,
          }}
        >
          Log inspection
        </button>
      </div>

      {error ? (
        <p
          style={{
            margin: 0,
            fontSize: '0.85rem',
            color: 'var(--ob-error-700)',
          }}
        >
          {error}
        </p>
      ) : isLoading ? (
        <p
          style={{
            margin: 0,
            fontSize: '0.9rem',
            color: 'var(--ob-color-text-muted)',
          }}
        >
          Loading inspection history...
        </p>
      ) : latestEntry ? (
        <div
          style={{
            border: '1px solid var(--ob-color-border-subtle)',
            borderRadius: 'var(--ob-radius-sm)',
            padding: '1rem 1.1rem',
            background: 'var(--ob-color-bg-surface-elevated)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.4rem',
          }}
        >
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--ob-color-text-muted)',
            }}
          >
            Most recent inspection
          </span>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: '0.5rem',
              flexWrap: 'wrap',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.25rem',
              }}
            >
              <span style={{ fontSize: '0.95rem', fontWeight: 600 }}>
                {formatScenario(latestEntry.scenario)}
              </span>
              <span
                style={{
                  fontSize: '0.85rem',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                {formatTimestamp(latestEntry.recordedAt)}
              </span>
            </div>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.25rem',
              }}
            >
              <span
                style={{
                  fontSize: '0.8rem',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                Rating: <strong>{latestEntry.overallRating}</strong>
              </span>
              <span
                style={{
                  fontSize: '0.8rem',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                Score: <strong>{latestEntry.overallScore}/100</strong>
              </span>
              <span
                style={{
                  fontSize: '0.8rem',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                Risk:{' '}
                <strong style={{ textTransform: 'capitalize' }}>
                  {latestEntry.riskLevel}
                </strong>
              </span>
            </div>
          </div>
          <p
            style={{
              margin: 0,
              fontSize: '0.85rem',
              color: 'var(--ob-color-text-secondary)',
            }}
          >
            {latestEntry.summary || 'No summary recorded.'}
          </p>
          {previousEntry && (
            <p
              style={{
                margin: '0.35rem 0 0',
                fontSize: '0.75rem',
                color: 'var(--ob-color-text-muted)',
              }}
            >
              Last change:{' '}
              <strong>
                {formatScenario(previousEntry.scenario)} —{' '}
                {formatTimestamp(previousEntry.recordedAt)}
              </strong>
            </p>
          )}
        </div>
      ) : (
        <p
          style={{
            margin: 0,
            fontSize: '0.9rem',
            color: 'var(--ob-color-text-muted)',
          }}
        >
          No developer inspections recorded yet. Save an inspection to begin the
          audit trail.
        </p>
      )}
    </div>
  )
}
