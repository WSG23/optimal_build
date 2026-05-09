import {
  Suspense,
  lazy,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import {
  Alert,
  Box,
  Button,
  Grid,
  Skeleton,
  Stack,
  Typography,
} from '@mui/material'
import {
  DEAL_STAGE_ORDER,
  fetchDealCommissions,
  fetchDealTimeline,
  fetchDeals,
  changeDealStage,
  type DealSummary,
} from '../../../api/deals'
import {
  fetchBenchmarks,
  fetchLatestSnapshot,
  fetchSnapshotsHistory,
} from '../../../api/performance'
import { PipelineBoard } from './components/PipelineBoard'
import { DealInsightsPanel } from './components/DealInsightsPanel'
import { RoiPanel } from './components/RoiPanel'
import { KpiSummarySection } from './components/KpiSummarySection'
import { Card } from '../../../components/canonical/Card'
import { getOpenPipelineMetricDisplay } from './metricDisplay'
import type {
  AnalyticsMetric,
  BenchmarkEntry,
  DealSnapshot,
  PipelineColumn,
  PipelineStageKey,
  RoiSummary,
  StageEvent,
  CommissionEntry,
  TrendPoint,
} from './types'
import {
  EMPTY_ROI_SUMMARY,
  buildMetrics,
  buildTrend,
  buildBenchmarks,
  buildRoiSummary,
  convertTimeline,
  mapCommissionEntry,
  totalPipeline,
  formatRelativeDate,
} from './utils'
import '../../../styles/business-performance.css'

const AnalyticsPanel = lazy(() =>
  import('./components/AnalyticsPanel').then((module) => ({
    default: module.AnalyticsPanel,
  })),
)

function AnalyticsPanelFallback() {
  return (
    <Card variant="default" sx={{ p: 'var(--ob-space-200)' }}>
      <Stack spacing="var(--ob-space-100)">
        <Skeleton
          variant="text"
          width="40%"
          height={32}
          sx={{ transform: 'none' }}
        />
        <Skeleton
          variant="rectangular"
          height={300}
          sx={{ borderRadius: 'var(--ob-radius-sm)' }}
        />
        <Skeleton
          variant="rectangular"
          height={120}
          sx={{ borderRadius: 'var(--ob-radius-sm)' }}
        />
      </Stack>
    </Card>
  )
}

export function BusinessPerformancePage() {
  const [deals, setDeals] = useState<DealSummary[]>([])
  const [columns, setColumns] = useState<PipelineColumn[]>([])
  const [pipelineLoading, setPipelineLoading] = useState(true)
  const [pipelineError, setPipelineError] = useState<string | null>(null)
  const [stageUpdateError, setStageUpdateError] = useState<string | null>(null)

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
  const [movingDealId, setMovingDealId] = useState<string | null>(null)

  const lastSnapshot = useMemo(
    () => new Date().toLocaleDateString(undefined, { dateStyle: 'medium' }),
    [],
  )

  const buildColumns = useCallback(
    (entries: DealSummary[]): PipelineColumn[] => {
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
        const stage =
          stageMap.get(deal.pipelineStage) ?? stageMap.get('lead_captured')
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
          stage.totalValue !== null
            ? (stage.totalValue ?? 0) + estimated
            : estimated
        const weightedContribution = estimated * confidence
        stage.weightedValue =
          stage.weightedValue !== null
            ? (stage.weightedValue ?? 0) + weightedContribution
            : weightedContribution
      })

      return Array.from(stageMap.values())
    },
    [],
  )

  const loadPipeline = useCallback(
    async (controller?: AbortController) => {
      const signal = controller?.signal
      try {
        setPipelineLoading(true)
        setPipelineError(null)
        const fetchedDeals = await fetchDeals(signal)
        if (signal?.aborted) {
          return
        }
        setDeals(fetchedDeals)
        setColumns(buildColumns(fetchedDeals))
        const firstDeal = fetchedDeals[0]
        if (firstDeal) {
          setSelectedDealId((prev) => prev ?? firstDeal.id)
        } else {
          setSelectedDealId(null)
        }
      } catch (error) {
        if (
          signal?.aborted ||
          (error as { name?: string }).name === 'AbortError'
        ) {
          return
        }
        console.error('Failed to load pipeline', error)
        setPipelineError(
          'We could not load your pipeline. Check your connection and try again.',
        )
      } finally {
        if (!signal?.aborted) {
          setPipelineLoading(false)
        }
      }
    },
    [buildColumns],
  )

  useEffect(() => {
    const controller = new AbortController()
    loadPipeline(controller)
    return () => controller.abort()
  }, [loadPipeline])

  const handlePipelineRetry = useCallback(() => {
    void loadPipeline()
  }, [loadPipeline])

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
        setTimeline(convertTimeline(timelineData))
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
        setDealError('We could not load deal history. Retry in a moment.')
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
    const validAgentId: string = agentId
    const controller = new AbortController()
    async function loadAnalytics() {
      try {
        setAnalyticsLoading(true)
        setAnalyticsError(null)

        const [snapshot, history, conversionBench, cycleBench, pipelineBench] =
          await Promise.all([
            fetchLatestSnapshot(validAgentId, controller.signal),
            fetchSnapshotsHistory(validAgentId, 30, controller.signal),
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

  const handleStageChange = useCallback(
    async (dealId: string, toStage: PipelineStageKey) => {
      const previousDeals = deals
      const optimisticDeals = deals.map((deal) =>
        deal.id === dealId ? { ...deal, pipelineStage: toStage } : deal,
      )
      setStageUpdateError(null)
      setMovingDealId(dealId)
      setDeals(optimisticDeals)
      setColumns(buildColumns(optimisticDeals))

      try {
        const response = await changeDealStage(dealId, { toStage })
        const { timeline: updatedTimeline, ...rest } = response
        const nextDeals = optimisticDeals.map((deal) =>
          deal.id === dealId
            ? {
                ...deal,
                ...rest,
              }
            : deal,
        )
        setDeals(nextDeals)
        setColumns(buildColumns(nextDeals))
        if (selectedDealId === dealId) {
          setSelectedDeal((prev) =>
            prev
              ? {
                  ...prev,
                  stage: rest.pipelineStage,
                  expectedCloseDate: rest.expectedCloseDate,
                }
              : prev,
          )
          setTimeline(convertTimeline(updatedTimeline))
        }
      } catch (error) {
        console.error('Failed to change stage', error)
        setDeals(previousDeals)
        setColumns(buildColumns(previousDeals))
        setStageUpdateError(
          'Unable to update deal stage. Reverted to previous state.',
        )
      } finally {
        setMovingDealId(null)
      }
    },
    [buildColumns, deals, selectedDealId],
  )

  const totalPipelineValue = useMemo(() => totalPipeline(columns), [columns])
  const openPipelineMetric = getOpenPipelineMetricDisplay(
    pipelineLoading,
    totalPipelineValue,
  )

  return (
    <Box className="bp-page" sx={{ width: '100%' }} role="main">
      {/* Page Header */}
      <Box
        component="header"
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-100)',
          mb: 'var(--ob-space-150)',
          animation:
            'ob-slide-down-fade var(--ob-motion-header-duration) var(--ob-motion-header-ease) both',
        }}
      >
        <Box>
          <Typography
            variant="h5"
            sx={{ fontWeight: 'var(--ob-font-weight-bold)', lineHeight: 1.2 }}
          >
            Business Performance
          </Typography>
          <Typography
            variant="body2"
            sx={{ color: 'text.secondary', mt: 'var(--ob-space-025)' }}
          >
            Pipeline tracking, deal insights, and analytics
          </Typography>
        </Box>
      </Box>

      {/* KPI Summary */}
      <KpiSummarySection
        analyticsLoading={analyticsLoading}
        lastSnapshot={lastSnapshot}
        openPipelineMetric={openPipelineMetric}
        roiProjectCount={roiSummary.projectCount}
      />

      {/* Alerts */}
      <Stack
        spacing="var(--ob-space-200)"
        className="bp-page__alerts"
        sx={{ mb: 'var(--ob-space-300)' }}
      >
        {pipelineError && (
          <Alert
            severity="error"
            action={
              <Button
                color="inherit"
                size="small"
                onClick={handlePipelineRetry}
                disabled={pipelineLoading}
              >
                Retry
              </Button>
            }
          >
            {pipelineError}
          </Alert>
        )}
        {stageUpdateError && (
          <Alert severity="warning">{stageUpdateError}</Alert>
        )}
      </Stack>

      <Grid container spacing="var(--ob-space-300)" className="bp-page__layout">
        <Grid item xs={12} md={8} className="bp-page__pipeline">
          <Card
            variant="default"
            className="bp-pipeline-wrapper"
            sx={{ height: '100%', p: 'var(--ob-space-200)' }}
          >
            {pipelineLoading ? (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--ob-space-150)',
                }}
              >
                <Skeleton
                  variant="rectangular"
                  height={40}
                  sx={{ borderRadius: 'var(--ob-radius-sm)' }}
                />
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: 'var(--ob-space-100)',
                  }}
                >
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton
                      key={i}
                      variant="rectangular"
                      height={200}
                      sx={{ borderRadius: 'var(--ob-radius-sm)' }}
                    />
                  ))}
                </Box>
              </Box>
            ) : (
              <PipelineBoard
                columns={columns}
                selectedDealId={selectedDealId}
                onSelectDeal={handleSelectDeal}
                onStageChange={handleStageChange}
                movingDealId={movingDealId}
              />
            )}
          </Card>
        </Grid>
        <Grid item xs={12} md={4} className="bp-page__sidebar">
          <Stack spacing="var(--ob-space-300)">
            <DealInsightsPanel
              deal={selectedDeal}
              timeline={timeline}
              commissions={commissions}
            />
            <Suspense fallback={<AnalyticsPanelFallback />}>
              <AnalyticsPanel
                metrics={metrics}
                trend={trend}
                benchmarks={benchmarks}
              />
            </Suspense>
            <RoiPanel summary={roiSummary} />
            {(dealLoading || analyticsLoading) && (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--ob-space-100)',
                }}
              >
                <Skeleton
                  variant="rectangular"
                  height={120}
                  sx={{ borderRadius: 'var(--ob-radius-sm)' }}
                />
                <Skeleton
                  variant="rectangular"
                  height={120}
                  sx={{ borderRadius: 'var(--ob-radius-sm)' }}
                />
              </Box>
            )}
            {(dealError || analyticsError) && (
              <Alert severity="error">{dealError ?? analyticsError}</Alert>
            )}
          </Stack>
        </Grid>
      </Grid>
    </Box>
  )
}
