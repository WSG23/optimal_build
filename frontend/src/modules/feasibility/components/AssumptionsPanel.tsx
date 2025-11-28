import type { ChangeEvent } from 'react'

import type { AssumptionInputs, AssumptionErrors } from '../types'
import { DEFAULT_ASSUMPTIONS } from '../types'

interface AssumptionsPanelProps {
  assumptionInputs: AssumptionInputs
  assumptionErrors: AssumptionErrors
  decimalFormatter: Intl.NumberFormat
  onAssumptionChange: (
    key: keyof AssumptionInputs,
  ) => (event: ChangeEvent<HTMLInputElement>) => void
  onResetAssumptions: () => void
  t: (key: string, options?: Record<string, unknown>) => string
}

export function AssumptionsPanel({
  assumptionInputs,
  assumptionErrors,
  decimalFormatter,
  onAssumptionChange,
  onResetAssumptions,
  t,
}: AssumptionsPanelProps) {
  const renderAssumptionError = (key: keyof AssumptionInputs) => {
    const error = assumptionErrors[key]
    if (!error) {
      return null
    }
    const messageKey =
      error === 'required'
        ? 'wizard.assumptions.errors.required'
        : error === 'range'
          ? 'wizard.assumptions.errors.range'
          : 'wizard.assumptions.errors.invalid'
    return <p className="feasibility-assumptions__error">{t(messageKey)}</p>
  }

  return (
    <section className="feasibility-assumptions">
      <header>
        <h2>{t('wizard.assumptions.title')}</h2>
        <p>{t('wizard.assumptions.subtitle')}</p>
      </header>
      <div className="feasibility-assumptions__grid">
        <div>
          <label htmlFor="assumption-floor">
            {t('wizard.assumptions.fields.typFloorToFloor.label')}
          </label>
          <input
            id="assumption-floor"
            type="number"
            step="0.1"
            min={0}
            value={assumptionInputs.typFloorToFloorM}
            onChange={onAssumptionChange('typFloorToFloorM')}
            data-testid="assumption-floor"
          />
          <p className="feasibility-assumptions__hint">
            {t('wizard.assumptions.fields.typFloorToFloor.hint', {
              value: decimalFormatter.format(DEFAULT_ASSUMPTIONS.typFloorToFloorM),
            })}
          </p>
          {renderAssumptionError('typFloorToFloorM')}
        </div>
        <div>
          <label htmlFor="assumption-efficiency">
            {t('wizard.assumptions.fields.efficiency.label')}
          </label>
          <input
            id="assumption-efficiency"
            type="number"
            step="0.01"
            min={0}
            max={1}
            value={assumptionInputs.efficiencyRatio}
            onChange={onAssumptionChange('efficiencyRatio')}
          />
          <p className="feasibility-assumptions__hint">
            {t('wizard.assumptions.fields.efficiency.hint', {
              value: decimalFormatter.format(DEFAULT_ASSUMPTIONS.efficiencyRatio),
            })}
          </p>
          {renderAssumptionError('efficiencyRatio')}
        </div>
      </div>
      <button
        type="button"
        className="feasibility-assumptions__reset"
        onClick={onResetAssumptions}
      >
        {t('wizard.assumptions.reset')}
      </button>
    </section>
  )
}
