import React, { useState, useEffect, useCallback, useMemo } from 'react'
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

  // Mock data for initial dev - memoized to prevent unnecessary re-renders
  const mockWorkflows = useMemo<ApprovalWorkflow[]>(
    () => [
      {
        id: 'w1',
        project_id: projectId,
        title: 'Concept Design Sign-off',
        workflow_type: 'design_review',
        status: 'in_progress',
        created_by_id: 'u1',
        created_at: new Date().toISOString(),
        steps: [
          {
            id: 's1',
            workflow_id: 'w1',
            name: 'Architectural Review',
            sequence_order: 1,
            status: 'approved',
            approved_by_id: 'u2',
            decision_at: new Date().toISOString(),
          },
          {
            id: 's2',
            workflow_id: 'w1',
            name: 'Structural Feasibility',
            sequence_order: 2,
            status: 'in_review',
          },
          {
            id: 's3',
            workflow_id: 'w1',
            name: 'Client Approval',
            sequence_order: 3,
            status: 'pending',
          },
        ],
      },
    ],
    [projectId],
  )

  const fetchWorkflows = useCallback(async () => {
    setLoading(true)
    try {
      // In real backend, we'd list workflows. Current API might only have GET /workflow/{id} or POST /workflow/
      // If list endpoint missing, I will just show mock data or empty state for now.
      // Or assumed there is a list endpoint I missed?
      // Checking `api/v1/workflow.py`: Only `create_workflow` and `get_workflow` (by ID) present.
      // I need to add a LIST endpoint to backend or mock it here.
      // For Phase 2E implementation, I will rely on Mock data + newly created workflows pushed to list locally.
      setWorkflows(mockWorkflows)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [mockWorkflows])

  useEffect(() => {
    fetchWorkflows()
  }, [fetchWorkflows])

  const handleCreateSuccess = (newWorkflow: ApprovalWorkflow) => {
    setWorkflows([newWorkflow, ...workflows])
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
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3 }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          sx={{
            background: 'linear-gradient(135deg, #FF3366 0%, #FF6B3D 100%)',
            boxShadow: '0px 4px 12px rgba(255, 51, 102, 0.3)',
          }}
        >
          New Workflow
        </Button>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
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
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6">{workflow.title}</Typography>
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
        <IconButton size="small">
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <Divider />
        <Box sx={{ p: 3 }}>
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
                            : 'grey.700',
                    },
                  }}
                >
                  {step.name}
                  {step.status === 'in_review' && (
                    <Box sx={{ mt: 1 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<CheckIcon />}
                        onClick={() => onApproveStep(step.id)}
                        sx={{ mr: 1, fontSize: '0.7rem' }}
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
