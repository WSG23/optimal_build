import { Box, Chip, Grid, Stack, Typography } from '@mui/material'

import {
  PARTNER_INTEGRATIONS,
  PRIMARY_MARKET,
  type PartnerIntegrationStatus,
} from '../../config/productFocus'

function statusLabel(status: PartnerIntegrationStatus): string {
  switch (status) {
    case 'live':
      return 'Live'
    case 'partner_access_required':
      return 'Partner access required'
    case 'coming_soon':
      return 'Coming soon'
    default:
      return status
  }
}

function statusColor(
  status: PartnerIntegrationStatus,
): 'success' | 'warning' | 'default' {
  switch (status) {
    case 'live':
      return 'success'
    case 'partner_access_required':
      return 'warning'
    case 'coming_soon':
    default:
      return 'default'
  }
}

export function IntegrationsPage() {
  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: 1200,
        mx: 'auto',
      }}
    >
      <Stack spacing="var(--ob-space-300)">
        <Box>
          <Typography variant="h3" sx={{ mb: 'var(--ob-space-050)' }}>
            Singapore data partnerships
          </Typography>
          <Typography variant="body1" color="text.secondary">
            This page no longer simulates live portal logins or listing
            publication. Every integration below is shown as live,
            partner-gated, or roadmap only.
          </Typography>
        </Box>

        <Box
          sx={{
            p: 'var(--ob-space-200)',
            borderRadius: 'var(--ob-radius-sm)',
            border: '1px solid',
            borderColor: 'divider',
            bgcolor: 'background.paper',
          }}
        >
          <Stack spacing="var(--ob-space-150)">
            <Stack
              direction={{ xs: 'column', md: 'row' }}
              spacing="var(--ob-space-150)"
              justifyContent="space-between"
            >
              <Box>
                <Typography variant="h6">Current product stance</Typography>
                <Typography variant="body2" color="text.secondary">
                  Prioritize one real {PRIMARY_MARKET} data source before adding
                  any more scaffolding. User-facing integrations should never
                  pretend a commercial partnership already exists.
                </Typography>
              </Box>
              <Chip
                color="primary"
                variant="outlined"
                label={`Primary market: ${PRIMARY_MARKET}`}
              />
            </Stack>
            <Typography variant="body2" color="text.secondary">
              Internal adapters and mocked connectors can remain in the codebase
              for development, but they are no longer presented as live actions
              in the product UX.
            </Typography>
          </Stack>
        </Box>

        <Grid container spacing="var(--ob-space-200)">
          {PARTNER_INTEGRATIONS.map((integration) => (
            <Grid item xs={12} md={6} key={integration.id}>
              <Box
                sx={{
                  p: 'var(--ob-space-200)',
                  borderRadius: 'var(--ob-radius-sm)',
                  border: '1px solid',
                  borderColor: 'divider',
                  bgcolor: 'background.paper',
                  height: '100%',
                }}
              >
                <Stack spacing="var(--ob-space-150)" sx={{ height: '100%' }}>
                  <Stack
                    direction="row"
                    spacing="var(--ob-space-100)"
                    justifyContent="space-between"
                    alignItems="flex-start"
                  >
                    <Box>
                      <Typography variant="h6">{integration.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {integration.description}
                      </Typography>
                    </Box>
                    <Chip
                      size="small"
                      color={statusColor(integration.status)}
                      label={statusLabel(integration.status)}
                    />
                  </Stack>

                  <Typography variant="body2" color="text.secondary">
                    {integration.detail}
                  </Typography>

                  <Box sx={{ mt: 'auto' }}>
                    <Typography variant="caption" color="text.secondary">
                      Next step
                    </Typography>
                    <Typography variant="body2">
                      {integration.nextStep}
                    </Typography>
                  </Box>
                </Stack>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Stack>
    </Box>
  )
}
