/**
 * History Timeline View Component
 *
 * Displays inspection history entries as a vertical timeline.
 * Each entry shows scenario, date, inspector, rating, score, risk level,
 * recommended actions preview, and attachments.
 */

import type {
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../../api/siteAcquisition'

// ============================================================================
// Types
// ============================================================================

export interface HistoryTimelineViewProps {
  assessmentHistory: ConditionAssessment[]
  activeScenario: 'all' | DevelopmentScenario

  // Formatters (stable callbacks from parent)
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

// ============================================================================
// Component
// ============================================================================

export function HistoryTimelineView({
  assessmentHistory,
  activeScenario,
  formatScenarioLabel,
  formatRecordedTimestamp,
}: HistoryTimelineViewProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
      {assessmentHistory.map((entry, index) => {
        const key = `${entry.recordedAt ?? 'draft'}-${index}`
        const matchesScenario =
          activeScenario === 'all' ||
          !entry.scenario ||
          entry.scenario === activeScenario
        const recommendedPreview = entry.recommendedActions.slice(0, 2)
        const remainingActions =
          entry.recommendedActions.length - recommendedPreview.length

        return (
          <div
            key={key}
            style={{
              border: '1px solid var(--ob-color-border-subtle)',
              borderLeft: `4px solid ${
                index === 0
                  ? 'var(--ob-color-brand-primary)'
                  : matchesScenario
                    ? 'var(--ob-success-500)'
                    : 'var(--ob-color-border-subtle)'
              }`,
              borderRadius: 'var(--ob-radius-sm)',
              padding: '1rem 1.25rem',
              background: index === 0 ? 'var(--ob-info-50)' : 'white',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
            }}
          >
            {/* Header with scenario and timestamp */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                flexWrap: 'wrap',
                gap: '0.5rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.25rem',
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
                  {index === 0
                    ? 'Most recent inspection'
                    : `Inspection ${index + 1}`}
                </span>
                <span style={{ fontSize: '0.9375rem', fontWeight: 600 }}>
                  {formatScenarioLabel(entry.scenario)}
                </span>
              </div>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.2rem',
                  alignItems: 'flex-end',
                }}
              >
                <span
                  style={{
                    fontSize: '0.85rem',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  {formatRecordedTimestamp(entry.recordedAt)}
                </span>
                <span
                  style={{
                    fontSize: '0.78rem',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  Inspector:{' '}
                  <strong>
                    {entry.inspectorName?.trim() || 'Not recorded'}
                  </strong>
                </span>
              </div>
            </div>

            {/* Summary */}
            <p
              style={{
                margin: 0,
                fontSize: '0.875rem',
                color: 'var(--ob-color-text-secondary)',
              }}
            >
              {entry.summary || 'No notes recorded.'}
            </p>

            {/* Rating, Score, Risk metrics */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.4rem',
                fontSize: '0.8rem',
                color: 'var(--ob-color-text-muted)',
              }}
            >
              <span>
                Rating: <strong>{entry.overallRating}</strong>
              </span>
              <span>
                Score: <strong>{entry.overallScore}/100</strong>
              </span>
              <span>
                Risk level:{' '}
                <strong style={{ textTransform: 'capitalize' }}>
                  {entry.riskLevel}
                </strong>
              </span>
            </div>

            {/* Recommended actions preview */}
            {recommendedPreview.length > 0 && (
              <div style={{ marginTop: '0.25rem' }}>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    color: 'var(--ob-color-text-muted)',
                    letterSpacing: '0.06em',
                  }}
                >
                  Recommended actions
                </span>
                <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1rem' }}>
                  {recommendedPreview.map((action, actionIndex) => (
                    <li
                      key={`${key}-action-${actionIndex}`}
                      style={{ fontSize: '0.85rem' }}
                    >
                      {action}
                    </li>
                  ))}
                </ul>
                {remainingActions > 0 && (
                  <p
                    style={{
                      margin: '0.35rem 0 0',
                      fontSize: '0.75rem',
                      color: 'var(--ob-color-text-muted)',
                    }}
                  >
                    +{remainingActions} more actions recorded in this
                    inspection.
                  </p>
                )}
              </div>
            )}

            {/* Attachments */}
            {entry.attachments.length > 0 && (
              <div style={{ marginTop: '0.35rem' }}>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    color: 'var(--ob-color-text-muted)',
                    letterSpacing: '0.06em',
                  }}
                >
                  Attachments
                </span>
                <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1rem' }}>
                  {entry.attachments.map((attachment, attachmentIndex) => (
                    <li
                      key={`${key}-attachment-${attachmentIndex}`}
                      style={{ fontSize: '0.85rem' }}
                    >
                      {attachment.url ? (
                        <a
                          href={attachment.url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: 'var(--ob-color-brand-primary)' }}
                        >
                          {attachment.label}
                        </a>
                      ) : (
                        attachment.label
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
