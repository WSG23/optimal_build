import { useEffect, useMemo, useState } from 'react'
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
import { AppLayout } from '../App'
import { useTranslation } from '../i18n'
import {
  DEAL_STAGE_ORDER,
  type DealStage,
  type DealSummary,
  type DealTimelineEvent,
  fetchDealTimeline,
  fetchDeals,
} from '../api/deals'
import {
  type PerformanceBenchmarkEntry,
  type PerformanceSnapshot,
  fetchBenchmarks,
  fetchLatestSnapshot,
  fetchSnapshotsHistory,
} from '../api/performance'

function formatDuration(seconds: number | null, fallback: string): string {
  if (seconds === null || Number.isNaN(seconds)) {
    return fallback
  }
  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  }
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) {
    return `${minutes}m`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  if (hours < 24) {
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
  }
  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24
  return remainingHours > 0
    ? `${days}d ${remainingHours}h`
    : `${days}d`
}

function formatDate(value: string, locale: string): string {
  if (!value) {
    return ''
  }
  try {
    const formatter = new Intl.DateTimeFormat(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
    return formatter.format(new Date(value))
  } catch (error) {
    console.warn('Failed to format date', error)
    return value
  }
}

function formatCurrency(
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
    }).format(value)
  } catch (error) {
    console.warn('Failed to format currency', error)
    return `${currency} ${value.toLocaleString(locale)}`
  }
}

function formatShortCurrency(
  value: number | null,
  currency: string,
  locale: string,
): string {
  if (value === null || Number.isNaN(value)) {
    return ''
  }
  const abs = Math.abs(value)
  const suffix =
    abs >= 1_000_000_000
      ? { divisor: 1_000_000_000, label: 'B' }
      : abs >= 1_000_000
      ? { divisor: 1_000_000, label: 'M' }
      : abs >= 1_000
      ? { divisor: 1_000, label: 'K' }
      : null

  if (!suffix) {
    return formatCurrency(value, currency, locale, '')
  }
  const scaled = value / suffix.divisor
  try {
    const formatted = new Intl.NumberFormat(locale, {
      maximumFractionDigits: 1,
    }).format(scaled)
    return `${formatted}${suffix.label}`
  } catch (error) {
    console.warn('Failed to format short currency', error)
    return `${(Math.round(scaled * 10) / 10).toString()}${suffix.label}`
  }
}

function formatPercent(
  value: number | null,
  fallback: string,
  fractionDigits = 1,
): string {
  if (value === null || Number.isNaN(value)) {
    return fallback
  }
  const percentValue = Math.abs(value) <= 1 ? value * 100 : value
  return `${percentValue.toFixed(fractionDigits)}%`
}

function formatDays(value: number | null, fallback: string): string {
  if (value === null || Number.isNaN(value)) {
    return fallback
  }
  return `${value.toFixed(0)}d`
}

function formatPercentagePointDelta(delta: number | null): string {
  if (delta === null || Number.isNaN(delta)) {
    return ''
  }
  const sign = delta > 0 ? '+' : ''
  return `${sign}${delta.toFixed(1)} pts`
}

function formatDayDelta(delta: number | null): string {
  if (delta === null || Number.isNaN(delta)) {
    return ''
  }
  const sign = delta > 0 ? '+' : ''
  return `${sign}${delta.toFixed(0)}d`
}

function toPercentValue(value: number | null): number | null {
  if (value === null || Number.isNaN(value)) {
    return null
  }
  return Math.abs(value) <= 1 ? value * 100 : value
}

function formatCurrencyDelta(
  delta: number | null,
  currency: string,
  locale: string,
): string {
  if (delta === null || Number.isNaN(delta)) {
    return ''
  }
  const sign = delta > 0 ? '+' : delta < 0 ? '-' : ''
  const magnitude = Math.abs(delta)
  try {
    const formatted = new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(magnitude)
    return `${sign}${formatted}`
  } catch (error) {
    console.warn('Failed to format currency delta', error)
    const fallback = magnitude.toLocaleString(locale, {
      maximumFractionDigits: 0,
    })
    return `${sign}${currency} ${fallback}`
  }
}

