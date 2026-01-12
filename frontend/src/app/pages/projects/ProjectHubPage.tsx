import { Box, Button, Grid, Stack, Typography } from '@mui/material'

import { useProject } from '../../../contexts/useProject'
import { useRouterController } from '../../../router'

export function ProjectHubPage() {
  const { navigate } = useRouterController()
  const { currentProject, isProjectLoading, projectError } = useProject()

  if (!currentProject) {
    return (
      <Box sx={{ width: '100%' }}>
        {isProjectLoading ? (
          <Typography color="text.secondary">Loading project...</Typography>
        ) : (
          <>
            <Typography variant="h5" sx={{ mb: 1 }}>
              No project selected
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {projectError?.message ??
                'Select a project to view results and navigate to modules.'}
            </Typography>
            <Button variant="contained" onClick={() => navigate('/projects')}>
              Go to projects
            </Button>
          </>
        )}
      </Box>
    )
  }

  const basePath = `/projects/${currentProject.id}`

  return (
    <Box sx={{ width: '100%' }}>
      <Stack spacing={1} sx={{ mb: 3 }}>
        <Typography variant="h4">{currentProject.name}</Typography>
        <Typography variant="body2" color="text.secondary">
          Project hub and quick navigation.
        </Typography>
      </Stack>

      <Grid container spacing={2}>
        {[
          { label: 'Capture Results', path: `${basePath}/capture` },
          { label: 'Feasibility', path: `${basePath}/feasibility` },
          { label: 'Finance', path: `${basePath}/finance` },
          { label: 'Phase Management', path: `${basePath}/phases` },
          { label: 'Team', path: `${basePath}/team` },
          { label: 'Regulatory', path: `${basePath}/regulatory` },
        ].map((item) => (
          <Grid item xs={12} md={6} key={item.path}>
            <Button
              variant="outlined"
              fullWidth
              onClick={() => navigate(item.path)}
              sx={{ justifyContent: 'flex-start', py: 2 }}
            >
              {item.label}
            </Button>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
