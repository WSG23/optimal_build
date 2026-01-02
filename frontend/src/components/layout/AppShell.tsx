import { ReactNode, useState } from 'react'
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  Toolbar,
  Typography,
  useTheme,
  alpha,
  useMediaQuery,
  Stack,
} from '@mui/material'
import { Menu as MenuIcon } from '@mui/icons-material'
import { AppNavigation } from '../../app/components/AppNavigation'
import { HeaderUtilityCluster } from './HeaderUtilityCluster'
import { DeveloperProvider } from '../../contexts/DeveloperContext'
import { useBaseLayoutContext } from '../../app/layout/useBaseLayout'
import { useRouterController } from '../../router'
import logoImage from '../../assets/logo_v2.png'
import type { NavItemKey } from '../../app/navigation'

const DRAWER_WIDTH = 'var(--ob-size-sidebar-width)'
const TOOLBAR_HEIGHT = 'calc(var(--ob-space-400) + var(--ob-space-050))'

interface AppShellProps {
  children: ReactNode
  activeItem?: NavItemKey
  title?: string
  description?: string
  hideSidebar?: boolean
  actions?: ReactNode
}

export function AppShell({
  children,
  activeItem = 'performance',
  title,
  description,
  hideSidebar,
  actions,
}: AppShellProps) {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [mobileOpen, setMobileOpen] = useState(false)
  const { path, navigate } = useRouterController()
  const { inBaseLayout, topOffset } = useBaseLayoutContext()

  // Default to hiding the legacy left sidebar if we're already inside the new BaseLayout.
  const resolvedHideSidebar =
    hideSidebar !== undefined ? hideSidebar : inBaseLayout
  const showLegacyAppBar = !inBaseLayout
  const stickyTop = inBaseLayout ? topOffset : TOOLBAR_HEIGHT

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const handleNavigate = (newPath: string) => {
    navigate(newPath)
    if (isMobile) {
      setMobileOpen(false)
    }
  }

  return (
    <DeveloperProvider>
      <Box
        sx={{
          display: 'flex',
          minHeight: '100vh',
          bgcolor: 'background.default',
        }}
      >
        {/* Legacy Header (hidden inside BaseLayout to avoid double top bars) */}
        {showLegacyAppBar && (
          <AppBar
            position="fixed"
            elevation={0}
            sx={{
              zIndex: (theme) => theme.zIndex.drawer + 1,
              bgcolor: 'background.paper',
              borderBottom: 1,
              borderColor: 'divider',
              backdropFilter: 'blur(var(--ob-blur-lg))',
              background: `linear-gradient(to right, ${alpha(theme.palette.background.paper, 0.9)}, ${alpha(
                theme.palette.background.paper,
                0.8,
              )})`,
            }}
          >
            <Toolbar
              sx={{
                height: TOOLBAR_HEIGHT,
                px: {
                  xs: 'var(--ob-space-100)',
                  md: 'var(--ob-space-200)',
                },
              }}
            >
              {!resolvedHideSidebar && (
                <IconButton
                  color="inherit"
                  aria-label="open drawer"
                  edge="start"
                  onClick={handleDrawerToggle}
                  sx={{
                    mr: 'var(--ob-space-100)',
                    display: { md: 'none' },
                    color: 'text.primary',
                  }}
                >
                  <MenuIcon />
                </IconButton>
              )}

              {/* Logo */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  flexGrow: 0,
                  mr: 'var(--ob-space-400)',
                }}
              >
                <Box
                  component="img"
                  src={logoImage}
                  alt="Optimal Build"
                  sx={{
                    display: 'block',
                    height: 'var(--ob-size-icon-md)',
                    width: 'auto',
                  }}
                />
              </Box>

              <Box sx={{ flexGrow: 1 }} />

              {/* Utility Cluster */}
              <HeaderUtilityCluster />
            </Toolbar>
          </AppBar>
        )}

        {/* Sidebar Navigation */}
        {!resolvedHideSidebar && (
          <Box
            component="nav"
            sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
            aria-label="mailbox folders"
          >
            {/* Mobile Drawer */}
            <Drawer
              variant="temporary"
              open={mobileOpen}
              onClose={handleDrawerToggle}
              ModalProps={{
                keepMounted: true, // Better open performance on mobile.
              }}
              sx={{
                display: { xs: 'block', md: 'none' },
                '& .MuiDrawer-paper': {
                  boxSizing: 'border-box',
                  width: DRAWER_WIDTH,
                  bgcolor: 'background.paper',
                  borderRight: 1,
                  borderColor: 'divider',
                },
              }}
            >
              {showLegacyAppBar && <Toolbar sx={{ height: TOOLBAR_HEIGHT }} />}
              <Box sx={{ overflow: 'auto', p: 'var(--ob-space-150)' }}>
                <AppNavigation
                  activeItem={activeItem}
                  onNavigate={handleNavigate}
                  currentPath={path}
                />
              </Box>
            </Drawer>

            {/* Desktop Drawer */}
            <Drawer
              variant="permanent"
              sx={{
                display: { xs: 'none', md: 'block' },
                '& .MuiDrawer-paper': {
                  boxSizing: 'border-box',
                  width: DRAWER_WIDTH,
                  bgcolor: 'background.paper',
                  borderRight: 1,
                  borderColor: 'divider',
                  height: '100vh',
                },
              }}
              open
            >
              {showLegacyAppBar && <Toolbar sx={{ height: TOOLBAR_HEIGHT }} />}
              <Box
                sx={{
                  overflow: 'auto',
                  p: 'var(--ob-space-150)',
                  height: showLegacyAppBar
                    ? `calc(100vh - ${TOOLBAR_HEIGHT})`
                    : '100vh',
                }}
              >
                <AppNavigation
                  activeItem={activeItem}
                  onNavigate={handleNavigate}
                  currentPath={path}
                />
              </Box>
            </Drawer>
          </Box>
        )}

        {/* Main Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            // p: { xs: 2, md: 4 }, // Removing padding here to let inner components handle it or the sub-header
            width: {
              md: resolvedHideSidebar ? '100%' : `calc(100% - ${DRAWER_WIDTH})`,
            },
            mt: showLegacyAppBar ? TOOLBAR_HEIGHT : 0,
            minHeight: '100vh',
            overflowY: 'auto',
            overflowX: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            // Ensure content is painted above fixed background elements
            position: 'relative',
            zIndex: 1,
          }}
        >
          {/* Page Header (recreating what seemed to be there in the 'residue') */}
          {(title || description || actions) && (
            <Box
              component="header"
              key={path}
              sx={{
                py: 'var(--ob-space-150)',
                px: 'var(--ob-space-200)',
                borderBottom: 1,
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                bgcolor: alpha(theme.palette.background.default, 0.8),
                backdropFilter: 'blur(var(--ob-blur-md))',
                position: 'sticky',
                top: stickyTop,
                zIndex: 'var(--ob-z-sticky)',
                animation:
                  'ob-slide-down-fade var(--ob-motion-header-duration) var(--ob-motion-header-ease) both',
                '@media (prefers-reduced-motion: reduce)': {
                  animation: 'none',
                },
              }}
            >
              <Box>
                {title && (
                  <Typography
                    variant="h4"
                    sx={{
                      color: 'text.primary',
                      fontWeight: 'var(--ob-font-weight-bold)',
                    }}
                  >
                    {title}
                  </Typography>
                )}
                {description && (
                  <Typography
                    variant="body1"
                    sx={{
                      color: 'text.secondary',
                      mt: 'var(--ob-space-025)',
                      maxWidth: 'var(--ob-max-width-content)',
                    }}
                  >
                    {description}
                  </Typography>
                )}
              </Box>
              {actions && (
                <Stack
                  direction="row"
                  spacing="var(--ob-space-100)"
                  alignItems="center"
                >
                  {actions}
                </Stack>
              )}
            </Box>
          )}

          <Box sx={{ p: 'var(--ob-space-200)', flexGrow: 1 }}>{children}</Box>
        </Box>
      </Box>
    </DeveloperProvider>
  )
}
