import { createTheme, ThemeOptions, Theme } from '@mui/material/styles';
import { getColors, darkColors, lightColors, typography, radii, spacing } from './tokens';
import type { ThemeMode } from './ThemeContext';

/**
 * Yōsai Theme Configuration
 * Maps custom tokens to MUI's system.
 * Supports both dark and light modes.
 */

function createYosaiTheme(mode: ThemeMode): Theme {
    const colors = getColors(mode);

    const themeOptions: ThemeOptions = {
        palette: {
            mode,
            background: {
                default: colors.sumi[900],
                paper: colors.sumi[800],
            },
            primary: {
                main: colors.kin[500],
                dark: colors.kin[600],
                contrastText: mode === 'dark' ? darkColors.sumi[900] : lightColors.sumi[900],
            },
            error: {
                main: colors.akarn[500],
            },
            info: {
                main: colors.aon[500],
            },
            text: {
                primary: colors.ishigaki[100],
                secondary: colors.ishigaki[500],
                disabled: colors.ishigaki[900],
            },
            divider: colors.sumi[600],
        },
        typography: {
            fontFamily: typography.fontFamily.sans,
            h1: {
                fontWeight: typography.weights.bold,
                fontSize: typography.sizes['2xl'],
                letterSpacing: '-0.02em',
            },
            h2: {
                fontWeight: typography.weights.bold,
                fontSize: typography.sizes.xl,
                letterSpacing: '-0.01em',
            },
            h3: {
                fontWeight: typography.weights.medium,
                fontSize: typography.sizes.lg,
            },
            body1: {
                fontSize: typography.sizes.base,
                letterSpacing: '0.01em', // Technical readability
            },
            body2: {
                fontSize: typography.sizes.sm,
                letterSpacing: '0.01em',
            },
            button: {
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                fontWeight: typography.weights.bold,
            },
        },
        shape: {
            borderRadius: parseInt(radii.sm), // 2px by default for sharp edges
        },
        components: {
            MuiButton: {
                styleOverrides: {
                    root: {
                        borderRadius: radii.sm,
                        boxShadow: 'none',
                        '&:hover': {
                            boxShadow: 'none',
                        },
                    },
                    containedPrimary: {
                        backgroundColor: colors.kin[500],
                        color: mode === 'dark' ? darkColors.sumi[900] : lightColors.sumi[900],
                        '&:hover': {
                            backgroundColor: colors.kin[600],
                        },
                    },
                },
            },
            MuiCard: {
                styleOverrides: {
                    root: {
                        backgroundImage: 'none', // Remove MUI gradient overlay
                        backgroundColor: colors.sumi[800],
                        border: `1px solid ${colors.sumi[600]}`,
                    },
                },
            },
            MuiPaper: {
                styleOverrides: {
                    root: {
                        backgroundImage: 'none',
                    },
                },
            },
            MuiTextField: {
                styleOverrides: {
                    root: {
                        '& .MuiOutlinedInput-root': {
                            '& fieldset': {
                                borderColor: colors.sumi[600],
                            },
                            '&:hover fieldset': {
                                borderColor: colors.ishigaki[500],
                            },
                            '&.Mui-focused fieldset': {
                                borderColor: colors.kin[500],
                            },
                        },
                    },
                },
            },
            MuiTableCell: {
                styleOverrides: {
                    root: {
                        borderColor: colors.sumi[600],
                    },
                    head: {
                        backgroundColor: colors.sumi[800],
                        fontWeight: typography.weights.bold,
                    },
                },
            },
            MuiCssBaseline: {
                styleOverrides: {
                    body: {
                        scrollbarColor: `${colors.sumi[600]} ${colors.sumi[900]}`,
                        '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
                            backgroundColor: colors.sumi[900],
                            width: spacing[2],
                            height: spacing[2],
                        },
                        '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
                            borderRadius: radii.full,
                            backgroundColor: colors.sumi[600],
                            minHeight: spacing[6],
                        },
                        '&::-webkit-scrollbar-thumb:focus, & *::-webkit-scrollbar-thumb:focus': {
                            backgroundColor: colors.ishigaki[700],
                        },
                    },
                },
            },
        },
    };

    return createTheme(themeOptions);
}

// Pre-create themes for performance
export const yosaiDarkTheme = createYosaiTheme('dark');
export const yosaiLightTheme = createYosaiTheme('light');

// Default export for backward compatibility
export const yosaiTheme = yosaiDarkTheme;

// Get theme by mode
export function getYosaiTheme(mode: ThemeMode): Theme {
    return mode === 'dark' ? yosaiDarkTheme : yosaiLightTheme;
}
