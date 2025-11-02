import {
  Box,
  Card,
  CardContent,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import type { RoiSummary } from '../types'

interface RoiPanelProps {
  summary: RoiSummary
}

const ROI_NOT_AVAILABLE = 'Not available yet'

export function RoiPanel({ summary }: RoiPanelProps) {
  return (
    <Paper elevation={0} className="bp-roi">
      <Box className="bp-roi__header">
        <Typography variant="h6">Automation ROI</Typography>
        <Typography variant="body2" color="text.secondary">
          Metrics derive from overlay workflows (automation score, hours saved,
          payback period) and connect directly to the ROI analytics service.
        </Typography>
      </Box>

      <Grid container spacing={2} className="bp-roi__grid">
        <Grid item xs={6} sm={4}>
          <RoiStat label="Projects tracked" value={summary.projectCount} />
        </Grid>
        <Grid item xs={6} sm={4}>
          <RoiStat
            label="Hours saved"
            value={
              summary.totalReviewHoursSaved !== null
                ? `${summary.totalReviewHoursSaved.toFixed(1)}h`
                : ROI_NOT_AVAILABLE
            }
          />
        </Grid>
        <Grid item xs={6} sm={4}>
          <RoiStat label="Avg automation" value={formatPercent(summary.averageAutomationScore)} />
        </Grid>
        <Grid item xs={6} sm={4}>
          <RoiStat label="Avg acceptance" value={formatPercent(summary.averageAcceptanceRate)} />
        </Grid>
        <Grid item xs={6} sm={4}>
          <RoiStat
            label="Avg savings"
            value={formatPercent(summary.averageSavingsPercent, true)}
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
          />
        </Grid>
      </Grid>

      <Box className="bp-roi__projects">
        <Typography variant="subtitle1" gutterBottom>
          Project breakdown
        </Typography>
        {summary.projects.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No ROI records yet. Metrics populate after overlay runs complete.
          </Typography>
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
}

function RoiStat({ label, value }: RoiStatProps) {
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
        <Typography variant="h6" className="bp-roi__stat-value">
          {displayValue}
        </Typography>
        {isPending && (
          <Typography variant="caption" color="text.secondary">
            Metrics will appear after your first automation run.
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
