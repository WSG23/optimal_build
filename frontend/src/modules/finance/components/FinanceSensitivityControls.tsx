import { FormEvent, useEffect, useMemo, useState } from 'react'

import type {
  FinanceScenarioSummary,
  SensitivityBandInput,
} from '../../../api/finance'
import { useTranslation } from '../../../i18n'

interface FinanceSensitivityControlsProps {
  scenario: FinanceScenarioSummary
  pendingJobs: number
  disabled?: boolean
  error?: string | null
  onRun: (bands: SensitivityBandInput[]) => Promise<void> | void
}

interface EditableBand {
  id: string
  parameter: string
  low: string
  base: string
  high: string
}

const DEFAULT_BANDS: EditableBand[] = [
  { id: 'band-rent', parameter: 'Rent', low: '-5', base: '0', high: '6' },
  {
    id: 'band-cost',
    parameter: 'Construction Cost',
    low: '8',
    base: '0',
    high: '-4',
  },
  {
    id: 'band-rate',
    parameter: 'Interest Rate (delta %)',
    low: '1.50',
    base: '0',
    high: '-0.75',
  },
]

function toEditableBands(scenario: FinanceScenarioSummary): EditableBand[] {
  if (scenario.sensitivityBands && scenario.sensitivityBands.length > 0) {
    return scenario.sensitivityBands.map((band, index) => ({
      id: `band-${scenario.scenarioId}-${index}`,
      parameter: band.parameter ?? '',
      low: band.low ?? '',
      base: band.base ?? '',
      high: band.high ?? '',
    }))
  }
  return DEFAULT_BANDS
}

export function FinanceSensitivityControls({
  scenario,
  pendingJobs,
  disabled = false,
  error,
  onRun,
}: FinanceSensitivityControlsProps) {
  const { t } = useTranslation()
  const [rows, setRows] = useState<EditableBand[]>(() =>
    toEditableBands(scenario),
  )
  const [localError, setLocalError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    setRows(toEditableBands(scenario))
    setLocalError(null)
    setSubmitting(false)
  }, [scenario])

  const maxRows = 8
  const canAddRow = rows.length < maxRows
  const controlsDisabled = disabled || submitting

  const handleFieldChange = (
    id: string,
    key: keyof Omit<EditableBand, 'id'>,
    value: string,
  ) => {
    setRows((prev) =>
      prev.map((row) => (row.id === id ? { ...row, [key]: value } : row)),
    )
  }

  const handleAddRow = () => {
    if (!canAddRow) {
      return
    }
    const nextId = `band-${Date.now()}-${rows.length}`
    setRows((prev) => [
      ...prev,
      { id: nextId, parameter: '', low: '', base: '', high: '' },
    ])
  }

  const handleRemoveRow = (id: string) => {
    setRows((prev) => prev.filter((row) => row.id !== id))
  }

  const preparedBands = useMemo(() => {
    return rows
      .map((row) => ({
        parameter: row.parameter.trim(),
        low: row.low.trim(),
        base: row.base.trim(),
        high: row.high.trim(),
      }))
      .filter((row) => row.parameter)
      .map<SensitivityBandInput>((row) => ({
        parameter: row.parameter,
        low: row.low || undefined,
        base: row.base || undefined,
        high: row.high || undefined,
      }))
      .filter(
        (row) => row.low !== undefined || row.base !== undefined || row.high !== undefined,
      )
  }, [rows])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (controlsDisabled) {
      return
    }
    if (preparedBands.length === 0) {
      setLocalError(
        t('finance.sensitivity.controls.errors.parameterRequired'),
      )
      return
    }
    setLocalError(null)
    setSubmitting(true)
    try {
      await onRun(preparedBands)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="finance-sensitivity-controls">
      <div className="finance-sensitivity-controls__header">
        <div>
          <h3>{t('finance.sensitivity.controls.title')}</h3>
          <p>{t('finance.sensitivity.controls.description')}</p>
        </div>
        <button
          type="button"
          className="finance-sensitivity-controls__add"
          onClick={handleAddRow}
          disabled={!canAddRow || controlsDisabled}
        >
          {t('finance.sensitivity.controls.add')}
        </button>
      </div>
      {pendingJobs > 0 ? (
        <p className="finance-sensitivity-controls__pending" role="status">
          {t('finance.sensitivity.pendingNotice', { count: pendingJobs })}
        </p>
      ) : null}
      {error ? (
        <p className="finance-sensitivity-controls__error" role="alert">
          {error}
        </p>
      ) : null}
      {localError ? (
        <p className="finance-sensitivity-controls__error" role="alert">
          {localError}
        </p>
      ) : null}
      <form onSubmit={handleSubmit}>
        <div className="finance-sensitivity-controls__grid">
          {rows.map((row, index) => (
            <div
              key={row.id}
              className="finance-sensitivity-controls__row"
              aria-label={t('finance.sensitivity.controls.parameter')}
            >
              <label>
                {t('finance.sensitivity.controls.parameter')}
                <input
                  type="text"
                  value={row.parameter}
                  onChange={(event) =>
                    handleFieldChange(row.id, 'parameter', event.target.value)
                  }
                  disabled={controlsDisabled}
                  placeholder={
                    index < DEFAULT_BANDS.length
                      ? DEFAULT_BANDS[index].parameter
                      : t('finance.sensitivity.controls.parameter')
                  }
                />
              </label>
              <label>
                {t('finance.sensitivity.controls.low')}
                <input
                  type="text"
                  value={row.low}
                  onChange={(event) =>
                    handleFieldChange(row.id, 'low', event.target.value)
                  }
                  disabled={controlsDisabled}
                  placeholder="-5"
                />
              </label>
              <label>
                {t('finance.sensitivity.controls.base')}
                <input
                  type="text"
                  value={row.base}
                  onChange={(event) =>
                    handleFieldChange(row.id, 'base', event.target.value)
                  }
                  disabled={controlsDisabled}
                  placeholder="0"
                />
              </label>
              <label>
                {t('finance.sensitivity.controls.high')}
                <input
                  type="text"
                  value={row.high}
                  onChange={(event) =>
                    handleFieldChange(row.id, 'high', event.target.value)
                  }
                  disabled={controlsDisabled}
                  placeholder="6"
                />
              </label>
              <button
                type="button"
                className="finance-sensitivity-controls__remove"
                onClick={() => handleRemoveRow(row.id)}
                disabled={controlsDisabled || rows.length === 1}
                aria-label={t('finance.sensitivity.controls.remove')}
              >
                {t('finance.sensitivity.controls.remove')}
              </button>
            </div>
          ))}
        </div>
        <div className="finance-sensitivity-controls__actions">
          <button
            type="submit"
            className="finance-sensitivity-controls__submit"
            disabled={controlsDisabled}
          >
            {submitting
              ? t('finance.sensitivity.controls.running')
              : t('finance.sensitivity.controls.run')}
          </button>
        </div>
      </form>
    </section>
  )
}
