import { ReactNode, Suspense, lazy, useMemo, useState } from 'react'
import { Box, Grid, Tooltip, Typography } from '@mui/material'
import AccountTreeOutlined from '@mui/icons-material/AccountTreeOutlined'
import AutoGraph from '@mui/icons-material/AutoGraph'
import CloseIcon from '@mui/icons-material/Close'
import ErrorOutline from '@mui/icons-material/ErrorOutline'
import FileDownloadOutlined from '@mui/icons-material/FileDownloadOutlined'
import HubOutlined from '@mui/icons-material/HubOutlined'
import InfoOutlined from '@mui/icons-material/InfoOutlined'
import SyncOutlined from '@mui/icons-material/SyncOutlined'
import WarningAmberOutlined from '@mui/icons-material/WarningAmberOutlined'

import { AppLayout } from '../../App'
import {
  AlertBlock,
  Button,
  EmptyState,
  MetricCard,
  Panel,
  SectionHeader,
  Skeleton,
  SkeletonText,
} from '../../components/canonical'
import {
  type CrossCorrelationIntelligenceState,
  type GraphIntelligenceState,
  type InvestigationAnalyticsServices,
  type PredictiveIntelligenceState,
  useInvestigationAnalytics,
} from '../../hooks/useInvestigationAnalytics'

const RelationshipGraph = lazy(async () => {
  const module = await import('./components/RelationshipGraph')
  return { default: module.RelationshipGraph }
})

const ConfidenceGauge = lazy(async () => {
  const module = await import('./components/ConfidenceGauge')
  return { default: module.ConfidenceGauge }
})

const CorrelationHeatmap = lazy(async () => {
  const module = await import('./components/CorrelationHeatmap')
  return { default: module.CorrelationHeatmap }
})

export interface AdvancedIntelligencePageProps {
  workspaceId?: string
  services?: Partial<InvestigationAnalyticsServices>
}

const DEFAULT_WORKSPACE_ID = 'default-investigation'

interface IntelligenceStatusPanelProps {
  status: 'loading' | 'empty' | 'error'
  icon: ReactNode
  loadingLabel: string
  emptyTitle: string
  emptyDescription?: string
  errorTitle: string
  errorMessage?: string
  minHeight?: number
}

type GraphOkState = Extract<GraphIntelligenceState, { status: 'ok' }>
type GraphEmptyState = Extract<GraphIntelligenceState, { status: 'empty' }>
type GraphErrorState = Extract<GraphIntelligenceState, { status: 'error' }>
type PredictiveOkState = Extract<PredictiveIntelligenceState, { status: 'ok' }>
type PredictiveEmptyState = Extract<
  PredictiveIntelligenceState,
  { status: 'empty' }
>
type PredictiveErrorState = Extract<
  PredictiveIntelligenceState,
  { status: 'error' }
>
type CorrelationOkState = Extract<
  CrossCorrelationIntelligenceState,
  { status: 'ok' }
>
type CorrelationEmptyState = Extract<
  CrossCorrelationIntelligenceState,
  { status: 'empty' }
>
type CorrelationErrorState = Extract<
  CrossCorrelationIntelligenceState,
  { status: 'error' }
>

/** Metric tooltips — each describes what the computation actually measures */
const METRIC_TOOLTIPS: Record<string, string> = {
  avgDealConfidence:
    'Average predicted probability across all forecast segments. Higher values indicate stronger model confidence in deal outcomes.',
  avgYieldDelta:
    'Mean percentage difference between projected and baseline values across segments with non-zero baselines.',
  activeSegments:
    'Number of forecast segments currently being tracked by the predictive model.',
  correlationStrength:
    'Average absolute correlation coefficient across all significant driver–outcome pairs. Higher values indicate stronger statistical relationships.',
}

function IntelligenceStatusPanel({
  status,
  icon,
  loadingLabel,
  emptyTitle,
  emptyDescription,
  errorTitle,
  errorMessage,
  minHeight = 280,
}: IntelligenceStatusPanelProps) {
  if (status === 'loading') {
    return (
      <Box
        sx={{
          minHeight,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          gap: 'var(--ob-space-150)',
          px: 'var(--ob-space-150)',
          py: 'var(--ob-space-200)',
        }}
      >
        <Typography
          sx={{
            color: 'var(--ob-color-text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: 'var(--ob-letter-spacing-wider)',
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 'var(--ob-font-weight-semibold)',
          }}
        >
          {loadingLabel}
        </Typography>
        <Skeleton variant="rounded" width="38%" height={18} />
        <Skeleton
          variant="rounded"
          width="100%"
          height={minHeight > 400 ? 320 : 120}
        />
        <SkeletonText lines={2} lastLineWidth="72%" />
      </Box>
    )
  }

  const isError = status === 'error'

  return (
    <EmptyState
      icon={icon}
      title={isError ? errorTitle : emptyTitle}
      description={
        isError
          ? (errorMessage ?? 'Try syncing the workspace.')
          : emptyDescription
      }
      size={minHeight > 400 ? 'lg' : 'md'}
      sx={{
        minHeight,
        border: isError
          ? '1px solid var(--ob-color-error-soft)'
          : '1px dashed var(--ob-color-border-subtle)',
      }}
    />
  )
}

