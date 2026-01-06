export interface FeasibilityIntelTapeProps {
  signalStrength: number
  signalId: string
  pathLabel: string
  timestamp: string
  opportunities: string[]
  risks: string[]
}

export function FeasibilityIntelTape({
  signalStrength,
  signalId,
  pathLabel,
  timestamp,
  opportunities,
  risks,
}: FeasibilityIntelTapeProps) {
  const hasOpportunities = opportunities.length > 0
  const hasRisks = risks.length > 0

  return (
    <div className="multi-scenario__intel-tape">
      <div className="multi-scenario__intel-tape-header">
        <div className="multi-scenario__intel-tape-signal">
          <div className="multi-scenario__intel-tape-strength-bar">
            {Array.from({ length: 10 }).map((_, idx) => (
              <div
                key={idx}
                className={`multi-scenario__intel-tape-strength-segment ${
                  idx < signalStrength
                    ? 'multi-scenario__intel-tape-strength-segment--active'
                    : ''
                }`}
              />
            ))}
          </div>
          <span className="multi-scenario__intel-tape-strength-value">
            STRENGTH: {signalStrength}/10
          </span>
        </div>
        <div className="multi-scenario__intel-tape-meta">
          <span className="multi-scenario__intel-tape-id">
            SIGNAL_ID: {signalId}
          </span>
          <span className="multi-scenario__intel-tape-path">
            PATH: {pathLabel}
          </span>
        </div>
        <div className="multi-scenario__intel-tape-updated">
          <span className="multi-scenario__intel-tape-updated-label">
            LAST UPDATED
          </span>
          <span className="multi-scenario__intel-tape-updated-value">
            {timestamp}
          </span>
        </div>
      </div>

      <div className="multi-scenario__intel-tape-divider" />

      {hasOpportunities && (
        <div className="multi-scenario__intel-tape-section">
          <span className="multi-scenario__intel-tape-type multi-scenario__intel-tape-type--opportunity">
            ● OPPORTUNITY
          </span>
          <ul className="multi-scenario__intel-tape-list">
            {opportunities.map((message, idx) => (
              <li key={`${idx}-${message}`}>
                <span className="multi-scenario__intel-tape-tree">
                  {idx === opportunities.length - 1 ? '└─' : '├─'}
                </span>
                {message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {hasRisks && (
        <div className="multi-scenario__intel-tape-section">
          <span className="multi-scenario__intel-tape-type multi-scenario__intel-tape-type--risk">
            ● RISK
          </span>
          <ul className="multi-scenario__intel-tape-list">
            {risks.map((message, idx) => (
              <li key={`${idx}-${message}`}>
                <span className="multi-scenario__intel-tape-tree">
                  {idx === risks.length - 1 ? '└─' : '├─'}
                </span>
                {message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!hasOpportunities && !hasRisks && (
        <p className="multi-scenario__intel-tape-empty">
          No automated guidance produced. Review the scenario notes for
          additional context.
        </p>
      )}
    </div>
  )
}
