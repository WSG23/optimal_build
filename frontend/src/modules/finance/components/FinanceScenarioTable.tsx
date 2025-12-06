import { useEffect, useMemo, useRef, useState } from 'react'

import { findResult, type FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'

interface FinanceScenarioTableProps {
  scenarios: FinanceScenarioSummary[]
  onMarkPrimary?: (scenarioId: number) => void
  updatingScenarioId?: number | null
  onDeleteScenario?: (scenario: FinanceScenarioSummary) => void
  deletingScenarioId?: number | null
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

function formatPercent(
  value: string | null | undefined,
  locale: string,
  fallback: string,
): string {
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

function formatDscr(
  value: number | null,
  locale: string,
  fallback: string,
): string {
  if (value === null) {
    return fallback
  }
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function formatDateTime(
  value: string | null | undefined,
  locale: string,
  fallback: string,
): string {
  if (!value) {
    return fallback
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return fallback
  }
  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export function FinanceScenarioTable({
  scenarios,
  onMarkPrimary,
  updatingScenarioId = null,
  onDeleteScenario,
  deletingScenarioId = null,
}: FinanceScenarioTableProps) {
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
        const loanToCost = scenario.capitalStack?.loanToCost ?? null

        return {
          id: scenario.scenarioId,
          name: scenario.scenarioName,
          currency: scenario.currency,
          escalatedCost,
          npv,
          irr,
          minDscr,
          loanToCost,
          isPrimary: Boolean(scenario.isPrimary),
          updatedAt: scenario.updatedAt ?? null,
          scenario,
        }
      }),
    [scenarios],
  )

  if (rows.length === 0) {
    return (
        <div className="finance-empty-state">
           <div className="finance-empty-state__visual">
             <div className="finance-empty-state__card-ghost" />
             <div className="finance-empty-state__card-ghost" />
             <div className="finance-empty-state__card-ghost" />
           </div>
           <p className="finance-empty-state__text">{t('finance.table.empty')}</p>
        </div>
    )
  }

  return (
    <div className="finance-table__wrapper">
      <table className="finance-table">
        <caption className="finance-table__caption">
          {t('finance.table.caption')}
        </caption>
        <thead>
          <tr>
            <th scope="col">{t('finance.table.headers.scenario')}</th>
            <th scope="col">{t('finance.table.headers.escalatedCost')}</th>
            <th scope="col">{t('finance.table.headers.npv')}</th>
            <th scope="col">{t('finance.table.headers.irr')}</th>
            <th scope="col">{t('finance.table.headers.minDscr')}</th>
            <th scope="col">{t('finance.table.headers.loanToCost')}</th>
            <th scope="col">{t('finance.table.headers.lastRun')}</th>
            <th scope="col">
              <span className="sr-only">
                {t('finance.table.headers.actions')}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <th scope="row">
                <div className="finance-table__scenario-cell">
                  <span>{row.name}</span>
                  {row.isPrimary ? (
                    <span className="finance-table__badge">
                      {t('finance.table.badges.primary')}
                    </span>
                  ) : null}
                  {!row.isPrimary && onMarkPrimary ? (
                    <button
                      type="button"
                      className="finance-table__primary-button"
                      onClick={() => onMarkPrimary(row.id)}
                      disabled={updatingScenarioId === row.id}
                    >
                      {updatingScenarioId === row.id
                        ? t('finance.table.actions.makingPrimary')
                        : t('finance.table.actions.makePrimary')}
                    </button>
                  ) : null}
                </div>
              </th>
              <td>
                {formatCurrency(
                  row.escalatedCost,
                  row.currency,
                  locale,
                  fallback,
                )}
              </td>
              <td>{formatCurrency(row.npv, row.currency, locale, fallback)}</td>
              <td>{formatPercent(row.irr, locale, fallback)}</td>
              <td>{formatDscr(row.minDscr, locale, fallback)}</td>
              <td>{formatPercent(row.loanToCost, locale, fallback)}</td>
              <td>{formatDateTime(row.updatedAt, locale, fallback)}</td>
              <td className="finance-table__actions-cell">
                {onDeleteScenario ? (
                  <FinanceScenarioActions
                    disabled={deletingScenarioId === row.id}
                    onDelete={() => onDeleteScenario(row.scenario)}
                    menuLabel={t('finance.table.actions.openMenu')}
                    deleteLabel={
                      deletingScenarioId === row.id
                        ? t('finance.table.actions.deleting')
                        : t('finance.table.actions.delete')
                    }
                  />
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

interface FinanceScenarioActionsProps {
  onDelete: () => void
  disabled?: boolean
  menuLabel: string
  deleteLabel: string
}

function FinanceScenarioActions({
  onDelete,
  disabled = false,
  menuLabel,
  deleteLabel,
}: FinanceScenarioActionsProps) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) {
      return undefined
    }
    function handleClick(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false)
      }
    }
    window.addEventListener('mousedown', handleClick)
    return () => window.removeEventListener('mousedown', handleClick)
  }, [open])

  return (
    <div className="finance-table__actions" ref={containerRef}>
      <button
        type="button"
        className="finance-table__actions-button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span aria-hidden="true">⋮</span>
        <span className="sr-only">{menuLabel}</span>
      </button>
      {open ? (
        <div className="finance-table__actions-menu" role="menu">
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false)
              onDelete()
            }}
            disabled={disabled}
          >
            {deleteLabel}
          </button>
        </div>
      ) : null}
    </div>
  )
}