function IntelligenceLoadingPanel({ minHeight = 280 }: { minHeight?: number }) {
  return (
    <Box
      sx={{
        minHeight,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        gap: 'var(--ob-space-150)',
        px: 'var(--ob-space-150)',
        py: 'var(--ob-space-200)',
      }}
    >
      <Skeleton variant="rounded" width="38%" height={18} />
      <Skeleton
        variant="rounded"
        width="100%"
        height={minHeight > 400 ? 320 : 120}
      />
      <SkeletonText lines={2} lastLineWidth="72%" />
    </Box>
  )
}

function isGraphOk(graph: GraphIntelligenceState): graph is GraphOkState {
  return graph.status === 'ok'
}

function isGraphEmpty(graph: GraphIntelligenceState): graph is GraphEmptyState {
  return graph.status === 'empty'
}

function isGraphError(graph: GraphIntelligenceState): graph is GraphErrorState {
  return graph.status === 'error'
}

function isPredictiveOk(
  predictive: PredictiveIntelligenceState,
): predictive is PredictiveOkState {
  return predictive.status === 'ok'
}

function isPredictiveEmpty(
  predictive: PredictiveIntelligenceState,
): predictive is PredictiveEmptyState {
  return predictive.status === 'empty'
}

function isPredictiveError(
  predictive: PredictiveIntelligenceState,
): predictive is PredictiveErrorState {
  return predictive.status === 'error'
}

function isCorrelationOk(
  correlation: CrossCorrelationIntelligenceState,
): correlation is CorrelationOkState {
  return correlation.status === 'ok'
}

function isCorrelationEmpty(
  correlation: CrossCorrelationIntelligenceState,
): correlation is CorrelationEmptyState {
  return correlation.status === 'empty'
}

function isCorrelationError(
  correlation: CrossCorrelationIntelligenceState,
): correlation is CorrelationErrorState {
  return correlation.status === 'error'
}

function getStatusFromState(state: {
  status: string
}): IntelligenceStatusPanelProps['status'] | 'ok' {
  return state.status as IntelligenceStatusPanelProps['status'] | 'ok'
}

/** Node detail panel shown when a graph node is clicked */
function NodeDetailPanel({
  nodeId,
  nodes,
  links,
  onClose,
}: {
  nodeId: string
  nodes: Array<{ id: string; label: string; category: string; weight: number }>
  links: Array<{ source: string; target: string; strength: number }>
  onClose: () => void
}) {
  const node = nodes.find((n) => n.id === nodeId)
  if (!node) return null

  const connections = links
    .filter((l) => l.source === nodeId || l.target === nodeId)
    .map((l) => {
      const connectedId = l.source === nodeId ? l.target : l.source
      const connectedNode = nodes.find((n) => n.id === connectedId)
      return {
        label: connectedNode?.label ?? connectedId,
        category: connectedNode?.category ?? 'unknown',
        strength: l.strength,
      }
    })
    .sort((a, b) => b.strength - a.strength)

  return (
    <Box
      sx={{
        p: 'var(--ob-space-150)',
        borderTop: 'var(--ob-divider-strong)',
        background: 'var(--ob-color-bg-surface-elevated)',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 'var(--ob-space-100)',
        }}
      >
        <Box>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-base)',
              fontWeight: 'var(--ob-font-weight-semibold)',
              color: 'var(--ob-color-text-primary)',
            }}
          >
            {node.label}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'var(--ob-color-text-muted)',
              textTransform: 'capitalize',
            }}
          >
            {node.category} &middot; weight {node.weight.toFixed(2)}
          </Typography>
        </Box>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <CloseIcon sx={{ fontSize: 'var(--ob-font-size-base)' }} />
        </Button>
      </Box>

      {connections.length > 0 ? (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-050)',
          }}
        >
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-2xs)',
              textTransform: 'uppercase',
              letterSpacing: 'var(--ob-letter-spacing-wider)',
              color: 'var(--ob-color-text-muted)',
              mb: 'var(--ob-space-025)',
            }}
          >
            Connections ({connections.length})
          </Typography>
          {connections.map((conn, i) => (
            <Box
              key={i}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                py: 'var(--ob-space-050)',
              }}
            >
              <Box>
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-sm)',
                    fontWeight: 'var(--ob-font-weight-medium)',
                    color: 'var(--ob-color-text-primary)',
                  }}
                >
                  {conn.label}
                </Typography>
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-xs)',
                    color: 'var(--ob-color-text-muted)',
                    textTransform: 'capitalize',
                  }}
                >
                  {conn.category}
                </Typography>
              </Box>
              <Typography
                sx={{
                  fontFamily: 'var(--ob-font-family-mono)',
                  fontSize: 'var(--ob-font-size-sm)',
                  fontWeight: 'var(--ob-font-weight-bold)',
                  color: 'var(--ob-color-text-secondary)',
                }}
              >
                {conn.strength.toFixed(1)}
              </Typography>
            </Box>
          ))}
        </Box>
      ) : (
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-color-text-muted)',
          }}
        >
          No connections found.
        </Typography>
      )}
    </Box>
  )
}

