import { useMemo } from 'react'

import type { FinanceSensitivityOutcome } from '../../../api/finance'
import { useTranslation } from '../../../i18n'

export interface SensitivitySummaryItem {
  parameter: string
  baseLabel: string | null
  baseValue: number | null
  bestDelta: SensitivityDelta | null
  worstDelta: SensitivityDelta | null
  deltas: SensitivityDelta[]
  maxMagnitude: number
}

export interface SensitivityDelta {
  label: string
  scenario: string
  delta: number
  isBase?: boolean
}

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

export function buildSensitivitySummaries(
  outcomes: FinanceSensitivityOutcome[],
): SensitivitySummaryItem[] {
  const groups = new Map<string, FinanceSensitivityOutcome[]>()
  for (const outcome of outcomes) {
    const key = outcome.parameter || 'unknown'
    if (!groups.has(key)) {
      groups.set(key, [])
    }
    groups.get(key)?.push(outcome)
  }

  const summaries: SensitivitySummaryItem[] = []
  groups.forEach((entries, parameter) => {
    const parsed = entries
      .map((entry) => ({
        ...entry,
        npvValue: entry.npv != null ? Number(entry.npv) : null,
      }))
      .filter((entry) => entry.npvValue !== null) as Array<
      FinanceSensitivityOutcome & { npvValue: number }
    >
    if (parsed.length === 0) {
      return
    }

    const baseEntry =
      parsed.find((entry) => entry.deltaValue === '0' || /base/i.test(entry.scenario)) ??
      parsed.find((entry) => entry.deltaLabel && /base/i.test(entry.deltaLabel))

    const baseValue = baseEntry?.npvValue ?? null
    const deltaSummaries =
      baseValue === null
        ? []
        : parsed.map((entry) => ({
            label: entry.deltaLabel ?? entry.scenario,
            scenario: entry.scenario,
            delta: entry.npvValue - baseValue,
            isBase: entry === baseEntry,
          }))
    const comparative = deltaSummaries.filter((entry) => !entry.isBase)

    const bestDelta =
      comparative.length > 0
        ? comparative.reduce((best, candidate) =>
            candidate.delta > (best?.delta ?? Number.NEGATIVE_INFINITY)
              ? candidate
              : best,
          )
        : null
    const worstDelta =
      comparative.length > 0
        ? comparative.reduce((worst, candidate) =>
            candidate.delta < (worst?.delta ?? Number.POSITIVE_INFINITY)
              ? candidate
              : worst,
          )
        : null
    const maxMagnitude = deltaSummaries.reduce(
      (max, entry) => Math.max(max, Math.abs(entry.delta)),
      0,
    )

    summaries.push({
      parameter,
      baseLabel: baseEntry?.deltaLabel ?? baseEntry?.scenario ?? null,
      baseValue,
      bestDelta,
      worstDelta,
      deltas: deltaSummaries,
      maxMagnitude,
    })
  })
  return summaries
}
