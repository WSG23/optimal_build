/**
 * Compliance Path Timeline - Gantt-style visualization for regulatory compliance paths.
 * Shows the sequence of regulatory submissions required for different asset types.
 */

import React, { useState, useEffect, useMemo } from 'react'
import {
  Box,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  SelectChangeEvent,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import HourglassIcon from '@mui/icons-material/HourglassEmpty'
import ScheduleIcon from '@mui/icons-material/Schedule'
import WarningIcon from '@mui/icons-material/Warning'
import AgencyIcon from '@mui/icons-material/Business'
import HeritageIcon from '@mui/icons-material/AccountBalance'
import RegulatoryIcon from '@mui/icons-material/Gavel'
import {
  regulatoryApi,
  AssetCompliancePath,
  AssetType,
  AuthoritySubmission,
} from '../../../../api/regulatory'
import { colors } from '@ob/tokens'
import { Card } from '../../../../components/canonical/Card'
import { StatusChip } from '../../../../components/canonical/StatusChip'
import { Tag } from '../../../../components/canonical/Tag'
import { ComplianceSummaryCards } from './ComplianceSummaryCards'
import {
  type StepStatus,
  ASSET_TYPE_OPTIONS,
  SUBMISSION_TYPE_LABELS,
  DAY_WIDTH,
  ROW_HEIGHT,
  LEFT_PANEL_WIDTH,
  readStoredAssetType,
  persistAssetType,
  deriveAssetTypeFromCapture,
  getStepProgress,
  getMockCompliancePaths,
} from './complianceTimelineUtils'

interface CompliancePathTimelineProps {
  projectId?: string
  projectName?: string
  preferredAssetType?: AssetType
  initialAssetType?: AssetType
  onStepClick?: (step: AssetCompliancePath) => void
}

// Agency display info (available for future use in tooltips/detailed views)
const _AGENCY_INFO: Record<string, { name: string; color: string }> = {
  URA: { name: 'Urban Redevelopment Authority', color: colors.brand[600] },
  BCA: {
    name: 'Building & Construction Authority',
    color: colors.success[700],
  },
  SCDF: { name: 'Singapore Civil Defence Force', color: colors.error[600] },
  NEA: { name: 'National Environment Agency', color: colors.info[600] },
  LTA: { name: 'Land Transport Authority', color: colors.warning[600] },
  STB: { name: 'Singapore Tourism Board', color: colors.accent[500] },
  JTC: { name: 'JTC Corporation', color: colors.neutral[600] },
}
void _AGENCY_INFO // Suppress unused warning - available for future tooltip enhancement

const STATUS_COLORS = {
  completed: colors.success[500],
  in_progress: colors.warning[500],
  pending: colors.neutral[400],
  delayed: colors.error[500],
}

const BAR_GRADIENTS = {
  completed:
    'linear-gradient(90deg, var(--ob-success-700) 0%, var(--ob-success-400) 100%)',
  in_progress:
    'linear-gradient(90deg, var(--ob-warning-700) 0%, var(--ob-warning-400) 100%)',
  pending:
    'linear-gradient(90deg, var(--ob-neutral-600) 0%, var(--ob-neutral-400) 100%)',
  delayed:
    'linear-gradient(90deg, var(--ob-error-600) 0%, var(--ob-error-400) 100%)',
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'completed':
      return <CheckCircleIcon sx={{ color: STATUS_COLORS.completed }} />
    case 'in_progress':
      return <HourglassIcon sx={{ color: STATUS_COLORS.in_progress }} />
    case 'delayed':
      return <WarningIcon sx={{ color: STATUS_COLORS.delayed }} />
    default:
      return <ScheduleIcon sx={{ color: STATUS_COLORS.pending }} />
  }
}

interface TimelineBarProps {
  step: AssetCompliancePath
  startOffset: number
  isSelected: boolean
  onClick: () => void
  progress: number
  status: StepStatus
}

