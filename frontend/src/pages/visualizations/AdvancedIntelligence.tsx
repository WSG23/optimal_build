import { ReactNode, Suspense, lazy, useCallback, useMemo } from 'react'
import { Box, Grid, Typography, useTheme } from '@mui/material'
import AccountTreeOutlined from '@mui/icons-material/AccountTreeOutlined'
import AutoGraph from '@mui/icons-material/AutoGraph'
import ErrorOutline from '@mui/icons-material/ErrorOutline'
import HubOutlined from '@mui/icons-material/HubOutlined'

import { AppLayout } from '../../App'
import { EmptyState, Skeleton, SkeletonText } from '../../components/canonical'
import {
  type CrossCorrelationIntelligenceState,
  type GraphIntelligenceState,
  type InvestigationAnalyticsServices,
  type PredictiveIntelligenceState,
  useInvestigationAnalytics,
} from '../../hooks/useInvestigationAnalytics'
import { KPITickerCard } from './components/KPITickerCard'
import '../../styles/visualizations.css'

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
          borderRadius: 'var(--ob-radius-sm)',
          border: '1px solid var(--ob-border-fine)',
          background:
            'radial-gradient(circle at top, rgba(0, 214, 255, 0.08), transparent 65%), var(--ob-surface-glass-1)',
        }}
      >
        <Typography
          sx={{
            color: 'var(--ob-color-text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
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
          ? (errorMessage ?? 'Try refreshing the workspace.')
          : emptyDescription
      }
      size={minHeight > 400 ? 'lg' : 'md'}
      sx={{
        minHeight,
        border: isError
          ? '1px solid rgba(255, 99, 132, 0.28)'
          : '1px dashed rgba(255, 255, 255, 0.12)',
        background: isError
          ? 'radial-gradient(circle at top, rgba(255, 99, 132, 0.08), transparent 65%), var(--ob-surface-glass-1)'
          : 'radial-gradient(circle at top, rgba(0, 214, 255, 0.08), transparent 65%), var(--ob-surface-glass-1)',
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
        borderRadius: 'var(--ob-radius-sm)',
        border: '1px solid var(--ob-border-fine)',
        background:
          'radial-gradient(circle at top, rgba(0, 214, 255, 0.08), transparent 65%), var(--ob-surface-glass-1)',
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

function getGraphStatus(
  graph: GraphIntelligenceState,
): IntelligenceStatusPanelProps['status'] | 'ok' {
  return graph.status
}

function getPredictiveStatus(
  predictive: PredictiveIntelligenceState,
): IntelligenceStatusPanelProps['status'] | 'ok' {
  return predictive.status
}

function getCorrelationStatus(
  correlation: CrossCorrelationIntelligenceState,
): IntelligenceStatusPanelProps['status'] | 'ok' {
  return correlation.status
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

// --- Mock Data Generators (until API provides trends) ---
function generateSparkline(seedValue: number, length = 20): number[] {
  let current = seedValue
  return Array.from({ length }, () => {
    current = current * (1 + (Math.random() - 0.5) * 0.1)
    return current
  })
}

export function AdvancedIntelligencePage({
  workspaceId = DEFAULT_WORKSPACE_ID,
  services,
}: AdvancedIntelligencePageProps) {
  const { graph, predictive, correlation, isLoading, refetch } =
    useInvestigationAnalytics(workspaceId, services)
  const theme = useTheme()

  const handleRefresh = useCallback(() => {
    return refetch()
  }, [refetch])

  // --- Derived Metrics ---
  const adoptionRate = useMemo(() => {
    if (predictive.status !== 'ok') return 0
    if (predictive.segments.length === 0) return 0
    const sum = predictive.segments.reduce((acc, s) => acc + s.probability, 0)
    return (sum / predictive.segments.length) * 100
  }, [predictive])

  const uplift = useMemo(() => {
    if (predictive.status !== 'ok') return 0
    let count = 0
    const sum = predictive.segments.reduce((acc, s) => {
      if (s.baseline === 0) return acc
      count++
      return acc + ((s.projection - s.baseline) / s.baseline) * 100
    }, 0)
    return count === 0 ? 0 : sum / count
  }, [predictive])

  // Mock trends for the Hero Cards
  const adoptionTrend = 12.5 // Fixed mock for demo
  const upliftTrend = 44.7
  const graphStatus = getGraphStatus(graph)
  const predictiveStatus = getPredictiveStatus(predictive)
  const correlationStatus = getCorrelationStatus(correlation)
  const graphData = isGraphOk(graph) ? graph : null
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

  return (
    <AppLayout
      title="Advanced Intelligence"
      subtitle="Predictive analytics and relationship insights"
      actions={
        <button
          type="button"
          className="advanced-intelligence__refresh"
          onClick={handleRefresh}
          disabled={isLoading}
          style={{
            background: 'transparent',
            border: `1px solid ${theme.palette.primary.main}`,
            color: theme.palette.primary.main,
            padding: '6px 12px',
            borderRadius: '2px',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            opacity: isLoading ? 0.5 : 1,
            fontSize: '0.875rem',
          }}
        >
          {isLoading ? 'SYNCING...' : 'SYNC WORKSPACE'}
        </button>
      }
    >
      <Box
        sx={{
          width: '100%',
          pb: 'var(--ob-space-400)',
        }}
      >
        {/* 1. Hero Section: Workspace Signals - Depth 1 (Glass Card with cyan edge) */}
        <Box className="ob-card-module ob-section-gap">
          <Typography
            variant="subtitle2"
            sx={{
              color: 'text.secondary',
              mb: 'var(--ob-space-200)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Workspace Signals
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <KPITickerCard
                label="Adoption Likelihood"
                value={`${adoptionRate.toFixed(1)}%`}
                trend={adoptionTrend}
                data={generateSparkline(adoptionRate)}
                active={true}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <KPITickerCard
                label="Projected Uplift"
                value={`${uplift.toFixed(1)}%`}
                trend={upliftTrend}
                data={generateSparkline(uplift)}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <KPITickerCard
                label="Active Experiments"
                value="12"
                trend={8.2}
                data={generateSparkline(12)}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <KPITickerCard
                label="Intelligence Score"
                value="94"
                trend={-2.4}
                data={generateSparkline(94)}
              />
            </Grid>
          </Grid>
        </Box>

        {/* Main Content Grid */}
        <Grid container spacing="var(--ob-space-300)">
          {/* 2. Relationship Intelligence (Main Centerpiece) - Depth 1 */}
          <Grid item xs={12} lg={8}>
            <Box
              className="ob-card-module"
              sx={{ height: '100%', minHeight: 500 }}
            >
              <Typography
                variant="subtitle2"
                sx={{
                  color: 'text.secondary',
                  mb: 'var(--ob-space-200)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Relationship Intelligence
              </Typography>
              {graphStatus === 'ok' ? (
                <Suspense
                  fallback={<IntelligenceLoadingPanel minHeight={600} />}
                >
                  <RelationshipGraph
                    nodes={graphData!.graph.nodes.map((n) => ({
                      id: n.id,
                      label: n.label,
                      category: n.category as 'Team' | 'Workflow',
                      weight: n.score,
                    }))}
                    links={graphData!.graph.edges.map((e) => ({
                      source: e.source,
                      target: e.target,
                      strength: e.weight ?? 1,
                    }))}
                    height={600}
                  />
                </Suspense>
              ) : (
                <IntelligenceStatusPanel
                  status={graphStatus}
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
                  minHeight={600}
                />
              )}
            </Box>
          </Grid>

          {/* 3. Predictive & Correlation (Side Panel) - Depth 1 */}
          <Grid item xs={12} lg={4}>
            <Box className="ob-card-module" sx={{ mb: 'var(--ob-space-300)' }}>
              <Typography
                variant="subtitle2"
                sx={{
                  color: 'text.secondary',
                  mb: 'var(--ob-space-200)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Predictive Forecast
              </Typography>
              {predictiveStatus === 'ok' ? (
                <Suspense
                  fallback={<IntelligenceLoadingPanel minHeight={280} />}
                >
                  {predictiveData!.segments.slice(0, 5).map((segment) => (
                    <ConfidenceGauge
                      key={segment.segmentId}
                      label={segment.segmentName}
                      value={Math.round(segment.probability * 100)}
                      projection={`Projection: ${segment.projection}`}
                    />
                  ))}
                </Suspense>
              ) : (
                <IntelligenceStatusPanel
                  status={predictiveStatus}
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
            </Box>

            <Box className="ob-card-module">
              <Typography
                variant="subtitle2"
                sx={{
                  color: 'text.secondary',
                  mb: 'var(--ob-space-200)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Cross-Correlation
              </Typography>
              {correlationStatus === 'ok' ? (
                <Suspense
                  fallback={<IntelligenceLoadingPanel minHeight={280} />}
                >
                  <CorrelationHeatmap
                    data={correlationData!.relationships.map((r) => ({
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
                  status={correlationStatus}
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
            </Box>
          </Grid>
        </Grid>
      </Box>
    </AppLayout>
  )
}

export default AdvancedIntelligencePage
