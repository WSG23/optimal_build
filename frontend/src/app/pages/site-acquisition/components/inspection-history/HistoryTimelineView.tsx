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
        const key = `${entry.recordedAt ?? 'draft'}-${entry.scenario ?? 'all'}-${entry.overallScore}`
        const matchesScenario =
          activeScenario === 'all' ||
          !entry.scenario ||
          entry.scenario === activeScenario
        const recommendedPreview = entry.recommendedActions.slice(0, 2)
        const remainingActions =
          entry.recommendedActions.length - recommendedPreview.length
        const isMostRecent = index === 0

        return (
          <details
            key={key}
            open={isMostRecent}
            style={{
              border: '1px solid var(--ob-color-border-primary)',
              borderRadius: 'var(--ob-radius-sm)',
              padding: '1rem 1.25rem',
              background: isMostRecent
                ? 'var(--ob-color-surface-brand-subtle)'
                : 'var(--ob-color-bg-primary)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}
          >
            <summary
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                flexWrap: 'wrap',
                gap: '0.65rem',
                cursor: 'pointer',
                listStyle: 'none',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.3rem',
                }}
              >
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-xs)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: isMostRecent
                      ? 'var(--ob-color-brand-500)'
                      : 'var(--ob-color-text-secondary)',
                  }}
                >
                  {isMostRecent
                    ? 'Most recent inspection'
                    : `Inspection ${index + 1}`}
                </span>
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-base)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    color: 'var(--ob-color-text-primary)',
                  }}
                >
                  {formatScenarioLabel(entry.scenario)}
                </span>
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-xs)',
                    color: matchesScenario
                      ? 'var(--ob-color-status-success)'
                      : 'var(--ob-color-text-secondary)',
                  }}
                >
                  {matchesScenario
                    ? 'Included in current scenario filter'
                    : 'Outside current scenario filter'}
                </span>
              </div>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.25rem',
                  alignItems: 'flex-end',
                  minWidth: '180px',
                }}
              >
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-sm)',
                    color: 'var(--ob-color-text-secondary)',
                  }}
                >
                  {formatRecordedTimestamp(entry.recordedAt)}
                </span>
                <span
                  style={{
                    display: 'inline-block',
                    maxWidth: '100%',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    fontSize: 'var(--ob-font-size-xs)',
                    color: 'var(--ob-color-text-secondary)',
                  }}
                  title={entry.inspectorName?.trim() || 'Not recorded'}
                >
                  Inspector:{' '}
                  <strong>
                    {entry.inspectorName?.trim() || 'Not recorded'}
                  </strong>
                </span>
              </div>
            </summary>

            <div
              style={{
                display: 'grid',
                gap: '0.75rem',
              }}
            >
              <p
                style={{
                  margin: 0,
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'var(--ob-color-text-primary)',
                  lineHeight: 'var(--ob-line-height-normal)',
                }}
              >
                {entry.summary || 'No notes recorded.'}
              </p>

              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'var(--ob-color-text-secondary)',
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
            </div>

            {/* Recommended actions preview */}
            {recommendedPreview.length > 0 && (
              <div style={{ marginTop: 'var(--ob-space-025)' }}>
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-xs)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    textTransform: 'uppercase',
                    color: 'var(--ob-color-text-secondary)',
                    letterSpacing: '0.06em',
                  }}
                >
                  Recommended actions
                </span>
                <ul
                  style={{
                    margin: 'var(--ob-space-035) 0 0',
                    paddingLeft: 'var(--ob-space-100)',
                  }}
                >
                  {recommendedPreview.map((action, actionIndex) => (
                    <li
                      key={`${key}-action-${actionIndex}`}
                      style={{ fontSize: 'var(--ob-font-size-sm)' }}
                    >
                      {action}
                    </li>
                  ))}
                </ul>
                {remainingActions > 0 && (
                  <p
                    style={{
                      margin: 'var(--ob-space-035) 0 0',
                      fontSize: 'var(--ob-font-size-xs)',
                      color: 'var(--ob-color-text-secondary)',
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
              <div style={{ marginTop: 'var(--ob-space-035)' }}>
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-xs)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    textTransform: 'uppercase',
                    color: 'var(--ob-color-text-secondary)',
                    letterSpacing: '0.06em',
                  }}
                >
                  Attachments
                </span>
                <ul
                  style={{
                    margin: 'var(--ob-space-035) 0 0',
                    paddingLeft: 'var(--ob-space-100)',
                  }}
                >
                  {entry.attachments.map((attachment, attachmentIndex) => (
                    <li
                      key={`${key}-attachment-${attachmentIndex}`}
                      style={{ fontSize: 'var(--ob-font-size-sm)' }}
                    >
                      {attachment.url ? (
                        <a
                          href={attachment.url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: 'var(--ob-color-brand-500)' }}
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
          </details>
        )
      })}
    </div>
  )
}
