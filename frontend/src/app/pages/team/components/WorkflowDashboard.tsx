import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Chip,
  CircularProgress,
  IconButton,
  Collapse,
  Step,
  StepLabel,
  Stepper,
  Divider,
} from '@mui/material'
import {
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material'
import { Button } from '../../../../components/canonical/Button'
import { GlassCard } from '../../../../components/canonical/GlassCard'
import { ApprovalWorkflow, workflowApi } from '../../../../api/workflow'
import { CreateWorkflowDialog } from './CreateWorkflowDialog'

interface WorkflowDashboardProps {
  projectId: string
}

const STORAGE_PREFIX = 'ob_team_workflows'

const buildStorageKey = (projectId: string) => `${STORAGE_PREFIX}:${projectId}`

const loadStoredWorkflows = (projectId: string): ApprovalWorkflow[] => {
  if (typeof window === 'undefined' || !projectId) {
    return []
  }
  const raw = window.localStorage.getItem(buildStorageKey(projectId))
  if (!raw) {
    return []
  }
  try {
    const parsed = JSON.parse(raw) as ApprovalWorkflow[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const persistWorkflows = (projectId: string, workflows: ApprovalWorkflow[]) => {
  if (typeof window === 'undefined' || !projectId) {
    return
  }
  window.localStorage.setItem(
    buildStorageKey(projectId),
    JSON.stringify(workflows),
  )
}

export const WorkflowDashboard: React.FC<WorkflowDashboardProps> = ({
  projectId,
}) => {
  const [workflows, setWorkflows] = useState<ApprovalWorkflow[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)

  // Fetch workflows from API
  const fetchWorkflows = React.useCallback(async () => {
    setLoading(true)
    const stored = loadStoredWorkflows(projectId)
    try {
      const data = await workflowApi.listWorkflows(projectId)
      if (data.length > 0) {
        setWorkflows(data)
        persistWorkflows(projectId, data)
        return
      }
      if (stored.length > 0) {
        setWorkflows(stored)
        return
      }
      setWorkflows([])
    } catch (error) {
      console.error('Failed to fetch workflows:', error)
      if (stored.length > 0) {
        setWorkflows(stored)
      } else {
        setWorkflows([])
      }
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchWorkflows()
  }, [fetchWorkflows])

  const handleCreateSuccess = (newWorkflow: ApprovalWorkflow) => {
    setWorkflows((prev) => {
      const next = [
        newWorkflow,
        ...prev.filter((workflow) => workflow.id !== newWorkflow.id),
      ]
      persistWorkflows(projectId, next)
      return next
    })
    setCreateOpen(false)
  }

  const handleApproveStep = async (stepId: string) => {
    // Check if this is a mock step (mock IDs start with 'mock-')
    if (stepId.startsWith('mock-')) {
      // Optimistic update for mock data
      setWorkflows((prev) =>
        prev.map((w) => ({
          ...w,
          steps: w.steps.map((s) =>
            s.id === stepId
              ? {
                  ...s,
                  status: 'approved' as const,
                  approved_at: new Date().toISOString(),
                }
              : s,
          ),
        })),
      )
      return
    }

    // Real API call for non-mock steps
    try {
      await workflowApi.approveStep(stepId, true, 'Approved from dashboard')
      // Refresh workflows to get updated state
      await fetchWorkflows()
    } catch (error) {
      console.error('Failed to approve step:', error)
      // Could show error notification here
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-150)',
      }}
    >
      {/* Section header on background with action button */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography
          variant="subtitle2"
          sx={{
            color: 'text.secondary',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Approval Workflows
        </Typography>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setCreateOpen(true)}
        >
          <AddIcon sx={{ fontSize: '1rem', mr: 'var(--ob-space-050)' }} />
          New Workflow
        </Button>
      </Box>

      {loading ? (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            p: 'var(--ob-space-400)',
          }}
        >
          <CircularProgress />
        </Box>
      ) : (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-150)',
          }}
        >
          {workflows.map((workflow) => (
            <WorkflowCard
              key={workflow.id}
              workflow={workflow}
              onApproveStep={handleApproveStep}
            />
          ))}
          {workflows.length === 0 && (
            <GlassCard sx={{ p: 'var(--ob-space-300)' }}>
              <Typography variant="body1" color="text.secondary" align="center">
                No active workflows. Create one to get started.
              </Typography>
            </GlassCard>
          )}
        </Box>
      )}

      <CreateWorkflowDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        projectId={projectId}
        onSuccess={handleCreateSuccess}
      />
    </Box>
  )
}

const WorkflowCard: React.FC<{
  workflow: ApprovalWorkflow
  onApproveStep: (id: string) => void
}> = ({ workflow, onApproveStep }) => {
  const [expanded, setExpanded] = useState(true)

  const activeStepIndex = workflow.steps.findIndex(
    (s) => s.status === 'in_review' || s.status === 'pending',
  )

  return (
    <GlassCard sx={{ overflow: 'hidden' }}>
      <Box
        sx={{
          p: 'var(--ob-space-200)',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box sx={{ flex: 1 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-200)',
              mb: workflow.description ? 'var(--ob-space-050)' : 0,
            }}
          >
            <Typography variant="h6">
              {workflow.name || workflow.title}
            </Typography>
            <Chip
              label={workflow.status.replace('_', ' ')}
              color={
                workflow.status === 'approved'
                  ? 'success'
                  : workflow.status === 'in_progress'
                    ? 'primary'
                    : 'default'
              }
              size="small"
              sx={{ textTransform: 'capitalize' }}
            />
          </Box>
          {workflow.description && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 'var(--ob-space-050)' }}
            >
              {workflow.description}
            </Typography>
          )}
          <Box
            sx={{
              display: 'flex',
              gap: 'var(--ob-space-200)',
              mt: 'var(--ob-space-100)',
            }}
          >
            <Typography variant="caption" color="text.secondary">
              <strong>Type:</strong> {workflow.workflow_type.replace('_', ' ')}
            </Typography>
          </Box>
        </Box>
        <IconButton size="small">
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <Divider />
        <Box sx={{ p: 'var(--ob-space-300)' }}>
          <Stepper
            activeStep={
              activeStepIndex === -1 ? workflow.steps.length : activeStepIndex
            }
            alternativeLabel
          >
            {workflow.steps.map((step) => (
              <Step key={step.id}>
                <StepLabel
                  StepIconProps={{
                    sx: {
                      color:
                        step.status === 'approved'
                          ? 'success.main'
                          : step.status === 'in_review'
                            ? 'primary.main'
                            : 'text.disabled',
                    },
                  }}
                >
                  <Box>
                    {step.name}
                    {step.approver_role && (
                      <Typography
                        variant="caption"
                        display="block"
                        color="text.secondary"
                      >
                        Approver: {step.approver_role}
                      </Typography>
                    )}
                  </Box>
                  {step.status === 'in_review' && (
                    <Box sx={{ mt: 'var(--ob-space-100)' }}>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={(e) => {
                          e.stopPropagation()
                          onApproveStep(step.id)
                        }}
                      >
                        <CheckIcon
                          sx={{ fontSize: '1rem', mr: 'var(--ob-space-050)' }}
                        />
                        Approve
                      </Button>
                    </Box>
                  )}
                </StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>
      </Collapse>
    </GlassCard>
  )
}
