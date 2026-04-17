/**
 * Agents Capture Context Panel
 *
 * Displays contextual information after a GPS capture: map, amenities,
 * market intelligence, and professional pack generation.
 * Extracted from AgentsGpsCapturePage for component size management.
 */

import { useMemo, type FormEvent } from 'react'

import type {
  GpsCaptureSummary,
  MarketIntelligenceSummary,
  ProfessionalPackSummary,
  ProfessionalPackType,
} from '../api/agents'
import { useTranslation } from '../i18n'
import {
  PACK_OPTIONS,
  formatDateDisplay,
  formatFileSize,
} from './agentsCaptureUtils'

// Inline QuickAnalysisMap import from parent - passed as a render prop instead
// to avoid circular dependency with Google Maps script loading

interface AgentsCaptureContextPanelProps {
  result: GpsCaptureSummary
  marketReport: MarketIntelligenceSummary | null
  marketLoading: boolean
  marketError: string | null
  packSummary: ProfessionalPackSummary | null
  packLoading: boolean
  packError: string | null
  packNotice: string | null
  packType: ProfessionalPackType
  setPackType: (type: ProfessionalPackType) => void
  onPackSubmit: (event: FormEvent<HTMLFormElement>) => void
  mapElement: React.ReactNode
}

export function AgentsCaptureContextPanel({
  result,
  marketReport,
  marketLoading,
  marketError,
  packSummary,
  packLoading,
  packError,
  packNotice,
  packType,
  setPackType,
  onPackSubmit,
  mapElement,
}: AgentsCaptureContextPanelProps) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language ?? 'en'

  const selectedPackOption = useMemo(
    () =>
      PACK_OPTIONS.find((option) => option.value === packType) ??
      PACK_OPTIONS[0],
    [packType],
  )

  return (
    <section className="agents-capture__context">
      <div className="agents-capture__map">
        <h4>{t('agentsCapture.context.mapTitle')}</h4>
        {mapElement}
      </div>
      {result.nearbyAmenities && (
        <aside className="agents-capture__amenities">
          <h4>{t('agentsCapture.context.amenitiesTitle')}</h4>
          <ul>
            {[
              {
                key: 'mrtStations' as const,
                label: t('agentsCapture.context.amenities.mrt'),
              },
              {
                key: 'busStops' as const,
                label: t('agentsCapture.context.amenities.bus'),
              },
              {
                key: 'schools' as const,
                label: t('agentsCapture.context.amenities.schools'),
              },
              {
                key: 'shoppingMalls' as const,
                label: t('agentsCapture.context.amenities.malls'),
              },
              {
                key: 'parks' as const,
                label: t('agentsCapture.context.amenities.parks'),
              },
            ].map(({ key, label }) => {
              const items = result.nearbyAmenities?.[key] ?? []
              if (!items.length) {
                return null
              }
              const nearest = items[0]
              return (
                <li key={key}>
                  <strong>{label}</strong>
                  {nearest.distanceM != null
                    ? t('agentsCapture.context.amenities.itemWithDistance', {
                        name: nearest.name,
                        distance: new Intl.NumberFormat(locale, {
                          maximumFractionDigits: 0,
                        }).format(nearest.distanceM),
                      })
                    : t('agentsCapture.context.amenities.item', {
                        name: nearest.name,
                      })}
                </li>
              )
            })}
          </ul>
        </aside>
      )}
      <aside className="agents-capture__market">
        <h4>{t('agentsCapture.market.title')}</h4>
        {marketLoading && (
          <p className="agents-capture__status">
            {t('agentsCapture.market.loading')}
          </p>
        )}
        {marketError && (
          <p className="agents-capture__error agents-capture__error--inline">
            {t('agentsCapture.market.error', { message: marketError })}
          </p>
        )}
        {marketReport && (
          <MarketReportDisplay summary={marketReport} locale={locale} />
        )}
      </aside>
      <aside className="agents-capture__pack">
        <h4>{t('agentsCapture.pack.title')}</h4>
        <p className="agents-capture__status">
          {t('agentsCapture.pack.subtitle')}
        </p>
        <form className="agents-capture__pack-form" onSubmit={onPackSubmit}>
          <label className="agents-capture__pack-field">
            <span>{t('agentsCapture.pack.selectLabel')}</span>
            <select
              value={packType}
              onChange={(event) =>
                setPackType(event.target.value as ProfessionalPackType)
              }
            >
              {PACK_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {t(option.labelKey)}
                </option>
              ))}
            </select>
          </label>
          <p className="agents-capture__pack-description">
            {t(selectedPackOption.descriptionKey)}
          </p>
          <button
            type="submit"
            className="agents-capture__pack-button"
            disabled={packLoading}
          >
            {packLoading
              ? t('agentsCapture.pack.generateLoading')
              : t('agentsCapture.pack.generate')}
          </button>
        </form>
        {packError && (
          <p className="agents-capture__error agents-capture__error--inline">
            {t('agentsCapture.pack.error', { message: packError })}
          </p>
        )}
        {packSummary && (
          <div className="agents-capture__pack-result">
            <p className="agents-capture__status">
              {t('agentsCapture.pack.generatedAt', {
                timestamp: new Date(packSummary.generatedAt).toLocaleString(
                  locale,
                ),
              })}
            </p>
            <p className="agents-capture__status">
              {t('agentsCapture.pack.size', {
                size: formatFileSize(packSummary.sizeBytes, locale),
              })}
            </p>
            {packSummary.downloadUrl ? (
              <a
                href={packSummary.downloadUrl}
                className="agents-capture__pack-download"
                target="_blank"
                rel="noopener noreferrer"
              >
                {t('agentsCapture.pack.downloadCta', {
                  filename: packSummary.filename,
                })}
              </a>
            ) : (
              <p className="agents-capture__status">
                {t('agentsCapture.pack.noDownload')}
              </p>
            )}
            {packNotice && (
              <p className="agents-capture__status">{packNotice}</p>
            )}
          </div>
        )}
      </aside>
    </section>
  )
}

