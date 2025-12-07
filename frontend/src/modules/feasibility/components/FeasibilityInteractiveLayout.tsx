import { Box, Paper, alpha, useTheme } from '@mui/material';
import { ReactNode } from 'react';

export interface FeasibilityInteractiveLayoutProps {
  renderMap: () => ReactNode;
  renderAddressBar: () => ReactNode;
  renderFooter?: () => ReactNode;
  children: ReactNode;
}

export function FeasibilityInteractiveLayout({
  renderMap,
  renderAddressBar,
  renderFooter,
  children
}: FeasibilityInteractiveLayoutProps) {
  const theme = useTheme();

  return (
    <Box sx={{
      display: 'flex',
      height: 'calc(100vh - 64px)', // Adjust based on AppShell header height
      position: 'relative',
      overflow: 'hidden',
      bgcolor: 'black' // Map fallback
    }}>
      {/* 2. Map Canvas (Background / Right Side) */}
      <Box sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 0
      }}>
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
          m: 3,
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 4,
          border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          bgcolor: alpha(theme.palette.background.paper, 0.65), // Semi-transparent
          backdropFilter: 'blur(20px)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
          overflow: 'hidden'
        }}
      >
        {/* Address Bar Area */}
        <Box sx={{
          p: 3,
          pb: 2,
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          bgcolor: alpha(theme.palette.background.paper, 0.4)
        }}>
           {renderAddressBar()}
        </Box>

        {/* Scrollable Form Content */}
        <Box sx={{
          flexGrow: 1,
          overflowY: 'auto',
          p: 3,
          '&::-webkit-scrollbar': { width: '6px' },
          '&::-webkit-scrollbar-track': { background: 'transparent' },
          '&::-webkit-scrollbar-thumb': {
              background: alpha(theme.palette.text.secondary, 0.2),
              borderRadius: '3px'
          }
        }}>
          {children}
        </Box>

        {/* Sticky Footer for Actions */}
        {renderFooter && (
           <Box sx={{
             p: 3,
             pt: 2,
             borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
             bgcolor: alpha(theme.palette.background.paper, 0.4)
           }}>
             {renderFooter()}
           </Box>
        )}
      </Paper>
    </Box>
  );
}
