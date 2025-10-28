import {
  type AssetFinancialSummary,
  type FinanceAssetBreakdown as FinanceAssetBreakdownType,
} from '../../../api/finance'
import { useTranslation } from '../../../i18n'

interface FinanceAssetBreakdownProps {
  summary: AssetFinancialSummary | null
  breakdowns: FinanceAssetBreakdownType[]
}

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

export function FinanceAssetBreakdown({
  summary,
  breakdowns,
}: FinanceAssetBreakdownProps) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language
  const fallback = t('common.fallback.dash')

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
      {hasSummary && summary ? (
        <dl className="finance-assets__summary">
          <div>
            <dt>{t('finance.assets.totals.revenue')}</dt>
            <dd>
              {formatCurrency(
                summary.totalEstimatedRevenueSgd ?? null,
                'SGD',
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
                'SGD',
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
                    {formatCurrency(
                      entry.noiAnnualSgd ?? null,
                      'SGD',
                      locale,
                      fallback,
                    )}
                  </td>
                  <td>
                    {formatCurrency(
                      entry.estimatedCapexSgd ?? null,
                      'SGD',
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