function TimelineBar({
  step,
  startOffset,
  isSelected,
  onClick,
  progress,
  status,
}: TimelineBarProps) {
  const duration = step.typical_duration_days || 14
  const width = Math.max(duration * DAY_WIDTH, 60)
  const left = startOffset * DAY_WIDTH

  const tooltipContent = (
    <Box sx={{ p: 'var(--ob-space-075)' }}>
      <Box
        component="span"
        sx={{
          fontWeight: 'var(--ob-font-weight-semibold)',
          fontSize: 'var(--ob-font-size-sm)',
          display: 'block',
        }}
      >
        {SUBMISSION_TYPE_LABELS[step.submission_type] || step.submission_type}
      </Box>
      <Box
        component="span"
        sx={{
          fontSize: 'var(--ob-font-size-xs)',
          display: 'block',
          mt: 'var(--ob-space-025)',
        }}
      >
        Duration: {duration} days
      </Box>
      <Box
        component="span"
        sx={{ fontSize: 'var(--ob-font-size-xs)', display: 'block' }}
      >
        Progress: {progress}%
      </Box>
      {step.is_mandatory && (
        <StatusChip status="error" size="sm" sx={{ mt: 'var(--ob-space-075)' }}>
          Mandatory
        </StatusChip>
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
          top: 'var(--ob-space-050)',
          width: `${width}px`,
          height: `${ROW_HEIGHT - 16}px`,
          borderRadius: 'var(--ob-radius-sm)',
          cursor: 'pointer',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          background: BAR_GRADIENTS[status],
          border: isSelected
            ? '2px solid var(--ob-color-border-brand)'
            : '1px solid var(--ob-border-glass)',
          boxShadow: isSelected
            ? 'var(--ob-glow-brand-strong)'
            : 'var(--ob-shadow-sm)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          '&:hover': {
            filter: 'brightness(1.2)',
            transform: 'scaleY(1.05)',
            zIndex: 10,
          },
        }}
      >
        {/* Progress overlay */}
        <Box
          sx={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: `${progress}%`,
            background:
              'linear-gradient(90deg, rgba(var(--ob-color-text-primary-rgb) / 0) 0%, rgba(var(--ob-color-text-primary-rgb) / 0.2) 100%)',
            borderRight:
              progress > 0 && progress < 100
                ? '2px solid rgba(var(--ob-color-text-primary-rgb) / 0.5)'
                : 'none',
          }}
        />

        {/* Label */}
        <Typography
          variant="caption"
          sx={{
            color: 'var(--ob-neutral-50)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            fontSize: 'var(--ob-font-size-2xs)',
            textShadow: '0 1px 2px rgba(0,0,0,0.5)',
            position: 'relative',
            zIndex: 1,
            px: 'var(--ob-space-100)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {SUBMISSION_TYPE_LABELS[step.submission_type]?.split(' ')[0] ||
            step.submission_type}
        </Typography>
      </Box>
    </Tooltip>
  )
}