// Inline market report display
function MarketReportDisplay({
  summary,
  locale,
}: {
  summary: MarketIntelligenceSummary
  locale: string
}) {
  const { t } = useTranslation()
  const report = summary.report ?? {}
  const comparables =
    (report.comparables_analysis as Record<string, unknown>) ?? {}
  const transactions =
    typeof comparables.transaction_count === 'number'
      ? comparables.transaction_count
      : null
  const propertyType =
    typeof report.property_type === 'string' ? report.property_type : null
  const location = typeof report.location === 'string' ? report.location : null
  const periodData = report.period as
    | { start?: string | null; end?: string | null }
    | undefined
  const periodStart = formatDateDisplay(periodData?.start, locale)
  const periodEnd = formatDateDisplay(periodData?.end, locale)
  const generatedAt = formatDateDisplay(report.generated_at, locale)

  const metrics = [
    {
      key: 'propertyType',
      label: t('agentsCapture.market.propertyType'),
      value: propertyType ?? '—',
    },
    {
      key: 'location',
      label: t('agentsCapture.market.location'),
      value: location ?? '—',
    },
    {
      key: 'period',
      label: t('agentsCapture.market.period'),
      value:
        periodStart && periodEnd
          ? `${periodStart} – ${periodEnd}`
          : (periodStart ?? periodEnd ?? '—'),
    },
    {
      key: 'transactions',
      label: t('agentsCapture.market.transactions'),
      value:
        transactions !== null
          ? new Intl.NumberFormat(locale).format(transactions)
          : '—',
    },
  ]

  return (
    <>
      <dl className="agents-capture__market-metrics">
        {metrics.map(({ key, label, value }) => (
          <div key={key} className="agents-capture__market-row">
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      {generatedAt && (
        <p className="agents-capture__status">
          {t('agentsCapture.market.generatedAt', {
            timestamp: generatedAt,
          })}
        </p>
      )}
    </>
  )
}
