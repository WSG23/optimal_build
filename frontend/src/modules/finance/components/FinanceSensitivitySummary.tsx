import { useTranslation } from '../../../i18n'
import type { SensitivitySummaryItem } from './sensitivitySummary'

interface FinanceSensitivitySummaryProps {
  summaries: SensitivitySummaryItem[]
  currency: string
}

function formatCurrencyDelta(
  value: number | null,
  currency: string,
  locale: string,
  fallback: string,
): string {
  if (value === null || Number.isNaN(value)) {
    return fallback
  }
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
      signDisplay: 'always',
    }).format(value)
  } catch {
    const formatted = value.toLocaleString(locale, { maximumFractionDigits: 0 })
    return value >= 0 ? `+${formatted} ${currency}` : `${formatted} ${currency}`
  }
}

export function FinanceSensitivitySummary({
  summaries,
  currency,
}: FinanceSensitivitySummaryProps) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language
  const fallback = t('common.fallback.dash')

  if (summaries.length === 0) {
    return null
  }

  return (
    <section className="finance-sensitivity-summary">
      <h2 className="finance-sensitivity-summary__title">
        {t('finance.sensitivity.summary.title')}
      </h2>
      <div className="finance-sensitivity-summary__grid">
        {summaries.map((summary) => {
          const maxAbsDelta = summary.maxMagnitude
          const bestWidth =
            summary.bestDelta && maxAbsDelta
              ? Math.min(100, (Math.abs(summary.bestDelta.delta) / maxAbsDelta) * 100)
              : 0
          const worstWidth =
            summary.worstDelta && maxAbsDelta
              ? Math.min(
                  100,
                  (Math.abs(summary.worstDelta.delta) / maxAbsDelta) * 100,
                )
              : 0
          return (
            <article
              key={summary.parameter}
              className="finance-sensitivity-summary__card"
            >
              <header className="finance-sensitivity-summary__card-header">
                <h3>{summary.parameter}</h3>
                <span>
                  {summary.baseValue !== null
                    ? formatCurrencyDelta(summary.baseValue, currency, locale, fallback)
                    : fallback}
                </span>
              </header>
              <p className="finance-sensitivity-summary__baseline">
                {summary.baseLabel
                  ? t('finance.sensitivity.summary.labels.base', {
                      label: summary.baseLabel,
                    })
                  : t('finance.sensitivity.summary.labels.baseUnknown')}
              </p>
              <dl className="finance-sensitivity-summary__deltas">
                <div className="finance-sensitivity-summary__delta-row">
                  <dt>{t('finance.sensitivity.summary.labels.best')}</dt>
                  <dd>
                    {formatCurrencyDelta(
                      summary.bestDelta?.delta ?? null,
                      currency,
                      locale,
                      fallback,
                    )}
                    <span className="finance-sensitivity-summary__scenario">
                      {summary.bestDelta?.label || summary.bestDelta?.scenario || ''}
                    </span>
                  </dd>
                  <div className="finance-sensitivity-summary__spark">
                    <span
                      className="finance-sensitivity-summary__spark-bar finance-sensitivity-summary__spark-bar--positive"
                      style={{ width: `${bestWidth}%` }}
                    />
                  </div>
                </div>
                <div className="finance-sensitivity-summary__delta-row">
                  <dt>{t('finance.sensitivity.summary.labels.worst')}</dt>
                  <dd>
                    {formatCurrencyDelta(
                      summary.worstDelta?.delta ?? null,
                      currency,
                      locale,
                      fallback,
                    )}
                    <span className="finance-sensitivity-summary__scenario">
                      {summary.worstDelta?.label || summary.worstDelta?.scenario || ''}
                    </span>
                  </dd>
                  <div className="finance-sensitivity-summary__spark">
                    <span
                      className="finance-sensitivity-summary__spark-bar finance-sensitivity-summary__spark-bar--negative"
                      style={{ width: `${worstWidth}%` }}
                    />
                  </div>
                </div>
              </dl>
              <div className="finance-sensitivity-summary__delta-list-wrapper">
                <h4 className="finance-sensitivity-summary__delta-heading">
                  {t('finance.sensitivity.summary.deltas.title')}
                </h4>
                {summary.deltas.length > 0 ? (
                  <ul className="finance-sensitivity-summary__delta-list">
                    {summary.deltas.map((delta) => {
                      const width =
                        summary.maxMagnitude > 0
                          ? Math.min(
                              100,
                              (Math.abs(delta.delta) / summary.maxMagnitude) * 100,
                            )
                          : 0
                      const polarity =
                        delta.delta > 0
                          ? 'positive'
                          : delta.delta < 0
                            ? 'negative'
                            : 'neutral'
                      return (
                        <li
                          key={`${summary.parameter}-${delta.scenario}`}
                          className={`finance-sensitivity-summary__delta-pill finance-sensitivity-summary__delta-pill--${polarity}${
                            delta.isBase ? ' finance-sensitivity-summary__delta-pill--base' : ''
                          }`}
                        >
                          <div className="finance-sensitivity-summary__delta-pill-text">
                            <span className="finance-sensitivity-summary__delta-label">
                              {delta.label}
                            </span>
                            <span className="finance-sensitivity-summary__delta-value">
                              {delta.isBase
                                ? t('finance.sensitivity.summary.labels.baseShort')
                                : formatCurrencyDelta(
                                    delta.delta,
                                    currency,
                                    locale,
                                    fallback,
                                  )}
                            </span>
                          </div>
                          <span
                            className="finance-sensitivity-summary__delta-bar"
                            style={{ width: `${width}%` }}
                            aria-hidden="true"
                          />
                        </li>
                      )
                    })}
                  </ul>
                ) : (
                  <p className="finance-sensitivity-summary__delta-empty">
                    {t('finance.sensitivity.summary.deltas.empty')}
                  </p>
                )}
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
