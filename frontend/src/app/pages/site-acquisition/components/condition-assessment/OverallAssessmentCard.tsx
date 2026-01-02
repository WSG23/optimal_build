/**
 * Overall Assessment Card Component
 *
 * Displays the overall assessment rating with a circular gauge visualization.
 * Compact layout optimized for 4-column grid placement (AI Studio pattern).
 *
 * Design tokens:
 * - Padding: --ob-space-150 (24px)
 * - Rating: --ob-font-size-4xl (2.25rem)
 * - Score: --ob-font-size-sm
 * - Border radius: --ob-radius-sm (4px)
 */

// ============================================================================
// Types
// ============================================================================

export interface AttachmentItem {
  label: string
  url: string | null
}

export interface OverallAssessmentCardProps {
  /** Overall rating letter (e.g., "A", "B+", "C") */
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
// Helper: Get rating color
// ============================================================================

function getRatingColor(rating: string): string {
  const letter = rating.charAt(0).toUpperCase()
  switch (letter) {
    case 'A':
      return 'var(--ob-success-500)'
    case 'B':
      return 'var(--ob-color-neon-cyan)'
    case 'C':
      return 'var(--ob-warning-500)'
    case 'D':
    case 'F':
      return 'var(--ob-error-500)'
    default:
      return 'var(--ob-color-text-secondary)'
  }
}

function getRiskBadgeClasses(riskLevel: string): { bg: string; text: string } {
  const level = riskLevel.toLowerCase()
  if (level.includes('low')) {
    return { bg: 'var(--ob-success-100)', text: 'var(--ob-success-700)' }
  }
  if (level.includes('elevated') || level.includes('medium')) {
    return { bg: 'var(--ob-warning-100)', text: 'var(--ob-warning-700)' }
  }
  if (level.includes('high') || level.includes('critical')) {
    return { bg: 'var(--ob-error-100)', text: 'var(--ob-error-700)' }
  }
  return { bg: 'var(--ob-neutral-100)', text: 'var(--ob-neutral-700)' }
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
}: OverallAssessmentCardProps) {
  const ratingColor = getRatingColor(rating)
  const riskStyles = getRiskBadgeClasses(riskLevel)

  // Calculate stroke dashoffset for the progress ring
  // Circumference = 2 * PI * radius = 2 * 3.14159 * 44 ≈ 276.46
  const circumference = 276.46
  const progress = Math.min(100, Math.max(0, score))
  const strokeDashoffset = circumference - (progress / 100) * circumference

  return (
    <div className="condition-assessment__overall-card">
      {/* Section label */}
      <span className="condition-assessment__overall-label">
        Overall Condition Rating
      </span>

      {/* Circular gauge */}
      <div className="condition-assessment__gauge-container">
        <svg
          className="condition-assessment__gauge-svg"
          viewBox="0 0 100 100"
          width="140"
          height="140"
        >
          {/* Background ring */}
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke="var(--ob-color-border-subtle)"
            strokeWidth="8"
          />
          {/* Progress ring */}
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke={ratingColor}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            transform="rotate(-90 50 50)"
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />
        </svg>
        {/* Center content */}
        <div className="condition-assessment__gauge-center">
          <span
            className="condition-assessment__rating-letter"
            style={{ color: ratingColor }}
          >
            {rating}
          </span>
          <span className="condition-assessment__score-label">{score}/100</span>
        </div>
      </div>

      {/* Risk level badge */}
      <span
        className="condition-assessment__risk-badge"
        style={{
          background: riskStyles.bg,
          color: riskStyles.text,
        }}
      >
        {riskLevel} Risk
      </span>

      {/* Summary */}
      <p className="condition-assessment__summary">{summary}</p>

      {/* Scenario context */}
      {scenarioContext && (
        <p className="condition-assessment__scenario-context">
          {scenarioContext}
        </p>
      )}

      {/* Inspector info */}
      <div className="condition-assessment__inspector-info">
        {inspectorName && (
          <span>
            Inspector: <strong>{inspectorName.trim()}</strong>
          </span>
        )}
        {recordedAtLabel && <span>Logged {recordedAtLabel}</span>}
      </div>
    </div>
  )
}
