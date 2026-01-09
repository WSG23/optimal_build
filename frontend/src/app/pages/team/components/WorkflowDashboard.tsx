import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  Button,
  Grid,
  Card,
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
import { ApprovalWorkflow } from '../../../../api/workflow' // Fixed import path
import { CreateWorkflowDialog } from './CreateWorkflowDialog'

interface WorkflowDashboardProps {
  projectId: string
}

export const WorkflowDashboard: React.FC<WorkflowDashboardProps> = ({
  projectId,
}) => {
  const [workflows, setWorkflows] = useState<ApprovalWorkflow[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)

  // Ref to track if we've initialized
  const hasInitializedRef = useRef(false)

  // Mock data for initial dev - using stable dates to prevent re-render loops
  const createMockWorkflows = React.useCallback(
    (pid: string): ApprovalWorkflow[] => [
      {
        id: 'mock-w1',
        project_id: pid,
        name: 'Concept Design Sign-off',
        description:
          'Initial concept design review and approval workflow for the project.',
        workflow_type: 'design_review',
        status: 'in_progress',
        current_step_order: 2,
        created_at: '2024-01-15T10:00:00.000Z', // Stable date
        steps: [
          {
            id: 'mock-s1',
            name: 'Architectural Review',
            order: 1,
            status: 'approved',
            approved_by_id: 'u2',
            approved_at: '2024-01-16T14:30:00.000Z', // Stable date
            approver_role: 'architect',
          },
          {
            id: 'mock-s2',
            name: 'Structural Feasibility',
            order: 2,
            status: 'in_review',
            approver_role: 'engineer',
          },
          {
            id: 'mock-s3',
            name: 'Client Approval',
            order: 3,
            status: 'pending',
            approver_role: 'developer',
          },
        ],
      },
    ],
    [],
  )

  // Initialize workflows only once on mount
  useEffect(() => {
    if (hasInitializedRef.current) {
      return
    }
    hasInitializedRef.current = true
    setLoading(true)
    // For Phase 2E implementation, we rely on mock data + newly created workflows pushed to list locally.
    // TODO: Add list endpoint to backend when available
    setWorkflows(createMockWorkflows(projectId))
    setLoading(false)
  }, [projectId, createMockWorkflows])

  const handleCreateSuccess = (newWorkflow: ApprovalWorkflow) => {
    // Add new workflow to list, keeping mock data at the end
    setWorkflows((prev) => {
      // Filter out mock workflows, add new one at start, then add mock back
      const realWorkflows = prev.filter((w) => !w.id.startsWith('mock-'))
      const mockWorkflowsInState = prev.filter((w) => w.id.startsWith('mock-'))
      return [newWorkflow, ...realWorkflows, ...mockWorkflowsInState]
    })
    setCreateOpen(false)
  }

  const handleApproveStep = async (stepId: string) => {
    // Optimistic update or call API
    // Since API returns updated object (assumed), we can update state.
    // Mock update for now:
    setWorkflows((prev) =>
      prev.map((w) => ({
        ...w,
        steps: w.steps.map((s) =>
          s.id === stepId
            ? {
                ...s,
                status: 'approved' as const,
                decision_at: new Date().toISOString(),
              }
            : s,
        ),
      })),
    )
    // Real call:
    // await workflowApi.approveStep(stepId, true, 'Approved from dashboard')
    // fetchWorkflows()
  }

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'flex-end',
          mb: 'var(--ob-space-300)',
        }}
      >
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          sx={{
            background:
              'linear-gradient(135deg, var(--ob-brand-500) 0%, var(--ob-brand-400) 100%)',
            boxShadow: 'var(--ob-shadow-md)',
          }}
        >
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
        <Grid container spacing="var(--ob-space-300)">
          {workflows.map((workflow) => (
            <Grid item xs={12} key={workflow.id}>
              <WorkflowCard
                workflow={workflow}
                onApproveStep={handleApproveStep}
              />
            </Grid>
          ))}
          {workflows.length === 0 && (
            <Grid item xs={12}>
              <Typography variant="body1" color="text.secondary" align="center">
                No active workflows. Create one to get started.
              </Typography>
            </Grid>
          )}
        </Grid>
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
    <Card
      sx={{
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        overflow: 'hidden',
      }}
    >
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
                        size="small"
                        variant="outlined"
                        startIcon={<CheckIcon />}
                        onClick={(e) => {
                          e.stopPropagation()
                          onApproveStep(step.id)
                        }}
                        sx={{
                          mr: 'var(--ob-space-100)',
                          fontSize: 'var(--ob-font-size-xs)',
                        }}
                      >
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
    </Card>
  )
}
