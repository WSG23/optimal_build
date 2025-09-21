import { useCallback, useMemo } from 'react'

import { useTranslation } from '../../i18n'

import {
  FeasibilityRule,
  FeasibilityRulesSummary,
  NewFeasibilityProjectInput,
} from './types'

interface Step2RulesProps {
  project: NewFeasibilityProjectInput
  rules: FeasibilityRule[]
  summary?: FeasibilityRulesSummary
  isLoading: boolean
  error?: string | null
  selectedRuleIds: string[]
  onSelectionChange: (ids: string[]) => void
  onBack: () => void
  onContinue: () => void
  isEvaluating?: boolean
}

export function Step2Rules({
  project,
  rules,
  summary,
  isLoading,
  error,
  selectedRuleIds,
  onSelectionChange,
  onBack,
  onContinue,
  isEvaluating = false,
}: Step2RulesProps) {
  const { t, i18n } = useTranslation()
  const recommendationText = useMemo(() => {
    if (!summary) {
      return null
    }

    return `${summary.complianceFocus}${summary.notes ? ` · ${summary.notes}` : ''}`
  }, [summary])

  const fallbackDash = t('common.fallback.dash')
  const numberFormatter = useMemo(
    () =>
      new Intl.NumberFormat(i18n.language, {
        maximumFractionDigits: 2,
      }),
    [i18n.language],
  )

  const formatValue = useCallback(
    (value: number | undefined) => {
      if (value === undefined || Number.isNaN(value)) {
        return fallbackDash
      }
      return numberFormatter.format(value)
    },
    [fallbackDash, numberFormatter],
  )

  const formatWithUnit = useCallback(
    (value: number | undefined, unit: string) => {
      const formatted = formatValue(value)
      if (formatted === fallbackDash) {
        return fallbackDash
      }
      return `${formatted} ${unit}`
    },
    [fallbackDash, formatValue],
  )

  const toggleRule = (ruleId: string) => {
    if (selectedRuleIds.includes(ruleId)) {
      onSelectionChange(selectedRuleIds.filter((id) => id !== ruleId))
    } else {
      onSelectionChange([...selectedRuleIds, ruleId])
    }
  }

  const selectedRulesSet = useMemo(() => new Set(selectedRuleIds), [selectedRuleIds])

  const units = useMemo(
    () => ({
      sqm: t('wizard.step2.panel.units.sqm'),
      meters: t('wizard.step2.panel.units.meters'),
    }),
    [t],
  )

  const landUseLabel = useMemo(() => t(`wizard.step1.landUseOptions.${project.landUse}`), [project.landUse, t])

  return (
    <div className="feasibility-step">
      <h2 className="feasibility-step__heading">{t('wizard.step2.heading')}</h2>
      <p className="feasibility-step__intro">{t('wizard.step2.description')}</p>

      <section className="feasibility-panel">
        <header className="feasibility-panel__header">
          <div>
            <h3 className="feasibility-panel__title">{t('wizard.step2.panel.title')}</h3>
            <p className="feasibility-panel__subtitle">
              {recommendationText ?? t('wizard.step2.panel.subtitleFallback')}
            </p>
          </div>
          <div className="feasibility-panel__metrics">
            <div>
              <span className="feasibility-panel__metric-label">{t('wizard.step2.panel.metrics.siteArea')}</span>
              <span className="feasibility-panel__metric-value">
                {formatWithUnit(project.siteAreaSqm, units.sqm)}
              </span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">{t('wizard.step2.panel.metrics.landUse')}</span>
              <span className="feasibility-panel__metric-value">{landUseLabel}</span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">{t('wizard.step2.panel.metrics.targetGfa')}</span>
              <span className="feasibility-panel__metric-value">
                {formatWithUnit(project.targetGrossFloorAreaSqm, units.sqm)}
              </span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">{t('wizard.step2.panel.metrics.targetHeight')}</span>
              <span className="feasibility-panel__metric-value">
                {formatWithUnit(project.buildingHeightMeters, units.meters)}
              </span>
            </div>
          </div>
        </header>

        <div className="feasibility-panel__content">
          {isLoading && <p>{t('wizard.step2.loading')}</p>}
          {error && <p className="feasibility-panel__error">{error}</p>}
          {!isLoading && !error && rules.length === 0 && (
            <p>{t('wizard.step2.empty')}</p>
          )}

          {!isLoading && !error && rules.length > 0 && (
            <ul className="feasibility-rules">
              {rules.map((rule) => {
                const isSelected = selectedRulesSet.has(rule.id)
                return (
                  <li
                    key={rule.id}
                    className={`feasibility-rules__item feasibility-rules__item--${rule.severity}`}
                  >
                    <label>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleRule(rule.id)}
                      />
                      <div>
                        <div className="feasibility-rules__meta">
                          <span className="feasibility-rules__authority">{rule.authority}</span>
                          <span className="feasibility-rules__topic">{rule.topic}</span>
                        </div>
                        <p className="feasibility-rules__title">{rule.title}</p>
                        <p className="feasibility-rules__description">{rule.description}</p>
                        <p className="feasibility-rules__requirement">
                          {t('wizard.step2.requirement', {
                            parameterKey: rule.parameterKey,
                            operator: rule.operator,
                            value: rule.value,
                            unit: rule.unit ? ` ${rule.unit}` : '',
                          })}
                        </p>
                      </div>
                    </label>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </section>

      <div className="feasibility-actions">
        <button type="button" className="feasibility-actions__secondary" onClick={onBack}>
          {t('wizard.step2.actions.back')}
        </button>
        <button
          type="button"
          className="feasibility-actions__primary"
          onClick={onContinue}
          disabled={selectedRuleIds.length === 0 || isEvaluating || isLoading}
        >
          {isEvaluating
            ? t('wizard.step2.actions.evaluating')
            : t('wizard.step2.actions.evaluate')}
        </button>
      </div>
    </div>
  )
}

export default Step2Rules
