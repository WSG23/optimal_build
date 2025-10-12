import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import {
  DEAL_STAGE_ORDER,
  fetchDealCommissions,
  fetchDealTimeline,
  fetchDeals,
  type DealCommission,
  type DealSummary,
} from '../../../api/deals'
import {
  fetchBenchmarks,
  fetchLatestSnapshot,
  fetchSnapshotsHistory,
  type PerformanceBenchmarkEntry,
  type PerformanceSnapshot,
} from '../../../api/performance'
import { PipelineBoard } from './components/PipelineBoard'
import { DealInsightsPanel } from './components/DealInsightsPanel'
import { AnalyticsPanel } from './components/AnalyticsPanel'
import { RoiPanel } from './components/RoiPanel'
import type {
  AnalyticsMetric,
  BenchmarkEntry,
  DealSnapshot,
  PipelineColumn,
  RoiSummary,
  StageEvent,
  CommissionEntry,
  TrendPoint,
} from './types'

const EMPTY_ROI_SUMMARY: RoiSummary = {
  projectCount: 0,
  totalReviewHoursSaved: null,
  averageAutomationScore: null,
  averageAcceptanceRate: null,
  averageSavingsPercent: null,
  bestPaybackWeeks: null,
  projects: [],
}

export function BusinessPerformancePage() {
  const [deals, setDeals] = useState<DealSummary[]>([])
  const [columns, setColumns] = useState<PipelineColumn[]>([])
  const [pipelineLoading, setPipelineLoading] = useState(true)
  const [pipelineError, setPipelineError] = useState<string | null>(null)

  const [selectedDealId, setSelectedDealId] = useState<string | null>(null)
  const [selectedDeal, setSelectedDeal] = useState<DealSnapshot | null>(null)
  const [timeline, setTimeline] = useState<StageEvent[]>([])
  const [commissions, setCommissions] = useState<CommissionEntry[]>([])
  const [dealLoading, setDealLoading] = useState(false)
  const [dealError, setDealError] = useState<string | null>(null)

  const [metrics, setMetrics] = useState<AnalyticsMetric[]>([])
  const [trend, setTrend] = useState<TrendPoint[]>([])
  const [benchmarks, setBenchmarks] = useState<BenchmarkEntry[]>([])
  const [roiSummary, setRoiSummary] = useState<RoiSummary>(EMPTY_ROI_SUMMARY)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [analyticsError, setAnalyticsError] = useState<string | null>(null)

  const lastSnapshot = useMemo(
    () => new Date().toLocaleDateString(undefined, { dateStyle: 'medium' }),
    [],
  )

  const buildColumns = useCallback((entries: DealSummary[]): PipelineColumn[] => {
    const stageMap = new Map<string, PipelineColumn>()

    DEAL_STAGE_ORDER.forEach((stage) => {
      stageMap.set(stage, {
        key: stage,
        label: stage.replace('_', ' '),
        deals: [],
        totalCount: 0,
        totalValue: 0,
        weightedValue: 0,
      })
    })

    entries.forEach((deal) => {
      const stage = stageMap.get(deal.pipelineStage) ?? stageMap.get('lead_captured')
      if (!stage) {
        return
      }
      const confidence = deal.confidence ?? 0
      const estimated = deal.estimatedValueAmount ?? 0

      const card = {
        id: deal.id,
        title: deal.title,
        assetType: deal.assetType,
        dealType: deal.dealType,
        estimatedValue: deal.estimatedValueAmount,
        currency: deal.estimatedValueCurrency,
        confidence: deal.confidence,
        latestActivity: formatRelativeDate(deal.updatedAt),
        hasDispute: false,
      }

      stage.deals = [...stage.deals, card]
      stage.totalCount += 1
      stage.totalValue =
        stage.totalValue !== null ? (stage.totalValue ?? 0) + estimated : estimated
      const weightedContribution = estimated * confidence
      stage.weightedValue =
        stage.weightedValue !== null
          ? (stage.weightedValue ?? 0) + weightedContribution
          : weightedContribution
    })

    return Array.from(stageMap.values())
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    async function loadPipeline() {
      try {
        setPipelineLoading(true)
        setPipelineError(null)
        const fetchedDeals = await fetchDeals(controller.signal)
        setDeals(fetchedDeals)
        setColumns(buildColumns(fetchedDeals))
        const firstDeal = fetchedDeals[0]
        if (firstDeal) {
          setSelectedDealId((prev) => prev ?? firstDeal.id)
        } else {
          setSelectedDealId(null)
        }
      } catch (error) {
        if ((error as { name?: string }).name === 'AbortError') {
          return
        }
        console.error('Failed to load pipeline', error)
        setPipelineError('Unable to load pipeline data.')
      } finally {
        setPipelineLoading(false)
      }
    }
    loadPipeline()
    return () => controller.abort()
  }, [buildColumns])

  useEffect(() => {
    if (!selectedDealId) {
      setSelectedDeal(null)
      setTimeline([])
      setCommissions([])
      return
    }
    const controller = new AbortController()
    const dealSummary = deals.find((deal) => deal.id === selectedDealId) ?? null
    setSelectedDeal(
      dealSummary
        ? {
            id: dealSummary.id,
            title: dealSummary.title,
            agentName: dealSummary.agentId,
            leadSource: dealSummary.leadSource,
            stage: dealSummary.pipelineStage,
            expectedCloseDate: dealSummary.expectedCloseDate,
          }
        : null,
    )

    async function loadDealDetails() {
      if (!dealSummary) {
        return
      }
      try {
        setDealLoading(true)
        setDealError(null)
        const [timelineData, commissionData] = await Promise.all([
          fetchDealTimeline(dealSummary.id, controller.signal),
          fetchDealCommissions(dealSummary.id, controller.signal),
        ])
        setTimeline(
          timelineData.map((event) => ({
            id: event.id,
            toStage: event.toStage,
            fromStage: event.fromStage,
            recordedAt: formatDateTime(event.recordedAt),
            durationSeconds: event.durationSeconds,
            changedBy: event.changedBy,
            note: event.note,
            auditHash: event.auditLog?.hash ?? null,
            auditSignature: event.auditLog?.signature ?? null,
          })),
        )
        const mappedCommissions = commissionData.map(mapCommissionEntry)
        setCommissions(mappedCommissions)
        if (mappedCommissions.some((entry) => entry.status === 'disputed')) {
          setColumns((prev) =>
            prev.map((column) => ({
              ...column,
              deals: column.deals.map((deal) =>
                deal.id === dealSummary.id
                  ? { ...deal, hasDispute: true }
                  : deal,
              ),
            })),
          )
        }
      } catch (error) {
        if ((error as { name?: string }).name === 'AbortError') {
          return
        }
        console.error('Failed to load deal details', error)
        setDealError('Unable to load deal timeline or commissions.')
        setTimeline([])
        setCommissions([])
      } finally {
        setDealLoading(false)
      }
    }

    loadDealDetails()
    return () => controller.abort()
  }, [deals, selectedDealId])

  useEffect(() => {
    const agentId =
      selectedDeal?.agentName ??
      deals.find((deal) => deal.id === selectedDealId)?.agentId
    if (!agentId) {
      setMetrics([])
      setTrend([])
      setBenchmarks([])
      setRoiSummary(EMPTY_ROI_SUMMARY)
      return
    }
    const controller = new AbortController()
    async function loadAnalytics() {
      try {
        setAnalyticsLoading(true)
        setAnalyticsError(null)

        const [snapshot, history, conversionBench, cycleBench, pipelineBench] =
          await Promise.all([
            fetchLatestSnapshot(agentId, controller.signal),
            fetchSnapshotsHistory(agentId, 30, controller.signal),
            fetchBenchmarks('conversion_rate', { signal: controller.signal }),
            fetchBenchmarks('avg_cycle_days', { signal: controller.signal }),
            fetchBenchmarks('pipeline_weighted_value', {
              signal: controller.signal,
            }),
          ])

        setMetrics(buildMetrics(snapshot))
        setTrend(buildTrend(history))
        setBenchmarks(
          buildBenchmarks(conversionBench, cycleBench, pipelineBench),
        )
        setRoiSummary(buildRoiSummary(snapshot))
      } catch (error) {
        if ((error as { name?: string }).name === 'AbortError') {
          return
        }
        console.error('Failed to load analytics', error)
        setAnalyticsError('Unable to load analytics and benchmarks.')
        setMetrics([])
        setTrend([])
        setBenchmarks([])
        setRoiSummary(EMPTY_ROI_SUMMARY)
      } finally {
        setAnalyticsLoading(false)
      }
    }
    loadAnalytics()
    return () => controller.abort()
  }, [deals, selectedDeal?.agentName, selectedDealId])

  const handleSelectDeal = useCallback((dealId: string) => {
    setSelectedDealId(dealId)
  }, [])

  return (
    <div className="bp-page">
      <section className="bp-page__summary">
        <div className="bp-summary-card">
          <header>
            <span className="bp-summary-card__label">Last snapshot</span>
            <span className="bp-summary-card__value">{lastSnapshot}</span>
          </header>
          <p className="bp-summary-card__meta">
            Snapshot jobs run nightly. Manual refresh will be available shortly.
          </p>
        </div>
        <div className="bp-summary-card">
          <header>
            <span className="bp-summary-card__label">Open pipeline value</span>
            <span className="bp-summary-card__value">
              {formatCurrency(totalPipeline(columns))}
            </span>
          </header>
          <p className="bp-summary-card__meta">
            Weighted pipeline:{' '}
            <strong>{formatCurrency(totalWeightedPipeline(columns))}</strong>
          </p>
        </div>
        <div className="bp-summary-card">
          <header>
            <span className="bp-summary-card__label">ROI projects tracked</span>
            <span className="bp-summary-card__value">
              {roiSummary.projectCount}
            </span>
          </header>
          <p className="bp-summary-card__meta">
            Automation ROI derives from overlay workflows and audit metrics.
          </p>
        </div>
      </section>

      {pipelineError && (
        <div className="bp-error">
          <p>{pipelineError}</p>
        </div>
      )}
      <div className="bp-page__layout">
        <section className="bp-page__pipeline">
          {pipelineLoading && (
            <p className="bp-loading">Loading pipeline…</p>
          )}
          <PipelineBoard
            columns={columns}
            selectedDealId={selectedDealId}
            onSelectDeal={handleSelectDeal}
          />
        </section>
        <aside className="bp-page__sidebar">
          <DealInsightsPanel
            deal={selectedDeal}
            timeline={timeline}
            commissions={commissions}
          />
          <AnalyticsPanel
            metrics={metrics}
            trend={trend}
            benchmarks={benchmarks}
          />
          <RoiPanel summary={roiSummary} />
          {(dealLoading || analyticsLoading) && (
            <p className="bp-loading">Loading insights…</p>
          )}
          {(dealError || analyticsError) && (
            <div className="bp-error">
              <p>{dealError ?? analyticsError}</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}

function mapCommissionEntry(entry: DealCommission): CommissionEntry {
  return {
    id: entry.id,
    type: entry.commissionType,
    status: entry.status,
    amount: entry.commissionAmount,
    currency: entry.basisCurrency,
    basisAmount: entry.basisAmount,
    confirmedAt: entry.confirmedAt,
    disputedAt: entry.disputedAt,
  }
}

function buildMetrics(snapshot: PerformanceSnapshot | null): AnalyticsMetric[] {
  if (!snapshot) {
    return []
  }
  const currencyFormatter = new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
    maximumFractionDigits: 0,
  })
  return [
    { key: 'dealsOpen', label: 'Open deals', value: snapshot.dealsOpen.toString() },
    {
      key: 'dealsWon',
      label: 'Deals won (30d)',
      value: snapshot.dealsClosedWon.toString(),
    },
    {
      key: 'grossPipeline',
      label: 'Gross pipeline',
      value: snapshot.grossPipelineValue !== null
        ? currencyFormatter.format(snapshot.grossPipelineValue)
        : '—',
      helperText: 'All open opportunities, unweighted.',
    },
    {
      key: 'weightedPipeline',
      label: 'Weighted pipeline',
      value: snapshot.weightedPipelineValue !== null
        ? currencyFormatter.format(snapshot.weightedPipelineValue)
        : '—',
      helperText: 'Weighted by confidence percentage.',
    },
    {
      key: 'conversionRate',
      label: 'Conversion rate',
      value:
        snapshot.conversionRate !== null
          ? `${(snapshot.conversionRate * 100).toFixed(1)}%`
          : '—',
    },
    {
      key: 'avgCycle',
      label: 'Average cycle',
      value:
        snapshot.avgCycleDays !== null
          ? `${snapshot.avgCycleDays.toFixed(0)} days`
          : '—',
    },
    {
      key: 'confirmedCommission',
      label: 'Confirmed commission',
      value:
        snapshot.confirmedCommissionAmount !== null
          ? currencyFormatter.format(snapshot.confirmedCommissionAmount)
          : '—',
    },
    {
      key: 'disputedCommission',
      label: 'Disputed commission',
      value:
        snapshot.disputedCommissionAmount !== null
          ? currencyFormatter.format(snapshot.disputedCommissionAmount)
          : '—',
    },
  ]
}

function buildTrend(history: PerformanceSnapshot[]): TrendPoint[] {
  return history
    .slice()
    .reverse()
    .map((snapshot) => ({
      label: snapshot.asOfDate,
      gross:
        snapshot.grossPipelineValue !== null
          ? snapshot.grossPipelineValue / 1_000_000
          : null,
      weighted:
        snapshot.weightedPipelineValue !== null
          ? snapshot.weightedPipelineValue / 1_000_000
          : null,
      conversion: snapshot.conversionRate,
      cycle: snapshot.avgCycleDays,
    }))
}

function buildBenchmarks(
  conversion: PerformanceBenchmarkEntry[],
  cycle: PerformanceBenchmarkEntry[],
  pipeline: PerformanceBenchmarkEntry[],
): BenchmarkEntry[] {
  const entries: BenchmarkEntry[] = []
  const convertLabel = (cohort: string | null) => cohort ?? 'benchmark'
  if (conversion[0]) {
    entries.push({
      key: 'conversion',
      label: 'Conversion rate',
      actual: conversion[0].valueNumeric !== null
        ? `${(conversion[0].valueNumeric * 100).toFixed(1)}%`
        : conversion[0].valueText ?? '—',
      benchmark:
        conversion[1]?.valueNumeric !== null
          ? `${(conversion[1].valueNumeric * 100).toFixed(1)}%`
          : conversion[1]?.valueText ?? null,
      cohort: convertLabel(conversion[0].cohort),
      deltaText: null,
    })
  }
  if (cycle[0]) {
    entries.push({
      key: 'cycle',
      label: 'Average cycle time',
      actual:
        cycle[0].valueNumeric !== null
          ? `${cycle[0].valueNumeric.toFixed(0)} days`
          : cycle[0].valueText ?? '—',
      benchmark:
        cycle[1]?.valueNumeric !== null
          ? `${cycle[1].valueNumeric.toFixed(0)} days`
          : cycle[1]?.valueText ?? null,
      cohort: convertLabel(cycle[0].cohort),
      deltaText: null,
    })
  }
  if (pipeline[0]) {
    const currencyFormatter = new Intl.NumberFormat('en-SG', {
      style: 'currency',
      currency: 'SGD',
      maximumFractionDigits: 0,
    })
    entries.push({
      key: 'pipeline',
      label: 'Weighted pipeline value',
      actual:
        pipeline[0].valueNumeric !== null
          ? currencyFormatter.format(pipeline[0].valueNumeric)
          : pipeline[0].valueText ?? '—',
      benchmark:
        pipeline[1]?.valueNumeric !== null
          ? currencyFormatter.format(pipeline[1].valueNumeric)
          : pipeline[1]?.valueText ?? null,
      cohort: convertLabel(pipeline[0].cohort),
      deltaText: null,
    })
  }
  return entries
}

function buildRoiSummary(snapshot: PerformanceSnapshot | null): RoiSummary {
  if (!snapshot) {
    return EMPTY_ROI_SUMMARY
  }
  const metrics = snapshot.roiMetrics
  const summary = (metrics?.summary ?? {}) as Record<string, unknown>
  const projects = Array.isArray(metrics?.projects)
    ? (metrics.projects as Record<string, unknown>[])
    : []
  return {
    projectCount: Number(summary.project_count ?? projects.length ?? 0),
    totalReviewHoursSaved: toNullableNumber(summary.total_review_hours_saved),
    averageAutomationScore: toNullableNumber(summary.average_automation_score),
    averageAcceptanceRate: toNullableNumber(summary.average_acceptance_rate),
    averageSavingsPercent: toNullableNumber(summary.savings_percent_average),
    bestPaybackWeeks: summary.best_payback_weeks
      ? Number(summary.best_payback_weeks)
      : null,
    projects: projects.map((project) => ({
      projectId: Number(project.project_id ?? 0),
      hoursSaved: toNullableNumber(project.review_hours_saved),
      automationScore: toNullableNumber(project.automation_score),
      acceptanceRate: toNullableNumber(project.acceptance_rate),
      paybackWeeks: project.payback_weeks
        ? Number(project.payback_weeks)
        : null,
    })),
  }
}

function totalPipeline(columns: PipelineColumn[]): number | null {
  const total = columns.reduce(
    (sum, column) => sum + (column.totalValue ?? 0),
    0,
  )
  return total === 0 ? null : total
}

function totalWeightedPipeline(columns: PipelineColumn[]): number | null {
  const total = columns.reduce(
    (sum, column) => sum + (column.weightedValue ?? 0),
    0,
  )
  return total === 0 ? null : total
}

function formatCurrency(value: number | null) {
  if (value === null) {
    return '—'
  }
  return new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatRelativeDate(value: string | null) {
  if (!value) {
    return null
  }
  try {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) {
      return value
    }
    return date.toLocaleDateString()
  } catch {
    return value
  }
}

function formatDateTime(value: string | null) {
  if (!value) {
    return ''
  }
  try {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) {
      return value
    }
    return date.toLocaleString()
  } catch {
    return value
  }
}

function toNullableNumber(value: unknown): number | null {
  if (value === null || value === undefined) {
    return null
  }
  const parsed = Number(value)
  return Number.isNaN(parsed) ? null : parsed
}
