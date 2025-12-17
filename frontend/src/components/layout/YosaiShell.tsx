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
  const { inBaseLayout, topOffset } = useBaseLayoutContext()

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
        gap: shouldHideSidebar ? 0 : 'var(--ob-space-200)', // Consistent gap between sidebar and content
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
        {/* Content (scroll container) */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            padding: 'var(--ob-space-100)',
            overflow: 'auto',
            scrollbarGutter: 'stable',
          }}
        >
          {/* Page Header (scrolls with content) */}
          {!hideHeader && (
            <Box
              component="header"
              sx={{
                py: 'var(--ob-space-200)',
                px: 'var(--ob-space-300)',
                borderBottom: 1,
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: 'var(--ob-space-150)',
                bgcolor: alpha(theme.palette.background.default, 0.8),
                backdropFilter: 'blur(var(--ob-blur-md))',
                // When the top ribbon is unpinned, it becomes an overlay; give the
                // content a small breathing room so the header doesn't feel cramped.
                mt: inBaseLayout && topOffset === 0 ? 'var(--ob-space-075)' : 0,
                mb: 'var(--ob-space-150)',
                borderRadius: 'var(--ob-radius-sm)',
                animation: 'slideDownFade 0.4s ease-out forwards',
                '@keyframes slideDownFade': {
                  from: {
                    opacity: 0,
                    transform: 'translateY(calc(-1 * var(--ob-space-050)))',
                  },
                  to: { opacity: 1, transform: 'translateY(0)' },
                },
              }}
            >
              <Box sx={{ minWidth: 0 }}>
                <Typography variant="h2" sx={{ color: 'text.primary' }}>
                  {title}
                </Typography>
                {subtitle && (
                  <Typography
                    variant="body2"
                    sx={{ color: 'text.secondary', mt: 'var(--ob-space-050)' }}
                  >
                    {subtitle}
                  </Typography>
                )}
              </Box>
              <Stack
                direction="row"
                spacing="var(--ob-space-200)"
                alignItems="center"
                sx={{ flexShrink: 0 }}
              >
                {!inBaseLayout && <HeaderUtilityCluster />}
                {actions}
              </Stack>
            </Box>
          )}

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
