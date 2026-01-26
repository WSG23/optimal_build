import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Stack,
  TextField,
  Typography,
} from '@mui/material'

import { useProject } from '../../../contexts/useProject'
import { useRouterController } from '../../../router'

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

  return (
    <Box sx={{ width: '100%' }}>
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        justifyContent="space-between"
        alignItems={{ xs: 'flex-start', sm: 'center' }}
        spacing="var(--ob-space-200)"
        sx={{ mb: 'var(--ob-space-300)' }}
      >
        <Box>
          <Typography variant="h4">Projects</Typography>
          <Typography variant="body2" color="text.secondary">
            Select a project to continue or create a new one.
          </Typography>
        </Box>
        <Button variant="contained" onClick={() => setCreateOpen(true)}>
          Create project
        </Button>
      </Stack>

      {isProjectLoading && (
        <Typography color="text.secondary">Loading projects...</Typography>
      )}

      {!isProjectLoading && projects.length === 0 && (
        <Typography color="text.secondary">No projects yet.</Typography>
      )}

      <Grid container spacing="var(--ob-space-200)">
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
            <Typography
              variant="body2"
              color="error"
              sx={{ mt: 'var(--ob-space-100)' }}
            >
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
