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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Snackbar,
} from '@mui/material'
import {
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckIcon,
  Cancel as RejectIcon,
} from '@mui/icons-material'
import { Button } from '../../../../components/canonical/Button'
import { Card } from '../../../../components/canonical/Card'
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
  const [snackbar, setSnackbar] = useState<string | null>(null)

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
    setSnackbar('Workflow created')
  }

  const handleStepAction = async (
    stepId: string,
    approved: boolean,
    comments: string,
  ) => {
    if (stepId.startsWith('mock-')) {
      setWorkflows((prev) =>
        prev.map((w) => ({
          ...w,
          steps: w.steps.map((s) =>
            s.id === stepId
              ? {
                  ...s,
                  status: approved
                    ? ('approved' as const)
                    : ('rejected' as const),
                  approved_at: new Date().toISOString(),
                }
              : s,
          ),
        })),
      )
      setSnackbar(approved ? 'Step approved' : 'Step rejected')
      return
    }

    try {
      await workflowApi.approveStep(stepId, approved, comments || undefined)
      await fetchWorkflows()
      setSnackbar(approved ? 'Step approved' : 'Step rejected')
    } catch (error) {
      console.error('Failed to update step:', error)
      setSnackbar('Failed to update step. Check your permissions.')
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
              onStepAction={handleStepAction}
            />
          ))}
          {workflows.length === 0 && (
            <Card sx={{ p: 'var(--ob-space-300)' }}>
              <Typography variant="body1" color="text.secondary" align="center">
                No active workflows. Create one to get started.
              </Typography>
            </Card>
          )}
        </Box>
      )}

      <CreateWorkflowDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        projectId={projectId}
        onSuccess={handleCreateSuccess}
      />

      <Snackbar
        open={!!snackbar}
        autoHideDuration={4000}
        onClose={() => setSnackbar(null)}
        message={snackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      />
    </Box>
  )
}

const WorkflowCard: React.FC<{
  workflow: ApprovalWorkflow
  onStepAction: (id: string, approved: boolean, comments: string) => void
}> = ({ workflow, onStepAction }) => {
  const [expanded, setExpanded] = useState(true)
  const [confirmStep, setConfirmStep] = useState<{
    id: string
    name: string
    approved: boolean
  } | null>(null)
  const [comments, setComments] = useState('')

  const activeStepIndex = workflow.steps.findIndex(
    (s) => s.status === 'in_review' || s.status === 'pending',
  )

  const statusColor =
    workflow.status === 'approved'
      ? 'success'
      : workflow.status === 'rejected'
        ? 'error'
        : workflow.status === 'in_progress'
          ? 'primary'
          : 'default'

  return (
    <Card sx={{ overflow: 'hidden' }}>
      <Box
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        sx={{
          p: 'var(--ob-space-200)',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setExpanded(!expanded)
          }
        }}
      >
        <Box sx={{ flex: 1 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-100)',
              mb: workflow.description ? 'var(--ob-space-050)' : 0,
            }}
          >
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {workflow.name || workflow.title}
            </Typography>
            <Chip
              label={workflow.status.replace('_', ' ')}
              color={statusColor}
              size="small"
              sx={{ textTransform: 'capitalize' }}
            />
            <Chip
              label={workflow.workflow_type.replace(/_/g, ' ')}
              size="small"
              variant="outlined"
              sx={{ textTransform: 'capitalize' }}
            />
          </Box>
          {workflow.description && (
            <Typography variant="body2" color="text.secondary">
              {workflow.description}
            </Typography>
          )}
        </Box>
        <IconButton size="small" tabIndex={-1} aria-hidden>
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <Divider />
        <Box sx={{ p: 'var(--ob-space-200)' }}>
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
                          : step.status === 'rejected'
                            ? 'error.main'
                            : step.status === 'in_review'
                              ? 'primary.main'
                              : 'text.disabled',
                    },
                  }}
                >
                  <Box>
                    <Typography variant="body2">{step.name}</Typography>
                    {step.approver_role && (
                      <Typography variant="caption" color="text.secondary">
                        Role: {step.approver_role}
                      </Typography>
                    )}
                    {step.approved_at && (
                      <Typography
                        variant="caption"
                        display="block"
                        color="text.secondary"
                      >
                        {step.status === 'rejected' ? 'Rejected' : 'Approved'}{' '}
                        {new Date(step.approved_at).toLocaleDateString()}
                      </Typography>
                    )}
                    {step.comments && (
                      <Typography
                        variant="caption"
                        display="block"
                        sx={{ fontStyle: 'italic', color: 'text.secondary' }}
                      >
                        &ldquo;{step.comments}&rdquo;
                      </Typography>
                    )}
                  </Box>
                  {step.status === 'in_review' && (
                    <Box
                      sx={{
                        mt: 'var(--ob-space-075)',
                        display: 'flex',
                        gap: 'var(--ob-space-050)',
                      }}
                    >
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={(e) => {
                          e.stopPropagation()
                          setConfirmStep({
                            id: step.id,
                            name: step.name,
                            approved: true,
                          })
                        }}
                      >
                        <CheckIcon sx={{ fontSize: '0.875rem' }} />
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        sx={{ color: 'error.main' }}
                        onClick={(e) => {
                          e.stopPropagation()
                          setConfirmStep({
                            id: step.id,
                            name: step.name,
                            approved: false,
                          })
                        }}
                      >
                        <RejectIcon sx={{ fontSize: '0.875rem' }} />
                        Reject
                      </Button>
                    </Box>
                  )}
                </StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>
      </Collapse>

      {/* Confirm approve/reject dialog */}
      <Dialog
        open={!!confirmStep}
        onClose={() => {
          setConfirmStep(null)
          setComments('')
        }}
      >
        <DialogTitle>
          {confirmStep?.approved ? 'Approve' : 'Reject'} Step
        </DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 'var(--ob-space-150)' }}>
            {confirmStep?.approved ? 'Approve' : 'Reject'}{' '}
            <strong>{confirmStep?.name}</strong>?
            {!confirmStep?.approved && ' This will reject the entire workflow.'}
          </Typography>
          <TextField
            label="Comments (optional)"
            fullWidth
            multiline
            rows={2}
            value={comments}
            onChange={(e) => setComments(e.target.value)}
          />
        </DialogContent>
        <DialogActions
          sx={{ p: 'var(--ob-space-200)', gap: 'var(--ob-space-100)' }}
        >
          <Button
            variant="ghost"
            onClick={() => {
              setConfirmStep(null)
              setComments('')
            }}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            sx={
              !confirmStep?.approved
                ? {
                    bgcolor: 'error.main',
                    '&:hover': { bgcolor: 'error.dark' },
                  }
                : {}
            }
            onClick={() => {
              if (confirmStep) {
                onStepAction(confirmStep.id, confirmStep.approved, comments)
                setConfirmStep(null)
                setComments('')
              }
            }}
          >
            {confirmStep?.approved ? 'Approve' : 'Reject'}
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  )
}
