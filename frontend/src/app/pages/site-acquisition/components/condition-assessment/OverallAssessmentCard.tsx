/**
 * Overall Assessment Card Component
 *
 * Displays the overall assessment rating, score, summary, and inspector info.
 * Pure presentational component - receives display-ready props.
 */

// ============================================================================
// Types
// ============================================================================

export interface AttachmentItem {
  label: string
  url: string | null
}

export interface OverallAssessmentCardProps {
  /** Overall rating letter (e.g., "A", "B+") */
  rating: string
  /** Score out of 100 */
  score: number
  /** Risk level string */
  riskLevel: string
  /** Summary text */
  summary: string
  /** Scenario context (optional) */
  scenarioContext: string | null
  /** Inspector name */
  inspectorName: string | null
  /** Recorded timestamp (pre-formatted) */
  recordedAtLabel: string | null
  /** Attachment items */
  attachments: AttachmentItem[]
}

// ============================================================================
// Component
// ============================================================================

export function OverallAssessmentCard({
  rating,
  score,
  riskLevel,
  summary,
  scenarioContext,
  inspectorName,
  recordedAtLabel,
  attachments,
}: OverallAssessmentCardProps) {
  return (
    <div
      style={{
        flex: '1 1 260px',
        background: '#f5f5f7',
        borderRadius: '12px',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}
    >
      <span
        style={{
          fontSize: '0.875rem',
          fontWeight: 600,
          color: '#6e6e73',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
        }}
      >
        Overall Rating
      </span>
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: '0.75rem',
        }}
      >
        <span style={{ fontSize: '2.5rem', fontWeight: 700 }}>{rating}</span>
        <span style={{ fontSize: '1rem', color: '#6e6e73' }}>
          {score}/100 · {riskLevel} risk
        </span>
      </div>
      <p
        style={{
          margin: 0,
          fontSize: '0.9375rem',
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
            fontSize: '0.875rem',
            color: '#0071e3',
          }}
        >
          {scenarioContext}
        </p>
      )}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.75rem',
          fontSize: '0.8125rem',
          color: '#6e6e73',
        }}
      >
        <span>
          Inspector: <strong>{inspectorName?.trim() || 'Not recorded'}</strong>
        </span>
        {recordedAtLabel && <span>Logged {recordedAtLabel}</span>}
      </div>
      {attachments.length > 0 && (
        <div>
          <span
            style={{
              display: 'inline-block',
              marginTop: '0.5rem',
              fontSize: '0.75rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              color: '#6e6e73',
              letterSpacing: '0.06em',
            }}
          >
            Attachments
          </span>
          <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1.2rem' }}>
            {attachments.map((attachment, index) => (
              <li key={`attachment-${index}`} style={{ fontSize: '0.85rem' }}>
                {attachment.url ? (
                  <a
                    href={attachment.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: '#0a84ff' }}
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
}
