import { Box, Typography, Stack, Button, useTheme, alpha } from '@mui/material'
import { useTranslation } from '../../i18n'
import { useRouterPath, Link } from '../../router'

type NavGroup = {
  title: string
  items: Array<{ path: string; label: string }>
}

export function YosaiSidebar() {
  const { t } = useTranslation()
  const path = useRouterPath()
  const theme = useTheme()

  const navGroups: NavGroup[] = [
    {
      title: 'Build',
      items: [
        { path: '/cad/upload', label: t('nav.upload') },
        { path: '/cad/detection', label: t('nav.detection') },
        { path: '/cad/pipelines', label: t('nav.pipelines') },
      ],
    },
    {
      title: 'Analyze',
      items: [
        { path: '/visualizations/intelligence', label: t('nav.intelligence') },
        { path: '/feasibility', label: t('nav.feasibility') },
        { path: '/finance', label: t('nav.finance') },
      ],
    },
    {
      title: 'Manage',
      items: [
        { path: '/agents/site-capture', label: t('nav.agentCapture') },
        { path: '/app/phase-management', label: 'Phase Management' },
      ],
    },
  ]

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
          sx={{ color: 'text.secondary', fontFamily: 'monospace' }}
        >
          v2.0 Command Center
        </Typography>
      </Box>

      {/* Nav */}
      <Box component="nav" sx={{ flexGrow: 1, px: 2, pb: 4 }}>
        <Box sx={{ mb: 2 }}>
          <Button
            component={Link}
            to="/"
            fullWidth
            sx={{
              justifyContent: 'flex-start',
              color: path === '/' ? 'primary.main' : 'text.secondary',
              px: 2,
              mb: 2,
            }}
          >
            {t('nav.home')}
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
                      sx={{
                        justifyContent: 'flex-start',
                        color: isActive ? 'primary.main' : 'text.secondary',
                        bgcolor: isActive
                          ? alpha(theme.palette.primary.main, 0.12)
                          : 'transparent',
                        borderLeft: 4,
                        borderColor: isActive ? 'primary.main' : 'transparent',
                        borderRadius: '0 8px 8px 0',
                        px: 3,
                        py: 1.25,
                        textAlign: 'left',
                        textTransform: 'none',
                        fontWeight: isActive ? 600 : 400,
                        fontSize: isActive ? '0.875rem' : '0.85rem',
                        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                        position: 'relative',
                        overflow: 'hidden',
                        '&::before': isActive
                          ? {
                              content: '""',
                              position: 'absolute',
                              left: 0,
                              top: '50%',
                              transform: 'translateY(-50%)',
                              width: '4px',
                              height: '70%',
                              borderRadius: '0 4px 4px 0',
                              bgcolor: 'primary.main',
                              boxShadow: `0 0 12px 2px ${alpha(theme.palette.primary.main, 0.6)}`,
                            }
                          : {},
                        '&::after': isActive
                          ? {
                              content: '""',
                              position: 'absolute',
                              right: '8px',
                              top: '50%',
                              transform: 'translateY(-50%)',
                              width: '6px',
                              height: '6px',
                              borderRadius: '50%',
                              bgcolor: 'primary.main',
                              boxShadow: `0 0 8px 2px ${alpha(theme.palette.primary.main, 0.5)}`,
                              animation: 'pulse 2s ease-in-out infinite',
                            }
                          : {},
                        '@keyframes pulse': {
                          '0%, 100%': {
                            opacity: 1,
                            transform: 'translateY(-50%) scale(1)',
                          },
                          '50%': {
                            opacity: 0.6,
                            transform: 'translateY(-50%) scale(0.8)',
                          },
                        },
                        '&:hover': {
                          bgcolor: isActive
                            ? alpha(theme.palette.primary.main, 0.15)
                            : alpha(theme.palette.text.primary, 0.06),
                          color: isActive ? 'primary.main' : 'text.primary',
                          transform: 'translateX(4px)',
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
