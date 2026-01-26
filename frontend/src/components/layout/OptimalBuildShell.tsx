import { ReactNode } from 'react'
import { Box, Typography, Stack } from '@mui/material'
import { OptimalBuildSidebar } from './OptimalBuildSidebar'
import { useBaseLayoutContext } from '../../app/layout/useBaseLayout'
import { HeaderUtilityCluster } from './HeaderUtilityCluster'
import { useRouterController } from '../../router'

export interface AppShellProps {
  title?: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
  hideSidebar?: boolean
  hideHeader?: boolean
}

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
  const { inBaseLayout, topOffset } = useBaseLayoutContext()
  const { path } = useRouterController()

  // Default to hiding sidebar if inside BaseLayout, unless explicitly forced.
  const shouldHideSidebar =
    hideSidebar !== undefined ? hideSidebar : inBaseLayout

  return (
    <Box
      sx={{
        display: 'flex',
        // When embedded in BaseLayout (new shell), avoid forcing a second 100vh
        // layout which can cause the window to scroll (breaking sticky behavior).
        minHeight: inBaseLayout ? 0 : '100vh',
        flexGrow: 1,
        bgcolor: 'background.default',
        color: 'text.primary',
        gap: shouldHideSidebar ? 0 : 'var(--ob-space-200)', // Consistent gap between sidebar and content
      }}
    >
      {/* "The Wall" - Sidebar */}
      {!shouldHideSidebar && <OptimalBuildSidebar />}

      {/* Main Content Area */}
      <Box
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          minHeight: 0,
        }}
      >
        {/* Content (scroll container) - TIGHT layout for command-center density */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            px: 'var(--ob-space-200)', // 16px horizontal - tighter than before
            pt: 'var(--ob-space-100)', // 8px top - minimal breathing room
            pb: 'var(--ob-space-400)', // 32px bottom - reduced from 48px
            overflow: 'auto',
            scrollbarGutter: 'stable',
            minHeight: 0,
          }}
        >
          {/* Page Header - Direct on Grid (Depth 0, no glass card)
              AI Studio Protocol: Headers sit directly on the background grid
              TIGHT LAYOUT: Reduced padding for information density */}
          {!hideHeader && (
            <Box
              component="header"
              key={path}
              className="ob-page-header"
              sx={{
                py: 'var(--ob-space-100)', // 8px vertical - was 16px
                px: '0', // No extra horizontal padding
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: 'var(--ob-space-150)',
                // When top ribbon is unpinned, minimal breathing room
                mt: inBaseLayout && topOffset === 0 ? 'var(--ob-space-050)' : 0,
                mb: 'var(--ob-space-150)', // 12px - tighter spacing to content
                animation:
                  'ob-slide-down-fade var(--ob-motion-header-duration) var(--ob-motion-header-ease) both',
                '@media (prefers-reduced-motion: reduce)': {
                  animation: 'none',
                },
              }}
            >
              <Box sx={{ minWidth: 0 }}>
                {title ? (
                  <Typography
                    variant="h2"
                    className="ob-page-header__title"
                    sx={{ color: 'text.primary' }}
                  >
                    {title}
                  </Typography>
                ) : null}
                {subtitle && (
                  <Typography
                    variant="body2"
                    className="ob-page-header__subtitle"
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

export const OptimalBuildShell = AppShell
