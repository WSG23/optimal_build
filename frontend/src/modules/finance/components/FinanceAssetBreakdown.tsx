import { useMemo } from 'react'

import {
  type AssetFinancialSummary,
  type FinanceAssetBreakdown as FinanceAssetBreakdownType,
} from '../../../api/finance'
import { useTranslation } from '../../../i18n'

interface FinanceAssetBreakdownProps {
  summary: AssetFinancialSummary | null
  breakdowns: FinanceAssetBreakdownType[]
  currency?: string
}

const COLOR_SCALE = [
  '#4f6bed',
  '#57a773',
  '#f4b000',
  '#cc5f82',
  '#6c5ce7',
  '#2cb3c8',
  '#f16e5c',
] as const

function toNumber(value: string | null | undefined): number | null {
  if (value == null) {
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
  const parsed = toNumber(value)
  if (parsed === null) {
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
  const parsed = toNumber(value)
  if (parsed === null) {
    return fallback
  }
  const ratio = parsed > 1 ? parsed / 100 : parsed
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(ratio)
}

function formatNumber(
  value: string | null | undefined,
  locale: string,
  fallback: string,
): string {
  const parsed = toNumber(value)
  if (parsed === null) {
    return fallback
  }
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: 1,
  }).format(parsed)
}

function toPercentValue(value: string | null | undefined): number {
  const numeric = toNumber(value)
  if (numeric === null) {
    return 0
  }
  if (numeric > 1) {
    return Math.min(numeric, 100)
  }
  return Math.min(numeric * 100, 100)
}

export function FinanceAssetBreakdown({
  summary,
  breakdowns,
  currency = 'SGD',
}: FinanceAssetBreakdownProps) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language
  const fallback = t('common.fallback.dash')

  const allocationSegments = useMemo(() => {
    return breakdowns
      .map((entry, index) => {
        const percent = toPercentValue(entry.allocationPct ?? null)
        return {
          assetType: entry.assetType || t('common.fallback.unknown'),
          percent,
          color: COLOR_SCALE[index % COLOR_SCALE.length],
        }
      })
      .filter((segment) => segment.percent > 0)
  }, [breakdowns, t])
  const totalPercent = allocationSegments.reduce(
    (sum, segment) => sum + segment.percent,
    0,
  )

  const hasSummary =
    summary &&
    (summary.totalEstimatedRevenueSgd ||
      summary.totalEstimatedCapexSgd ||
      summary.dominantRiskProfile)

  const hasBreakdowns = breakdowns.length > 0

  if (!hasSummary && !hasBreakdowns) {
    return (
      <section className="finance-assets">
        <h2 className="finance-assets__title">
          {t('finance.assets.title')}
        </h2>
        <p className="finance-assets__empty">{t('finance.assets.empty')}</p>
      </section>
    )
  }

  return (
    <section className="finance-assets">
      <h2 className="finance-assets__title">{t('finance.assets.title')}</h2>
      {allocationSegments.length > 0 ? (
        <div className="finance-assets__bar" aria-hidden="true">
          {allocationSegments.map((segment) => (
            <span
              key={segment.assetType}
              className="finance-assets__bar-segment"
              style={{
                width: `${
                  totalPercent > 0 ? (segment.percent / totalPercent) * 100 : 0
                }%`,
                backgroundColor: segment.color,
              }}
              title={`${segment.assetType} · ${segment.percent.toFixed(1)}%`}
            />
          ))}
        </div>
      ) : null}
      {allocationSegments.length > 0 ? (
        <ul className="finance-assets__legend">
          {allocationSegments.map((segment) => (
            <li key={`${segment.assetType}-legend`}>
              <span
                className="finance-assets__legend-swatch"
                style={{ backgroundColor: segment.color }}
                aria-hidden="true"
              />
              <span className="finance-assets__legend-label">
                {segment.assetType}
              </span>
              <span className="finance-assets__legend-value">
                {segment.percent.toFixed(1)}%
              </span>
            </li>
          ))}
        </ul>
      ) : null}
      {hasSummary && summary ? (
        <dl className="finance-assets__summary">
          <div>
            <dt>{t('finance.assets.totals.revenue')}</dt>
            <dd>
              {formatCurrency(
                summary.totalEstimatedRevenueSgd ?? null,
                currency,
                locale,
                fallback,
              )}
            </dd>
          </div>
          <div>
            <dt>{t('finance.assets.totals.capex')}</dt>
            <dd>
              {formatCurrency(
                summary.totalEstimatedCapexSgd ?? null,
                currency,
                locale,
                fallback,
              )}
            </dd>
          </div>
          <div>
            <dt>{t('finance.assets.totals.risk')}</dt>
            <dd>{summary.dominantRiskProfile ?? fallback}</dd>
          </div>
        </dl>
      ) : null}
      {hasBreakdowns ? (
        <div className="finance-assets__table-wrapper">
          <table className="finance-assets__table">
            <caption className="finance-assets__caption">
              {t('finance.assets.table.caption')}
            </caption>
            <thead>
              <tr>
                <th scope="col">{t('finance.assets.table.headers.asset')}</th>
                <th scope="col">
                  {t('finance.assets.table.headers.allocation')}
                </th>
                <th scope="col">
                  {t('finance.assets.table.headers.nia')}
                </th>
                <th scope="col">
                  {t('finance.assets.table.headers.rent')}
                </th>
                <th scope="col">
                  {t('finance.assets.table.headers.noi')}
                </th>
                <th scope="col">
                  {t('finance.assets.table.headers.capex')}
                </th>
                <th scope="col">
                  {t('finance.assets.table.headers.payback')}
                </th>
                <th scope="col">
                  {t('finance.assets.table.headers.absorption')}
                </th>
                <th scope="col">{t('finance.assets.table.headers.risk')}</th>
              </tr>
            </thead>
            <tbody>
              {breakdowns.map((entry, index) => (
                <tr key={`${entry.assetType}-${index}`}>
                  <th scope="row">{entry.assetType}</th>
                  <td>{formatPercent(entry.allocationPct ?? null, locale, fallback)}</td>
                  <td>
                    {formatNumber(
                      entry.niaSqm ?? null,
                      locale,
                      fallback,
                    )}
                  </td>
                  <td>
                    {formatCurrency(
                      entry.rentPsmMonth ?? null,
                      currency,
                      locale,
                      fallback,
                    )}
                  </td>
                  <td>
                    {formatCurrency(
                      entry.noiAnnualSgd ?? null,
                      currency,
                      locale,
                      fallback,
                    )}
                  </td>
                  <td>
                    {formatCurrency(
                      entry.estimatedCapexSgd ?? null,
                      currency,
                      locale,
                      fallback,
                    )}
                  </td>
                  <td>
                    {formatNumber(entry.paybackYears ?? null, locale, fallback)}
                  </td>
                  <td>
                    {formatNumber(
                      entry.absorptionMonths ?? null,
                      locale,
                      fallback,
                    )}
                  </td>
                  <td>{entry.riskLevel ?? fallback}</td>
                  <td>
                    {entry.notes?.length
                      ? entry.notes.join('; ')
                      : fallback}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {summary && summary.notes.length > 0 ? (
        <ul className="finance-assets__notes">
          {summary.notes.map((note, index) => (
            <li key={`${note}-${index}`}>{note}</li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}

export default FinanceAssetBreakdown
