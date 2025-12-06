interface ClashItem {
  id: string
  discipline: string // e.g., 'Structural vs MEP'
  severity: 'critical' | 'warning' | 'resolved'
  description: string
  impact_area_sqm: number
  impact_cost: number
}

const SAMPLE_CLASHES: ClashItem[] = [
  {
    id: '1',
    discipline: 'Structural vs MEP',
    severity: 'critical',
    description: 'HVAC Duct clashes with primary beam at L3',
    impact_area_sqm: 12.5,
    impact_cost: 15000,
  },
  {
    id: '2',
    discipline: 'Façade vs Civil',
    severity: 'warning',
    description: 'Canopy overlap with drainage clearance',
    impact_area_sqm: 4.0,
    impact_cost: 5000,
  },
  {
    id: '3',
    discipline: 'MEP vs Architecture',
    severity: 'resolved',
    description: 'Riser adjustment for corridor width',
    impact_area_sqm: 0,
    impact_cost: 0,
  },
]

export function ClashImpactBoard() {
  const criticalCount = SAMPLE_CLASHES.filter(
    (c) => c.severity === 'critical',
  ).length
  const warningCount = SAMPLE_CLASHES.filter(
    (c) => c.severity === 'warning',
  ).length
  const resolvedCount = SAMPLE_CLASHES.filter(
    (c) => c.severity === 'resolved',
  ).length

  return (
    <div className="page__card clash-impact">
      <div className="clash-impact__header">
        <h3 className="clash-impact__title">
          <span className="clash-impact__title-icon">⚠</span>
          Clash & Impact Board
        </h3>
      </div>
      <div className="clash-impact__summary">
        <span className="clash-impact__summary-item">
          <span className="clash-impact__dot clash-impact__dot--critical">
            ●
          </span>{' '}
          {criticalCount} Critical
        </span>
        <span className="clash-impact__summary-item">
          <span className="clash-impact__dot clash-impact__dot--warning">
            ●
          </span>{' '}
          {warningCount} Warnings
        </span>
        <span className="clash-impact__summary-item">
          <span className="clash-impact__dot clash-impact__dot--resolved">
            ●
          </span>{' '}
          {resolvedCount} Resolved
        </span>
      </div>

      <div className="clash-impact__list">
        {SAMPLE_CLASHES.map((clash) => (
          <div
            key={clash.id}
            className={`clash-impact__item clash-impact__item--${clash.severity}`}
          >
            <div className="clash-impact__item-content">
              <div className="clash-impact__item-header">
                <span className="clash-impact__item-discipline">
                  {clash.discipline}
                </span>
                <span
                  className={`clash-impact__badge clash-impact__badge--${clash.severity}`}
                >
                  {clash.severity}
                </span>
              </div>
              <p className="clash-impact__item-description">
                {clash.description}
              </p>
            </div>
            <div className="clash-impact__item-impact">
              <div className="clash-impact__item-cost">
                -${clash.impact_cost.toLocaleString()}
              </div>
              <div className="clash-impact__item-area">
                {clash.impact_area_sqm} sqm lost
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
