import { ReactNode } from 'react'
import { YosaiSidebar } from '../../components/layout/YosaiSidebar'
import { Box } from '@mui/material'
import { BaseLayoutProvider } from './BaseLayoutContext'

export function BaseLayout({ children }: { children: ReactNode }) {
  return (
    <BaseLayoutProvider value={{ inBaseLayout: true }}>
      <Box
        sx={{
          display: 'flex',
          minHeight: '100vh',
          bgcolor: 'background.default',
          color: 'text.primary',
        }}
      >
        <Box
          sx={{ position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 1200 }}
        >
          <YosaiSidebar />
        </Box>
        <Box
          sx={{
            flexGrow: 1,
            marginLeft: '280px',
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