export function AdvancedIntelligencePage({
  workspaceId = DEFAULT_WORKSPACE_ID,
  services,
}: AdvancedIntelligencePageProps) {
  const {
    graph,
    predictive,
    correlation,
    isLoading,
    isUsingFixtureData,
    refetch,
  } = useInvestigationAnalytics(workspaceId, services)

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [showAllSegments, setShowAllSegments] = useState(false)

  // --- Derived Metrics (labels match computations) ---
  const avgDealConfidence = useMemo(() => {
    if (predictive.status !== 'ok') return null
    if (predictive.segments.length === 0) return 0
    const sum = predictive.segments.reduce((acc, s) => acc + s.probability, 0)
    return (sum / predictive.segments.length) * 100
  }, [predictive])

  const avgYieldDelta = useMemo(() => {
    if (predictive.status !== 'ok') return null
    let count = 0
    const sum = predictive.segments.reduce((acc, s) => {
      if (s.baseline === 0) return acc
      count++
      return acc + ((s.projection - s.baseline) / s.baseline) * 100
    }, 0)
    return count === 0 ? 0 : sum / count
  }, [predictive])

  const activeSegments = useMemo(() => {
    if (predictive.status !== 'ok') return null
    return predictive.segments.length
  }, [predictive])

  const correlationStrength = useMemo(() => {
    if (correlation.status !== 'ok') return null
    if (correlation.relationships.length === 0) return 0
    const avgCoeff =
      correlation.relationships.reduce(
        (acc, r) => acc + Math.abs(r.coefficient),
        0,
      ) / correlation.relationships.length
    return Math.round(avgCoeff * 100)
  }, [correlation])

  // Memoize graph arrays to prevent force simulation restarts on re-render
  const graphData = isGraphOk(graph) ? graph : null
  const graphNodes = useMemo(
    () =>
      graphData?.graph.nodes.map((n) => ({
        id: n.id,
        label: n.label,
        category: n.category,
        weight: n.score,
      })) ?? [],
    [graphData],
  )
  const graphLinks = useMemo(
    () =>
      graphData?.graph.edges.map((e) => ({
        source: e.source,
        target: e.target,
        strength: e.weight ?? 1,
      })) ?? [],
    [graphData],
  )

  const graphStatus = getStatusFromState(graph)
  const predictiveStatus = getStatusFromState(predictive)
  const correlationStatus = getStatusFromState(correlation)
  const predictiveData = isPredictiveOk(predictive) ? predictive : null
  const correlationData = isCorrelationOk(correlation) ? correlation : null
  const graphEmptySummary = isGraphEmpty(graph) ? graph.summary : undefined
  const graphErrorMessage = isGraphError(graph) ? graph.error : undefined
  const predictiveEmptySummary = isPredictiveEmpty(predictive)
    ? predictive.summary
    : undefined
  const predictiveErrorMessage = isPredictiveError(predictive)
    ? predictive.error
    : undefined
  const correlationEmptySummary = isCorrelationEmpty(correlation)
    ? correlation.summary
    : undefined
  const correlationErrorMessage = isCorrelationError(correlation)
    ? correlation.error
    : undefined

  const visibleSegments = predictiveData
    ? showAllSegments
      ? predictiveData.segments
      : predictiveData.segments.slice(0, 5)
    : []
  const hiddenSegmentCount = predictiveData
    ? Math.max(0, predictiveData.segments.length - 5)
    : 0

  return (
    <AppLayout
      title="Deal Intelligence"
      subtitle="Pipeline analytics and cross-asset correlation"
      actions={
        <Box
          sx={{
            display: 'flex',
            gap: 'var(--ob-space-100)',
            alignItems: 'center',
          }}
        >
          <Tooltip title="Export coming soon" placement="bottom" arrow>
            <span>
              <Button
                variant="ghost"
                size="sm"
                startIcon={<FileDownloadOutlined />}
                disabled
              >
                Export
              </Button>
            </span>
          </Tooltip>
          <Button
            variant="secondary"
            size="sm"
            startIcon={<SyncOutlined />}
            onClick={() => {
              void refetch()
            }}
            disabled={isLoading}
          >
            {isLoading ? 'Syncing...' : 'Sync'}
          </Button>
        </Box>
      }
    >
      <Box sx={{ width: '100%', pb: 'var(--ob-space-400)' }}>
        {/* Sample data warning banner */}
        {isUsingFixtureData && (
          <AlertBlock
            type="warning"
            icon={<WarningAmberOutlined />}
            sx={{ mb: 'var(--ob-space-200)' }}
          >
            Showing sample data — analytics service is unreachable. Values below
            are illustrative, not live.
          </AlertBlock>
        )}

        {/* 1. KPI Section */}
        <Box sx={{ mb: 'var(--ob-space-300)' }}>
          <SectionHeader
            title="Portfolio Signals"
            size="sm"
            sx={{ mb: 'var(--ob-space-150)' }}
          />

          <Grid container spacing="var(--ob-space-150)">
            <Grid item xs={12} sm={6} lg={3}>
              <MetricCard
                label="Avg. Deal Confidence"
                value={
                  avgDealConfidence !== null
                    ? `${avgDealConfidence.toFixed(1)}%`
                    : '—'
                }
                loading={isLoading}
                icon={
                  <Tooltip
                    title={METRIC_TOOLTIPS.avgDealConfidence}
                    placement="top"
                    arrow
                  >
                    <InfoOutlined
                      sx={{
                        fontSize: 'var(--ob-font-size-base)',
                        cursor: 'help',
                      }}
                    />
                  </Tooltip>
                }
              />
            </Grid>
            <Grid item xs={12} sm={6} lg={3}>
              <MetricCard
                label="Avg. Yield Delta"
                value={
                  avgYieldDelta !== null ? `${avgYieldDelta.toFixed(1)}%` : '—'
                }
                loading={isLoading}
                icon={
                  <Tooltip
                    title={METRIC_TOOLTIPS.avgYieldDelta}
                    placement="top"
                    arrow
                  >
                    <InfoOutlined
                      sx={{
                        fontSize: 'var(--ob-font-size-base)',
                        cursor: 'help',
                      }}
                    />
                  </Tooltip>
                }
              />
            </Grid>
            <Grid item xs={12} sm={6} lg={3}>
              <MetricCard
                label="Active Segments"
                value={activeSegments ?? '—'}
                loading={isLoading}
                icon={
                  <Tooltip
                    title={METRIC_TOOLTIPS.activeSegments}
                    placement="top"
                    arrow
                  >
                    <InfoOutlined
                      sx={{
                        fontSize: 'var(--ob-font-size-base)',
                        cursor: 'help',
                      }}
                    />
                  </Tooltip>
                }
              />
            </Grid>
            <Grid item xs={12} sm={6} lg={3}>
              <MetricCard
                label="Correlation Strength"
                value={correlationStrength ?? '—'}
                loading={isLoading}
                icon={
                  <Tooltip
                    title={METRIC_TOOLTIPS.correlationStrength}
                    placement="top"
                    arrow
                  >
                    <InfoOutlined
                      sx={{
                        fontSize: 'var(--ob-font-size-base)',
                        cursor: 'help',
                      }}
                    />
                  </Tooltip>
                }
              />
            </Grid>
          </Grid>
        </Box>

        {/* Main Content Grid */}
        <Grid container spacing="var(--ob-space-200)">
          {/* 2. Relationship Intelligence (Main Centerpiece) */}
          <Grid item xs={12} lg={8}>
            <Panel
              title="Relationship Intelligence"
              subtitle="Entity connections across deals and workflows"
              variant="glass"
              padding="compact"
              sx={{ height: '100%', minHeight: 500 }}
            >
              {graphStatus === 'ok' && graphData ? (
                <Suspense
                  fallback={<IntelligenceLoadingPanel minHeight={600} />}
                >
                  <RelationshipGraph
                    nodes={graphNodes}
                    links={graphLinks}
                    height={560}
                    onNodeClick={(id) => {
                      setSelectedNodeId((prev) => (prev === id ? null : id))
                    }}
                  />
                  {selectedNodeId && (
                    <NodeDetailPanel
                      nodeId={selectedNodeId}
                      nodes={graphNodes}
                      links={graphLinks}
                      onClose={() => {
                        setSelectedNodeId(null)
                      }}
                    />
                  )}
                </Suspense>
              ) : (
                <IntelligenceStatusPanel
                  status={graphStatus as 'loading' | 'empty' | 'error'}
                  icon={
                    graphStatus === 'error' ? (
                      <ErrorOutline
                        sx={{ color: 'var(--ob-color-status-error-text)' }}
                      />
                    ) : (
                      <HubOutlined
                        sx={{ color: 'var(--ob-color-brand-primary)' }}
                      />
                    )
                  }
                  loadingLabel="Mapping organization network..."
                  emptyTitle="Awaiting investigation metadata to construct intelligence graph"
                  emptyDescription={graphEmptySummary}
                  errorTitle="Unable to load intelligence graph"
                  errorMessage={graphErrorMessage}
                  minHeight={560}
                />
              )}
            </Panel>
          </Grid>

          {/* 3. Predictive & Correlation (Side Panel) */}
          <Grid item xs={12} lg={4}>
            <Panel
              title="Predictive Forecast"
              subtitle="Deal outcome probability by segment"
              variant="glass"
              padding="compact"
              sx={{ mb: 'var(--ob-space-200)' }}
            >
              {predictiveStatus === 'ok' && predictiveData ? (
                <Suspense
                  fallback={<IntelligenceLoadingPanel minHeight={280} />}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--ob-space-100)',
                    }}
                  >
                    {visibleSegments.map((segment) => (
                      <ConfidenceGauge
                        key={segment.segmentId}
                        label={segment.segmentName}
                        value={Math.round(segment.probability * 100)}
                        projection={segment.projection}
                        baseline={segment.baseline}
                      />
                    ))}
                    {!showAllSegments && hiddenSegmentCount > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setShowAllSegments(true)
                        }}
                        sx={{ alignSelf: 'center' }}
                      >
                        Show {hiddenSegmentCount} more
                      </Button>
                    )}
                    {showAllSegments && hiddenSegmentCount > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setShowAllSegments(false)
                        }}
                        sx={{ alignSelf: 'center' }}
                      >
                        Show less
                      </Button>
                    )}
                  </Box>
                </Suspense>
              ) : (
                <IntelligenceStatusPanel
                  status={predictiveStatus as 'loading' | 'empty' | 'error'}
                  icon={
                    predictiveStatus === 'error' ? (
                      <ErrorOutline
                        sx={{ color: 'var(--ob-color-status-error-text)' }}
                      />
                    ) : (
                      <AutoGraph
                        sx={{ color: 'var(--ob-color-brand-primary)' }}
                      />
                    )
                  }
                  loadingLabel="Running predictive models..."
                  emptyTitle="No predictive signals available for this workspace yet"
                  emptyDescription={predictiveEmptySummary}
                  errorTitle="Unable to load predictive forecast"
                  errorMessage={predictiveErrorMessage}
                  minHeight={280}
                />
              )}
            </Panel>

            <Panel
              title="Cross-Correlation"
              subtitle="Driver–outcome relationships"
              variant="glass"
              padding="compact"
            >
              {correlationStatus === 'ok' && correlationData ? (
                <Suspense
                  fallback={<IntelligenceLoadingPanel minHeight={280} />}
                >
                  <CorrelationHeatmap
                    data={correlationData.relationships.map((r) => ({
                      id: r.pairId,
                      driver: r.driver,
                      outcome: r.outcome,
                      coefficient: r.coefficient,
                      pValue: r.pValue,
                    }))}
                  />
                </Suspense>
              ) : (
                <IntelligenceStatusPanel
                  status={correlationStatus as 'loading' | 'empty' | 'error'}
                  icon={
                    correlationStatus === 'error' ? (
                      <ErrorOutline
                        sx={{ color: 'var(--ob-color-status-error-text)' }}
                      />
                    ) : (
                      <AccountTreeOutlined
                        sx={{ color: 'var(--ob-color-brand-primary)' }}
                      />
                    )
                  }
                  loadingLabel="Analyzing correlations..."
                  emptyTitle="No significant cross-correlations detected yet"
                  emptyDescription={correlationEmptySummary}
                  errorTitle="Unable to load correlation analysis"
                  errorMessage={correlationErrorMessage}
                  minHeight={280}
                />
              )}
            </Panel>
          </Grid>
        </Grid>
      </Box>
    </AppLayout>
  )
}

export default AdvancedIntelligencePage
