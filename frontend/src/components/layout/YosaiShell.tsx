import { ReactNode } from 'react'
import { Box, Typography, Stack, useTheme, alpha } from '@mui/material'
import { YosaiSidebar } from './YosaiSidebar'
import { useBaseLayoutContext } from '../../app/layout/BaseLayoutContext'
import { HeaderUtilityCluster } from './HeaderUtilityCluster'

export interface AppShellProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
  hideSidebar?: boolean
  hideHeader?: boolean
}

/**
 * @deprecated Use AppShell from './AppShell' instead
 */
export type YosaiShellProps = AppShellProps

/**
 * AppShell
 * Main application layout with sidebar navigation and header.
 * Supports dark and light modes via the theme system.
 */
export function AppShell({
  title,
  subtitle,
  actions,
  children,
  hideSidebar,
  hideHeader = false,
}: AppShellProps) {
  const theme = useTheme()
  const { inBaseLayout } = useBaseLayoutContext()

  // Default to hiding sidebar if inside BaseLayout, unless explicitly forced.
  const shouldHideSidebar =
    hideSidebar !== undefined ? hideSidebar : inBaseLayout

  return (
    <Box
      sx={{
        display: 'flex',
        minHeight: '100vh',
        bgcolor: 'background.default',
        color: 'text.primary',
        gap: shouldHideSidebar ? 0 : 2, // Consistent gap between sidebar and content
      }}
    >
      {/* "The Wall" - Sidebar */}
      {!shouldHideSidebar && <YosaiSidebar />}

      {/* Main Content Area */}
      <Box
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
        }}
      >
        {/* Header */}
        {!hideHeader && (
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
              <Typography variant="h2" sx={{ color: 'text.primary' }}>
                {title}
              </Typography>
              {subtitle && (
                <Typography
                  variant="body2"
                  sx={{ color: 'text.secondary', mt: 0.5 }}
                >
                  {subtitle}
                </Typography>
              )}
            </Box>
            <Stack direction="row" spacing={2} alignItems="center">
              <HeaderUtilityCluster />
              {actions}
            </Stack>
          </Box>
        )}

        {/* Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            padding: 'var(--ob-space-100)', // 16px - canonical layout padding (matches nav button spacing)
            overflow: 'auto',
            scrollbarGutter: 'stable',
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  )
}

/**
 * @deprecated Use AppShell instead
 */
export const YosaiShell = AppShell
