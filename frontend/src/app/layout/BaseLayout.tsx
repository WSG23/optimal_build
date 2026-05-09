import { lazy, ReactNode, Suspense, useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { BaseLayoutProvider } from './BaseLayoutContext'
import { TopNav } from '../../components/layout/TopNav'
import { ErrorBoundary } from '../../components/ErrorBoundary'
import { NavErrorFallback } from '../../components/layout/NavErrorFallback'
import { OfflineBanner } from '../../components/layout/OfflineBanner'
import { SessionExpiredDialog } from '../../components/layout/SessionExpiredDialog'
import { useSessionMonitor } from '../../hooks/useSessionMonitor'

const CommandPalette = lazy(() =>
  import('../../components/CommandPalette').then((m) => ({
    default: m.CommandPalette,
  })),
)

const ShortcutOverlay = lazy(() =>
  import('../../components/ShortcutOverlay').then((m) => ({
    default: m.ShortcutOverlay,
  })),
)

export function BaseLayout({ children }: { children: ReactNode }) {
  const { isSessionExpired, dismissExpiry } = useSessionMonitor()
  const [isNavPinned, setIsNavPinned] = useState(() => {
    if (typeof window === 'undefined') return true
    const value = window.localStorage.getItem('ob_top_nav_pinned')
    return value !== 'false'
  })

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem('ob_top_nav_pinned', String(isNavPinned))
  }, [isNavPinned])

  const topOffset = isNavPinned ? 'var(--ob-space-300)' : '0px'

  return (
    <BaseLayoutProvider value={{ inBaseLayout: true, topOffset }}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100dvh',
          // Fallback for browsers without dvh support
          '@supports not (height: 100dvh)': {
            height: '100vh',
          },
          overflow: 'hidden',
          bgcolor: 'background.default',
          color: 'text.primary',
          position: 'relative',
        }}
      >
        <Box
          component="a"
          href="#main-content"
          sx={{
            position: 'absolute',
            left: '-9999px',
            top: 'var(--ob-space-050)',
            zIndex: 9999,
            '&:focus': {
              position: 'fixed',
              left: 'var(--ob-space-200)',
              top: 'var(--ob-space-050)',
              px: 'var(--ob-space-150)',
              py: 'var(--ob-space-075)',
              bgcolor: 'background.paper',
              border: '2px solid var(--ob-color-brand-primary)',
              borderRadius: 'var(--ob-radius-xs)',
              color: 'var(--ob-color-brand-primary)',
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 'var(--ob-font-weight-bold)',
              textDecoration: 'none',
            },
          }}
        >
          Skip to main content
        </Box>
        <ErrorBoundary fallback={<NavErrorFallback />}>
          <Suspense fallback={null}>
            <CommandPalette />
            <ShortcutOverlay />
          </Suspense>
        </ErrorBoundary>
        <TopNav
          isPinned={isNavPinned}
          onTogglePinned={() => setIsNavPinned((prev) => !prev)}
        />
        <OfflineBanner />
        <SessionExpiredDialog
          open={isSessionExpired}
          onDismiss={dismissExpiry}
        />
        <Box
          sx={{
            flexGrow: 1,
            minWidth: 0,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            // Allow child components (AppShell, Shell) to handle their own scrolling
            overflow: 'visible',
            position: 'relative',
            zIndex: 1,
          }}
        >
          <ErrorBoundary>{children}</ErrorBoundary>
        </Box>
      </Box>
    </BaseLayoutProvider>
  )
}
