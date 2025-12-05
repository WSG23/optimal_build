import { ReactNode } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { getYosaiTheme } from './yosaiTheme';
import { ThemeModeProvider, useThemeMode } from './ThemeContext';

interface YosaiThemeProviderProps {
    children: ReactNode;
}

/**
 * Inner component that uses the theme mode context
 */
function YosaiThemeProviderInner({ children }: YosaiThemeProviderProps) {
    const { mode } = useThemeMode();
    const theme = getYosaiTheme(mode);

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            {children}
        </ThemeProvider>
    );
}

/**
 * YosaiThemeProvider
 * Wraps the application with the "Fortress" design system overrides.
 * Supports dark and light modes with persistence.
 */
export function YosaiThemeProvider({ children }: YosaiThemeProviderProps) {
    return (
        <ThemeModeProvider>
            <YosaiThemeProviderInner>
                {children}
            </YosaiThemeProviderInner>
        </ThemeModeProvider>
    );
}

// Re-export for convenience
export { useThemeMode } from './ThemeContext';
export type { ThemeMode } from './ThemeContext';
