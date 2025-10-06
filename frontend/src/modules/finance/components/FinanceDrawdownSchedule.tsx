import { useMemo } from 'react'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'

interface FinanceDrawdownScheduleProps {
  scenarios: FinanceScenarioSummary[]
  maxRows?: number
}

function toNumber(value: string | undefined): number | null {
  if (typeof value !== 'string') {
    return null
  }
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function formatCurrency(
  amount: string,
  currency: string,
  locale: string,
  fallback: string,
): string {
  const numeric = toNumber(amount)
  if (numeric === null) {
    return fallback
  }
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(numeric)
  } catch {
    return `${numeric.toLocaleString(locale)} ${currency}`
  }
}

export function FinanceDrawdownSchedule({
  scenarios,
  maxRows = 6,
}: FinanceDrawdownScheduleProps) {
  const { t, i18n } = useTranslation()
  const fallback = t('common.fallback.dash')
  const locale = i18n.language

  const cards = useMemo(
    () =>
      scenarios
        .map((scenario) => ({
          id: scenario.scenarioId,
          name: scenario.scenarioName,
          currency: scenario.currency,
          drawdown: scenario.drawdownSchedule,
        }))
        .filter(
          (entry): entry is typeof entry & {
            drawdown: NonNullable<FinanceScenarioSummary['drawdownSchedule']>
          } => Boolean(entry.drawdown),
        ),
    [scenarios],
  )

  if (cards.length === 0) {
    return null
  }

  return (
    <section className="finance-drawdown">
      <h2 className="finance-drawdown__title">{t('finance.drawdown.title')}</h2>
      <div className="finance-drawdown__grid">
        {cards.map((card) => {
          const { drawdown } = card
          const entries = drawdown.entries.slice(0, maxRows)
          const hasMore = drawdown.entries.length > entries.length
          return (
            <article key={card.id} className="finance-drawdown__card">
              <header className="finance-drawdown__card-header">
                <h3 className="finance-drawdown__card-title">{card.name}</h3>
                <dl className="finance-drawdown__totals">
                  <div>
                    <dt>{t('finance.drawdown.totals.equity')}</dt>
                    <dd>
                      {formatCurrency(
                        drawdown.totalEquity,
                        card.currency,
                        locale,
                        fallback,
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('finance.drawdown.totals.debt')}</dt>
                    <dd>
                      {formatCurrency(
                        drawdown.totalDebt,
                        card.currency,
                        locale,
                        fallback,
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('finance.drawdown.totals.peakDebt')}</dt>
                    <dd>
                      {formatCurrency(
                        drawdown.peakDebtBalance,
                        card.currency,
                        locale,
                        fallback,
                      )}
                    </dd>
                  </div>
                </dl>
              </header>
              <div className="finance-drawdown__table-wrapper">
                <table className="finance-drawdown__table">
                  <caption className="finance-drawdown__table-caption">
                    {t('finance.drawdown.caption')}
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">{t('finance.drawdown.headers.period')}</th>
                      <th scope="col">{t('finance.drawdown.headers.equity')}</th>
                      <th scope="col">{t('finance.drawdown.headers.debt')}</th>
                      <th scope="col">{t('finance.drawdown.headers.outstanding')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((entry) => (
                      <tr key={`${card.id}-${entry.period}`}>
                        <th scope="row">{entry.period}</th>
                        <td>
                          {formatCurrency(
                            entry.equityDraw,
                            card.currency,
                            locale,
                            fallback,
                          )}
                        </td>
                        <td>
                          {formatCurrency(
                            entry.debtDraw,
                            card.currency,
                            locale,
                            fallback,
                          )}
                        </td>
                        <td>
                          {formatCurrency(
                            entry.outstandingDebt,
                            card.currency,
                            locale,
                            fallback,
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {hasMore ? (
                <p className="finance-drawdown__more">
                  {t('finance.drawdown.moreEntries', {
                    count: drawdown.entries.length - entries.length,
                  })}
                </p>
              ) : null}
            </article>
          )
        })}
      </div>
    </section>
  )
}

export default FinanceDrawdownSchedule
