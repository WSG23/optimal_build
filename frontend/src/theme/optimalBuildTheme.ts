/**
 * @deprecated This file is deprecated. Use `./theme.ts` instead.
 * All exports are re-exported from theme.ts for backward compatibility.
 */
import { createTheme, ThemeOptions, Theme } from '@mui/material/styles'
import { colors, typography, radii, spacing } from '@ob/tokens'
import type { ThemeMode } from './ThemeContext'

/**
 * Theme Configuration (LEGACY - use theme.ts)
 * =============================================================================
 * Maps canonical design tokens from @ob/tokens to MUI's theme system.
 * CSS variables in tokens.css are the SINGLE SOURCE OF TRUTH.
 * This theme uses the static JS values for MUI compatibility.
 * =============================================================================
 */

/**
 * Get mode-specific color values
 * Dark mode uses the standard palette, light mode inverts where needed
 */
function getModeColors(mode: ThemeMode) {
  if (mode === 'dark') {
    return {
      background: {
        default: colors.neutral[950],
        paper: colors.neutral[900],
      },
      text: {
        primary: colors.neutral[100],
        secondary: colors.neutral[400],
        disabled: colors.neutral[600],
      },
      divider: colors.neutral[700],
      surface: {
        elevated: colors.neutral[800],
      },
    }
  }
  // Light mode
  return {
    background: {
      default: colors.neutral[50],
      paper: '#ffffff',
    },
    text: {
      primary: colors.neutral[900],
      secondary: colors.neutral[600],
      disabled: colors.neutral[400],
    },
    divider: colors.neutral[200],
    surface: {
      elevated: colors.neutral[100],
    },
  }
}

function createOptimalBuildTheme(mode: ThemeMode): Theme {
  const modeColors = getModeColors(mode)

  const themeOptions: ThemeOptions = {
    palette: {
      mode,
      background: modeColors.background,
      primary: {
        main: colors.brand[600],
        light: colors.brand[400],
        dark: colors.brand[700],
        contrastText: '#ffffff',
      },
      secondary: {
        main: colors.accent[500],
        light: colors.accent[400],
        dark: colors.accent[600],
        contrastText: colors.neutral[900],
      },
      error: {
        main: colors.error[600],
        light: colors.error[400],
        dark: colors.error[700],
      },
      warning: {
        main: colors.warning[500],
        light: colors.warning[400],
        dark: colors.warning[700],
      },
      success: {
        main: colors.success[600],
        light: colors.success[400],
        dark: colors.success[700],
      },
      info: {
        main: colors.info[600],
        light: colors.info[400],
        dark: colors.info[700],
      },
      text: modeColors.text,
      divider: modeColors.divider,
    },
    typography: {
      fontFamily: typography.family.base,
      h1: {
        fontWeight: typography.weight.bold,
        fontSize: typography.size['2xl'],
        letterSpacing: '-0.02em',
        lineHeight: typography.lineHeight.tight,
      },
      h2: {
        fontWeight: typography.weight.bold,
        fontSize: typography.size.xl,
        letterSpacing: '-0.01em',
        lineHeight: typography.lineHeight.tight,
      },
      h3: {
        fontWeight: typography.weight.semibold,
        fontSize: typography.size.lg,
        lineHeight: typography.lineHeight.normal,
      },
      h4: {
        fontWeight: typography.weight.semibold,
        fontSize: typography.size.base,
        lineHeight: typography.lineHeight.normal,
      },
      body1: {
        fontSize: typography.size.base,
        letterSpacing: '0.01em',
        lineHeight: typography.lineHeight.relaxed,
      },
      body2: {
        fontSize: typography.size.sm,
        letterSpacing: '0.01em',
        lineHeight: typography.lineHeight.relaxed,
      },
      button: {
        textTransform: 'none', // Modern style - no uppercase
        letterSpacing: '0.02em',
        fontWeight: typography.weight.semibold,
      },
      caption: {
        fontSize: typography.size.xs,
        lineHeight: typography.lineHeight.normal,
      },
    },
    shape: {
      borderRadius: 6, // Matches --ob-radius-sm (0.375rem = 6px)
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: radii.md,
            boxShadow: 'none',
            padding: `${spacing['075']} ${spacing['150']}`,
            '&:hover': {
              boxShadow: 'none',
            },
          },
          containedPrimary: {
            '&:hover': {
              backgroundColor: colors.brand[700],
            },
          },
          containedSecondary: {
            '&:hover': {
              backgroundColor: colors.accent[600],
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            backgroundColor: modeColors.background.paper,
            border: `1px solid ${modeColors.divider}`,
            borderRadius: radii.lg,
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
              borderRadius: radii.md,
              '& fieldset': {
                borderColor: modeColors.divider,
              },
              '&:hover fieldset': {
                borderColor: colors.neutral[500],
              },
              '&.Mui-focused fieldset': {
                borderColor: colors.brand[500],
              },
            },
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          root: {
            borderColor: modeColors.divider,
          },
          head: {
            backgroundColor: modeColors.surface.elevated,
            fontWeight: typography.weight.semibold,
          },
        },
      },
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            scrollbarColor: `${colors.neutral[600]} ${colors.neutral[900]}`,
            '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
              backgroundColor: modeColors.background.default,
              width: spacing['050'],
              height: spacing['050'],
            },
            '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
              borderRadius: radii.pill,
              backgroundColor: colors.neutral[600],
              minHeight: spacing['150'],
            },
            '&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover':
              {
                backgroundColor: colors.neutral[500],
              },
          },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: colors.neutral[800],
            color: colors.neutral[100],
            fontSize: typography.size.xs,
            borderRadius: radii.sm,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: radii.md,
          },
        },
      },
    },
  }

  return createTheme(themeOptions)
}

// Pre-create themes for performance
export const optimalBuildDarkTheme = createOptimalBuildTheme('dark')
export const optimalBuildLightTheme = createOptimalBuildTheme('light')

// Default export for backward compatibility
export const optimalBuildTheme = optimalBuildDarkTheme

// Get theme by mode
export function getOptimalBuildTheme(mode: ThemeMode): Theme {
  return mode === 'dark' ? optimalBuildDarkTheme : optimalBuildLightTheme
}
