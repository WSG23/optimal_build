import HistoryIcon from '@mui/icons-material/History'
import TimelineIcon from '@mui/icons-material/Timeline'
import {
  Alert,
  Box,
  Chip,
  Divider,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material'
import {
  Timeline,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineItem,
  TimelineOppositeContent,
  TimelineSeparator,
} from '@mui/lab'
import type { CommissionEntry, DealSnapshot, StageEvent } from '../types'

interface DealInsightsPanelProps {
  deal: DealSnapshot | null
  timeline: StageEvent[]
  commissions: CommissionEntry[]
}

export function DealInsightsPanel({
  deal,
  timeline,
  commissions,
}: DealInsightsPanelProps) {
  if (!deal) {
    return (
      <Paper elevation={0} className="bp-deal-panel bp-deal-panel--empty">
        <Typography variant="h6" gutterBottom>
          Select a deal to inspect
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Choose any card in the pipeline to review stage history, commission
          records, and audit metadata.
        </Typography>
      </Paper>
    )
  }

  return (
    <Paper elevation={0} className="bp-deal-panel">
      <Box className="bp-deal-panel__header">
        <Box>
          <Typography variant="h6">{deal.title ?? deal.id}</Typography>
          <Stack
            direction="row"
            spacing="var(--ob-space-100)"
            className="bp-deal-panel__meta"
          >
            <Chip size="small" label={`Assigned to ${deal.agentName}`} />
            {deal.leadSource && (
              <Chip size="small" label={`Source ${deal.leadSource}`} />
            )}
            {deal.expectedCloseDate && (
              <Chip
                size="small"
                label={`Expected close ${deal.expectedCloseDate}`}
              />
            )}
          </Stack>
        </Box>
      </Box>

      <Divider sx={{ my: 'var(--ob-space-200)' }} />

      <Box className="bp-deal-panel__section">
        <Stack
          direction="row"
          spacing="var(--ob-space-100)"
          alignItems="center"
          mb="var(--ob-space-100)"
        >
          <TimelineIcon fontSize="small" color="primary" />
          <Typography variant="subtitle1">Stage timeline</Typography>
        </Stack>
        {timeline.length === 0 ? (
          <Alert severity="info" icon={<HistoryIcon fontSize="small" />}>
            No stage events yet.
          </Alert>
        ) : (
          <Timeline position="right" className="bp-deal-panel__timeline">
            {timeline.map((event, index) => (
              <TimelineItem key={event.id}>
                <TimelineOppositeContent color="text.secondary">
                  <Typography variant="caption">{event.recordedAt}</Typography>
                </TimelineOppositeContent>
                <TimelineSeparator>
                  <TimelineDot
                    color={
                      index === timeline.length - 1 ? 'primary' : 'inherit'
                    }
                  />
                  {index < timeline.length - 1 && <TimelineConnector />}
                </TimelineSeparator>
                <TimelineContent>
                  <Typography
                    variant="body1"
                    className="bp-deal-panel__timeline-stage"
                  >
                    {event.toStage.replace('_', ' ')}
                  </Typography>
                  <Stack
                    direction="row"
                    spacing="var(--ob-space-100)"
                    flexWrap="wrap"
                    className="bp-deal-panel__timeline-body"
                  >
                    {event.durationSeconds !== null &&
                      event.durationSeconds !== undefined && (
                        <Chip
                          size="small"
                          variant="outlined"
                          label={`${Math.round(event.durationSeconds / 3600).toFixed(0)}h duration`}
                        />
                      )}
                    {event.changedBy && (
                      <Chip
                        size="small"
                        variant="outlined"
                        label={`By ${event.changedBy}`}
                      />
                    )}
                  </Stack>
                  {event.note && (
                    <Typography
                      variant="body2"
                      className="bp-deal-panel__timeline-note"
                    >
                      {event.note}
                    </Typography>
                  )}
                  {(event.auditHash || event.auditSignature) && (
                    <Tooltip
                      title={
                        <span>
                          Hash: {event.auditHash ?? '—'}
                          <br /> Signature: {event.auditSignature ?? '—'}
                        </span>
                      }
                    >
                      <Chip
                        size="small"
                        color="secondary"
                        label="Audit metadata"
                      />
                    </Tooltip>
                  )}
                </TimelineContent>
              </TimelineItem>
            ))}
          </Timeline>
        )}
      </Box>

      <Divider sx={{ my: 'var(--ob-space-200)' }} />

      <Box className="bp-deal-panel__section">
        <Stack
          direction="row"
          spacing="var(--ob-space-100)"
          alignItems="center"
          mb="var(--ob-space-100)"
        >
          <HistoryIcon fontSize="small" color="primary" />
          <Typography variant="subtitle1">Commission ledger</Typography>
        </Stack>
        {commissions.length === 0 ? (
          <Alert severity="info">No commission records yet.</Alert>
        ) : (
          <TableContainer
            component={Paper}
            variant="outlined"
            className="bp-commission-table"
          >
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  <TableCell align="right">Updated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {commissions.map((commission) => (
                  <TableRow key={commission.id} hover>
                    <TableCell>{commission.type}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        className={`bp-status bp-status--${commission.status}`}
                        label={commission.status}
                      />
                    </TableCell>
                    <TableCell align="right">
                      {commission.amount !== null
                        ? `${commission.currency} ${commission.amount.toLocaleString()}`
                        : '—'}
                    </TableCell>
                    <TableCell align="right">
                      {commission.confirmedAt ?? commission.disputedAt ?? '—'}
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
