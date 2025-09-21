import { useMemo } from 'react'

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

function formatNumber(value: number | undefined) {
  if (value === undefined || Number.isNaN(value)) {
    return '—'
  }

  return value.toLocaleString(undefined, {
    maximumFractionDigits: 2,
  })
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
  const recommendationText = useMemo(() => {
    if (!summary) {
      return null
    }

    return `${summary.complianceFocus}${summary.notes ? ` · ${summary.notes}` : ''}`
  }, [summary])

  const toggleRule = (ruleId: string) => {
    if (selectedRuleIds.includes(ruleId)) {
      onSelectionChange(selectedRuleIds.filter((id) => id !== ruleId))
    } else {
      onSelectionChange([...selectedRuleIds, ruleId])
    }
  }

  const selectedRulesSet = useMemo(() => new Set(selectedRuleIds), [selectedRuleIds])

  return (
    <div className="feasibility-step">
      <h2 className="feasibility-step__heading">Step 2 · Review suggested rules</h2>
      <p className="feasibility-step__intro">
        We analysed the project details and surfaced the most relevant codes across agencies.
        You can adjust the scope before running the compliance engine.
      </p>

      <section className="feasibility-panel">
        <header className="feasibility-panel__header">
          <div>
            <h3 className="feasibility-panel__title">Project summary</h3>
            <p className="feasibility-panel__subtitle">
              {recommendationText ?? 'Provide a quick confirmation before running the checks.'}
            </p>
          </div>
          <div className="feasibility-panel__metrics">
            <div>
              <span className="feasibility-panel__metric-label">Site area</span>
              <span className="feasibility-panel__metric-value">
                {formatNumber(project.siteAreaSqm)} m²
              </span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">Land use</span>
              <span className="feasibility-panel__metric-value">{project.landUse}</span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">Target GFA</span>
              <span className="feasibility-panel__metric-value">
                {formatNumber(project.targetGrossFloorAreaSqm)} m²
              </span>
            </div>
            <div>
              <span className="feasibility-panel__metric-label">Target height</span>
              <span className="feasibility-panel__metric-value">
                {formatNumber(project.buildingHeightMeters)} m
              </span>
            </div>
          </div>
        </header>

        <div className="feasibility-panel__content">
          {isLoading && <p>Loading recommended rules…</p>}
          {error && <p className="feasibility-panel__error">{error}</p>}
          {!isLoading && !error && rules.length === 0 && (
            <p>No rules were found for this project configuration.</p>
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
                          Requirement: {rule.parameterKey} {rule.operator} {rule.value}
                          {rule.unit ? ` ${rule.unit}` : ''}
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
          Back
        </button>
        <button
          type="button"
          className="feasibility-actions__primary"
          onClick={onContinue}
          disabled={selectedRuleIds.length === 0 || isEvaluating || isLoading}
        >
          {isEvaluating ? 'Running assessment…' : 'Run buildability checks'}
        </button>
      </div>
    </div>
  )
}

export default Step2Rules
