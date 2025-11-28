/**
 * Simplified heritage context display for GPS Capture page
 * Shows heritage flags, constraints, and conservation requirements
 */

import type { DeveloperHeritageContext } from '../../../api/agents'

interface HeritageContextCardProps {
  context: DeveloperHeritageContext
}

function getRiskBadgeClass(risk: string | null): string {
  if (!risk) return ''
  const normalized = risk.toLowerCase()
  if (normalized.includes('low') || normalized === 'none')
    return 'heritage-context-card__risk--low'
  if (normalized.includes('high') || normalized.includes('critical'))
    return 'heritage-context-card__risk--high'
  return 'heritage-context-card__risk--medium'
}

export function HeritageContextCard({ context }: HeritageContextCardProps) {
  if (
    !context.flag &&
    context.constraints.length === 0 &&
    context.notes.length === 0
  ) {
    return (
      <div className="heritage-context-card heritage-context-card--none">
        <h4 className="heritage-context-card__title">Heritage Context</h4>
        <p className="heritage-context-card__status heritage-context-card__status--clear">
          No heritage constraints identified
        </p>
      </div>
    )
  }

  return (
    <div
      className={`heritage-context-card ${context.flag ? 'heritage-context-card--flagged' : ''}`}
    >
      <h4 className="heritage-context-card__title">
        Heritage Context
        {context.flag && (
          <span className="heritage-context-card__flag">Heritage Site</span>
        )}
      </h4>

      {context.risk && (
        <div className="heritage-context-card__risk-row">
          <span className="heritage-context-card__risk-label">Risk Level:</span>
          <span
            className={`heritage-context-card__risk ${getRiskBadgeClass(context.risk)}`}
          >
            {context.risk}
          </span>
        </div>
      )}

      {context.overlay && context.overlay.name && (
        <div className="heritage-context-card__overlay">
          <span className="heritage-context-card__overlay-name">
            {context.overlay.name}
          </span>
          {context.overlay.source && (
            <span className="heritage-context-card__overlay-source">
              Source: {context.overlay.source}
            </span>
          )}
          {context.overlay.heritagePremiumPct != null && (
            <span className="heritage-context-card__overlay-premium">
              Premium: +{(context.overlay.heritagePremiumPct * 100).toFixed(0)}%
            </span>
          )}
        </div>
      )}

      {context.constraints.length > 0 && (
        <div className="heritage-context-card__constraints">
          <span className="heritage-context-card__constraints-label">
            Constraints:
          </span>
          <ul className="heritage-context-card__constraints-list">
            {context.constraints.map((constraint, index) => (
              <li key={index}>{constraint}</li>
            ))}
          </ul>
        </div>
      )}

      {context.notes.length > 0 && (
        <ul className="heritage-context-card__notes">
          {context.notes.slice(0, 3).map((note, index) => (
            <li key={index}>{note}</li>
          ))}
        </ul>
      )}

      {context.assumption && (
        <p className="heritage-context-card__assumption">
          <em>Assumption: {context.assumption}</em>
        </p>
      )}
    </div>
  )
}
