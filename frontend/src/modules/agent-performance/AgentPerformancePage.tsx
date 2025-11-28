import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { AppLayout } from '../../App'
import { useTranslation } from '../../i18n'

import { TimelinePanel } from './components'
import { useDeals, useTimeline, useAnalytics, useBenchmarks } from './hooks'
import { STAGE_TRANSLATION_KEYS } from './types'
import {
  formatCurrency,
  formatDays,
  formatPercent,
  formatShortCurrency,
} from './utils/formatters'

export default function AgentPerformancePage() {
  const { t, i18n } = useTranslation()
  const locale = i18n.language

  const {
    loadingDeals,
    dealError,
    selectedDealId,
    selectedDeal,
    groupedDeals,
    stageOrder,
    setSelectedDealId,
  } = useDeals({ t })

  const { timeline, timelineLoading, timelineError } = useTimeline({
    selectedDealId,
    t,
  })

  const selectedAgentId = selectedDeal?.agentId ?? null
  const primaryCurrency = selectedDeal?.estimatedValueCurrency ?? 'SGD'

  const { latestSnapshot, analyticsLoading, analyticsError, trendData } =
    useAnalytics({
      selectedAgentId,
      locale,
      t,
    })

  const fallbackText = t('agentPerformance.common.fallback')

  const {
    benchmarksLoading,
    benchmarksError,
    benchmarkComparisons,
    benchmarksHasContent,
  } = useBenchmarks({
    selectedDeal,
    latestSnapshot,
    locale,
    fallbackText,
    t,
  })

  const loadingText = t('common.loading')
  const analyticsLoadingText = t('agentPerformance.analytics.loading')
  const benchmarksLoadingText = t('agentPerformance.analytics.benchmarksLoading')

  const analyticsHasContent =
    Boolean(latestSnapshot) ||
    trendData.length > 0 ||
    analyticsLoading ||
    analyticsError ||
    benchmarksHasContent

  return (
    <AppLayout
      title={t('agentPerformance.title')}
      subtitle={t('agentPerformance.subtitle')}
    >
      <div className="agent-performance">
        <section className="agent-performance__kanban">
          {dealError && (
            <p className="agent-performance__error agent-performance__error--inline">
              {dealError}
            </p>
          )}
          {stageOrder.map((stage) => {
            const items = groupedDeals[stage] ?? []
            const label =
              t(STAGE_TRANSLATION_KEYS[stage]) ?? STAGE_TRANSLATION_KEYS[stage]
            return (
              <article key={stage} className="agent-performance__column">
                <header>
                  <h3>{label}</h3>
                  <span className="agent-performance__count">{items.length}</span>
                </header>
                {loadingDeals && (
                  <p className="agent-performance__column-placeholder">
                    {t('common.loading')}
                  </p>
                )}
                {!loadingDeals && items.length === 0 && (
                  <p className="agent-performance__column-placeholder">
                    {fallbackText}
                  </p>
                )}
                <ul>
                  {items.map((deal) => {
                    const isSelected = selectedDealId === deal.id
                    return (
                      <li key={deal.id}>
                        <button
                          type="button"
                          className={`agent-performance__deal${
                            isSelected ? ' agent-performance__deal--selected' : ''
                          }`}
                          onClick={() => setSelectedDealId(deal.id)}
                        >
                          <strong>{deal.title}</strong>
                          {deal.leadSource && <span>{deal.leadSource}</span>}
                          {deal.estimatedValueAmount !== null && (
                            <span>
                              {deal.estimatedValueCurrency}{' '}
                              {deal.estimatedValueAmount.toLocaleString(locale)}
                            </span>
                          )}
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </article>
            )
          })}
        </section>
        <aside className="agent-performance__timeline">
          {dealError && (
            <p className="agent-performance__error">{dealError}</p>
          )}
          {timelineError && !timelineLoading && (
            <p className="agent-performance__error">{timelineError}</p>
          )}
          {!dealError && (
            <TimelinePanel
              events={timeline}
              loading={timelineLoading}
              locale={locale}
              fallbackText={fallbackText}
              loadingText={loadingText}
              auditLabel={t('agentPerformance.timeline.auditLabel')}
              durationLabel={t('agentPerformance.timeline.durationLabel')}
              changedByLabel={t('agentPerformance.timeline.changedBy')}
              noteLabel={t('agentPerformance.timeline.note')}
              hashLabel={t('agentPerformance.timeline.hash')}
              signatureLabel={t('agentPerformance.timeline.signature')}
              stageLabelFor={(stage) =>
                t(STAGE_TRANSLATION_KEYS[stage]) ?? stage
              }
            />
          )}
        </aside>
      </div>
      {analyticsHasContent && (
        <section className="agent-performance__analytics">
          <header className="agent-performance__analytics-header">
            <h3>{t('agentPerformance.analytics.title')}</h3>
            {selectedAgentId && (
              <span className="agent-performance__analytics-agent">
                {t('agentPerformance.analytics.agentLabel', {
                  id: selectedAgentId,
                })}
              </span>
            )}
          </header>
          {analyticsError && (
            <p className="agent-performance__error">{analyticsError}</p>
          )}
          {analyticsLoading && !analyticsError && (
            <p className="agent-performance__analytics-loading">
              {analyticsLoadingText}
            </p>
          )}
          {latestSnapshot && (
            <div className="agent-performance__metrics-grid">
              {[
                {
                  key: 'open',
                  label: t('agentPerformance.analytics.metrics.openDeals'),
                  value: latestSnapshot.dealsOpen.toLocaleString(locale),
                },
                {
                  key: 'won',
                  label: t('agentPerformance.analytics.metrics.closedWon'),
                  value: latestSnapshot.dealsClosedWon.toLocaleString(locale),
                },
                {
                  key: 'gross',
                  label: t(
                    'agentPerformance.analytics.metrics.grossPipelineValue',
                  ),
                  value: formatCurrency(
                    latestSnapshot.grossPipelineValue,
                    primaryCurrency,
                    locale,
                    fallbackText,
                  ),
                },
                {
                  key: 'weighted',
                  label: t(
                    'agentPerformance.analytics.metrics.weightedPipelineValue',
                  ),
                  value: formatCurrency(
                    latestSnapshot.weightedPipelineValue,
                    primaryCurrency,
                    locale,
                    fallbackText,
                  ),
                },
                {
                  key: 'conversion',
                  label: t('agentPerformance.analytics.metrics.conversionRate'),
                  value: formatPercent(latestSnapshot.conversionRate, fallbackText),
                },
                {
                  key: 'cycle',
                  label: t('agentPerformance.analytics.metrics.avgCycleDays'),
                  value: formatDays(latestSnapshot.avgCycleDays, fallbackText),
                },
              ]
                .concat(
                  latestSnapshot.confirmedCommissionAmount !== null
                    ? [
                        {
                          key: 'confirmed',
                          label: t(
                            'agentPerformance.analytics.metrics.confirmedCommission',
                          ),
                          value: formatCurrency(
                            Number(latestSnapshot.confirmedCommissionAmount),
                            primaryCurrency,
                            locale,
                            fallbackText,
                          ),
                        },
                      ]
                    : [],
                )
                .concat(
                  latestSnapshot.disputedCommissionAmount !== null
                    ? [
                        {
                          key: 'disputed',
                          label: t(
                            'agentPerformance.analytics.metrics.disputedCommission',
                          ),
                          value: formatCurrency(
                            Number(latestSnapshot.disputedCommissionAmount),
                            primaryCurrency,
                            locale,
                            fallbackText,
                          ),
                        },
                      ]
                    : [],
                )
                .map((metric) => (
                  <article
                    key={metric.key}
                    className="agent-performance__metric-card"
                  >
                    <h4>{metric.label}</h4>
                    <strong>{metric.value}</strong>
                  </article>
                ))}
            </div>
          )}
          {trendData.length > 0 && (
            <div className="agent-performance__charts">
              <div className="agent-performance__chart-card">
                <h4>
                  {t('agentPerformance.analytics.trend.pipelineHeading')}
                </h4>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="label" />
                    <YAxis
                      tickFormatter={(value) => {
                        const numeric =
                          typeof value === 'number'
                            ? value
                            : Number.parseFloat(String(value))
                        if (Number.isNaN(numeric)) {
                          return ''
                        }
                        return formatShortCurrency(numeric, primaryCurrency, locale)
                      }}
                    />
                    <Tooltip
                      formatter={(value: number | string, name: string) => {
                        const numeric =
                          typeof value === 'number'
                            ? value
                            : Number.parseFloat(String(value))
                        if (name === 'gross' || name === 'weighted') {
                          return [
                            formatCurrency(
                              Number.isNaN(numeric) ? null : numeric,
                              primaryCurrency,
                              locale,
                              fallbackText,
                            ),
                            t(
                              name === 'gross'
                                ? 'agentPerformance.analytics.trend.grossLabel'
                                : 'agentPerformance.analytics.trend.weightedLabel',
                            ),
                          ]
                        }
                        return [value, name]
                      }}
                    />
                    <Legend
                      formatter={(value: string) =>
                        t(
                          value === 'gross'
                            ? 'agentPerformance.analytics.trend.grossLabel'
                            : 'agentPerformance.analytics.trend.weightedLabel',
                        )
                      }
                    />
                    <Line
                      type="monotone"
                      dataKey="gross"
                      stroke="#2563eb"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="weighted"
                      stroke="#7c3aed"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="agent-performance__chart-card">
                <h4>
                  {t('agentPerformance.analytics.trend.conversionHeading')}
                </h4>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="label" />
                    <YAxis
                      yAxisId="rate"
                      tickFormatter={(value) => {
                        const numeric =
                          typeof value === 'number'
                            ? value
                            : Number.parseFloat(String(value))
                        if (Number.isNaN(numeric)) {
                          return ''
                        }
                        return `${numeric.toFixed(0)}%`
                      }}
                    />
                    <YAxis
                      yAxisId="cycle"
                      orientation="right"
                      tickFormatter={(value) => {
                        const numeric =
                          typeof value === 'number'
                            ? value
                            : Number.parseFloat(String(value))
                        if (Number.isNaN(numeric)) {
                          return ''
                        }
                        return formatDays(numeric, fallbackText)
                      }}
                    />
                    <Tooltip
                      formatter={(value: number | string, name: string) => {
                        const numeric =
                          typeof value === 'number'
                            ? value
                            : Number.parseFloat(String(value))
                        if (name === 'conversion') {
                          return [
                            Number.isNaN(numeric)
                              ? fallbackText
                              : `${numeric.toFixed(1)}%`,
                            t(
                              'agentPerformance.analytics.trend.conversionSeriesLabel',
                            ),
                          ]
                        }
                        if (name === 'cycle') {
                          return [
                            Number.isNaN(numeric)
                              ? fallbackText
                              : formatDays(numeric, fallbackText),
                            t(
                              'agentPerformance.analytics.trend.cycleSeriesLabel',
                            ),
                          ]
                        }
                        return [value, name]
                      }}
                    />
                    <Legend
                      formatter={(value: string) =>
                        t(
                          value === 'conversion'
                            ? 'agentPerformance.analytics.trend.conversionSeriesLabel'
                            : 'agentPerformance.analytics.trend.cycleSeriesLabel',
                        )
                      }
                    />
                    <Line
                      yAxisId="rate"
                      type="monotone"
                      dataKey="conversion"
                      stroke="#16a34a"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      yAxisId="cycle"
                      type="monotone"
                      dataKey="cycle"
                      stroke="#9333ea"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          {benchmarksHasContent && (
            <div className="agent-performance__benchmarks">
              <h4>{t('agentPerformance.analytics.benchmarks.title')}</h4>
              {benchmarksError && (
                <p className="agent-performance__error">{benchmarksError}</p>
              )}
              {benchmarksLoading && !benchmarksError && (
                <p className="agent-performance__analytics-loading">
                  {benchmarksLoadingText}
                </p>
              )}
              {benchmarkComparisons.length > 0 && (
                <ul className="agent-performance__benchmark-list">
                  {benchmarkComparisons.map((item) => (
                    <li key={item.key}>
                      <header>
                        <span>{item.label}</span>
                        <strong>{item.actual}</strong>
                      </header>
                      {(item.benchmark || item.deltaText) && (
                        <p>
                          {item.benchmark && item.cohort && (
                            <span>
                              {t(
                                'agentPerformance.analytics.benchmarks.versus',
                                {
                                  cohort: item.cohort,
                                  value: item.benchmark,
                                },
                              )}
                            </span>
                          )}
                          {item.deltaText && item.deltaText !== '' && (
                            <span
                              className={`agent-performance__benchmark-delta${
                                item.deltaPositive
                                  ? ' agent-performance__benchmark-delta--positive'
                                  : ' agent-performance__benchmark-delta--negative'
                              }`}
                            >
                              {item.deltaText}
                            </span>
                          )}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </section>
      )}
    </AppLayout>
  )
}
