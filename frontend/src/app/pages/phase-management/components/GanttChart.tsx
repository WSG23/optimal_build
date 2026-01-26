import { useMemo } from 'react'
import { Box, Paper, Tooltip, Typography, Chip, Stack } from '@mui/material'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import PeopleIcon from '@mui/icons-material/People'
import type {
  GanttChart as GanttChartData,
  GanttTask,
} from '../../../../api/development'

interface GanttChartProps {
  data: GanttChartData
  onTaskClick?: (taskId: string) => void
  selectedTaskId?: string | null
}

const STATUS_COLORS: Record<string, string> = {
  not_started: 'var(--ob-color-text-tertiary)',
  planning: 'var(--ob-color-primary)',
  in_progress: 'var(--ob-color-warning)', // Changed to orange for gradient
  on_hold: '#ef4444',
  completed: 'var(--ob-color-success)',
  cancelled: 'var(--ob-color-text-secondary)',
}

const BAR_GRADIENTS: Record<string, string> = {
  not_started: 'linear-gradient(90deg, #64748b 0%, #94a3b8 100%)',
  planning: 'linear-gradient(90deg, #2563eb 0%, #60a5fa 100%)',
  in_progress: 'linear-gradient(90deg, #ea580c 0%, #fbbf24 100%)',
  on_hold: 'linear-gradient(90deg, #dc2626 0%, #ef4444 100%)',
  completed: 'linear-gradient(90deg, #059669 0%, #34d399 100%)',
  cancelled: 'linear-gradient(90deg, #475569 0%, #64748b 100%)',
}

const DAY_WIDTH = 24 // pixels per day
const ROW_HEIGHT = 40
const HEADER_HEIGHT = 60
const LEFT_PANEL_WIDTH = 280

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-SG', { month: 'short', day: 'numeric' })
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

