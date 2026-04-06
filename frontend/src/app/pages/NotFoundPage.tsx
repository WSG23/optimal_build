import { useMemo, useState } from 'react'
import { Box, Button, Stack, TextField, Typography } from '@mui/material'

import { Link } from '../../router'

export function NotFoundPage() {
  const [query, setQuery] = useState('')
  const quickLinks = useMemo(
    () =>
      [
        { label: 'Projects', to: '/projects' },
        { label: 'Deal Calculator', to: '/developers/deal-calculator' },
        { label: 'Site Acquisition', to: '/app/site-acquisition' },
        { label: 'Financial Control', to: '/developers/finance' },
        { label: 'Team Coordination', to: '/developers/team-coordination' },
      ].filter((item) =>
        query.trim()
          ? item.label.toLowerCase().includes(query.trim().toLowerCase())
          : true,
      ),
    [query],
  )

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        gap: 'var(--ob-space-150)',
        bgcolor: 'var(--ob-color-bg-root)',
        p: 'var(--ob-space-200)',
      }}
    >
      <Typography
        variant="h1"
        sx={{
          fontSize: 'var(--ob-font-size-5xl)',
          fontWeight: 'var(--ob-font-weight-bold)',
          color: 'var(--ob-color-text-muted)',
        }}
      >
        404
      </Typography>
      <Typography
        variant="h5"
        sx={{
          fontSize: 'var(--ob-font-size-xl)',
          color: 'var(--ob-color-text-secondary)',
        }}
      >
        Page not found
      </Typography>
      <Typography
        variant="body1"
        sx={{
          fontSize: 'var(--ob-font-size-md)',
          color: 'var(--ob-color-text-muted)',
        }}
      >
        This page doesn't exist — but your next project could.
      </Typography>
      <Box sx={{ width: '100%', maxWidth: 420 }}>
        <TextField
          fullWidth
          size="small"
          label="Find a workspace"
          placeholder="Search projects, finance, site acquisition..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </Box>
      <Stack
        direction="row"
        spacing="var(--ob-space-075)"
        flexWrap="wrap"
        useFlexGap
      >
        {quickLinks.map((item) => (
          <Button
            key={item.to}
            component={Link}
            to={item.to}
            variant="outlined"
            sx={{ borderRadius: 'var(--ob-radius-xs)' }}
          >
            {item.label}
          </Button>
        ))}
      </Stack>
      <Box
        sx={{
          display: 'flex',
          gap: 'var(--ob-space-100)',
          mt: 'var(--ob-space-100)',
        }}
      >
        <Button
          component={Link}
          to="/"
          variant="contained"
          sx={{ borderRadius: 'var(--ob-radius-xs)' }}
        >
          Start a project
        </Button>
        <Button
          component={Link}
          to="/agents"
          variant="outlined"
          sx={{ borderRadius: 'var(--ob-radius-xs)' }}
        >
          View pipeline
        </Button>
      </Box>
    </Box>
  )
}
