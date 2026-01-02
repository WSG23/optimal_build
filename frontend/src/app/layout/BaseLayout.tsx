import { ReactNode, useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { BaseLayoutProvider } from './BaseLayoutContext'
import { YosaiTopNav } from '../../components/layout/YosaiTopNav'
import { useThemeMode } from '../../theme/ThemeContext'

export function BaseLayout({ children }: { children: ReactNode }) {
  const { mode } = useThemeMode()
  const [isNavPinned, setIsNavPinned] = useState(() => {
    if (typeof window === 'undefined') return true
    const value = window.localStorage.getItem('ob_top_nav_pinned')
    return value !== 'false'
  })

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem('ob_top_nav_pinned', String(isNavPinned))
  }, [isNavPinned])

  const topOffset = isNavPinned
    ? 'calc(var(--ob-space-250) + var(--ob-space-300))'
    : 0

  return (
    <BaseLayoutProvider value={{ inBaseLayout: true, topOffset }}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          overflow: 'hidden',
          bgcolor: 'background.default',
          color: 'text.primary',
          position: 'relative',
        }}
      >
        {/* Background Grid Pattern - promoted to own layer to prevent paint blocking */}
        <Box
          aria-hidden
          sx={{
            position: 'fixed',
            inset: 0,
            pointerEvents: 'none',
            opacity: mode === 'dark' ? 0.5 : 0.3,
            backgroundImage: `
              linear-gradient(var(--ob-bg-grid-color) 1px, transparent 1px),
              linear-gradient(90deg, var(--ob-bg-grid-color) 1px, transparent 1px)
            `,
            backgroundSize: 'var(--ob-bg-grid-size) var(--ob-bg-grid-size)',
            zIndex: 0,
            // Promote to compositing layer to prevent blocking main content paint
            transform: 'translateZ(0)',
            willChange: 'opacity',
          }}
        />

        {/* Scanline Animation (dark mode only) */}
        {mode === 'dark' && <Box className="ob-scanline" aria-hidden />}

        <YosaiTopNav
          isPinned={isNavPinned}
          onTogglePinned={() => setIsNavPinned((prev) => !prev)}
        />
        <Box
          sx={{
            flexGrow: 1,
            minWidth: 0,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            // Allow child components (AppShell, YosaiShell) to handle their own scrolling
            overflow: 'visible',
            position: 'relative',
            zIndex: 1,
          }}
        >
          {children}
        </Box>
      </Box>
    </BaseLayoutProvider>
  )
}
