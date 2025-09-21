import { useMemo } from 'react'

import { useTranslation } from '../../i18n'

import { FeasibilityAssessmentResponse } from './types'

interface Step3BuildableProps {
  assessment: FeasibilityAssessmentResponse
  onBack: () => void
  onRestart: () => void
  isLoading?: boolean
}

export function Step3Buildable({
  assessment,
  onBack,
  onRestart,
  isLoading = false,
}: Step3BuildableProps) {
  const { t, i18n } = useTranslation()
  const { summary, rules, recommendations } = assessment

  const siteEfficiency = useMemo(() => {
    if (!summary.maxPermissibleGfaSqm) {
      return t('common.fallback.dash')
    }

    const ratio = summary.estimatedAchievableGfaSqm / summary.maxPermissibleGfaSqm
    if (!Number.isFinite(ratio)) {
      return t('common.fallback.dash')
    }

    return t('wizard.step3.siteEfficiency', { percentage: Math.round(ratio * 100) })
  }, [summary, t])

  const numberFormatter = useMemo(
    () =>
      new Intl.NumberFormat(i18n.language, {
        maximumFractionDigits: 0,
      }),
    [i18n.language],
  )

  const decimalFormatter = useMemo(
    () =>
      new Intl.NumberFormat(i18n.language, {
        maximumFractionDigits: 1,
        minimumFractionDigits: 1,
      }),
    [i18n.language],
  )

  return (
    <div className="feasibility-step">
      <h2 className="feasibility-step__heading">{t('wizard.step3.heading')}</h2>
      <p className="feasibility-step__intro">
        {isLoading ? t('wizard.step3.intro.loading') : t('wizard.step3.intro.ready')}
      </p>

      <section className="feasibility-panel">
        <header className="feasibility-panel__header">
          <div>
            <h3 className="feasibility-panel__title">{t('wizard.step3.panel.title')}</h3>
            <p className="feasibility-panel__subtitle">{summary.remarks ?? siteEfficiency}</p>
          </div>
          <div className="feasibility-panel__metrics">
            <div>
              <span className="feasibility-panel__metric-label">{t('wizard.step3.panel.metrics.maxGfa')}</span>
              <span className="feasibility-panel__metric-value">
                {numberFormatter.format(summary.maxPermissibleGfaSqm)} {t('wizard.step2.panel.units.sqm')}
              </span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">{t('wizard.step3.panel.metrics.estimatedGfa')}</span>
              <span className="feasibility-panel__metric-value">
                {numberFormatter.format(summary.estimatedAchievableGfaSqm)} {t('wizard.step2.panel.units.sqm')}
              </span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">{t('wizard.step3.panel.metrics.estimatedUnits')}</span>
              <span className="feasibility-panel__metric-value">
                {numberFormatter.format(summary.estimatedUnitCount)}
              </span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">{t('wizard.step3.panel.metrics.siteCoverage')}</span>
              <span className="feasibility-panel__metric-value">
                {decimalFormatter.format(summary.siteCoveragePercent)}%
              </span>
            </div>
          </div>
        </header>

        <div className="feasibility-panel__content">
          {rules.length === 0 ? (
            <p>{t('wizard.step3.allClear')}</p>
          ) : (
            <table className="feasibility-results">
              <thead>
                <tr>
                  <th scope="col">{t('wizard.step3.table.rule')}</th>
                  <th scope="col">{t('wizard.step3.table.agency')}</th>
                  <th scope="col">{t('wizard.step3.table.status')}</th>
                  <th scope="col">{t('wizard.step3.table.notes')}</th>
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
                        {t(`wizard.step3.status.${rule.status}`)}
                      </span>
                    </td>
                    <td>
                      <span>{rule.notes ?? rule.actualValue ?? t('common.fallback.dash')}</span>
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
              <h3 className="feasibility-panel__title">{t('wizard.step3.recommendations.title')}</h3>
              <p className="feasibility-panel__subtitle">
                {t('wizard.step3.recommendations.subtitle')}
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
          {t('wizard.step3.actions.back')}
        </button>
        <button type="button" className="feasibility-actions__primary" onClick={onRestart}>
          {t('wizard.step3.actions.restart')}
        </button>
      </div>
    </div>
  )
}

export default Step3Buildable
