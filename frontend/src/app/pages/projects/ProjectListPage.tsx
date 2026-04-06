import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import {
  FolderOpenOutlined,
  CalculateOutlined,
  UploadFileOutlined,
  AutoStoriesOutlined,
} from '@mui/icons-material'

import { EmptyState } from '../../../components/canonical'
import { useProject } from '../../../contexts/useProject'
import { useRouterController } from '../../../router'
import {
  PRIMARY_MARKET,
  PUBLIC_JURISDICTIONS,
  SINGAPORE_SAMPLE_PROJECT,
} from '../../config/productFocus'

export function ProjectListPage() {
  const { navigate } = useRouterController()
  const {
    projects,
    isProjectLoading,
    refreshProjects,
    setCurrentProject,
    createProject,
  } = useProject()
  const [createOpen, setCreateOpen] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [createError, setCreateError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [launchingAction, setLaunchingAction] = useState<
    'workbook' | 'sample' | null
  >(null)

  useEffect(() => {
    void refreshProjects()
  }, [refreshProjects])

  const handleCreate = async () => {
    if (!projectName.trim()) {
      setCreateError('Project name is required.')
      return
    }
    setCreating(true)
    setCreateError(null)
    try {
      const created = await createProject({ name: projectName.trim() })
      setCurrentProject(created)
      setProjectName('')
      setCreateOpen(false)
      navigate(`/projects/${created.id}`)
    } catch (error) {
      setCreateError(
        error instanceof Error ? error.message : 'Unable to create project.',
      )
    } finally {
      setCreating(false)
    }
  }

  const handleLaunchWorkbook = async () => {
    setLaunchingAction('workbook')
    setCreateError(null)
    try {
      const created = await createProject({
        name: `Singapore workbook intake ${new Date().toLocaleDateString()}`,
        description:
          'Developer-first workbook onboarding project for Singapore feasibility and finance.',
      })
      setCurrentProject(created)
      navigate(`/projects/${created.id}/finance?onboarding=workbook`)
    } catch (error) {
      setCreateError(
        error instanceof Error
          ? error.message
          : 'Unable to start workbook intake.',
      )
    } finally {
      setLaunchingAction(null)
    }
  }

  const handleOpenSampleProject = async () => {
    setLaunchingAction('sample')
    setCreateError(null)
    try {
      const created = await createProject({
        name: SINGAPORE_SAMPLE_PROJECT.name,
        description: SINGAPORE_SAMPLE_PROJECT.description,
      })
      setCurrentProject(created)
      navigate(
        `/projects/${created.id}/finance?onboarding=sample&template=${SINGAPORE_SAMPLE_PROJECT.templateId}`,
      )
    } catch (error) {
      setCreateError(
        error instanceof Error
          ? error.message
          : 'Unable to open the sample project.',
      )
    } finally {
      setLaunchingAction(null)
    }
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Stack spacing={2.5}>
            <Stack
              direction={{ xs: 'column', md: 'row' }}
              justifyContent="space-between"
              spacing={2}
            >
              <Box>
                <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                  <Chip
                    size="small"
                    color="primary"
                    label={`${PRIMARY_MARKET} first`}
                  />
                  <Chip
                    size="small"
                    variant="outlined"
                    label={`Primary UX: ${PUBLIC_JURISDICTIONS.join(', ')}`}
                  />
                </Stack>
                <Typography variant="h4">
                  Singapore developer workspace
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Start where real underwriting starts: model a deal, import an
                  existing workbook, or open a guided Singapore sample project.
                </Typography>
              </Box>
              <Box sx={{ maxWidth: 320 }}>
                <Typography variant="body2" color="text.secondary">
                  The primary workflow is now Singapore-only on the surface.
                  Multi-jurisdiction support stays in the architecture, behind
                  internal flags.
                </Typography>
              </Box>
            </Stack>

            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack spacing={1.25}>
                      <CalculateOutlined color="primary" />
                      <Typography variant="h6">Model a deal</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Paste an address or enter assumptions to get Singapore
                        feasibility and finance in one screen.
                      </Typography>
                    </Stack>
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => navigate('/developers/deal-calculator')}
                    >
                      Open deal calculator
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack spacing={1.25}>
                      <UploadFileOutlined color="primary" />
                      <Typography variant="h6">Import workbook</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Upload an existing Excel model and structure it into the
                        finance workspace without building a project manually.
                      </Typography>
                    </Stack>
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => void handleLaunchWorkbook()}
                      disabled={launchingAction !== null}
                    >
                      {launchingAction === 'workbook'
                        ? 'Preparing workbook flow...'
                        : 'Start workbook intake'}
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack spacing={1.25}>
                      <AutoStoriesOutlined color="primary" />
                      <Typography variant="h6">Open sample project</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Walk through a seeded Singapore mixed-use example with
                        template guidance, audit context, and next-step prompts.
                      </Typography>
                    </Stack>
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => void handleOpenSampleProject()}
                      disabled={launchingAction !== null}
                    >
                      {launchingAction === 'sample'
                        ? 'Opening sample...'
                        : 'Open sample project'}
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            </Grid>

            <Stack spacing={1}>
              <Typography variant="subtitle2">What to do next</Typography>
              <Typography variant="body2" color="text.secondary">
                1. Run a quick deal screen or import a workbook.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                2. Turn the result into a finance scenario and compare export
                presets.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                3. Review evidence packs before handing numbers to lenders, IC,
                or compliance.
              </Typography>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        justifyContent="space-between"
        alignItems={{ xs: 'flex-start', sm: 'center' }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Box>
          <Typography variant="h4">Projects</Typography>
          <Typography variant="body2" color="text.secondary">
            Select an existing Singapore development workflow or create a new
            project.
          </Typography>
        </Box>
        <Button variant="contained" onClick={() => setCreateOpen(true)}>
          Create project
        </Button>
      </Stack>

      {createError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {createError}
        </Alert>
      )}

      {isProjectLoading && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: 'var(--ob-space-150)',
          }}
        >
          {[1, 2, 3].map((i) => (
            <Skeleton
              key={i}
              variant="rectangular"
              height={120}
              sx={{ borderRadius: 'var(--ob-radius-sm)' }}
            />
          ))}
        </Box>
      )}

      {!isProjectLoading && projects.length === 0 && (
        <EmptyState
          icon={<FolderOpenOutlined />}
          title="No projects yet"
          description="Start with the deal calculator, import an existing workbook, or open the seeded Singapore sample project."
          actionLabel="Model a deal"
          onAction={() => navigate('/developers/deal-calculator')}
          secondaryActionLabel="Import workbook"
          onSecondaryAction={() => void handleLaunchWorkbook()}
          size="lg"
          sx={{ py: 8, mb: 3 }}
        />
      )}

      <Grid container spacing={2}>
        {projects.map((project) => (
          <Grid item xs={12} md={6} lg={4} key={project.id}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6">{project.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Status: {project.status ?? 'active'}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  onClick={() => {
                    setCurrentProject(project)
                    navigate(`/projects/${project.id}`)
                  }}
                >
                  Open
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)}>
        <DialogTitle>Create Project</DialogTitle>
        <DialogContent>
          <TextField
            label="Project name"
            value={projectName}
            onChange={(event) => setProjectName(event.target.value)}
            fullWidth
            margin="dense"
          />
          {createError && (
            <Typography variant="body2" color="error" sx={{ mt: 1 }}>
              {createError}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)} disabled={creating}>
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={creating}>
            {creating ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
