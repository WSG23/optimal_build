import { ReactNode } from 'react'
import { Box } from '@mui/material'
import { BaseLayoutProvider } from './BaseLayoutContext'
import { YosaiTopNav } from '../../components/layout/YosaiTopNav'

export function BaseLayout({ children }: { children: ReactNode }) {
  const TOP_NAV_HEIGHT = 56

  return (
    <BaseLayoutProvider
      value={{ inBaseLayout: true, topOffset: TOP_NAV_HEIGHT }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          bgcolor: 'background.default',
          color: 'text.primary',
        }}
      >
        <YosaiTopNav height={TOP_NAV_HEIGHT} />
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
