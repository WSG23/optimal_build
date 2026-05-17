import { ReactNode, Suspense, lazy } from 'react'
import { Box, Typography, Stack } from '@mui/material'
import { ErrorBoundary } from '../ErrorBoundary'
import { NavErrorFallback } from './NavErrorFallback'
import { useBaseLayoutContext } from '../../app/layout/useBaseLayout'
import { useRouterController } from '../../router'
import { usePageViewTelemetry } from '../../hooks/usePageViewTelemetry'
import { ProjectBreadcrumbs } from './Breadcrumbs'

const Sidebar = lazy(async () => {
  const module = await import('./Sidebar')
  return { default: module.Sidebar }
})

const TopUtilityMenu = lazy(async () => {
  const module = await import('./TopUtilityMenu')
  return { default: module.TopUtilityMenu }
})

export interface AppShellProps {
  title?: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
  hideSidebar?: boolean
  hideHeader?: boolean
  workspace?: 'agent' | 'developer'
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
  workspace = 'developer',
}: AppShellProps) {
  const { inBaseLayout, topOffset } = useBaseLayoutContext()
  const { path } = useRouterController()
  usePageViewTelemetry()

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
        gap: shouldHideSidebar ? 0 : 'var(--ob-space-100)', // Tight gap between sidebar and content
      }}
    >
      {/* "The Wall" - Sidebar */}
      {!shouldHideSidebar && (
        <ErrorBoundary fallback={<NavErrorFallback />}>
          <Suspense fallback={null}>
            <Sidebar workspace={workspace} />
          </Suspense>
        </ErrorBoundary>
      )}

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
          id="main-content"
          component="main"
          sx={{
            flexGrow: 1,
            px: 'var(--ob-space-150)', // 24px horizontal - dense terminal spacing
            pt: 'var(--ob-space-075)', // 12px top - minimal breathing room
            pb: 'var(--ob-space-250)', // 40px bottom - comfortable scroll end
            overflow: 'auto',
            scrollbarGutter: 'stable',
            minHeight: 0,
            animation: 'ob-fade-in 300ms ease both',
            '@media (prefers-reduced-motion: reduce)': {
              animation: 'none',
            },
            // Mobile: tighten padding for small screens
            '@media (max-width: 600px)': {
              px: 'var(--ob-space-075)', // 12px horizontal on mobile
              pt: 'var(--ob-space-050)', // 8px top
              pb: 'var(--ob-space-150)', // 24px bottom
            },
          }}
        >
          {/* Project Breadcrumbs - shown only on /projects/:id/* routes */}
          <ProjectBreadcrumbs />

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
                px: 0, // No extra horizontal padding
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: 'var(--ob-space-150)',
                // When top ribbon is unpinned, minimal breathing room
                mt: inBaseLayout && topOffset === 0 ? 'var(--ob-space-050)' : 0,
                mb: 'var(--ob-space-100)', // 16px - tight spacing to content
                animation:
                  'ob-slide-down-fade var(--ob-motion-header-duration) var(--ob-motion-header-ease) both',
                '@media (prefers-reduced-motion: reduce)': {
                  animation: 'none',
                },
                // Mobile: stack title and actions vertically
                '@media (max-width: 600px)': {
                  flexDirection: 'column',
                  alignItems: 'stretch',
                  gap: 'var(--ob-space-075)',
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
                spacing="var(--ob-space-100)"
                alignItems="center"
                sx={{ flexShrink: 0 }}
              >
                {!inBaseLayout && (
                  <ErrorBoundary fallback={<NavErrorFallback />}>
                    <Suspense fallback={null}>
                      <TopUtilityMenu />
                    </Suspense>
                  </ErrorBoundary>
                )}
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
