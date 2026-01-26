import { useState } from 'react'
import {
  Box,
  Typography,
  Container,
  Grid,
  Button,
  TextField,
  Divider,
} from '@mui/material'
import {
  Science as ScienceIcon,
  ViewInAr as ViewInArIcon,
  BugReport as BugReportIcon,
} from '@mui/icons-material'
import { FeatureTogglePanel } from '../../components/gps-capture/FeatureTogglePanel'
import { useFeaturePreferences } from '../../../hooks/useFeaturePreferences'
import { useRouterController } from '../../../router'
import { Card } from '../../../components/canonical/Card'

export function DeveloperControlPanel() {
  const { preferences, toggleFeature, entitlements, unlockFeature } =
    useFeaturePreferences('developer')
  const { navigate } = useRouterController()
  const [propertyId, setPropertyId] = useState('')

  const handlePreviewNavigate = () => {
    if (propertyId) {
      navigate(`/agents/developers/${propertyId}/preview`)
    }
  }

  return (
    <Container maxWidth="lg">
      <Grid
        container
        spacing="var(--ob-space-400)"
        sx={{ mt: 'var(--ob-space-200)' }}
      >
        {/* Feature Flags Section */}
        <Grid item xs={12} md={6}>
          <Card variant="glass">
            <Box sx={{ p: 'var(--ob-space-300)' }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  mb: 'var(--ob-space-200)',
                }}
              >
                <ScienceIcon
                  sx={{ mr: 'var(--ob-space-100)', color: 'primary.main' }}
                />
                <Typography variant="h6">Experimental Features</Typography>
              </Box>
              <Divider sx={{ mb: 'var(--ob-space-200)' }} />
              <FeatureTogglePanel
                preferences={preferences}
                entitlements={entitlements}
                onToggle={toggleFeature}
                onUnlock={unlockFeature}
              />
            </Box>
          </Card>
        </Grid>

        {/* Tools Section */}
        <Grid item xs={12} md={6}>
          <Card variant="glass">
            <Box sx={{ p: 'var(--ob-space-300)' }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  mb: 'var(--ob-space-200)',
                }}
              >
                <ViewInArIcon
                  sx={{ mr: 'var(--ob-space-100)', color: 'secondary.main' }}
                />
                <Typography variant="h6">3D Preview Tool</Typography>
              </Box>
              <Divider sx={{ mb: 'var(--ob-space-200)' }} />
              <Typography variant="body2" color="text.secondary" paragraph>
                Directly access the 3D 2B preview viewer for a specific property
                ID.
              </Typography>
              <Box sx={{ display: 'flex', gap: 'var(--ob-space-100)' }}>
                <TextField
                  size="small"
                  placeholder="Property ID (e.g. PROP-123)"
                  value={propertyId}
                  onChange={(e) => setPropertyId(e.target.value)}
                  fullWidth
                />
                <Button
                  variant="contained"
                  onClick={handlePreviewNavigate}
                  disabled={!propertyId}
                >
                  Go
                </Button>
              </Box>
            </Box>
          </Card>

          <Box sx={{ mt: 'var(--ob-space-300)' }}>
            <Card variant="glass">
              <Box sx={{ p: 'var(--ob-space-300)' }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    mb: 'var(--ob-space-200)',
                  }}
                >
                  <BugReportIcon
                    sx={{ mr: 'var(--ob-space-100)', color: 'error.main' }}
                  />
                  <Typography variant="h6">Debug Info</Typography>
                </Box>
                <Divider sx={{ mb: 'var(--ob-space-200)' }} />
                <Typography variant="body2" fontFamily="monospace">
                  Build Version: v2.0.0-alpha
                  <br />
                  Environment: {import.meta.env.MODE}
                  <br />
                  User Role: Developer (Simulated)
                </Typography>
              </Box>
            </Card>
          </Box>
        </Grid>
      </Grid>
    </Container>
  )
}