export const CompliancePathTimeline: React.FC<CompliancePathTimelineProps> = ({
  projectId,
  projectName,
  preferredAssetType,
  initialAssetType = 'office',
  onStepClick,
}) => {
  const [assetType, setAssetType] = useState<AssetType>(initialAssetType)
  const [hasManualSelection, setHasManualSelection] = useState(false)
  const [compliancePaths, setCompliancePaths] = useState<AssetCompliancePath[]>(
    [],
  )
  const [submissions, setSubmissions] = useState<AuthoritySubmission[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedStep, setSelectedStep] = useState<string | null>(null)

  useEffect(() => {
    setHasManualSelection(false)
  }, [projectId])

  useEffect(() => {
    if (!projectId) {
      setAssetType(initialAssetType)
      return
    }

    const stored = readStoredAssetType(projectId)
    if (stored) {
      setAssetType(stored)
      setHasManualSelection(true)
      return
    }

    if (hasManualSelection) {
      return
    }

    const derived =
      preferredAssetType ??
      deriveAssetTypeFromCapture(projectId) ??
      initialAssetType
    if (derived && derived !== assetType) {
      setAssetType(derived)
    }
  }, [
    assetType,
    hasManualSelection,
    initialAssetType,
    preferredAssetType,
    projectId,
  ])

  // Fetch compliance paths when asset type changes
  useEffect(() => {
    const fetchPaths = async () => {
      setLoading(true)
      try {
        const paths = await regulatoryApi.getCompliancePaths(assetType)
        setCompliancePaths(paths)
      } catch {
        // Use mock data for demonstration if API fails
        setCompliancePaths(getMockCompliancePaths(assetType))
      } finally {
        setLoading(false)
      }
    }
    fetchPaths()
  }, [assetType])

  // Fetch submissions when projectId changes
  useEffect(() => {
    const fetchSubmissions = async () => {
      if (!projectId) {
        setSubmissions([])
        return
      }
      setSelectedStep(null)
      try {
        const subs = await regulatoryApi.listSubmissions(projectId)
        setSubmissions(subs)
      } catch {
        setSubmissions([])
      }
    }
    fetchSubmissions()
  }, [projectId])

  const handleAssetTypeChange = (event: SelectChangeEvent) => {
    const nextType = event.target.value as AssetType
    setAssetType(nextType)
    setHasManualSelection(true)
    if (projectId) {
      persistAssetType(projectId, nextType)
    }
    setSelectedStep(null)
  }

  const handleStepClick = (step: AssetCompliancePath) => {
    setSelectedStep(step.id)
    onStepClick?.(step)
  }

  // Calculate timeline dimensions
  const totalDuration = useMemo(() => {
    if (compliancePaths.length === 0) return 180
    let currentOffset = 0
    compliancePaths.forEach((p) => {
      currentOffset += p.typical_duration_days || 14
    })
    return currentOffset + 30 // Add buffer
  }, [compliancePaths])

  // Calculate cumulative offsets for each step
  const stepOffsets = useMemo(() => {
    const offsets: Record<string, number> = {}
    let currentOffset = 0
    compliancePaths.forEach((step) => {
      offsets[step.id] = currentOffset
      currentOffset += step.typical_duration_days || 14
    })
    return offsets
  }, [compliancePaths])

  // Calculate step progress using real submissions
  const stepProgressMap = useMemo(() => {
    const map: Record<string, { progress: number; status: StepStatus }> = {}
    compliancePaths.forEach((step) => {
      map[step.id] = getStepProgress(step, submissions)
    })
    return map
  }, [compliancePaths, submissions])

  // Calculate overall progress
  const overallProgress = useMemo(() => {
    if (compliancePaths.length === 0) return 0
    const totalProgress = compliancePaths.reduce(
      (acc, step) => acc + (stepProgressMap[step.id]?.progress || 0),
      0,
    )
    return Math.round(totalProgress / compliancePaths.length)
  }, [compliancePaths, stepProgressMap])

  const completedSteps = compliancePaths.filter(
    (s) => stepProgressMap[s.id]?.status === 'completed',
  ).length

  if (loading) {
    return (
      <Box sx={{ p: 'var(--ob-space-300)', textAlign: 'center' }}>
        <Typography>Loading compliance path...</Typography>
        <LinearProgress
          sx={{ mt: 'var(--ob-space-200)', maxWidth: 300, mx: 'auto' }}
        />
      </Box>
    )
  }

  return (
    <Box>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          mb: 'var(--ob-space-200)',
        }}
      >
        <Box>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-075)',
            }}
          >
            <RegulatoryIcon
              sx={{ color: 'var(--ob-color-brand-primary)', fontSize: 24 }}
            />
            <Box
              component="h2"
              sx={{
                fontSize: 'var(--ob-font-size-lg)',
                fontWeight: 'var(--ob-font-weight-bold)',
                color: 'var(--ob-color-text-primary)',
                m: 0,
              }}
            >
              Compliance Path Timeline
            </Box>
          </Box>
          <Box
            component="p"
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-secondary)',
              m: 0,
              mt: 'var(--ob-space-025)',
            }}
          >
            Regulatory submission sequence for Singapore developments
          </Box>
          <Box
            component="span"
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'var(--ob-color-text-tertiary)',
              display: 'block',
              mt: 'var(--ob-space-025)',
            }}
          >
            Project: {projectName?.trim() || projectId || 'Unknown'} •{' '}
            {submissions.length} submission{submissions.length === 1 ? '' : 's'}
          </Box>
        </Box>

        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Asset Type</InputLabel>
          <Select
            value={assetType}
            label="Asset Type"
            onChange={handleAssetTypeChange}
          >
            {ASSET_TYPE_OPTIONS.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Summary Cards */}
      <ComplianceSummaryCards
        overallProgress={overallProgress}
        completedSteps={completedSteps}
        totalSteps={compliancePaths.length}
        totalDuration={totalDuration - 30}
      />

      {/* Timeline */}
      <Card
        variant="default"
        sx={{
          overflow: 'auto',
          maxHeight: 'calc(100vh - 450px)',
        }}
      >
        <Box
          sx={{
            minWidth: `${LEFT_PANEL_WIDTH + totalDuration * DAY_WIDTH + 50}px`,
            position: 'relative',
          }}
        >
          {/* Header */}
          <Box
            sx={{
              height: '50px', // canon-ok: timeline step row
              display: 'flex',
              borderBottom: '1px solid var(--ob-border-glass)',
              backgroundColor:
                'rgba(var(--ob-color-surface-default-rgb) / 0.9)',
              backdropFilter: 'blur(var(--ob-blur-md))',
              position: 'sticky',
              top: 0,
              zIndex: 20,
            }}
          >
            <Box
              sx={{
                width: `${LEFT_PANEL_WIDTH}px`,
                minWidth: `${LEFT_PANEL_WIDTH}px`,
                borderRight: '1px solid var(--ob-border-glass)',
                display: 'flex',
                alignItems: 'center',
                px: 'var(--ob-space-200)',
              }}
            >
              <Typography
                variant="subtitle2"
                sx={{
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  color: 'var(--ob-neutral-50)',
                }}
              >
                SUBMISSION STEP
              </Typography>
            </Box>
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                px: 'var(--ob-space-200)',
              }}
            >
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Timeline (Days from project start)
              </Typography>
            </Box>
          </Box>

          {/* Rows */}
          {compliancePaths.map((step) => {
            const { progress, status } = stepProgressMap[step.id] || {
              progress: 0,
              status: 'pending' as StepStatus,
            }
            return (
              <Box
                key={step.id}
                sx={{
                  display: 'flex',
                  height: `${ROW_HEIGHT}px`,
                  borderBottom: '1px solid rgba(245, 235, 220, 0.05)',
                  backgroundColor:
                    selectedStep === step.id
                      ? 'var(--ob-color-brand-soft)'
                      : 'transparent',
                  '&:hover': {
                    backgroundColor:
                      selectedStep === step.id
                        ? 'var(--ob-color-brand-soft)'
                        : 'rgba(255, 255, 255, 0.02)',
                  },
                }}
              >
                {/* Left panel - step info */}
                <Box
                  sx={{
                    width: `${LEFT_PANEL_WIDTH}px`,
                    minWidth: `${LEFT_PANEL_WIDTH}px`,
                    borderRight: '1px solid var(--ob-border-glass)',
                    display: 'flex',
                    alignItems: 'center',
                    px: 'var(--ob-space-200)',
                    gap: 'var(--ob-space-150)',
                    bgcolor: 'rgba(var(--ob-color-surface-default-rgb) / 0.3)',
                    backdropFilter: 'blur(var(--ob-blur-sm))',
                  }}
                >
                  {getStatusIcon(status)}
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: 'var(--ob-font-weight-medium)',
                        color: 'text.primary',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {SUBMISSION_TYPE_LABELS[step.submission_type] ||
                        step.submission_type}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{ color: 'text.secondary' }}
                    >
                      {step.typical_duration_days || 14} days
                      {step.is_mandatory && ' • Mandatory'}
                    </Typography>
                  </Box>
                  <Tag size="sm">{step.sequence_order}</Tag>
                </Box>

                {/* Right panel - timeline bars */}
                <Box sx={{ flex: 1, position: 'relative' }}>
                  <TimelineBar
                    step={step}
                    startOffset={stepOffsets[step.id] || 0}
                    isSelected={selectedStep === step.id}
                    onClick={() => handleStepClick(step)}
                    progress={progress}
                    status={status}
                  />
                </Box>
              </Box>
            )
          })}
        </Box>

        {/* Legend */}
        <Box
          sx={{
            display: 'flex',
            gap: 'var(--ob-space-200)',
            p: 'var(--ob-space-200)',
            borderTop: '1px solid var(--ob-border-glass)',
            background: 'rgba(var(--ob-color-surface-default-rgb) / 0.95)',
            flexWrap: 'wrap',
            color: 'var(--ob-neutral-50)',
          }}
        >
          {Object.entries(STATUS_COLORS).map(([status, color]) => (
            <Stack
              key={status}
              direction="row"
              spacing="var(--ob-space-050)"
              alignItems="center"
            >
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: color,
                }}
              />
              <Typography
                variant="caption"
                sx={{ textTransform: 'capitalize' }}
              >
                {status.replace('_', ' ')}
              </Typography>
            </Stack>
          ))}
          <Box sx={{ display: 'flex', gap: 'var(--ob-space-200)', ml: 'auto' }}>
            <Stack
              direction="row"
              spacing="var(--ob-space-050)"
              alignItems="center"
            >
              <AgencyIcon
                sx={{ fontSize: 16, color: 'var(--ob-color-text-muted)' }}
              />
              <Typography variant="caption">Regulatory Agency</Typography>
            </Stack>
            <Stack
              direction="row"
              spacing="var(--ob-space-050)"
              alignItems="center"
            >
              <HeritageIcon
                sx={{ fontSize: 16, color: 'var(--ob-color-text-muted)' }}
              />
              <Typography variant="caption">Heritage/Conservation</Typography>
            </Stack>
          </Box>
        </Box>
      </Card>
    </Box>
  )
}

export default CompliancePathTimeline
