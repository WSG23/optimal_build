import { ReactNode, useCallback, useContext, useMemo } from 'react'
import { Box, Grid, Typography, useTheme } from '@mui/material'
import {
  AccountTreeOutlined,
  AutoGraph,
  ErrorOutline,
  HubOutlined,
} from '@mui/icons-material'

import { AppLayout } from '../../App'
import { EmptyState, Skeleton, SkeletonText } from '../../components/canonical'
import { ProjectContext } from '../../contexts/projectContextDef'
import { useRouterParams } from '../../router'
import {
  type CrossCorrelationIntelligenceState,
  type GraphIntelligenceState,
  type InvestigationAnalyticsServices,
  type PredictiveIntelligenceState,
  useInvestigationAnalytics,
} from '../../hooks/useInvestigationAnalytics'
import { KPITickerCard } from './components/KPITickerCard'
import { RelationshipGraph } from './components/RelationshipGraph'
import { ConfidenceGauge } from './components/ConfidenceGauge'
import { CorrelationHeatmap } from './components/CorrelationHeatmap'

export interface AdvancedIntelligencePageProps {
  projectId?: string
  services?: Partial<InvestigationAnalyticsServices>
}

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
            'radial-gradient(circle at top, var(--ob-overlay-brand-faint), transparent 65%), var(--ob-surface-glass-1)',
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
          ? '1px solid var(--ob-overlay-error-subtle)'
          : '1px dashed var(--ob-overlay-white-subtle)',
        background: isError
          ? 'radial-gradient(circle at top, var(--ob-overlay-error-faint), transparent 65%), var(--ob-surface-glass-1)'
          : 'radial-gradient(circle at top, var(--ob-overlay-brand-faint), transparent 65%), var(--ob-surface-glass-1)',
      }}
    />
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

interface AdvancedIntelligenceContentProps {
  projectId: string
  services?: Partial<InvestigationAnalyticsServices>
}

function AdvancedIntelligenceContent({
  projectId,
  services,
}: AdvancedIntelligenceContentProps) {
  const { graph, predictive, correlation, isLoading, refetch } =
    useInvestigationAnalytics(projectId, services)
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

  const predictiveSegments =
    predictive.status === 'ok' ? predictive.segments : []
  const experimentCount = predictiveSegments.length
  const hasPredictiveSignals = predictive.status === 'ok' && experimentCount > 0
  const intelligenceScore = useMemo(() => {
    if (graph.status !== 'ok') {
      return null
    }
    if (graph.graph.nodes.length === 0) {
      return null
    }
    const total = graph.graph.nodes.reduce((sum, node) => sum + node.score, 0)
    return (total / graph.graph.nodes.length) * 100
  }, [graph])
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
            fontSize: 'var(--ob-font-size-sm)',
          }}
        >
          {isLoading ? 'SYNCING...' : 'SYNC PROJECT'}
        </button>
      }
    >
      <Box
        sx={{
          width: '100%',
          pb: 'var(--ob-space-400)',
        }}
      >
        {/* 1. Hero Section: Project Signals - Depth 1 (Glass Card with cyan edge) */}
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
            Project Signals
          </Typography>
          <Grid container spacing="var(--ob-space-150)">
            <Grid item xs={12} md={3}>
              <KPITickerCard
                label="Adoption Likelihood"
                value={
                  hasPredictiveSignals ? `${adoptionRate.toFixed(1)}%` : 'N/A'
                }
                trend={null}
                data={null}
                active={true}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <KPITickerCard
                label="Projected Uplift"
                value={hasPredictiveSignals ? `${uplift.toFixed(1)}%` : 'N/A'}
                trend={null}
                data={null}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <KPITickerCard
                label="Active Experiments"
                value={hasPredictiveSignals ? String(experimentCount) : 'N/A'}
                trend={null}
                data={null}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <KPITickerCard
                label="Intelligence Score"
                value={
                  intelligenceScore === null
                    ? 'N/A'
                    : Math.round(intelligenceScore).toString()
                }
                trend={null}
                data={null}
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
                predictiveData!.segments
                  .slice(0, 5)
                  .map((segment) => (
                    <ConfidenceGauge
                      key={segment.segmentId}
                      label={segment.segmentName}
                      value={Math.round(segment.probability * 100)}
                      projection={`Projection: ${segment.projection}`}
                    />
                  ))
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
                  emptyTitle="No predictive signals available for this project yet"
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
                <CorrelationHeatmap
                  data={correlationData!.relationships.map((r) => ({
                    id: r.pairId,
                    driver: r.driver,
                    outcome: r.outcome,
                    coefficient: r.coefficient,
                    pValue: r.pValue,
                  }))}
                />
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

