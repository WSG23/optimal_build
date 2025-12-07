import {
  Box,
  Button, // Added Button
  Card,
  CardContent,
  Grid,
  Paper,
  Skeleton, // Added Skeleton
  Stack, // Added Stack
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { PlayArrow } from '@mui/icons-material' // Added icon
import type { RoiSummary } from '../types'

interface RoiPanelProps {
  summary: RoiSummary
}

const ROI_NOT_AVAILABLE = 'Not available yet'

export function RoiPanel({ summary }: RoiPanelProps) {
  // Simple heuristic: if we have 0 projects but summary counts are null, it might be loading/fresh.
  // For this "World Class" UI, we treat explicit nulls as "Connecting..." -> Skeleton,
  // and explicit 0 count as "Empty State".

  const isLoading = summary.projectCount === 0 && summary.totalReviewHoursSaved === null;

  return (
    <Paper elevation={0} className="bp-roi">
      <Box className="bp-roi__header">
        <Typography variant="h6">Automation ROI</Typography>
        <Typography variant="body2" color="text.secondary">
          Metrics derive from overlay workflows (automation score, hours saved,
          payback period).
        </Typography>
      </Box>

      <Grid container spacing={2} className="bp-roi__grid">
        <Grid item xs={6} sm={4}>
          <RoiStat label="Projects tracked" value={summary.projectCount} loading={isLoading} />
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
          <RoiStat label="Avg automation" value={formatPercent(summary.averageAutomationScore)} loading={isLoading} />
        </Grid>
        <Grid item xs={6} sm={4}>
          <RoiStat label="Avg acceptance" value={formatPercent(summary.averageAcceptanceRate)} loading={isLoading} />
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

      <Box className="bp-roi__projects" sx={{ mt: 4 }}>
        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
          Project breakdown
        </Typography>
        {summary.projects.length === 0 ? (
          <Paper
            variant="outlined"
            sx={{
                p: 4,
                textAlign: 'center',
                background: 'rgba(255,255,255,0.02)',
                borderStyle: 'dashed'
            }}
          >
            <Stack spacing={2} alignItems="center">
                <Box sx={{ p: 2, borderRadius: '50%', background: 'rgba(33, 150, 243, 0.1)', color: '#2196f3' }}>
                    <PlayArrow fontSize="large" />
                </Box>
                <Typography variant="h6" color="text.primary">
                    Start your first Automation Run
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 400 }}>
                    Connect your project data to the overlay engine to start tracking hours saved and efficiency gains.
                </Typography>
                <Button
                    variant="contained"
                    color="primary"
                    startIcon={<PlayArrow />}
                    sx={{ mt: 1 }}
                >
                    Launch Overlay Engine
                </Button>
            </Stack>
          </Paper>
        ) : (
          <TableContainer component={Paper} variant="outlined">
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
                      {project.paybackWeeks ? `${project.paybackWeeks}w` : ROI_NOT_AVAILABLE}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>
    </Paper>
  )
}

interface RoiStatProps {
  label: string
  value: string | number
  loading?: boolean
}

function RoiStat({ label, value, loading }: RoiStatProps) {
  const displayValue = value
  const isPending = displayValue === ROI_NOT_AVAILABLE

  return (
    <Card
      variant="outlined"
      className={`bp-roi__stat${isPending ? ' bp-roi__stat--pending' : ''}`}
    >
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          {label}
        </Typography>
        {loading ? (
             <Skeleton width="60%" height={32} />
        ) : (
            <Typography variant="h6" className="bp-roi__stat-value">
              {displayValue}
            </Typography>
        )}
        {isPending && !loading && (
          <Typography variant="caption" color="text.secondary">
            Waiting for data...
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
