import { useMemo } from 'react'
import { Box, Paper, Tooltip, Typography, Chip, Stack } from '@mui/material'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import PeopleIcon from '@mui/icons-material/People'
import type { GanttChart as GanttChartData, GanttTask } from '../../../../api/development'

interface GanttChartProps {
  data: GanttChartData
  onTaskClick?: (taskId: string) => void
  selectedTaskId?: string | null
}

const STATUS_COLORS: Record<string, string> = {
  not_started: '#94a3b8',
  planning: '#60a5fa',
  in_progress: '#22c55e',
  on_hold: '#f59e0b',
  completed: '#10b981',
  cancelled: '#ef4444',
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
    <Box sx={{ p: 1 }}>
      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
        {task.name}
      </Typography>
      <Typography variant="body2" sx={{ mt: 0.5 }}>
        {formatDate(task.startDate)} - {formatDate(task.endDate)}
      </Typography>
      <Typography variant="body2">Duration: {task.duration} days</Typography>
      <Typography variant="body2">Progress: {Math.round(task.progress * 100)}%</Typography>
      {task.budgetAmount !== null && (
        <Typography variant="body2">Budget: {formatCurrency(task.budgetAmount)}</Typography>
      )}
      {task.isCritical && (
        <Chip
          size="small"
          label="Critical Path"
          color="error"
          sx={{ mt: 1 }}
        />
      )}
    </Box>
  )

  return (
    <Tooltip title={tooltipContent} arrow placement="top">
      <Box
        onClick={onClick}
        sx={{
          position: 'absolute',
          left: `${left}px`,
          top: '4px',
          width: `${width}px`,
          height: `${ROW_HEIGHT - 8}px`,
          backgroundColor: task.color,
          borderRadius: '4px',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          border: isSelected ? '2px solid #1976d2' : task.isCritical ? '2px solid #ef4444' : '1px solid transparent',
          boxShadow: isSelected ? '0 2px 8px rgba(25, 118, 210, 0.4)' : 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          '&:hover': {
            filter: 'brightness(1.1)',
            transform: 'scaleY(1.05)',
          },
        }}
      >
        {/* Progress bar */}
        <Box
          sx={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: `${task.progress * 100}%`,
            backgroundColor: 'rgba(255, 255, 255, 0.3)',
            borderRadius: '4px 0 0 4px',
          }}
        />
        {/* Icons */}
        <Stack direction="row" spacing={0.5} sx={{ position: 'relative', zIndex: 1 }}>
          {task.isCritical && (
            <WarningAmberIcon sx={{ fontSize: 14, color: 'white' }} />
          )}
          {task.isHeritage && (
            <AccountBalanceIcon sx={{ fontSize: 14, color: 'white' }} />
          )}
          {task.hasTenantCoordination && (
            <PeopleIcon sx={{ fontSize: 14, color: 'white' }} />
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
      const monthLabel = currentDate.toLocaleDateString('en-SG', { month: 'short', year: '2-digit' })

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
        borderBottom: '1px solid #e0e0e0',
        backgroundColor: '#f5f5f5',
        position: 'sticky',
        top: 0,
        zIndex: 2,
      }}
    >
      {/* Left panel header */}
      <Box
        sx={{
          width: `${LEFT_PANEL_WIDTH}px`,
          minWidth: `${LEFT_PANEL_WIDTH}px`,
          borderRight: '1px solid #e0e0e0',
          display: 'flex',
          alignItems: 'center',
          px: 2,
        }}
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
          Phase
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
                borderRight: '1px solid #e0e0e0',
                textAlign: 'center',
                py: 1,
              }}
            >
              <Typography variant="caption" sx={{ fontWeight: 600 }}>
                {month.label}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  )
}

export function GanttChart({ data, onTaskClick, selectedTaskId }: GanttChartProps) {
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
      <Paper sx={{ p: 4, textAlign: 'center' }}>
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
        border: '1px solid #e0e0e0',
      }}
    >
      <Box sx={{ minWidth: `${LEFT_PANEL_WIDTH + totalDuration * DAY_WIDTH + 100}px` }}>
        <TimeHeader startDate={chartStartDate} totalDays={totalDuration} />

        {/* Task rows */}
        {tasks.map((task) => (
          <Box
            key={task.id}
            sx={{
              display: 'flex',
              height: `${ROW_HEIGHT}px`,
              borderBottom: '1px solid #f0f0f0',
              backgroundColor: selectedTaskId === task.id ? '#e3f2fd' : 'white',
              '&:hover': {
                backgroundColor: selectedTaskId === task.id ? '#e3f2fd' : '#fafafa',
              },
            }}
          >
            {/* Left panel - task info */}
            <Box
              sx={{
                width: `${LEFT_PANEL_WIDTH}px`,
                minWidth: `${LEFT_PANEL_WIDTH}px`,
                borderRight: '1px solid #e0e0e0',
                display: 'flex',
                alignItems: 'center',
                px: 2,
                gap: 1,
              }}
            >
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: STATUS_COLORS[task.status] || '#94a3b8',
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
                }}
              >
                {task.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {getStatusLabel(task.status)}
              </Typography>
            </Box>

            {/* Right panel - Gantt bars */}
            <Box
              sx={{
                flex: 1,
                position: 'relative',
                backgroundColor: task.isCritical ? 'rgba(239, 68, 68, 0.05)' : 'transparent',
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

      {/* Legend */}
      <Box
        sx={{
          display: 'flex',
          gap: 3,
          p: 2,
          borderTop: '1px solid #e0e0e0',
          backgroundColor: '#fafafa',
          flexWrap: 'wrap',
        }}
      >
        <Stack direction="row" spacing={0.5} alignItems="center">
          <WarningAmberIcon sx={{ fontSize: 16, color: '#ef4444' }} />
          <Typography variant="caption">Critical Path</Typography>
        </Stack>
        <Stack direction="row" spacing={0.5} alignItems="center">
          <AccountBalanceIcon sx={{ fontSize: 16, color: '#666' }} />
          <Typography variant="caption">Heritage Phase</Typography>
        </Stack>
        <Stack direction="row" spacing={0.5} alignItems="center">
          <PeopleIcon sx={{ fontSize: 16, color: '#666' }} />
          <Typography variant="caption">Tenant Coordination</Typography>
        </Stack>
        <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
          {Object.entries(STATUS_COLORS).map(([status, color]) => (
            <Stack key={status} direction="row" spacing={0.5} alignItems="center">
              <Box
                sx={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: color,
                }}
              />
              <Typography variant="caption">{getStatusLabel(status)}</Typography>
            </Stack>
          ))}
        </Box>
      </Box>
    </Paper>
  )
}
