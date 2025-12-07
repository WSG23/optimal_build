import { useEffect, useMemo, useRef, useState } from 'react'

import { findResult, type FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'
import { CapitalStackMiniBar } from './CapitalStackMiniBar'

interface FinanceScenarioTableProps {
  scenarios: FinanceScenarioSummary[]
  onMarkPrimary?: (id: number) => void
  onDeleteScenario?: (scenario: FinanceScenarioSummary) => void
  deletingScenarioId?: number | null
  updatingScenarioId?: number | null
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
  onDeleteScenario,
  deletingScenarioId = null,
  updatingScenarioId = null,
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
    <div className="finance-ticker-grid">
      {rows.map((row) => (
        <article
          key={row.id}
          className={`finance-ticker-card ${row.isPrimary ? 'finance-ticker-card--primary' : ''}`}
        >
          {/* Column 1: Header / Title */}
          <div className="finance-ticker-card__header">
            <h3 className="finance-ticker-card__title">{row.name}</h3>
            <div className="finance-ticker-card__meta">
              {row.isPrimary && (
                <span className="finance-ticker-card__badge">
                  {t('finance.table.badges.primary')}
                </span>
              )}
              <span>{formatDateTime(row.updatedAt, locale, fallback)}</span>
            </div>
          </div>

          {/* Column 2: Large Cost */}
          <div className="finance-ticker-value">
            <span className="finance-ticker-value__label">
              {t('finance.table.headers.escalatedCost')}
            </span>
            <span className="finance-ticker-value__number finance-ticker-value__number--large">
              {formatCurrency(
                row.escalatedCost,
                row.currency,
                locale,
                fallback,
              )}
            </span>
          </div>

          {/* Column 3: IRR (Conditional) */}
          <div className="finance-ticker-value">
            <span className="finance-ticker-value__label">
              {t('finance.table.headers.irr')}
            </span>
            <span
              className={`finance-ticker-value__number ${
                (Number(row.irr) || 0) >= 0.15
                  ? 'finance-ticker-value__number--positive'
                  : (Number(row.irr) || 0) < 0.1
                    ? 'finance-ticker-value__number--negative'
                    : ''
              }`}
            >
              {formatPercent(row.irr, locale, fallback)}
            </span>
          </div>

          {/* Column 4: DSCR (Conditional) */}
          <div className="finance-ticker-value">
            <span className="finance-ticker-value__label">
              {t('finance.table.headers.minDscr')}
            </span>
            <span
              className={`finance-ticker-value__number ${
                (Number(row.minDscr) || 0) >= 1.2
                  ? 'finance-ticker-value__number--positive'
                  : (Number(row.minDscr) || 0) < 1.0
                    ? 'finance-ticker-value__number--negative'
                    : ''
              }`}
            >
              {formatDscr(row.minDscr, locale, fallback)}
            </span>
          </div>

          {/* Column 5: NPV */}
          <div className="finance-ticker-value">
            <span className="finance-ticker-value__label">
              {t('finance.table.headers.npv')}
            </span>
            <span className="finance-ticker-value__number">
              {formatCurrency(row.npv, row.currency, locale, fallback)}
            </span>
          </div>

          {/* Column 6: Capital Stack Visualization */}
          <div className="finance-ticker-card__stack">
            <span className="finance-ticker-value__label">Capital Stack</span>
            {row.scenario.capitalStack ? (
              <CapitalStackMiniBar stack={row.scenario.capitalStack} />
            ) : (
              <span
                style={{
                  fontSize: '0.7rem',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                No data
              </span>
            )}
          </div>

          {/* Column 7: Actions */}
          <div className="finance-ticker-card__actions">
            {/* Only show make primary if not already primary */}
            {!row.isPrimary && onMarkPrimary && (
              <button
                type="button"
                onClick={() => onMarkPrimary(row.id)}
                disabled={updatingScenarioId === row.id}
                className="finance-table__primary-button" // Reusing this class for now or make a simpler icon
                style={{
                  padding: '4px',
                  minWidth: 'auto',
                  border: 'none',
                  color: 'var(--ob-color-text-muted)',
                }}
                title={
                  updatingScenarioId === row.id
                    ? t('finance.table.actions.updating')
                    : t('finance.table.actions.makePrimary')
                }
                aria-label={
                  updatingScenarioId === row.id
                    ? t('finance.table.actions.updating')
                    : t('finance.table.actions.makePrimary')
                }
              >
                {updatingScenarioId === row.id ? '⏳' : '⭐'}
              </button>
            )}
            {onDeleteScenario && (
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
            )}
          </div>
        </article>
      ))}
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
