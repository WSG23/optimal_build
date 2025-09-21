import { useMemo } from 'react'

import { FeasibilityAssessmentResponse } from './types'

interface Step3BuildableProps {
  assessment: FeasibilityAssessmentResponse
  onBack: () => void
  onRestart: () => void
  isLoading?: boolean
}

const statusLabels = {
  pass: 'Pass',
  fail: 'Fail',
  warning: 'Review',
} as const

export function Step3Buildable({
  assessment,
  onBack,
  onRestart,
  isLoading = false,
}: Step3BuildableProps) {
  const { summary, rules, recommendations } = assessment

  const siteEfficiency = useMemo(() => {
    if (!summary.maxPermissibleGfaSqm) {
      return '—'
    }

    const ratio = summary.estimatedAchievableGfaSqm / summary.maxPermissibleGfaSqm
    if (!Number.isFinite(ratio)) {
      return '—'
    }

    return `${Math.round(ratio * 100)}% of permissible GFA utilised`
  }, [summary])

  return (
    <div className="feasibility-step">
      <h2 className="feasibility-step__heading">Step 3 · Buildability outlook</h2>
      <p className="feasibility-step__intro">
        {isLoading
          ? 'Finalising the analysis…'
          : 'This snapshot summarises the achievable massing and highlights rules that require attention.'}
      </p>

      <section className="feasibility-panel">
        <header className="feasibility-panel__header">
          <div>
            <h3 className="feasibility-panel__title">Envelope summary</h3>
            <p className="feasibility-panel__subtitle">{summary.remarks ?? siteEfficiency}</p>
          </div>
          <div className="feasibility-panel__metrics">
            <div>
              <span className="feasibility-panel__metric-label">Max permissible GFA</span>
              <span className="feasibility-panel__metric-value">
                {summary.maxPermissibleGfaSqm.toLocaleString()} m²
              </span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">Estimated achievable GFA</span>
              <span className="feasibility-panel__metric-value">
                {summary.estimatedAchievableGfaSqm.toLocaleString()} m²
              </span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">Estimated units</span>
              <span className="feasibility-panel__metric-value">
                {summary.estimatedUnitCount.toLocaleString()}
              </span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">Site coverage</span>
              <span className="feasibility-panel__metric-value">
                {summary.siteCoveragePercent.toFixed(1)}%
              </span>
            </div>
          </div>
        </header>

        <div className="feasibility-panel__content">
          {rules.length === 0 ? (
            <p>All tracked rules passed – consider expanding the scope to include more topics.</p>
          ) : (
            <table className="feasibility-results">
              <thead>
                <tr>
                  <th scope="col">Rule</th>
                  <th scope="col">Agency</th>
                  <th scope="col">Status</th>
                  <th scope="col">Notes</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => (
                  <tr
                    key={rule.id}
                    className={`feasibility-results__row feasibility-results__row--${rule.status}`}
                  >
                    <td>
                      <p className="feasibility-results__title">{rule.title}</p>
                      <p className="feasibility-results__requirement">
                        {rule.parameterKey} {rule.operator} {rule.value}
                        {rule.unit ? ` ${rule.unit}` : ''}
                      </p>
                    </td>
                    <td>
                      <span>{rule.authority}</span>
                    </td>
                    <td>
                      <span
                        className={`feasibility-results__status feasibility-results__status--${rule.status}`}
                      >
                        {statusLabels[rule.status]}
                      </span>
                    </td>
                    <td>
                      <span>{rule.notes ?? rule.actualValue ?? '—'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {recommendations.length > 0 && (
        <section className="feasibility-panel">
          <header className="feasibility-panel__header">
            <div>
              <h3 className="feasibility-panel__title">Next steps</h3>
              <p className="feasibility-panel__subtitle">
                Prioritised guidance to resolve outstanding compliance gaps.
              </p>
            </div>
          </header>
          <div className="feasibility-panel__content">
            <ol className="feasibility-recommendations">
              {recommendations.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ol>
          </div>
        </section>
      )}

      <div className="feasibility-actions">
        <button type="button" className="feasibility-actions__secondary" onClick={onBack}>
          Back to rules
        </button>
        <button type="button" className="feasibility-actions__primary" onClick={onRestart}>
          Start a new assessment
        </button>
      </div>
    </div>
  )
}

export default Step3Buildable
