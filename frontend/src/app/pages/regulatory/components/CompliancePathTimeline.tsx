/**
 * Compliance Path Timeline - Gantt-style visualization for regulatory compliance paths.
 * Shows the sequence of regulatory submissions required for different asset types.
 */

import React, { useState, useEffect, useMemo } from 'react'
import {
  Box,
  Card,
  CardContent,
  Chip,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  SelectChangeEvent,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
import {
  CheckCircle as CheckCircleIcon,
  HourglassEmpty as HourglassIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  Business as AgencyIcon,
  AccountBalance as HeritageIcon,
  Gavel as RegulatoryIcon,
} from '@mui/icons-material'
import {
  regulatoryApi,
  AssetCompliancePath,
  AssetType,
  AuthoritySubmission,
} from '../../../../api/regulatory'
import { colors } from '@ob/tokens'

interface CompliancePathTimelineProps {
  projectId?: string
  initialAssetType?: AssetType
  onStepClick?: (step: AssetCompliancePath) => void
}

type ComplianceStepDraft = Omit<
  AssetCompliancePath,
  'asset_type' | 'agency_id' | 'sequence_order' | 'created_at'
>

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

// Submission type display names - includes both API values and legacy mock values
const SUBMISSION_TYPE_LABELS: Record<string, string> = {
  // Actual API submission types
  DC: 'Development Control (URA)',
  BP: 'Building Plan (BCA)',
  TOP: 'Temporary Occupation Permit',
  CSC: 'Certificate of Statutory Completion',
  CONSULTATION: 'Agency Consultation',
  WAIVER: 'Waiver Application',
  HERITAGE_APPROVAL: 'Heritage Conservation (STB)',
  INDUSTRIAL_PERMIT: 'Industrial Permit (JTC)',
  CHANGE_OF_USE: 'Change of Use',
  // Legacy mock values (fallback)
  planning_permission: 'Planning Permission',
  development_control: 'Development Control',
  building_plan: 'Building Plan Approval',
  structural_plan: 'Structural Plan',
  fire_safety: 'Fire Safety Certificate',
  environmental: 'Environmental Clearance',
  heritage_conservation: 'Heritage Conservation',
  change_of_use: 'Change of Use',
  csc_application: 'CSC Application',
  top_application: 'TOP Application',
}

const ASSET_TYPE_OPTIONS: { value: AssetType; label: string }[] = [
  { value: 'office', label: 'Office' },
  { value: 'retail', label: 'Retail' },
  { value: 'residential', label: 'Residential' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'hospitality', label: 'Hospitality' },
  { value: 'mixed_use', label: 'Mixed Use' },
  { value: 'heritage', label: 'Heritage / Conservation' },
]

// Status type for compliance steps
type StepStatus = 'completed' | 'in_progress' | 'pending' | 'delayed'

// Get progress and status from real submissions
function getStepProgress(
  step: AssetCompliancePath,
  submissions: AuthoritySubmission[],
): { progress: number; status: StepStatus } {
  // Find submissions matching this step's submission type
  const matchingSubmissions = submissions.filter(
    (s) => s.submission_type === step.submission_type,
  )

  if (matchingSubmissions.length === 0) {
    return { progress: 0, status: 'pending' }
  }

  // Check for approved submissions
  const approved = matchingSubmissions.find((s) => s.status === 'APPROVED')
  if (approved) {
    return { progress: 100, status: 'completed' }
  }

  // Check for rejected submissions (delayed)
  const rejected = matchingSubmissions.find((s) => s.status === 'REJECTED')
  if (rejected) {
    return { progress: 0, status: 'delayed' }
  }

  // Check for in-progress submissions (submitted, in_review, rfi)
  const inProgress = matchingSubmissions.find((s) =>
    ['SUBMITTED', 'IN_REVIEW', 'RFI'].includes(s.status),
  )
  if (inProgress) {
    // Estimate progress based on status
    if (inProgress.status === 'RFI')
      return { progress: 75, status: 'in_progress' }
    if (inProgress.status === 'IN_REVIEW')
      return { progress: 50, status: 'in_progress' }
    return { progress: 25, status: 'in_progress' }
  }

  // Check for draft submissions
  const draft = matchingSubmissions.find((s) => s.status === 'DRAFT')
  if (draft) {
    return { progress: 10, status: 'in_progress' }
  }

  return { progress: 0, status: 'pending' }
}

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

const DAY_WIDTH = 8
const ROW_HEIGHT = 56
const LEFT_PANEL_WIDTH = 320

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
    <Box sx={{ p: 1 }}>
      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
        {SUBMISSION_TYPE_LABELS[step.submission_type] || step.submission_type}
      </Typography>
      <Typography variant="body2" sx={{ mt: 0.5 }}>
        Duration: {duration} days
      </Typography>
      <Typography variant="body2">Progress: {progress}%</Typography>
      {step.is_mandatory && (
        <Chip
          label="Mandatory"
          size="small"
          color="error"
          variant="outlined"
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
          top: '8px',
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
            px: 1,
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
  initialAssetType = 'office',
  onStepClick,
}) => {
  const [assetType, setAssetType] = useState<AssetType>(initialAssetType)
  const [compliancePaths, setCompliancePaths] = useState<AssetCompliancePath[]>(
    [],
  )
  const [submissions, setSubmissions] = useState<AuthoritySubmission[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedStep, setSelectedStep] = useState<string | null>(null)

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
    setAssetType(event.target.value as AssetType)
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
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography>Loading compliance path...</Typography>
        <LinearProgress sx={{ mt: 2, maxWidth: 300, mx: 'auto' }} />
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
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Box>
          <Typography
            variant="h6"
            fontWeight="bold"
            sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
          >
            <RegulatoryIcon color="primary" />
            Compliance Path Timeline
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Regulatory submission sequence for Singapore developments
          </Typography>
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
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Card
          sx={{
            flex: 1,
            background:
              'linear-gradient(135deg, var(--ob-brand-700) 0%, var(--ob-brand-400) 100%)',
            color: 'var(--ob-neutral-50)',
          }}
        >
          <CardContent sx={{ py: 2 }}>
            <Typography variant="caption">Overall Progress</Typography>
            <Typography variant="h4" fontWeight="bold">
              {overallProgress}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={overallProgress}
              sx={{
                mt: 1,
                bgcolor: 'rgba(255 255 255 / 0.3)',
                '& .MuiLinearProgress-bar': {
                  bgcolor: 'var(--ob-neutral-50)',
                },
              }}
            />
          </CardContent>
        </Card>

        <Card
          sx={{
            flex: 1,
            background:
              'linear-gradient(135deg, var(--ob-success-700) 0%, var(--ob-success-400) 100%)',
            color: 'var(--ob-neutral-50)',
          }}
        >
          <CardContent sx={{ py: 2 }}>
            <Typography variant="caption">Completed Steps</Typography>
            <Typography variant="h4" fontWeight="bold">
              {completedSteps}/{compliancePaths.length}
            </Typography>
          </CardContent>
        </Card>

        <Card
          sx={{
            flex: 1,
            background:
              'linear-gradient(135deg, var(--ob-info-700) 0%, var(--ob-info-400) 100%)',
            color: 'var(--ob-neutral-50)',
          }}
        >
          <CardContent sx={{ py: 2 }}>
            <Typography variant="caption">Est. Total Duration</Typography>
            <Typography variant="h4" fontWeight="bold">
              {totalDuration - 30} days
            </Typography>
          </CardContent>
        </Card>
      </Stack>

      {/* Timeline */}
      <Paper
        elevation={1}
        sx={{
          overflow: 'auto',
          maxHeight: 'calc(100vh - 450px)',
          border: '1px solid var(--ob-border-glass)',
          background: 'transparent',
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
              height: '50px',
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
                px: 2,
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
                px: 2,
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
                  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                  backgroundColor:
                    selectedStep === step.id
                      ? 'rgba(0, 243, 255, 0.05)'
                      : 'transparent',
                  '&:hover': {
                    backgroundColor:
                      selectedStep === step.id
                        ? 'rgba(0, 243, 255, 0.05)'
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
                    px: 2,
                    gap: 1.5,
                    bgcolor: 'rgba(var(--ob-color-surface-default-rgb) / 0.3)',
                    backdropFilter: 'blur(var(--ob-blur-sm))',
                  }}
                >
                  {getStatusIcon(status)}
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: 500,
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
                  <Chip
                    label={step.sequence_order}
                    size="small"
                    sx={{
                      bgcolor: 'rgba(var(--ob-color-text-primary-rgb) / 0.12)',
                      color: 'var(--ob-neutral-50)',
                      fontWeight: 'var(--ob-font-weight-semibold)',
                      minWidth: 28,
                    }}
                  />
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
            gap: 3,
            p: 2,
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
              spacing={0.5}
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
          <Box sx={{ display: 'flex', gap: 2, ml: 'auto' }}>
            <Stack direction="row" spacing={0.5} alignItems="center">
              <AgencyIcon
                sx={{ fontSize: 16, color: 'var(--ob-color-text-muted)' }}
              />
              <Typography variant="caption">Regulatory Agency</Typography>
            </Stack>
            <Stack direction="row" spacing={0.5} alignItems="center">
              <HeritageIcon
                sx={{ fontSize: 16, color: 'var(--ob-color-text-muted)' }}
              />
              <Typography variant="caption">Heritage/Conservation</Typography>
            </Stack>
          </Box>
        </Box>
      </Paper>
    </Box>
  )
}

// Mock data generator for demonstration
function getMockCompliancePaths(assetType: AssetType): AssetCompliancePath[] {
  const baseSteps: ComplianceStepDraft[] = [
    {
      id: '1',
      submission_type: 'planning_permission' as const,
      typical_duration_days: 21,
      is_mandatory: true,
    },
    {
      id: '2',
      submission_type: 'development_control' as const,
      typical_duration_days: 14,
      is_mandatory: true,
    },
    {
      id: '3',
      submission_type: 'building_plan' as const,
      typical_duration_days: 28,
      is_mandatory: true,
    },
    {
      id: '4',
      submission_type: 'structural_plan' as const,
      typical_duration_days: 21,
      is_mandatory: true,
    },
    {
      id: '5',
      submission_type: 'fire_safety' as const,
      typical_duration_days: 14,
      is_mandatory: true,
    },
    {
      id: '6',
      submission_type: 'environmental' as const,
      typical_duration_days: 14,
      is_mandatory: assetType === 'industrial',
    },
  ]

  if (assetType === 'heritage') {
    baseSteps.splice(1, 0, {
      id: '1b',
      submission_type: 'heritage_conservation' as const,
      typical_duration_days: 35,
      is_mandatory: true,
    })
  }

  baseSteps.push(
    {
      id: '7',
      submission_type: 'csc_application' as const,
      typical_duration_days: 7,
      is_mandatory: true,
    },
    {
      id: '8',
      submission_type: 'top_application' as const,
      typical_duration_days: 14,
      is_mandatory: true,
    },
  )

  return baseSteps.map((step, index) => ({
    ...step,
    asset_type: assetType,
    agency_id: 'mock-agency-id',
    sequence_order: index + 1,
    created_at: new Date().toISOString(),
  }))
}

export default CompliancePathTimeline
