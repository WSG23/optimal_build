import { useMemo } from 'react'

import type { FinanceSensitivityOutcome } from '../../../api/finance'
import { useTranslation } from '../../../i18n'

interface FinanceSensitivityTableProps {
  outcomes: FinanceSensitivityOutcome[]
  currency: string
  parameters: string[]
  selectedParameters: string[]
  onToggleParameter: (parameter: string) => void
  onSelectAll: () => void
  onDownloadCsv: () => void
  onDownloadJson: () => void
}

function formatCurrency(
  value: string | null | undefined,
  currency: string,
  locale: string,
  fallback: string,
): string {
  if (value == null) {
    return fallback
  }
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) {
    return fallback
  }
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(parsed)
  } catch {
    return `${parsed.toLocaleString(locale)} ${currency}`
  }
}

function formatPercent(
  value: string | null | undefined,
  locale: string,
  fallback: string,
): string {
  if (value == null) {
    return fallback
  }
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) {
    return fallback
  }
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(parsed)
}

export function FinanceSensitivityTable({
  outcomes,
  currency,
  parameters,
  selectedParameters,
  onToggleParameter,
  onSelectAll,
  onDownloadCsv,
  onDownloadJson,
}: FinanceSensitivityTableProps) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language
  const fallback = t('common.fallback.dash')

  const selectedSet = useMemo(
    () => new Set(selectedParameters),
    [selectedParameters],
  )

  const grouped = useMemo(() => {
    const map = new Map<string, FinanceSensitivityOutcome[]>()
    for (const outcome of outcomes) {
      const key = outcome.parameter || 'unknown'
      if (!map.has(key)) {
        map.set(key, [])
      }
      map.get(key)?.push(outcome)
    }
    for (const entries of map.values()) {
      entries.sort((a, b) => a.scenario.localeCompare(b.scenario))
    }
    return Array.from(map.entries())
  }, [outcomes])

  return (
    <section className="finance-sensitivity">
      <h2 className="finance-sensitivity__title">
        {t('finance.sensitivity.title')}
      </h2>
      <div className="finance-sensitivity__controls">
        <div className="finance-sensitivity__checkboxes">
          <span className="finance-sensitivity__controls-label">
            {t('finance.sensitivity.controls.parameters')}
          </span>
          <button
            type="button"
            className="finance-sensitivity__select-all"
            onClick={onSelectAll}
            disabled={parameters.length === 0}
          >
            {t('finance.sensitivity.controls.selectAll')}
          </button>
          {parameters.map((parameter) => (
            <label key={parameter} className="finance-sensitivity__checkbox">
              <input
                type="checkbox"
                checked={selectedSet.has(parameter)}
                disabled={parameters.length === 0}
                onChange={() => onToggleParameter(parameter)}
              />
              <span>{parameter}</span>
            </label>
          ))}
        </div>
        <div className="finance-sensitivity__downloads">
          <button
            type="button"
            className="finance-sensitivity__download"
            onClick={onDownloadCsv}
            disabled={outcomes.length === 0}
          >
            {t('finance.sensitivity.actions.downloadCsv')}
          </button>
          <button
            type="button"
            className="finance-sensitivity__download"
            onClick={onDownloadJson}
            disabled={outcomes.length === 0}
          >
            {t('finance.sensitivity.actions.downloadJson')}
          </button>
        </div>
      </div>
      {grouped.length === 0 ? (
        <p className="finance-sensitivity__empty">
          {t('finance.sensitivity.empty')}
        </p>
      ) : null}
      {grouped.map(([parameter, entries]) => (
        <div key={parameter} className="finance-sensitivity__group">
          <h3 className="finance-sensitivity__group-title">{parameter}</h3>
          <table className="finance-sensitivity__table">
            <caption className="finance-sensitivity__caption">
              {t('finance.sensitivity.table.caption', { parameter })}
            </caption>
            <thead>
              <tr>
                <th scope="col">
                  {t('finance.sensitivity.table.headers.delta')}
                </th>
                <th scope="col">
                  {t('finance.sensitivity.table.headers.npv')}
                </th>
                <th scope="col">
                  {t('finance.sensitivity.table.headers.irr')}
                </th>
                <th scope="col">
                  {t('finance.sensitivity.table.headers.escalatedCost')}
                </th>
                <th scope="col">
                  {t('finance.sensitivity.table.headers.totalInterest')}
                </th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, index) => (
                <tr key={`${entry.scenario}-${index}`}>
                  <th scope="row">{entry.deltaLabel || entry.deltaValue}</th>
                  <td>
                    {formatCurrency(
                      entry.npv ?? null,
                      currency,
                      locale,
                      fallback,
                    )}
                  </td>
                  <td>{formatPercent(entry.irr ?? null, locale, fallback)}</td>
                  <td>
                    {formatCurrency(
                      entry.escalatedCost ?? null,
                      currency,
                      locale,
                      fallback,
                    )}
                  </td>
                  <td>
                    {entry.totalInterest != null
                      ? formatCurrency(
                          entry.totalInterest,
                          currency,
                          locale,
                          fallback,
                        )
                      : fallback}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  )
}

export default FinanceSensitivityTable
