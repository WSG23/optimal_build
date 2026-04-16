import { Box, Typography, Stack, Button, useTheme, alpha } from '@mui/material'
import { useRouterPath, Link } from '../../router'
import {
  AGENT_NAV_ITEMS,
  DEVELOPER_NAV_ITEMS,
  resolveNavPath,
} from '../../app/navigation'
import { useProject } from '../../contexts/useProject'

type NavGroup = {
  title: string
  items: Array<{ path: string; label: string }>
}

type Workspace = 'agent' | 'developer'

interface SidebarProps {
  workspace?: Workspace
}

const AGENT_GROUPS = [
  {
    title: 'Agent Workspace',
    keys: ['performance', 'gpsCapture'] as const,
  },
  {
    title: 'Campaigns',
    keys: ['marketing', 'advisory', 'integrations'] as const,
  },
]

const DEVELOPER_GROUPS = [
  {
    title: 'Singapore Developer Workspace',
    keys: ['projects', 'dealCalculator', 'siteAcquisition'] as const,
  },
  {
    title: 'Execution',
    keys: [
      'dueDiligence',
      'assetFeasibility',
      'financialControl',
      'phaseManagement',
      'teamCoordination',
      'regulatoryNavigation',
      'evidence',
    ] as const,
  },
]

export function Sidebar({ workspace = 'developer' }: SidebarProps) {
  const path = useRouterPath()
  const theme = useTheme()
  const { currentProject } = useProject()

  const navSource =
    workspace === 'agent' ? AGENT_NAV_ITEMS : DEVELOPER_NAV_ITEMS
  const groupConfig = workspace === 'agent' ? AGENT_GROUPS : DEVELOPER_GROUPS
  const homePath = workspace === 'agent' ? '/agents' : '/developers'
  const homeLabel =
    workspace === 'agent' ? 'Agent Dashboard' : 'Developer Dashboard'
  const navGroups: NavGroup[] = groupConfig.map((group) => ({
    title: group.title,
    items: group.keys
      .map((key) => navSource.find((item) => item.key === key))
      .filter((item): item is NonNullable<typeof item> => Boolean(item))
      .filter((item) => !item.comingSoon)
      .map((item) => ({
        path: resolveNavPath(item, currentProject?.id),
        label: item.label,
      })),
  }))

  return (
    <Box
      component="aside"
      sx={{
        width: '280px',
        height: '100vh',
        flexShrink: 0,
        borderRight: 1,
        borderColor: 'divider',
        bgcolor: 'background.default',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
      }}
    >
      {/* Brand */}
      <Box sx={{ p: 4, mb: 1 }}>
        <Typography
          variant="h6"
          sx={{
            color: 'primary.main',
            fontWeight: 'bold',
            letterSpacing: '0.05em',
          }}
        >
          OPTIMAL BUILD
        </Typography>
        <Typography
          variant="caption"
          sx={{
            color: 'text.secondary',
            fontFamily: 'var(--ob-font-family-mono)',
          }}
        >
          v2.0 Command Center
        </Typography>
      </Box>

      {/* Nav */}
      <Box component="nav" sx={{ flexGrow: 1, px: 2, pb: 4 }}>
        <Box sx={{ mb: 2 }}>
          <Button
            component={Link}
            to={homePath}
            fullWidth
            sx={{
              justifyContent: 'flex-start',
              color: path === homePath ? 'primary.main' : 'text.secondary',
              px: 2,
              mb: 2,
            }}
          >
            {homeLabel}
          </Button>
        </Box>

        <Stack spacing={3}>
          {navGroups.map((group) => (
            <Box key={group.title}>
              <Typography
                variant="caption"
                sx={{
                  px: 2,
                  mb: 1,
                  display: 'block',
                  fontWeight: 700,
                  color: 'text.disabled',
                  textTransform: 'uppercase',
                  fontSize: '0.7rem',
                  letterSpacing: '0.1em',
                }}
              >
                {group.title}
              </Typography>
              <Stack spacing={0.5}>
                {group.items.map((item) => {
                  const isActive = path.startsWith(item.path)
                  return (
                    <Button
                      key={item.path}
                      component={Link}
                      to={item.path}
                      variant="text"
                      aria-current={isActive ? 'page' : undefined}
                      sx={{
                        justifyContent: 'flex-start',
                        color: isActive ? 'primary.main' : 'text.secondary',
                        bgcolor: isActive
                          ? alpha(theme.palette.primary.main, 0.12)
                          : 'transparent',
                        border: '1px solid',
                        borderColor: isActive
                          ? alpha(theme.palette.primary.main, 0.36)
                          : 'transparent',
                        borderRadius: 'var(--ob-radius-sm)',
                        px: 2,
                        py: 1.25,
                        textAlign: 'left',
                        textTransform: 'none',
                        fontWeight: isActive ? 600 : 400,
                        fontSize: '0.85rem',
                        transition: 'background 0.2s ease, color 0.2s ease',
                        '&:hover': {
                          bgcolor: isActive
                            ? alpha(theme.palette.primary.main, 0.15)
                            : alpha(theme.palette.text.primary, 0.06),
                          color: isActive ? 'primary.main' : 'text.primary',
                        },
                      }}
                    >
                      {item.label}
                    </Button>
                  )
                })}
              </Stack>
            </Box>
          ))}
        </Stack>
      </Box>
    </Box>
  )
}