function getStatusLabel(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

interface TaskBarProps {
  task: GanttTask
  startOffset: number
  isSelected: boolean
  onClick: () => void
}

function TaskBar({ task, startOffset, isSelected, onClick }: TaskBarProps) {
  const width = Math.max(task.duration * DAY_WIDTH, 20)
  const left = startOffset * DAY_WIDTH

  const tooltipContent = (
    <Box sx={{ p: 'var(--ob-space-100)' }}>
      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
        {task.name}
      </Typography>
      <Typography variant="body2" sx={{ mt: 'var(--ob-space-50)' }}>
        {formatDate(task.startDate)} - {formatDate(task.endDate)}
      </Typography>
      <Typography variant="body2">Duration: {task.duration} days</Typography>
      <Typography variant="body2">
        Progress: {Math.round(task.progress * 100)}%
      </Typography>
      {task.budgetAmount !== null && (
        <Typography variant="body2">
          Budget: {formatCurrency(task.budgetAmount)}
        </Typography>
      )}
      {task.isCritical && (
        <Chip
          size="small"
          label="Critical Path"
          color="error"
          sx={{ mt: 'var(--ob-space-100)' }}
        />
      )}
    </Box>
  )

  const gradient = BAR_GRADIENTS[task.status] || BAR_GRADIENTS.not_started

  // Striped animation for in-progress
  const stripeStyle =
    task.status === 'in_progress'
      ? {
          backgroundImage: `
      repeating-linear-gradient(
        45deg,
        var(--ob-color-surface-overlay),
        var(--ob-color-surface-overlay) 10px,
        transparent 10px,
        transparent 20px
      ),
      ${gradient}
    `,
          backgroundSize: '200% 100%',
          animation: 'progress-stripes 20s linear infinite',
          '@keyframes progress-stripes': {
            '0%': { backgroundPosition: '100% 0' },
            '100%': { backgroundPosition: '0 0' },
          },
        }
      : { background: gradient }

  return (
    <Tooltip title={tooltipContent} arrow placement="top">
      <Box
        onClick={onClick}
        sx={{
          position: 'absolute',
          left: `${left}px`,
          top: '6px',
          width: `${width}px`,
          height: `${ROW_HEIGHT - 12}px`,
          borderRadius: 'var(--ob-radius-sm)',
          cursor: 'pointer',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          border: isSelected
            ? '2px solid #00f3ff'
            : task.isCritical
              ? '1px solid rgba(255, 51, 102, 0.5)'
              : '1px solid var(--ob-color-surface-overlay)',
          boxShadow: isSelected
            ? '0 0 15px var(--ob-color-neon-cyan-muted)'
            : task.isCritical
              ? '0 2px 8px rgba(255, 51, 102, 0.2)'
              : '0 2px 4px var(--ob-color-overlay-backdrop-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          ...stripeStyle,
          '&:hover': {
            filter: 'brightness(1.2)',
            transform: 'scaleY(1.1)',
            zIndex: 10,
          },
        }}
      >
        {/* Progress bar overlay (darker) */}
        <Box
          sx={{
            position: 'absolute',
            left: 0,
            top: '0',
            bottom: '0',
            width: `${task.progress * 100}%`,
            background:
              'linear-gradient(90deg, rgba(255,255,255,0) 0%, var(--ob-color-surface-overlay-medium) 100%)',
            borderRight: '1px solid var(--ob-color-text-tertiary)',
          }}
        />

        {/* Icons */}
        <Stack
          direction="row"
          spacing="var(--ob-space-50)"
          sx={{ position: 'relative', zIndex: 1, px: 'var(--ob-space-100)' }}
        >
          <Typography
            variant="caption"
            sx={{
              color: 'var(--ob-color-bg-default)',
              fontWeight: 600,
              fontSize: '0.7rem',
              textShadow: '0 1px 2px var(--ob-color-overlay-backdrop)',
            }}
          >
            {task.name}
          </Typography>
          {task.isCritical && (
            <WarningAmberIcon
              sx={{
                fontSize: 14,
                color: 'var(--ob-color-bg-default)',
                filter: 'drop-shadow(0 0 2px var(--ob-color-overlay-backdrop))',
              }}
            />
          )}
          {task.isHeritage && (
            <AccountBalanceIcon
              sx={{
                fontSize: 14,
                color: 'var(--ob-color-bg-default)',
                filter: 'drop-shadow(0 0 2px var(--ob-color-overlay-backdrop))',
              }}
            />
          )}
          {task.hasTenantCoordination && (
            <PeopleIcon
              sx={{
                fontSize: 14,
                color: 'var(--ob-color-bg-default)',
                filter: 'drop-shadow(0 0 2px var(--ob-color-overlay-backdrop))',
              }}
            />
          )}
        </Stack>
      </Box>
    </Tooltip>
  )
}

interface TimeHeaderProps {
  startDate: Date
  totalDays: number
}

function TimeHeader({ startDate, totalDays }: TimeHeaderProps) {
  const months = useMemo(() => {
    const result: Array<{ label: string; startDay: number; days: number }> = []
    let currentDate = new Date(startDate)
    let dayCounter = 0

    while (dayCounter < totalDays) {
      const monthStart = dayCounter
      const monthLabel = currentDate.toLocaleDateString('en-SG', {
        month: 'short',
        year: '2-digit',
      })

      // Find days until end of month
      const monthDays: number[] = []
      while (dayCounter < totalDays) {
        monthDays.push(currentDate.getDate())
        dayCounter++
        const nextDate = new Date(currentDate)
        nextDate.setDate(nextDate.getDate() + 1)
        if (nextDate.getMonth() !== currentDate.getMonth()) {
          currentDate = nextDate
          break
        }
        currentDate = nextDate
      }

      result.push({
        label: monthLabel,
        startDay: monthStart,
        days: monthDays.length,
      })
    }

    return result
  }, [startDate, totalDays])

  return (
    <Box
      sx={{
        height: `${HEADER_HEIGHT}px`,
        display: 'flex',
        borderBottom: '1px solid var(--ob-color-surface-overlay)',
        backgroundColor: 'rgba(30,30,30,0.9)',
        backdropFilter: 'blur(var(--ob-blur-md))',
        position: 'sticky',
        top: '0',
        zIndex: 20,
      }}
    >
      {/* Left panel header */}
      <Box
        sx={{
          width: `${LEFT_PANEL_WIDTH}px`,
          minWidth: `${LEFT_PANEL_WIDTH}px`,
          borderRight: '1px solid var(--ob-color-surface-overlay)',
          display: 'flex',
          alignItems: 'center',
          px: 'var(--ob-space-200)',
        }}
      >
        <Typography
          variant="subtitle2"
          sx={{ fontWeight: 600, color: 'var(--ob-color-bg-default)' }}
        >
          PHASE
        </Typography>
      </Box>

      {/* Timeline header */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <Box sx={{ display: 'flex' }}>
          {months.map((month, idx) => (
            <Box
              key={idx}
              sx={{
                width: `${month.days * DAY_WIDTH}px`,
                borderRight: '1px solid var(--ob-color-surface-overlay-light)',
                textAlign: 'center',
                py: 'var(--ob-space-100)',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 600,
                  color: 'var(--ob-color-text-secondary)',
                  textTransform: 'uppercase',
                }}
              >
                {month.label}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  )
}

export function GanttChart({
  data,
  onTaskClick,
  selectedTaskId,
}: GanttChartProps) {
  const { tasks, projectStartDate, totalDuration } = data

  const chartStartDate = useMemo(() => {
    if (projectStartDate) {
      return new Date(projectStartDate)
    }
    if (tasks.length > 0) {
      const dates = tasks.map((t) => new Date(t.startDate).getTime())
      return new Date(Math.min(...dates))
    }
    return new Date()
  }, [projectStartDate, tasks])

  const getTaskOffset = (task: GanttTask): number => {
    const taskStart = new Date(task.startDate)
    const diffTime = taskStart.getTime() - chartStartDate.getTime()
    return Math.floor(diffTime / (1000 * 60 * 60 * 24))
  }

  if (tasks.length === 0) {
    return (
      <Paper sx={{ p: 'var(--ob-space-400)', textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No phases defined for this project. Add phases to see the Gantt chart.
        </Typography>
      </Paper>
    )
  }

  return (
    <Paper
      elevation={1}
      sx={{
        overflow: 'auto',
        maxHeight: 'calc(100vh - 300px)',
        border: '1px solid var(--ob-color-surface-overlay)',
        background: 'transparent',
      }}
    >
      <Box
        sx={{
          minWidth: `${LEFT_PANEL_WIDTH + totalDuration * DAY_WIDTH + 100}px`,
          position: 'relative',
        }}
      >
        <TimeHeader startDate={chartStartDate} totalDays={totalDuration} />

        {/* Dependency Lines Layer */}
        <svg
          style={{
            position: 'absolute',
            top: HEADER_HEIGHT,
            left: 0,
            width: '100%',
            height: tasks.length * ROW_HEIGHT,
            pointerEvents: 'none',
            zIndex: 1, // Below task bars (which have zIndex 10 on hover) but above background
          }}
        >
          <defs>
            <filter id="glow-red" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>
          {tasks.map((task, taskIndex) => {
            if (!task.dependencies || task.dependencies.length === 0)
              return null

            return task.dependencies.map((depId) => {
              const depTask = tasks.find((t) => t.id === depId)
              const depIndex = tasks.findIndex((t) => t.id === depId)

              if (!depTask || depIndex === -1) return null

              const depEndOffset = getTaskOffset(depTask) + depTask.duration
              const currentStartOffset = getTaskOffset(task)

              const startX = LEFT_PANEL_WIDTH + depEndOffset * DAY_WIDTH
              const startY = depIndex * ROW_HEIGHT + ROW_HEIGHT / 2

              const endX = LEFT_PANEL_WIDTH + currentStartOffset * DAY_WIDTH
              const endY = taskIndex * ROW_HEIGHT + ROW_HEIGHT / 2

              // Bezier Curve Logic
              const controlPointX1 = startX + 40
              const controlPointX2 = endX - 40

              const pathData = `M ${startX} ${startY} C ${controlPointX1} ${startY}, ${controlPointX2} ${endY}, ${endX} ${endY}`

              const isHighlighted =
                selectedTaskId &&
                (selectedTaskId === task.id || selectedTaskId === depId)

              // Highlight if this is a critical link
              const isCriticalLink = task.isCritical && depTask.isCritical

              return (
                <path
                  key={`${task.id}-${depId}`}
                  d={pathData}
                  fill="none"
                  stroke={
                    selectedTaskId &&
                    (task.id === selectedTaskId || depId === selectedTaskId)
                      ? '#00f3ff'
                      : isCriticalLink
                        ? 'rgba(239, 68, 68, 0.4)'
                        : 'var(--ob-color-surface-overlay)'
                  }
                  strokeWidth={isCriticalLink || isHighlighted ? 2 : 1}
                  style={{
                    transition: 'all 0.3s ease',
                    filter: isHighlighted ? 'url(#glow-red)' : 'none',
                  }}
                />
              )
            })
          })}
        </svg>

        {/* Task rows */}
        {tasks.map((task) => (
          <Box
            key={task.id}
            sx={{
              display: 'flex',
              height: `${ROW_HEIGHT}px`,
              borderBottom: '1px solid var(--ob-color-surface-overlay-light)',
              backgroundColor:
                selectedTaskId === task.id
                  ? 'var(--ob-color-table-row-hover)'
                  : 'transparent',
              '&:hover': {
                backgroundColor:
                  selectedTaskId === task.id
                    ? 'var(--ob-color-table-row-hover)'
                    : 'var(--ob-color-table-row-alt)',
              },
            }}
          >
            {/* Left panel - task info */}
            <Box
              sx={{
                width: `${LEFT_PANEL_WIDTH}px`,
                minWidth: `${LEFT_PANEL_WIDTH}px`,
                borderRight: '1px solid var(--ob-color-surface-overlay)',
                display: 'flex',
                alignItems: 'center',
                px: 'var(--ob-space-200)',
                gap: 'var(--ob-space-100)',
                bgcolor: 'rgba(30,30,30,0.3)',
                backdropFilter: 'blur(var(--ob-blur-sm))',
              }}
            >
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: STATUS_COLORS[task.status] || '#94a3b8',
                  boxShadow: `0 0 8px ${STATUS_COLORS[task.status] || '#94a3b8'}`,
                  flexShrink: 0,
                }}
              />
              <Typography
                variant="body2"
                sx={{
                  flex: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  color: 'var(--ob-color-bg-default)',
                }}
              >
                {task.name}
              </Typography>
              <Typography
                variant="caption"
                sx={{ color: 'var(--ob-color-border-default)' }}
              >
                {getStatusLabel(task.status)}
              </Typography>
            </Box>

            {/* Right panel - Gantt bars */}
            <Box
              sx={{
                flex: 1,
                position: 'relative',
                backgroundColor: task.isCritical
                  ? 'rgba(239, 68, 68, 0.05)'
                  : 'transparent',
              }}
            >
              <TaskBar
                task={task}
                startOffset={getTaskOffset(task)}
                isSelected={selectedTaskId === task.id}
                onClick={() => onTaskClick?.(task.id)}
              />

              {/* Dependency lines would go here in a full implementation */}
            </Box>
          </Box>
        ))}
      </Box>

      {/* Now Line */}
      {(() => {
        const now = new Date()
        const diffTime = now.getTime() - chartStartDate.getTime()
        const dayOffset = diffTime / (1000 * 60 * 60 * 24)
        if (dayOffset >= 0 && dayOffset <= totalDuration) {
          return (
            <Box
              sx={{
                position: 'absolute',
                left: `${LEFT_PANEL_WIDTH + dayOffset * DAY_WIDTH}px`,
                top: HEADER_HEIGHT,
                bottom: 'var(--ob-space-800)', // Leave room for legend
                width: '2px',
                background: 'var(--ob-color-neon-cyan)',
                boxShadow: '0 0 10px #00f3ff',
                zIndex: 15,
                pointerEvents: 'none',
              }}
            >
              <Box
                sx={{
                  position: 'absolute',
                  top: '-24px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: 'var(--ob-color-neon-cyan)',
                  color: 'var(--ob-color-bg-inverse)',
                  fontSize: '0.65rem',
                  fontWeight: 'bold',
                  padding: '2px 6px',
                  borderRadius: 'var(--ob-radius-sm)',
                  boxShadow: '0 0 10px #00f3ff',
                  whiteSpace: 'nowrap',
                }}
              >
                TODAY
              </Box>
            </Box>
          )
        }
        return null
      })()}

      {/* Legend */}
      <Box
        sx={{
          display: 'flex',
          gap: 'var(--ob-space-300)',
          p: 'var(--ob-space-200)',
          borderTop: '1px solid var(--ob-color-surface-overlay)',
          background: 'rgba(20, 20, 20, 0.95)',
          flexWrap: 'wrap',
          color: 'var(--ob-color-bg-default)',
        }}
      >
        <Stack direction="row" spacing="var(--ob-space-50)" alignItems="center">
          <WarningAmberIcon sx={{ fontSize: 16, color: '#ef4444' }} />
          <Typography variant="caption">Critical Path</Typography>
        </Stack>
        <Stack direction="row" spacing="var(--ob-space-50)" alignItems="center">
          <AccountBalanceIcon sx={{ fontSize: 16, color: '#666' }} />
          <Typography variant="caption">Heritage Phase</Typography>
        </Stack>
        <Stack direction="row" spacing="var(--ob-space-50)" alignItems="center">
          <PeopleIcon sx={{ fontSize: 16, color: '#666' }} />
          <Typography variant="caption">Tenant Coordination</Typography>
        </Stack>
        <Box sx={{ display: 'flex', gap: 'var(--ob-space-100)', ml: 'auto' }}>
          {Object.entries(STATUS_COLORS).map(([status, color]) => (
            <Stack
              key={status}
              direction="row"
              spacing="var(--ob-space-50)"
              alignItems="center"
            >
              <Box
                sx={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: color,
                }}
              />
              <Typography variant="caption">
                {getStatusLabel(status)}
              </Typography>
            </Stack>
          ))}
        </Box>
      </Box>
    </Paper>
  )
}
