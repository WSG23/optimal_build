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
import { useRouterController } from '../../router'
import logoImage from '../../assets/logo_v2.png'
import type { NavItemKey } from '../../app/navigation'

const DRAWER_WIDTH = 280
const TOOLBAR_HEIGHT = 72

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
  hideSidebar = false,
  actions,
}: AppShellProps) {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [mobileOpen, setMobileOpen] = useState(false)
  const { path, navigate } = useRouterController()

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
        {/* Header */}
        <AppBar
          position="fixed"
          elevation={0}
          sx={{
            zIndex: (theme) => theme.zIndex.drawer + 1,
            bgcolor: 'background.paper',
            borderBottom: `1px solid ${theme.palette.divider}`,
            backdropFilter: 'blur(20px)',
            background: `linear-gradient(to right, ${alpha(theme.palette.background.paper, 0.9)}, ${alpha(
              theme.palette.background.paper,
              0.8,
            )})`,
          }}
        >
          <Toolbar sx={{ height: TOOLBAR_HEIGHT, px: { xs: 2, md: 4 } }}>
            {!hideSidebar && (
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
                sx={{ mr: 2, display: { md: 'none' }, color: 'text.primary' }}
              >
                <MenuIcon />
              </IconButton>
            )}

            {/* Logo */}
            <Box
              sx={{ display: 'flex', alignItems: 'center', flexGrow: 0, mr: 8 }}
            >
              <img
                src={logoImage}
                alt="Optimal Build"
                style={{ height: '32px' }}
              />
            </Box>

            {/* Page Title in Header (Optional, if we want it there) */}
            {/*
            <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                <Typography variant="subtitle1" sx={{ color: 'text.primary', fontWeight: 600 }}>
                    {title}
                </Typography>
            </Box>
            */}

            <Box sx={{ flexGrow: 1 }} />

            {/* Utility Cluster */}
            <HeaderUtilityCluster />
          </Toolbar>
        </AppBar>

        {/* Sidebar Navigation */}
        {!hideSidebar && (
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
                  borderRight: `1px solid ${theme.palette.divider}`,
                },
              }}
            >
              <Toolbar sx={{ height: TOOLBAR_HEIGHT }} />
              <Box sx={{ overflow: 'auto', p: 3 }}>
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
                  borderRight: `1px solid ${theme.palette.divider}`,
                  height: '100vh',
                },
              }}
              open
            >
              <Toolbar sx={{ height: TOOLBAR_HEIGHT }} />
              <Box
                sx={{
                  overflow: 'auto',
                  p: 3,
                  height: `calc(100vh - ${TOOLBAR_HEIGHT}px)`,
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
            width: { md: `calc(100% - ${hideSidebar ? 0 : DRAWER_WIDTH}px)` },
            mt: `${TOOLBAR_HEIGHT}px`,
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Page Header (recreating what seemed to be there in the 'residue') */}
          {(title || description || actions) && (
            <Box
              component="header"
              sx={{
                py: 3,
                px: 4,
                borderBottom: 1,
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                bgcolor: alpha(theme.palette.background.default, 0.8),
                backdropFilter: 'blur(12px)',
                position: 'sticky',
                top: 0,
                zIndex: 10,
              }}
            >
              <Box>
                {title && (
                  <Typography
                    variant="h4"
                    sx={{ color: 'text.primary', fontWeight: 'bold' }}
                  >
                    {title}
                  </Typography>
                )}
                {description && (
                  <Typography
                    variant="body1"
                    sx={{ color: 'text.secondary', mt: 0.5, maxWidth: '800px' }}
                  >
                    {description}
                  </Typography>
                )}
              </Box>
              {actions && (
                <Stack direction="row" spacing={2} alignItems="center">
                  {actions}
                </Stack>
              )}
            </Box>
          )}

          <Box sx={{ p: 4, flexGrow: 1 }}>{children}</Box>
        </Box>
      </Box>
    </DeveloperProvider>
  )
}
