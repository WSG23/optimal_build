import { Box, Paper, alpha, useTheme } from '@mui/material'
import { ReactNode } from 'react'

export interface FeasibilityInteractiveLayoutProps {
  renderMap: () => ReactNode
  renderAddressBar: () => ReactNode
  renderFooter?: () => ReactNode
  children: ReactNode
}

export function FeasibilityInteractiveLayout({
  renderMap,
  renderAddressBar,
  renderFooter,
  children,
}: FeasibilityInteractiveLayoutProps) {
  const theme = useTheme()

  return (
    <Box
      sx={{
        display: 'flex',
        height: 'calc(100vh - 64px)', // Adjust based on AppShell header height
        position: 'relative',
        overflow: 'hidden',
        bgcolor: 'black', // Map fallback
      }}
    >
      {/* 2. Map Canvas (Background / Right Side) */}
      <Box
        sx={{
          position: 'absolute',
          top: '0',
          left: 0,
          right: 0,
          bottom: '0',
          zIndex: 0,
        }}
      >
        {renderMap()}
      </Box>

      {/* 1. Glass Sidebar (Left Overlay) */}
      <Paper
        elevation={0}
        sx={{
          position: 'relative',
          width: '35%',
          minWidth: 400,
          maxWidth: 500,
          zIndex: 10,
          m: 'var(--ob-space-300)',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 'var(--ob-radius-sm)', // Square Cyber-Minimalism: sm for panels
          border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          bgcolor: alpha(theme.palette.background.paper, 0.65), // Semi-transparent
          backdropFilter: 'blur(var(--ob-blur-lg))',
          boxShadow: '0 8px 32px 0 var(--ob-color-overlay-backdrop-light)',
          overflow: 'hidden',
        }}
      >
        {/* Address Bar Area */}
        <Box
          sx={{
            p: 'var(--ob-space-300)',
            pb: 'var(--ob-space-200)',
            borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            bgcolor: alpha(theme.palette.background.paper, 0.4),
          }}
        >
          {renderAddressBar()}
        </Box>

        {/* Scrollable Form Content */}
        <Box
          sx={{
            flexGrow: 1,
            overflowY: 'auto',
            p: 'var(--ob-space-300)',
            '&::-webkit-scrollbar': { width: '6px' },
            '&::-webkit-scrollbar-track': { background: 'transparent' },
            '&::-webkit-scrollbar-thumb': {
              background: alpha(theme.palette.text.secondary, 0.2),
              borderRadius: 'var(--ob-radius-sm)',
            },
          }}
        >
          {children}
        </Box>

        {/* Sticky Footer for Actions */}
        {renderFooter && (
          <Box
            sx={{
              p: 'var(--ob-space-300)',
              pt: 'var(--ob-space-200)',
              borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              bgcolor: alpha(theme.palette.background.paper, 0.4),
            }}
          >
            {renderFooter()}
          </Box>
        )}
      </Paper>
    </Box>
  )
}
