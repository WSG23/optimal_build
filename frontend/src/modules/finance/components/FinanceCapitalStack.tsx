import { useMemo } from 'react'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'

interface FinanceCapitalStackProps {
  scenarios: FinanceScenarioSummary[]
}

function toNumber(value: string | null | undefined): number | null {
  if (typeof value !== 'string') {
    return null
  }
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function toPercent(value: string | null | undefined): number {
  const ratio = toNumber(value)
  if (ratio === null) {
    return 0
  }
  const percent = ratio * 100
  if (!Number.isFinite(percent) || percent < 0) {
    return 0
  }
  return Math.min(100, percent)
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

function formatPercent(
  ratio: string | null | undefined,
  locale: string,
  fallback: string,
): string {
  const numeric = toNumber(ratio)
  if (numeric === null) {
    return fallback
  }
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numeric)
}

export function FinanceCapitalStack({
  scenarios,
}: FinanceCapitalStackProps) {
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
          capitalStack: scenario.capitalStack,
        }))
        .filter(
          (entry): entry is typeof entry & {
            capitalStack: NonNullable<FinanceScenarioSummary['capitalStack']>
          } => Boolean(entry.capitalStack),
        ),
    [scenarios],
  )

  if (cards.length === 0) {
    return null
  }

  return (
    <section className="finance-capital">
      <h2 className="finance-capital__title">
        {t('finance.capitalStack.title')}
      </h2>
      <div className="finance-capital__grid">
        {cards.map((card) => {
          const { capitalStack } = card
          const equityWidth = toPercent(capitalStack.equityRatio)
          const debtWidth = toPercent(capitalStack.debtRatio)
          const otherWidth = toPercent(capitalStack.otherRatio)
          return (
            <article key={card.id} className="finance-capital__card">
              <header className="finance-capital__card-header">
                <h3 className="finance-capital__card-title">{card.name}</h3>
                <p className="finance-capital__total">
                  {formatCurrency(capitalStack.total, card.currency, locale, fallback)}
                </p>
              </header>
              <div className="finance-capital__bar" aria-hidden="true">
                <span
                  className="finance-capital__segment finance-capital__segment--equity"
                  style={{ width: `${equityWidth}%` }}
                />
                <span
                  className="finance-capital__segment finance-capital__segment--debt"
                  style={{ width: `${debtWidth}%` }}
                />
                {otherWidth > 0 ? (
                  <span
                    className="finance-capital__segment finance-capital__segment--other"
                    style={{ width: `${otherWidth}%` }}
                  />
                ) : null}
              </div>
              <dl className="finance-capital__ratios">
                <div>
                  <dt>{t('finance.capitalStack.labels.equity')}</dt>
                  <dd>{formatPercent(capitalStack.equityRatio, locale, fallback)}</dd>
                </div>
                <div>
                  <dt>{t('finance.capitalStack.labels.debt')}</dt>
                  <dd>{formatPercent(capitalStack.debtRatio, locale, fallback)}</dd>
                </div>
                <div>
                  <dt>{t('finance.capitalStack.labels.loanToCost')}</dt>
                  <dd>{formatPercent(capitalStack.loanToCost, locale, fallback)}</dd>
                </div>
                <div>
                  <dt>{t('finance.capitalStack.labels.weightedDebtRate')}</dt>
                  <dd>
                    {formatPercent(
                      capitalStack.weightedAverageDebtRate,
                      locale,
                      fallback,
                    )}
                  </dd>
                </div>
              </dl>
              <ul className="finance-capital__slices">
                {capitalStack.slices.map((slice) => (
                  <li key={`${card.id}-${slice.name}`}>
                    <div className="finance-capital__slice-header">
                      <span className="finance-capital__slice-name">{slice.name}</span>
                      <span className="finance-capital__slice-share">
                        {formatPercent(slice.share, locale, fallback)}
                      </span>
                    </div>
                    <div className="finance-capital__slice-meta">
                      <span>
                        {formatCurrency(slice.amount, card.currency, locale, fallback)}
                      </span>
                      <span className="finance-capital__slice-category">
                        {t(`finance.capitalStack.categories.${slice.category}`, {
                          defaultValue: slice.category,
                        })}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </article>
          )
        })}
      </div>
    </section>
  )
}

export default FinanceCapitalStack