const STAGE_TRANSLATION_KEYS: Record<DealStage, string> = {
  lead_captured: 'agentPerformance.stages.lead_captured',
  qualification: 'agentPerformance.stages.qualification',
  needs_analysis: 'agentPerformance.stages.needs_analysis',
  proposal: 'agentPerformance.stages.proposal',
  negotiation: 'agentPerformance.stages.negotiation',
  agreement: 'agentPerformance.stages.agreement',
  due_diligence: 'agentPerformance.stages.due_diligence',
  awaiting_closure: 'agentPerformance.stages.awaiting_closure',
  closed_won: 'agentPerformance.stages.closed_won',
  closed_lost: 'agentPerformance.stages.closed_lost',
}

interface TimelinePanelProps {
  events: DealTimelineEvent[]
  loading: boolean
  locale: string
  fallbackText: string
  loadingText: string
  auditLabel: string
  durationLabel: string
  changedByLabel: string
  noteLabel: string
  hashLabel: string
  signatureLabel: string
}

function TimelinePanel({
  events,
  loading,
  locale,
  fallbackText,
  loadingText,
  auditLabel,
  durationLabel,
  changedByLabel,
  noteLabel,
  hashLabel,
  signatureLabel,
  stageLabelFor,
}: TimelinePanelProps & {
  stageLabelFor: (stage: DealStage) => string
}) {
  if (loading) {
    return (
      <p className="agent-performance__timeline-loading">{loadingText}</p>
    )
  }

  if (events.length === 0) {
    return <p className="agent-performance__timeline-empty">{fallbackText}</p>
  }

  return (
    <ol className="agent-performance__timeline-list">
      {events.map((event) => (
        <li key={event.id} className="agent-performance__timeline-item">
          <header>
            <span className="agent-performance__timeline-stage">
              {stageLabelFor(event.toStage)}
            </span>
            <span className="agent-performance__timeline-date">
              {formatDate(event.recordedAt, locale) || fallbackText}
            </span>
          </header>
          <dl>
            <div>
              <dt>{durationLabel}</dt>
              <dd>{formatDuration(event.durationSeconds, fallbackText)}</dd>
            </div>
            <div>
              <dt>{changedByLabel}</dt>
              <dd>{event.changedBy ?? fallbackText}</dd>
            </div>
            <div>
              <dt>{noteLabel}</dt>
              <dd>{event.note ?? fallbackText}</dd>
            </div>
            <div>
              <dt>{auditLabel}</dt>
              <dd>
                {event.auditLog ? (
                  <div className="agent-performance__audit">
                    <p>
                      <strong>{hashLabel}</strong>{' '}
                      <span>{event.auditLog.hash}</span>
                    </p>
                    <p>
                      <strong>{signatureLabel}</strong>{' '}
                      <span>{event.auditLog.signature}</span>
                    </p>
                  </div>
                ) : (
                  fallbackText
                )}
              </dd>
            </div>
          </dl>
        </li>
      ))}
    </ol>
  )
}

function groupDealsByStage(deals: DealSummary[]): Record<DealStage, DealSummary[]> {
  return deals.reduce<Record<DealStage, DealSummary[]>>((acc, deal) => {
    const stage = deal.pipelineStage
    const bucket = acc[stage] ?? []
    bucket.push(deal)
    acc[stage] = bucket
    return acc
  }, {} as Record<DealStage, DealSummary[]>)
}

