import { useMemo } from 'react'

import { findResult, type FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'

interface FinanceScenarioTableProps {
  scenarios: FinanceScenarioSummary[]
}

function toNumber(value: string | null | undefined): number | null {
  if (value === null || value === undefined) {
    return null
  }
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function formatCurrency(
  value: string | null | undefined,
  currency: string,
  locale: string,
  fallback: string,
): string {
  const amount = toNumber(value)
  if (amount === null) {
    return fallback
  }
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(amount)
  } catch {
    const formatted = new Intl.NumberFormat(locale, {
      maximumFractionDigits: 0,
    }).format(amount)
    return `${formatted} ${currency}`
  }
}

function formatPercent(value: string | null | undefined, locale: string, fallback: string): string {
  const parsed = toNumber(value)
  if (parsed === null) {
    return fallback
  }
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(parsed)
}

function formatDscr(value: number | null, locale: string, fallback: string): string {
  if (value === null) {
    return fallback
  }
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export function FinanceScenarioTable({ scenarios }: FinanceScenarioTableProps) {
  const { t, i18n } = useTranslation()
  const fallback = t('common.fallback.dash')
  const locale = i18n.language

  const rows = useMemo(
    () =>
      scenarios.map((scenario) => {
        const escalatedCost = scenario.escalatedCost
        const npv = findResult(scenario, 'npv')?.value ?? null
        const irr = findResult(scenario, 'irr')?.value ?? null
        const dscrValues = scenario.dscrTimeline
          .map((entry) => toNumber(entry.dscr ?? null))
          .filter((value): value is number => value !== null)
        const minDscr = dscrValues.length > 0 ? Math.min(...dscrValues) : null

        return {
          id: scenario.scenarioId,
          name: scenario.scenarioName,
          currency: scenario.currency,
          escalatedCost,
          npv,
          irr,
          minDscr,
        }
      }),
    [scenarios],
  )

  if (rows.length === 0) {
    return null
  }

  return (
    <div className="finance-table__wrapper">
      <table className="finance-table">
        <caption className="finance-table__caption">{t('finance.table.caption')}</caption>
        <thead>
          <tr>
            <th scope="col">{t('finance.table.headers.scenario')}</th>
            <th scope="col">{t('finance.table.headers.escalatedCost')}</th>
            <th scope="col">{t('finance.table.headers.npv')}</th>
            <th scope="col">{t('finance.table.headers.irr')}</th>
            <th scope="col">{t('finance.table.headers.minDscr')}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <th scope="row">{row.name}</th>
              <td>{formatCurrency(row.escalatedCost, row.currency, locale, fallback)}</td>
              <td>{formatCurrency(row.npv, row.currency, locale, fallback)}</td>
              <td>{formatPercent(row.irr, locale, fallback)}</td>
              <td>{formatDscr(row.minDscr, locale, fallback)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
