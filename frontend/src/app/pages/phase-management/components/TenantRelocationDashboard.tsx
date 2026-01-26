import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import PendingIcon from '@mui/icons-material/Pending'
import EventIcon from '@mui/icons-material/Event'
import type {
  TenantCoordinationSummary,
  TenantRelocation,
} from '../../../../api/development'

interface TenantRelocationDashboardProps {
  data: TenantCoordinationSummary
  onTenantClick?: (tenantId: number) => void
}

const STATUS_CONFIG: Record<
  string,
  {
    color:
      | 'default'
      | 'primary'
      | 'secondary'
      | 'error'
      | 'warning'
      | 'success'
      | 'info'
    label: string
  }
> = {
  pending_notification: { color: 'warning', label: 'Pending Notification' },
  notified: { color: 'info', label: 'Notified' },
  confirmed: { color: 'primary', label: 'Confirmed' },
  in_progress: { color: 'secondary', label: 'In Progress' },
  relocated: { color: 'success', label: 'Relocated' },
  returned: { color: 'success', label: 'Returned' },
  cancelled: { color: 'error', label: 'Cancelled' },
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString('en-SG', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

function formatCurrency(value: number | null): string {
  if (value === null) return '-'
  return new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
    maximumFractionDigits: 0,
  }).format(value)
}

interface StatusSummaryCardProps {
  title: string
  count: number
  total: number
  color: string
}

function StatusSummaryCard({
  title,
  count,
  total,
  color,
}: StatusSummaryCardProps) {
  const percentage = total > 0 ? (count / total) * 100 : 0

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h4" sx={{ fontWeight: 600, color }}>
          {count}
        </Typography>
        <LinearProgress
          variant="determinate"
          value={percentage}
          sx={{
            mt: 'var(--ob-space-100)',
            height: 6,
            borderRadius: 'var(--ob-radius-md)',
            backgroundColor: '#e0e0e0',
            '& .MuiLinearProgress-bar': {
              backgroundColor: color,
              borderRadius: 'var(--ob-radius-md)',
            },
          }}
        />
        <Typography variant="caption" color="text.secondary">
          {percentage.toFixed(0)}% of total
        </Typography>
      </CardContent>
    </Card>
  )
}

interface RelocationTableProps {
  relocations: TenantRelocation[]
  title: string
  emptyMessage: string
  onRowClick?: (id: number) => void
}

