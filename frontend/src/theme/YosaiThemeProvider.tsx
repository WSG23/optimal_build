/* eslint-disable react-refresh/only-export-components */
import { ReactNode } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { getTheme } from './theme';
import { ThemeModeProvider, useThemeMode } from './ThemeContext';

interface AppThemeProviderProps {
    children: ReactNode;
}

/** @deprecated Use AppThemeProviderProps instead */
export type YosaiThemeProviderProps = AppThemeProviderProps;

/**
 * Inner component that uses the theme mode context
 */
function ThemeProviderInner({ children }: AppThemeProviderProps) {
    const { mode } = useThemeMode();
    const theme = getTheme(mode);

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            {children}
        </ThemeProvider>
    );
}

/**
 * AppThemeProvider
 * Wraps the application with the Optimal Build design system.
 * Supports dark and light modes with persistence.
 */
export function AppThemeProvider({ children }: AppThemeProviderProps) {
    return (
        <ThemeModeProvider>
            <ThemeProviderInner>
                {children}
            </ThemeProviderInner>
        </ThemeModeProvider>
    );
}

/** @deprecated Use AppThemeProvider instead */
export const YosaiThemeProvider = AppThemeProvider;

// Re-export for convenience
export { useThemeMode } from './ThemeContext';
export type { ThemeMode } from './ThemeContext';
