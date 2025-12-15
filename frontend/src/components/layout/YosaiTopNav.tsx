import { Box, Button, Stack, Typography, alpha, useTheme } from '@mui/material'
import { Link, useRouterPath } from '../../router'
import { useTranslation } from '../../i18n'

type NavGroup = {
  title: string
  items: Array<{ path: string; label: string }>
}

interface YosaiTopNavProps {
  height: number
}

export function YosaiTopNav({ height }: YosaiTopNavProps) {
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

  const renderItem = (item: { path: string; label: string }) => {
    const isActive = path === item.path || path.startsWith(`${item.path}/`)
    return (
      <Button
        key={item.path}
        component={Link}
        to={item.path}
        variant="text"
        sx={{
          justifyContent: 'center',
          color: isActive ? 'primary.main' : 'text.secondary',
          bgcolor: isActive
            ? alpha(theme.palette.primary.main, 0.12)
            : 'transparent',
          borderRadius: 'var(--ob-radius-xs)',
          px: 'var(--ob-space-075)',
          py: 'var(--ob-space-050)',
          textTransform: 'none',
          fontWeight: isActive ? 600 : 500,
          fontSize: 'var(--ob-font-size-sm)',
          whiteSpace: 'nowrap',
          border: `1px solid ${
            isActive ? alpha(theme.palette.primary.main, 0.25) : 'transparent'
          }`,
          '&:hover': {
            bgcolor: isActive
              ? alpha(theme.palette.primary.main, 0.16)
              : alpha(theme.palette.text.primary, 0.06),
            color: isActive ? 'primary.main' : 'text.primary',
            transform: 'translateY(-1px)',
          },
        }}
      >
        {item.label}
      </Button>
    )
  }

  return (
    <Box
      component="nav"
      aria-label="Primary"
      sx={{
        position: 'sticky',
        top: 0,
        zIndex: 1200,
        height,
        minHeight: height,
        borderBottom: 1,
        borderColor: 'divider',
        bgcolor: alpha(theme.palette.background.default, 0.85),
        backdropFilter: 'blur(var(--ob-blur-md))',
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        sx={{
          height: '100%',
          px: 'var(--ob-space-200)',
          gap: 'var(--ob-space-150)',
        }}
      >
        <Button
          component={Link}
          to="/"
          variant="text"
          sx={{
            px: 'var(--ob-space-050)',
            py: 'var(--ob-space-050)',
            borderRadius: 'var(--ob-radius-xs)',
            textTransform: 'none',
            whiteSpace: 'nowrap',
            minWidth: 0,
          }}
        >
          <Stack direction="row" alignItems="baseline" spacing={1}>
            <Typography
              component="span"
              sx={{
                color: 'primary.main',
                fontWeight: 700,
                letterSpacing: 'var(--ob-letter-spacing-wider)',
                fontSize: 'var(--ob-font-size-sm)',
              }}
            >
              OPTIMAL BUILD
            </Typography>
            <Typography
              component="span"
              sx={{
                color: 'text.secondary',
                fontFamily: 'var(--ob-font-family-mono)',
                fontSize: 'var(--ob-font-size-2xs)',
                letterSpacing: 'var(--ob-letter-spacing-wider)',
              }}
            >
              v2
            </Typography>
          </Stack>
        </Button>

        <Stack
          direction="row"
          alignItems="center"
          sx={{
            flex: 1,
            minWidth: 0,
            gap: 'var(--ob-space-150)',
            overflowX: 'auto',
            scrollbarWidth: 'none',
            '&::-webkit-scrollbar': { display: 'none' },
          }}
        >
          {navGroups.map((group) => (
            <Stack
              key={group.title}
              direction="row"
              alignItems="center"
              sx={{ gap: 'var(--ob-space-050)', flexShrink: 0 }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: 'text.disabled',
                  textTransform: 'uppercase',
                  fontWeight: 700,
                  letterSpacing: 'var(--ob-letter-spacing-caps)',
                  fontSize: 'var(--ob-font-size-2xs)',
                  display: { xs: 'none', lg: 'block' },
                }}
              >
                {group.title}
              </Typography>
              {group.items.map(renderItem)}
            </Stack>
          ))}
        </Stack>
      </Stack>
    </Box>
  )
}
