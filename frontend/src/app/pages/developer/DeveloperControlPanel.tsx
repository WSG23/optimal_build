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
import { GlassCard } from '../../../components/canonical/GlassCard'
import { AnimatedPageHeader } from '../../../components/canonical/AnimatedPageHeader'

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
      <AnimatedPageHeader
        title="Developer Control Panel"
        subtitle="Manage feature flags, debug tools, and system configurations."
      />

      <Grid container spacing={4} sx={{ mt: 2 }}>
        {/* Feature Flags Section */}
        <Grid item xs={12} md={6}>
          <GlassCard>
            <Box sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ScienceIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Experimental Features</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <FeatureTogglePanel
                preferences={preferences}
                entitlements={entitlements}
                onToggle={toggleFeature}
                onUnlock={unlockFeature}
              />
            </Box>
          </GlassCard>
        </Grid>

        {/* Tools Section */}
        <Grid item xs={12} md={6}>
          <GlassCard>
            <Box sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ViewInArIcon sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="h6">3D Preview Tool</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary" paragraph>
                Directly access the 3D 2B preview viewer for a specific property
                ID.
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
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
          </GlassCard>

          <Box sx={{ mt: 3 }}>
            <GlassCard>
              <Box sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <BugReportIcon sx={{ mr: 1, color: 'error.main' }} />
                  <Typography variant="h6">Debug Info</Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="body2" fontFamily="monospace">
                  Build Version: v2.0.0-alpha
                  <br />
                  Environment: {import.meta.env.MODE}
                  <br />
                  User Role: Developer (Simulated)
                </Typography>
              </Box>
            </GlassCard>
          </Box>
        </Grid>
      </Grid>
    </Container>
  )
}
