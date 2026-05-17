import {
  Box,
  Button, // Added Button
  Card,
  CardContent,
  Grid,
  Paper,
  Skeleton, // Added Skeleton
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import PlayArrow from '@mui/icons-material/PlayArrow'
import { ChartPlaceholder } from '../../../../components/common/ChartPlaceholder'
import type { RoiSummary } from '../types'
import { GlassCard } from '../../../../components/canonical/GlassCard'

interface RoiPanelProps {
  summary: RoiSummary
}

const ROI_NOT_AVAILABLE = 'Not available yet'

export function RoiPanel({ summary }: RoiPanelProps) {
  // Simple heuristic: if we have 0 projects but summary counts are null, it might be loading/fresh.
  // For this "World Class" UI, we treat explicit nulls as "Connecting..." -> Skeleton,
  // and explicit 0 count as "Empty State".

  const isLoading =
    summary.projectCount === 0 && summary.totalReviewHoursSaved === null

  return (
    <GlassCard elevation={0} className="bp-roi">
      <Box className="bp-roi__header">
        <Typography variant="h6">Automation ROI</Typography>
        <Typography variant="body2" color="text.secondary">
          Metrics derive from overlay workflows (automation score, hours saved,
          payback period).
        </Typography>
      </Box>

      <Grid container spacing="var(--ob-space-200)" className="bp-roi__grid">
        <Grid item xs={6} sm={4}>
          <RoiStat
            label="Projects tracked"
            value={summary.projectCount}
            loading={isLoading}
          />
        </Grid>
        <Grid item xs={6} sm={4}>
          <RoiStat
            label="Hours saved"
            value={
              summary.totalReviewHoursSaved !== null
                ? `${summary.totalReviewHoursSaved.toFixed(1)}h`
                : ROI_NOT_AVAILABLE
            }
            loading={isLoading}
          />
        </Grid>
        <Grid item xs={6} sm={4}>
          <RoiStat
            label="Avg automation"
            value={formatPercent(summary.averageAutomationScore)}
            loading={isLoading}
          />
        </Grid>
        <Grid item xs={6} sm={4}>
          <RoiStat
            label="Avg acceptance"
            value={formatPercent(summary.averageAcceptanceRate)}
            loading={isLoading}
          />
        </Grid>
        <Grid item xs={6} sm={4}>
          <RoiStat
            label="Avg savings"
            value={formatPercent(summary.averageSavingsPercent, true)}
            loading={isLoading}
          />
        </Grid>
        <Grid item xs={6} sm={4}>
          <RoiStat
            label="Best payback"
            value={
              summary.bestPaybackWeeks !== null
                ? `${summary.bestPaybackWeeks} weeks`
                : ROI_NOT_AVAILABLE
            }
            loading={isLoading}
          />
        </Grid>
      </Grid>

      <Box className="bp-roi__projects" sx={{ mt: 'var(--ob-space-300)' }}>
        <Typography
          variant="subtitle1"
          gutterBottom
          sx={{ fontWeight: 'var(--ob-font-weight-semibold)' }}
        >
          Project breakdown
        </Typography>
        {summary.projects.length === 0 ? (
          <Box sx={{ mt: 'var(--ob-space-200)' }}>
            <ChartPlaceholder
              height={300}
              label="No Projects Tracked"
              subLabel="Connect your project data to the overlay engine to start tracking hours saved and efficiency gains."
            />
            <Box sx={{ textAlign: 'center', mt: 'var(--ob-space-200)' }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={<PlayArrow />}
              >
                Launch Overlay Engine
              </Button>
            </Box>
          </Box>
        ) : (
          <TableContainer component={Paper} variant="outlined"> // canon-ok: MUI TableContainer needs Paper as component
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Project</TableCell>
                  <TableCell align="right">Hours saved</TableCell>
                  <TableCell align="right">Automation</TableCell>
                  <TableCell align="right">Acceptance</TableCell>
                  <TableCell align="right">Payback</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {summary.projects.map((project) => (
                  <TableRow key={project.projectId} hover>
                    <TableCell>#{project.projectId}</TableCell>
                    <TableCell align="right">
                      {formatNumber(project.hoursSaved, 'h')}
                    </TableCell>
                    <TableCell align="right">
                      {formatPercent(project.automationScore)}
                    </TableCell>
                    <TableCell align="right">
                      {formatPercent(project.acceptanceRate)}
                    </TableCell>
                    <TableCell align="right">
                      {project.paybackWeeks
                        ? `${project.paybackWeeks}w`
                        : ROI_NOT_AVAILABLE}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>
    </GlassCard>
  )
}

interface RoiStatProps {
  label: string
  value: string | number
  loading?: boolean
}

function RoiStat({ label, value, loading }: RoiStatProps) {
  // If explicitly loading OR value is the "Not available" sentinel, show skeleton
  const showSkeleton = loading || value === ROI_NOT_AVAILABLE || value === null

  // If we have a real value but it's 0 (and not loading), we show it.

  return (
    <Card
      variant="outlined"
      className="bp-roi__stat"
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}
    >
      <CardContent>
        <Typography
          variant="overline"
          color="text.secondary"
          sx={{ opacity: 0.8 }}
        >
          {label}
        </Typography>
        {showSkeleton ? (
          <Skeleton
            width="60%"
            height={40}
            sx={{
              mt: 'var(--ob-space-100)',
              borderRadius: 'var(--ob-radius-sm)',
            }}
            animation="wave"
          />
        ) : (
          <Typography
            variant="h4"
            className="bp-roi__stat-value"
            sx={{
              mt: 'var(--ob-space-100)',
              fontWeight: 'var(--ob-font-weight-bold)',
            }}
          >
            {value}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}

function formatNumber(value: number | null, suffix: string = '') {
  if (value === null || Number.isNaN(value)) return ROI_NOT_AVAILABLE
  return `${value.toFixed(1)}${suffix}`
}

function formatPercent(value: number | null, absolute = false) {
  if (value === null || Number.isNaN(value)) return ROI_NOT_AVAILABLE
  const normalized = absolute ? value : value * 100
  return `${normalized.toFixed(1)}%`
}