export default function AgentPerformancePage() {
  const { t, i18n } = useTranslation()
  const locale = i18n.language
  const [deals, setDeals] = useState<DealSummary[]>([])
  const [loadingDeals, setLoadingDeals] = useState<boolean>(false)
  const [dealError, setDealError] = useState<string | null>(null)
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null)
  const [timeline, setTimeline] = useState<DealTimelineEvent[]>([])
  const [timelineLoading, setTimelineLoading] = useState<boolean>(false)
  const [timelineError, setTimelineError] = useState<string | null>(null)
  const [latestSnapshot, setLatestSnapshot] = useState<PerformanceSnapshot | null>(
    null,
  )
  const [snapshotHistory, setSnapshotHistory] = useState<PerformanceSnapshot[]>(
    [],
  )
  const [analyticsLoading, setAnalyticsLoading] = useState<boolean>(false)
  const [analyticsError, setAnalyticsError] = useState<string | null>(null)
  const [benchmarks, setBenchmarks] = useState<{
    conversion: PerformanceBenchmarkEntry | null
    cycle: PerformanceBenchmarkEntry | null
    pipeline: PerformanceBenchmarkEntry | null
  }>({
    conversion: null,
    cycle: null,
    pipeline: null,
  })
  const [benchmarksLoading, setBenchmarksLoading] = useState<boolean>(false)
  const [benchmarksError, setBenchmarksError] = useState<string | null>(null)

  const selectedDeal = useMemo(
    () => deals.find((deal) => deal.id === selectedDealId) ?? null,
    [deals, selectedDealId],
  )
  const selectedAgentId = selectedDeal?.agentId ?? null
  const primaryCurrency = selectedDeal?.estimatedValueCurrency ?? 'SGD'

  useEffect(() => {
    let abort = new AbortController()
    setLoadingDeals(true)
    setDealError(null)
    fetchDeals(abort.signal)
      .then((payload) => {
        setDeals(payload)
        if (payload.length > 0) {
          setSelectedDealId(payload[0].id)
        } else {
          setSelectedDealId(null)
        }
      })
      .catch((error: unknown) => {
        console.error('Failed to load deals', error)
        setDealError(t('agentPerformance.errors.loadDeals'))
      })
      .finally(() => {
        setLoadingDeals(false)
      })
    return () => {
      abort.abort()
    }
  }, [t])

  useEffect(() => {
    if (!selectedDealId) {
      setTimeline([])
      return
    }
    let abort = new AbortController()
    setTimelineLoading(true)
    setTimelineError(null)
    fetchDealTimeline(selectedDealId, abort.signal)
      .then((events) => {
        setTimeline(events)
      })
      .catch((error: unknown) => {
        console.error('Failed to load timeline', error)
        setTimelineError(t('agentPerformance.errors.loadTimeline'))
      })
      .finally(() => {
        setTimelineLoading(false)
      })
    return () => {
      abort.abort()
    }
  }, [selectedDealId, t])

  useEffect(() => {
    if (!selectedAgentId) {
      setLatestSnapshot(null)
      setSnapshotHistory([])
      setAnalyticsError(null)
      setAnalyticsLoading(false)
      return
    }
    const controller = new AbortController()
    let isActive = true
    setAnalyticsLoading(true)
    setAnalyticsError(null)
    ;(async () => {
      try {
        const [latest, history] = await Promise.all([
          fetchLatestSnapshot(selectedAgentId, controller.signal),
          fetchSnapshotsHistory(selectedAgentId, 30, controller.signal),
        ])
        if (!isActive) {
          return
        }
        setLatestSnapshot(latest)
        setSnapshotHistory(history)
      } catch (error) {
        if ((error as { name?: string }).name === 'AbortError') {
          return
        }
        console.error('Failed to load agent analytics', error)
        if (!controller.signal.aborted && isActive) {
          setAnalyticsError(t('agentPerformance.analytics.errors.analytics'))
        }
        setLatestSnapshot(null)
        setSnapshotHistory([])
      } finally {
        if (isActive) {
          setAnalyticsLoading(false)
        }
      }
    })()
    return () => {
      isActive = false
      controller.abort()
    }
  }, [selectedAgentId, t])

  useEffect(() => {
    if (!selectedDeal) {
      setBenchmarks({
        conversion: null,
        cycle: null,
        pipeline: null,
      })
      setBenchmarksError(null)
      setBenchmarksLoading(false)
      return
    }
    const controller = new AbortController()
    let isActive = true
    setBenchmarksLoading(true)
    setBenchmarksError(null)
    ;(async () => {
      try {
        const [conversion, cycle, pipeline] = await Promise.all([
          fetchBenchmarks('conversion_rate', {
            assetType: selectedDeal.assetType,
            dealType: selectedDeal.dealType,
            signal: controller.signal,
          }),
          fetchBenchmarks('avg_cycle_days', {
            assetType: selectedDeal.assetType,
            dealType: selectedDeal.dealType,
            signal: controller.signal,
          }),
          fetchBenchmarks('pipeline_weighted_value', {
            signal: controller.signal,
          }),
        ])
        if (!isActive) {
          return
        }
        setBenchmarks({
          conversion: conversion[0] ?? null,
          cycle: cycle[0] ?? null,
          pipeline: pipeline[0] ?? null,
        })
      } catch (error) {
        if ((error as { name?: string }).name === 'AbortError') {
          return
        }
        console.error('Failed to load performance benchmarks', error)
        if (!controller.signal.aborted && isActive) {
          setBenchmarksError(
            t('agentPerformance.analytics.errors.benchmarks'),
          )
        }
        setBenchmarks({
          conversion: null,
          cycle: null,
          pipeline: null,
        })
      } finally {
        if (isActive) {
          setBenchmarksLoading(false)
        }
      }
    })()

    return () => {
      isActive = false
      controller.abort()
    }
  }, [selectedDeal, t])

  const groupedDeals = useMemo(() => groupDealsByStage(deals), [deals])

  const fallbackText = t('agentPerformance.common.fallback')
  const auditLabel = t('agentPerformance.timeline.auditLabel')
  const durationLabel = t('agentPerformance.timeline.durationLabel')
  const changedByLabel = t('agentPerformance.timeline.changedBy')
  const noteLabel = t('agentPerformance.timeline.note')
  const hashLabel = t('agentPerformance.timeline.hash')
  const signatureLabel = t('agentPerformance.timeline.signature')
  const loadingText = t('common.loading')
  const analyticsLoadingText = t('agentPerformance.analytics.loading')
  const benchmarksLoadingText = t('agentPerformance.analytics.benchmarksLoading')

  const trendData = useMemo(() => {
    if (snapshotHistory.length === 0) {
      return []
    }
    const ordered = [...snapshotHistory].sort((a, b) => {
      const left = new Date(a.asOfDate).getTime()
      const right = new Date(b.asOfDate).getTime()
      return left - right
    })
    return ordered.map((snapshot) => {
      let label = snapshot.asOfDate
      try {
        label = new Intl.DateTimeFormat(locale, {
          month: 'short',
          day: 'numeric',
        }).format(new Date(snapshot.asOfDate))
      } catch (error) {
        console.warn('Failed to format chart label', error)
      }
      return {
        label,
        gross: snapshot.grossPipelineValue,
        weighted: snapshot.weightedPipelineValue,
        conversion: toPercentValue(snapshot.conversionRate ?? null),
        cycle: snapshot.avgCycleDays,
      }
    })
  }, [snapshotHistory, locale])

  const conversionBenchmark = benchmarks.conversion
  const cycleBenchmark = benchmarks.cycle
  const pipelineBenchmark = benchmarks.pipeline

  const conversionActualPercent = toPercentValue(
    latestSnapshot?.conversionRate ?? null,
  )
  const conversionBenchmarkPercent = toPercentValue(
    conversionBenchmark?.valueNumeric ?? null,
  )
  const conversionDelta =
    conversionActualPercent !== null && conversionBenchmarkPercent !== null
      ? conversionActualPercent - conversionBenchmarkPercent
      : null

  const cycleActual = latestSnapshot?.avgCycleDays ?? null
  const cycleBenchmarkValue = cycleBenchmark?.valueNumeric ?? null
  const cycleDelta =
    cycleActual !== null && cycleBenchmarkValue !== null
      ? cycleActual - cycleBenchmarkValue
      : null

  const pipelineActual = latestSnapshot?.weightedPipelineValue ?? null
  const pipelineBenchmarkValue = pipelineBenchmark?.valueNumeric ?? null
  const pipelineDelta =
    pipelineActual !== null && pipelineBenchmarkValue !== null
      ? pipelineActual - pipelineBenchmarkValue
      : null

  const analyticsHasContent =
    Boolean(latestSnapshot) ||
    trendData.length > 0 ||
    analyticsLoading ||
    analyticsError ||
    benchmarksHasContent

  const benchmarksHasContent =
    benchmarksLoading ||
    benchmarksError ||
    Boolean(conversionBenchmark || cycleBenchmark || pipelineBenchmark)

  const benchmarkComparisons = useMemo(() => {
    if (!latestSnapshot) {
      return []
    }

    const cohortLabelFor = (entry: PerformanceBenchmarkEntry | null) => {
      if (!entry) {
        return null
      }
      const key = `agentPerformance.analytics.benchmarks.cohort.${entry.cohort}`
      const translated = t(key)
      if (translated === key) {
        return entry.cohort.replace(/_/g, ' ')
      }
      return translated
    }

    const items: Array<{
      key: string
      label: string
      actual: string
      benchmark: string | null
      cohort: string | null
      deltaText: string
      deltaPositive: boolean
    }> = []

    if (conversionBenchmark && conversionActualPercent !== null) {
      const benchmarkValue =
        conversionBenchmarkPercent !== null
          ? formatPercent(conversionBenchmarkPercent / 100, fallbackText)
          : null
      const deltaText = formatPercentagePointDelta(conversionDelta)
      items.push({
        key: 'conversion',
        label: t('agentPerformance.analytics.benchmarks.conversion'),
        actual: formatPercent(latestSnapshot.conversionRate, fallbackText),
        benchmark: benchmarkValue,
        cohort: cohortLabelFor(conversionBenchmark),
        deltaText,
        deltaPositive: (conversionDelta ?? 0) >= 0,
      })
    }

    if (cycleBenchmark && cycleActual !== null) {
      const benchmarkValue =
        cycleBenchmarkValue !== null
          ? formatDays(cycleBenchmarkValue, fallbackText)
          : null
      const deltaText = formatDayDelta(cycleDelta)
      items.push({
        key: 'cycle',
        label: t('agentPerformance.analytics.benchmarks.cycle'),
        actual: formatDays(cycleActual, fallbackText),
        benchmark: benchmarkValue,
        cohort: cohortLabelFor(cycleBenchmark),
        deltaText,
        deltaPositive: (cycleDelta ?? 0) <= 0,
      })
    }

    if (pipelineBenchmark && pipelineActual !== null) {
      const benchmarkValue =
        pipelineBenchmarkValue !== null
          ? formatCurrency(
              pipelineBenchmarkValue,
              primaryCurrency,
              locale,
              fallbackText,
            )
          : null
      const deltaText = formatCurrencyDelta(
        pipelineDelta,
        primaryCurrency,
        locale,
      )
      items.push({
        key: 'pipeline',
        label: t('agentPerformance.analytics.benchmarks.pipeline'),
        actual: formatCurrency(
          pipelineActual,
          primaryCurrency,
          locale,
          fallbackText,
        ),
        benchmark: benchmarkValue,
        cohort: cohortLabelFor(pipelineBenchmark),
        deltaText,
        deltaPositive: (pipelineDelta ?? 0) >= 0,
      })
    }

    return items
  }, [
    conversionActualPercent,
    conversionBenchmark,
    conversionBenchmarkPercent,
    conversionDelta,
    cycleActual,
    cycleBenchmark,
    cycleBenchmarkValue,
    cycleDelta,
    fallbackText,
    latestSnapshot,
    locale,
    pipelineActual,
    pipelineBenchmark,
    pipelineBenchmarkValue,
    pipelineDelta,
    primaryCurrency,
    t,
  ])


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
          {DEAL_STAGE_ORDER.map((stage) => {
            const items = groupedDeals[stage] ?? []
            const label =
              t(STAGE_TRANSLATION_KEYS[stage]) ?? STAGE_TRANSLATION_KEYS[stage]
            return (
              <article key={stage} className="agent-performance__column">
                <header>
                  <h3>{label}</h3>
                  <span className="agent-performance__count">
                    {items.length}
                  </span>
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
                            isSelected
                              ? ' agent-performance__deal--selected'
                              : ''
                          }`}
                          onClick={() => setSelectedDealId(deal.id)}
                        >
                          <strong>{deal.title}</strong>
                          {deal.leadSource && (
                            <span>{deal.leadSource}</span>
                          )}
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
              auditLabel={auditLabel}
              durationLabel={durationLabel}
              changedByLabel={changedByLabel}
              noteLabel={noteLabel}
              hashLabel={hashLabel}
              signatureLabel={signatureLabel}
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
                  value: formatPercent(
                    latestSnapshot.conversionRate,
                    fallbackText,
                  ),
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
                        return formatShortCurrency(
                          numeric,
                          primaryCurrency,
                          locale,
                        )
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