export function AdvancedIntelligencePage({
  projectId,
  services,
}: AdvancedIntelligencePageProps) {
  const params = useRouterParams()
  const projectContext = useContext(ProjectContext)
  const theme = useTheme()
  const effectiveProjectId =
    projectId?.trim() ||
    params.projectId?.trim() ||
    projectContext?.currentProject?.id ||
    ''

  if (!effectiveProjectId) {
    return (
      <AppLayout
        title="Advanced Intelligence"
        subtitle="Predictive analytics and relationship insights"
        actions={
          <button
            type="button"
            className="advanced-intelligence__refresh"
            disabled={true}
            style={{
              background: 'transparent',
              border: `1px solid ${theme.palette.primary.main}`,
              color: theme.palette.primary.main,
              padding: '6px 12px',
              borderRadius: '2px',
              cursor: 'not-allowed',
              opacity: 0.5,
              fontSize: 'var(--ob-font-size-sm)',
            }}
          >
            SELECT PROJECT
          </button>
        }
      >
        <Box
          sx={{
            width: '100%',
            pb: 'var(--ob-space-400)',
          }}
        >
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
              Project Signals
            </Typography>
            <Grid container spacing="var(--ob-space-150)">
              <Grid item xs={12} md={3}>
                <KPITickerCard
                  label="Adoption Likelihood"
                  value="N/A"
                  trend={null}
                  data={null}
                  active={true}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <KPITickerCard
                  label="Projected Uplift"
                  value="N/A"
                  trend={null}
                  data={null}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <KPITickerCard
                  label="Active Experiments"
                  value="N/A"
                  trend={null}
                  data={null}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <KPITickerCard
                  label="Intelligence Score"
                  value="N/A"
                  trend={null}
                  data={null}
                />
              </Grid>
            </Grid>
          </Box>

          <Grid container spacing="var(--ob-space-300)">
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
                <IntelligenceStatusPanel
                  status="empty"
                  icon={
                    <HubOutlined
                      sx={{ color: 'var(--ob-color-brand-primary)' }}
                    />
                  }
                  loadingLabel="Mapping organization network..."
                  emptyTitle="Select a project to load intelligence graph"
                  emptyDescription="Advanced Intelligence now runs against a real project scope. Pick a project from the selector or open a project route first."
                  errorTitle="Unable to load intelligence graph"
                  minHeight={600}
                />
              </Box>
            </Grid>

            <Grid item xs={12} lg={4}>
              <Box
                className="ob-card-module"
                sx={{ mb: 'var(--ob-space-300)' }}
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
                  Predictive Forecast
                </Typography>
                <IntelligenceStatusPanel
                  status="empty"
                  icon={
                    <AutoGraph
                      sx={{ color: 'var(--ob-color-brand-primary)' }}
                    />
                  }
                  loadingLabel="Running predictive models..."
                  emptyTitle="Select a project to load predictive signals"
                  emptyDescription="Choose a project to evaluate workflow, finance, and delivery signals."
                  errorTitle="Unable to load predictive forecast"
                  minHeight={280}
                />
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
                <IntelligenceStatusPanel
                  status="empty"
                  icon={
                    <AccountTreeOutlined
                      sx={{ color: 'var(--ob-color-brand-primary)' }}
                    />
                  }
                  loadingLabel="Analyzing correlations..."
                  emptyTitle="Select a project to analyze correlations"
                  emptyDescription="Correlation analysis needs a concrete project scope before it can inspect approvals, workflow activity, and finance history."
                  errorTitle="Unable to load correlation analysis"
                  minHeight={280}
                />
              </Box>
            </Grid>
          </Grid>
        </Box>
      </AppLayout>
    )
  }

  return (
    <AdvancedIntelligenceContent
      projectId={effectiveProjectId}
      services={services}
    />
  )
}

export default AdvancedIntelligencePage
