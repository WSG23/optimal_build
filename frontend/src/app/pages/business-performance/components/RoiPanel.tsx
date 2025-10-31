import type { RoiSummary } from '../types'

interface RoiPanelProps {
  summary: RoiSummary
}

export function RoiPanel({ summary }: RoiPanelProps) {
  return (
    <section className="bp-roi">
      <header className="bp-roi__header">
        <h3>Automation ROI</h3>
        <p>
          Metrics derive from overlay workflows (automation score, hours saved,
          payback period). Integrates with ROI analytics service.
        </p>
      </header>
      <div className="bp-roi__grid">
        <RoiStat label="Projects tracked" value={summary.projectCount} />
        <RoiStat
          label="Hours saved"
          value={
            summary.totalReviewHoursSaved !== null
              ? `${summary.totalReviewHoursSaved?.toFixed(2)}h`
              : '—'
          }
        />
        <RoiStat
          label="Avg automation"
          value={formatPercent(summary.averageAutomationScore)}
        />
        <RoiStat
          label="Avg acceptance"
          value={formatPercent(summary.averageAcceptanceRate)}
        />
        <RoiStat
          label="Avg savings"
          value={formatPercent(summary.averageSavingsPercent, true)}
        />
        <RoiStat
          label="Best payback"
          value={
            summary.bestPaybackWeeks !== null
              ? `${summary.bestPaybackWeeks} weeks`
              : '—'
          }
        />
      </div>
      <div className="bp-roi__projects">
        <h4>Project breakdown</h4>
        {summary.projects.length === 0 ? (
          <p>No ROI records yet. Metrics populate after overlay runs complete.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Hours saved</th>
                <th>Automation</th>
                <th>Acceptance</th>
                <th>Payback</th>
              </tr>
            </thead>
            <tbody>
              {summary.projects.map((project) => (
                <tr key={project.projectId}>
                  <td>#{project.projectId}</td>
                  <td>{formatNumber(project.hoursSaved, 'h')}</td>
                  <td>{formatPercent(project.automationScore)}</td>
                  <td>{formatPercent(project.acceptanceRate)}</td>
                  <td>
                    {project.paybackWeeks
                      ? `${project.paybackWeeks}w`
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}

interface RoiStatProps {
  label: string
  value: string | number
}

function RoiStat({ label, value }: RoiStatProps) {
  return (
    <div className="bp-roi__stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function formatNumber(value: number | null, suffix: string = '') {
  if (value === null || Number.isNaN(value)) return '—'
  return `${value.toFixed(2)}${suffix}`
}

function formatPercent(value: number | null, absolute = false) {
  if (value === null || Number.isNaN(value)) return '—'
  const normalized = absolute ? value : value * 100
  return `${normalized.toFixed(1)}%`
}