function RelocationTable({
  relocations,
  title,
  emptyMessage,
  onRowClick,
}: RelocationTableProps) {
  if (relocations.length === 0) {
    return (
      <Paper
        variant="outlined"
        sx={{ p: 'var(--ob-space-300)', textAlign: 'center' }}
      >
        <Typography color="text.secondary">{emptyMessage}</Typography>
      </Paper>
    )
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow sx={{ backgroundColor: '#fafafa' }}>
            <TableCell colSpan={6}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {title} ({relocations.length})
              </Typography>
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Tenant</TableCell>
            <TableCell>Current Unit</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Notification</TableCell>
            <TableCell>Move Date</TableCell>
            <TableCell align="right">Compensation</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {relocations.map((relocation) => {
            const statusConfig = STATUS_CONFIG[relocation.status] || {
              color: 'default' as const,
              label: relocation.status,
            }
            return (
              <TableRow
                key={relocation.id}
                hover
                sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
                onClick={() => onRowClick?.(relocation.id)}
              >
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {relocation.tenantName}
                  </Typography>
                </TableCell>
                <TableCell>{relocation.currentUnit}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={statusConfig.label}
                    color={statusConfig.color}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>{formatDate(relocation.notificationDate)}</TableCell>
                <TableCell>
                  {relocation.actualMoveDate
                    ? formatDate(relocation.actualMoveDate)
                    : formatDate(relocation.plannedMoveDate)}
                </TableCell>
                <TableCell align="right">
                  {formatCurrency(relocation.compensationAmount)}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

// Custom Timeline component (simpler alternative to MUI Lab Timeline)
interface TimelineEventProps {
  date: string
  tenantName: string
  event: string
  status: string
  isLast: boolean
}

function TimelineEvent({
  date,
  tenantName,
  event,
  status,
  isLast,
}: TimelineEventProps) {
  const isCompleted = status === 'relocated' || status === 'returned'
  const isPending = status === 'pending_notification' || status === 'notified'

  const dotColor = isCompleted
    ? '#10b981'
    : isPending
      ? '#f59e0b'
      : 'var(--ob-color-primary)'

  return (
    <Box sx={{ display: 'flex', mb: isLast ? 0 : 2 }}>
      {/* Left side - date */}
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{
          width: 80,
          flexShrink: 0,
          textAlign: 'right',
          pr: 'var(--ob-space-200)',
          pt: 'var(--ob-space-50)',
        }}
      >
        {formatDate(date)}
      </Typography>

      {/* Middle - dot and line */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          px: 'var(--ob-space-100)',
        }}
      >
        <Box
          sx={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            backgroundColor: isCompleted ? dotColor : 'white',
            border: `2px solid ${dotColor}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          {isCompleted ? (
            <CheckCircleIcon sx={{ fontSize: 16, color: 'white' }} />
          ) : isPending ? (
            <PendingIcon sx={{ fontSize: 14, color: dotColor }} />
          ) : (
            <EventIcon sx={{ fontSize: 14, color: dotColor }} />
          )}
        </Box>
        {!isLast && (
          <Box
            sx={{
              width: 2,
              flex: 1,
              minHeight: 20,
              backgroundColor: '#e0e0e0',
              mt: 'var(--ob-space-50)',
            }}
          />
        )}
      </Box>

      {/* Right side - content */}
      <Box sx={{ flex: 1, pl: 'var(--ob-space-100)', pb: isLast ? 0 : 1 }}>
        <Typography variant="body2" sx={{ fontWeight: 500 }}>
          {tenantName}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {event}
        </Typography>
      </Box>
    </Box>
  )
}

export function TenantRelocationDashboard({
  data,
  onTenantClick,
}: TenantRelocationDashboardProps) {
  const {
    totalTenants,
    statusBreakdown,
    relocations,
    upcomingMoves,
    overdueNotifications,
    timeline,
    warnings,
  } = data

  // Calculate summary counts
  const relocated =
    (statusBreakdown['relocated'] ?? 0) + (statusBreakdown['returned'] ?? 0)
  const inProgress = statusBreakdown['in_progress'] ?? 0
  const pending =
    (statusBreakdown['pending_notification'] ?? 0) +
    (statusBreakdown['notified'] ?? 0) +
    (statusBreakdown['confirmed'] ?? 0)

  return (
    <Box>
      {/* Warnings */}
      {warnings.length > 0 && (
        <Stack spacing="var(--ob-space-100)" sx={{ mb: 'var(--ob-space-300)' }}>
          {warnings.map((warning, idx) => (
            <Alert key={idx} severity="warning" icon={<WarningAmberIcon />}>
              {warning}
            </Alert>
          ))}
        </Stack>
      )}

      {/* Summary Cards */}
      <Grid
        container
        spacing="var(--ob-space-200)"
        sx={{ mb: 'var(--ob-space-300)' }}
      >
        <Grid item xs={6} md={3}>
          <StatusSummaryCard
            title="Total Tenants"
            count={totalTenants}
            total={totalTenants}
            color="#3b82f6"
          />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatusSummaryCard
            title="Pending"
            count={pending}
            total={totalTenants}
            color="#f59e0b"
          />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatusSummaryCard
            title="In Progress"
            count={inProgress}
            total={totalTenants}
            color="#8b5cf6"
          />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatusSummaryCard
            title="Completed"
            count={relocated}
            total={totalTenants}
            color="#10b981"
          />
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing="var(--ob-space-300)">
        {/* Left Column - Tables */}
        <Grid item xs={12} lg={8}>
          <Stack spacing="var(--ob-space-300)">
            {/* Overdue Notifications */}
            {overdueNotifications.length > 0 && (
              <Box>
                <Typography
                  variant="subtitle1"
                  sx={{
                    mb: 'var(--ob-space-100)',
                    fontWeight: 600,
                    color: 'error.main',
                  }}
                >
                  Overdue Notifications
                </Typography>
                <RelocationTable
                  relocations={overdueNotifications}
                  title="Requires Immediate Action"
                  emptyMessage="No overdue notifications"
                  onRowClick={onTenantClick}
                />
              </Box>
            )}

            {/* Upcoming Moves */}
            <Box>
              <Typography
                variant="subtitle1"
                sx={{ mb: 'var(--ob-space-100)', fontWeight: 600 }}
              >
                Upcoming Relocations
              </Typography>
              <RelocationTable
                relocations={upcomingMoves}
                title="Next 30 Days"
                emptyMessage="No upcoming relocations scheduled"
                onRowClick={onTenantClick}
              />
            </Box>

            {/* All Relocations */}
            <Box>
              <Typography
                variant="subtitle1"
                sx={{ mb: 'var(--ob-space-100)', fontWeight: 600 }}
              >
                All Tenant Relocations
              </Typography>
              <RelocationTable
                relocations={relocations}
                title="Complete List"
                emptyMessage="No tenant relocations recorded"
                onRowClick={onTenantClick}
              />
            </Box>
          </Stack>
        </Grid>

        {/* Right Column - Timeline */}
        <Grid item xs={12} lg={4}>
          <Paper variant="outlined" sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle1"
              sx={{ mb: 'var(--ob-space-200)', fontWeight: 600 }}
            >
              Activity Timeline
            </Typography>

            {timeline.length === 0 ? (
              <Typography
                color="text.secondary"
                sx={{ textAlign: 'center', py: 'var(--ob-space-300)' }}
              >
                No activity recorded yet
              </Typography>
            ) : (
              <Box>
                {timeline.slice(0, 10).map((event, idx) => (
                  <TimelineEvent
                    key={idx}
                    date={event.date}
                    tenantName={event.tenantName}
                    event={event.event}
                    status={event.status}
                    isLast={idx === Math.min(timeline.length, 10) - 1}
                  />
                ))}
              </Box>
            )}

            {timeline.length > 10 && (
              <Divider sx={{ my: 'var(--ob-space-100)' }}>
                <Typography variant="caption" color="text.secondary">
                  +{timeline.length - 10} more events
                </Typography>
              </Divider>
            )}
          </Paper>

          {/* Status Breakdown */}
          <Paper
            variant="outlined"
            sx={{ p: 'var(--ob-space-200)', mt: 'var(--ob-space-200)' }}
          >
            <Typography
              variant="subtitle1"
              sx={{ mb: 'var(--ob-space-200)', fontWeight: 600 }}
            >
              Status Breakdown
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {Object.entries(statusBreakdown).map(([status, count]) => {
                const config = STATUS_CONFIG[status] || {
                  color: 'default' as const,
                  label: status,
                }
                return (
                  <Box
                    key={status}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <Chip
                      size="small"
                      label={config.label}
                      color={config.color}
                      variant="outlined"
                    />
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {count}
                    </Typography>
                  </Box>
                )
              })}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
