import { ReactNode, useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { BaseLayoutProvider } from './BaseLayoutContext'
import { YosaiTopNav } from '../../components/layout/YosaiTopNav'

export function BaseLayout({ children }: { children: ReactNode }) {
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
          minHeight: '100vh',
          bgcolor: 'background.default',
          color: 'text.primary',
        }}
      >
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
          }}
        >
          {children}
        </Box>
      </Box>
    </BaseLayoutProvider>
  )
}
