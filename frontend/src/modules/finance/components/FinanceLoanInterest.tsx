import { useTranslation } from '../../../i18n'
import type { ConstructionLoanInterest } from '../../../api/finance'

interface FinanceLoanInterestProps {
  schedule: ConstructionLoanInterest | null
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

function formatNumber(
  value: string | null | undefined,
  locale: string,
  fallback: string,
  options: Intl.NumberFormatOptions = {
    maximumFractionDigits: 2,
  },
): string {
  if (value == null) {
    return fallback
  }
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) {
    return fallback
  }
  return new Intl.NumberFormat(locale, options).format(parsed)
}

function hasAmount(value: string | null | undefined): boolean {
  if (value == null) {
    return false
  }
  const parsed = Number(value)
  return Number.isFinite(parsed)
}

export function FinanceLoanInterest({
  schedule,
}: FinanceLoanInterestProps) {
  const { t, i18n } = useTranslation()
  if (!schedule) {
    return null
  }

  const locale = i18n.language
  const fallback = t('common.fallback.dash')
  const capitalisedLabel = schedule.capitalised
    ? t('finance.loanInterest.totals.capitalisedYes')
    : t('finance.loanInterest.totals.capitalisedNo')
  const summaryItems: Array<{ label: string; value: string | number }> = [
    {
      label: t('finance.loanInterest.totals.interest'),
      value: formatCurrency(
        schedule.totalInterest,
        schedule.currency,
        locale,
        fallback,
      ),
    },
    {
      label: t('finance.loanInterest.totals.rate'),
      value: formatNumber(schedule.interestRate, locale, fallback, {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
    },
    {
      label: t('finance.loanInterest.totals.periods'),
      value: schedule.periodsPerYear ?? fallback,
    },
    {
      label: t('finance.loanInterest.totals.capitalised'),
      value: capitalisedLabel,
    },
  ]

  if (hasAmount(schedule.upfrontFeeTotal)) {
    summaryItems.push({
      label: t('finance.loanInterest.totals.upfront'),
      value: formatCurrency(
        schedule.upfrontFeeTotal,
        schedule.currency,
        locale,
        fallback,
      ),
    })
  }

  if (hasAmount(schedule.exitFeeTotal)) {
    summaryItems.push({
      label: t('finance.loanInterest.totals.exit'),
      value: formatCurrency(
        schedule.exitFeeTotal,
        schedule.currency,
        locale,
        fallback,
      ),
    })
  }

  const hasFacilities = schedule.facilities.length > 0

  return (
    <section className="finance-interest">
      <h2 className="finance-interest__title">
        {t('finance.loanInterest.title')}
      </h2>
      <dl className="finance-interest__summary">
        {summaryItems.map((item) => (
          <div key={item.label}>
            <dt>{item.label}</dt>
            <dd>{item.value}</dd>
          </div>
        ))}
      </dl>
      {hasFacilities && (
        <div className="finance-interest__facilities">
          <h3 className="finance-interest__subtitle">
            {t('finance.loanInterest.facilities.title')}
          </h3>
          <div className="finance-interest__table-wrapper">
            <table className="finance-interest__table finance-interest__facility-table">
              <caption className="finance-interest__caption">
                {t('finance.loanInterest.facilities.caption')}
              </caption>
              <thead>
                <tr>
                  <th scope="col">
                    {t('finance.loanInterest.facilities.headers.name')}
                  </th>
                  <th scope="col">
                    {t('finance.loanInterest.facilities.headers.amount')}
                  </th>
                  <th scope="col">
                    {t('finance.loanInterest.facilities.headers.rate')}
                  </th>
                  <th scope="col">
                    {t('finance.loanInterest.facilities.headers.periods')}
                  </th>
                  <th scope="col">
                    {t('finance.loanInterest.facilities.headers.capitalised')}
                  </th>
                  <th scope="col">
                    {t('finance.loanInterest.facilities.headers.interest')}
                  </th>
                  <th scope="col">
                    {t('finance.loanInterest.facilities.headers.upfront')}
                  </th>
                  <th scope="col">
                    {t('finance.loanInterest.facilities.headers.exit')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {schedule.facilities.map((facility) => (
                  <tr key={facility.name}>
                    <th scope="row">{facility.name}</th>
                    <td>
                      {formatCurrency(
                        facility.amount,
                        schedule.currency,
                        locale,
                        fallback,
                      )}
                    </td>
                    <td>
                      {formatNumber(facility.interestRate, locale, fallback, {
                        style: 'percent',
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </td>
                    <td>{facility.periodsPerYear ?? fallback}</td>
                    <td>
                      {facility.capitalised
                        ? t('finance.loanInterest.totals.capitalisedYes')
                        : t('finance.loanInterest.totals.capitalisedNo')}
                    </td>
                    <td>
                      {formatCurrency(
                        facility.totalInterest,
                        schedule.currency,
                        locale,
                        fallback,
                      )}
                    </td>
                    <td>
                      {formatCurrency(
                        facility.upfrontFee ?? null,
                        schedule.currency,
                        locale,
                        fallback,
                      )}
                    </td>
                    <td>
                      {formatCurrency(
                        facility.exitFee ?? null,
                        schedule.currency,
                        locale,
                        fallback,
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      <div className="finance-interest__table-wrapper">
        <table className="finance-interest__table">
          <caption className="finance-interest__caption">
            {t('finance.loanInterest.table.caption')}
          </caption>
          <thead>
            <tr>
              <th scope="col">
                {t('finance.loanInterest.table.headers.period')}
              </th>
              <th scope="col">
                {t('finance.loanInterest.table.headers.opening')}
              </th>
              <th scope="col">
                {t('finance.loanInterest.table.headers.closing')}
              </th>
              <th scope="col">
                {t('finance.loanInterest.table.headers.average')}
              </th>
              <th scope="col">
                {t('finance.loanInterest.table.headers.interest')}
              </th>
            </tr>
          </thead>
          <tbody>
            {schedule.entries.map((entry, index) => (
              <tr key={`${entry.period}-${index}`}>
                <th scope="row">{entry.period}</th>
                <td>
                  {formatCurrency(
                    entry.openingBalance,
                    schedule.currency,
                    locale,
                    fallback,
                  )}
                </td>
                <td>
                  {formatCurrency(
                    entry.closingBalance,
                    schedule.currency,
                    locale,
                    fallback,
                  )}
                </td>
                <td>
                  {formatCurrency(
                    entry.averageBalance,
                    schedule.currency,
                    locale,
                    fallback,
                  )}
                </td>
                <td>
                  {formatCurrency(
                    entry.interestAccrued,
                    schedule.currency,
                    locale,
                    fallback,
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default FinanceLoanInterest
