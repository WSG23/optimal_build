/* eslint-disable react-refresh/only-export-components */
import { ReactNode } from 'react'
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { getTheme } from './theme'
import { ThemeModeProvider, useThemeMode } from './ThemeContext'

interface AppThemeProviderProps {
  children: ReactNode
}

/**
 * Inner component that uses the theme mode context
 */
function ThemeProviderInner({ children }: AppThemeProviderProps) {
  const { mode } = useThemeMode()
  const theme = getTheme(mode)

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </MuiThemeProvider>
  )
}

/**
 * AppThemeProvider
 * Wraps the application with the Optimal Build design system.
 * Supports dark and light modes with persistence.
 */
export function AppThemeProvider({ children }: AppThemeProviderProps) {
  return (
    <ThemeModeProvider>
      <ThemeProviderInner>{children}</ThemeProviderInner>
    </ThemeModeProvider>
  )
}

// Re-export for convenience
export { useThemeMode } from './ThemeContext'
export type { ThemeMode } from './ThemeContext'
