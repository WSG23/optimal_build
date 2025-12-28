import { useCallback, useMemo } from 'react'
import { Box, Grid, Typography, useTheme } from '@mui/material'

import { AppLayout } from '../../App'
import {
  type InvestigationAnalyticsServices,
  useInvestigationAnalytics,
} from '../../hooks/useInvestigationAnalytics'
import { KPITickerCard } from './components/KPITickerCard'
import { RelationshipGraph } from './components/RelationshipGraph'
import { ConfidenceGauge } from './components/ConfidenceGauge'
import { CorrelationHeatmap } from './components/CorrelationHeatmap'

export interface AdvancedIntelligencePageProps {
  workspaceId?: string
  services?: Partial<InvestigationAnalyticsServices>
}

const DEFAULT_WORKSPACE_ID = 'default-investigation'

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
              {graph.status === 'ok' ? (
                <RelationshipGraph
                  nodes={graph.graph.nodes.map((n) => ({
                    id: n.id,
                    label: n.label,
                    category: n.category as 'Team' | 'Workflow',
                    weight: n.score,
                  }))}
                  links={graph.graph.edges.map((e) => ({
                    source: e.source,
                    target: e.target,
                    strength: e.weight ?? 1,
                  }))}
                  height={600}
                />
              ) : (
                <Box
                  sx={{
                    height: 600,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px dashed grey',
                    borderRadius: '4px', // Square Cyber-Minimalism: sm
                  }}
                >
                  <Typography color="text.secondary">
                    {graph.status === 'loading'
                      ? 'Mapping organization network...'
                      : 'No relationship data available'}
                  </Typography>
                </Box>
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
              {predictive.status === 'ok' ? (
                predictive.segments
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
                <Typography color="text.secondary">
                  Loading forecasts...
                </Typography>
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
              {correlation.status === 'ok' ? (
                <CorrelationHeatmap
                  data={correlation.relationships.map((r) => ({
                    id: r.pairId,
                    driver: r.driver,
                    outcome: r.outcome,
                    coefficient: r.coefficient,
                    pValue: r.pValue,
                  }))}
                />
              ) : (
                <Typography color="text.secondary">
                  Analyzing correlations...
                </Typography>
              )}
            </Box>
          </Grid>
        </Grid>
      </Box>
    </AppLayout>
  )
}

export default AdvancedIntelligencePage
