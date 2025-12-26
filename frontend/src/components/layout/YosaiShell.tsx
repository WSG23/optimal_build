import { ReactNode } from 'react'
import { Box, Typography, Stack } from '@mui/material'
import { YosaiSidebar } from './YosaiSidebar'
import { useBaseLayoutContext } from '../../app/layout/BaseLayoutContext'
import { HeaderUtilityCluster } from './HeaderUtilityCluster'
import { useRouterController } from '../../router'

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
      {!shouldHideSidebar && <YosaiSidebar />}

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
        {/* Content (scroll container) */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            padding: 'var(--ob-space-100)',
            overflow: 'auto',
            scrollbarGutter: 'stable',
            minHeight: 0,
          }}
        >
          {/* Page Header (scrolls with content) */}
          {!hideHeader && (
            <Box
              component="header"
              key={path}
              className="ob-glass ob-card-accent"
              sx={{
                py: 'var(--ob-space-200)',
                px: 'var(--ob-space-300)',
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: 'var(--ob-space-150)',
                // When the top ribbon is unpinned, it becomes an overlay; give the
                // content a small breathing room so the header doesn't feel cramped.
                mt: inBaseLayout && topOffset === 0 ? 'var(--ob-space-075)' : 0,
                mb: 'var(--ob-space-150)',
                borderRadius: 'var(--ob-radius-sm)',
                animation:
                  'ob-slide-down-fade var(--ob-motion-header-duration) var(--ob-motion-header-ease) both',
                '@media (prefers-reduced-motion: reduce)': {
                  animation: 'none',
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
