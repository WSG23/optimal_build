import { createTheme, ThemeOptions, Theme } from '@mui/material/styles'
import { colors, typography, radii, spacing } from '@ob/tokens'
import type { ThemeMode } from './ThemeContext'

/**
 * Theme Configuration
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
        default: '#121212', // User specific request "Darkest"
        paper: '#1E1E1E', // User specific request "Lighter"
      },
      text: {
        primary: colors.neutral[100],
        secondary: colors.neutral[400],
        disabled: colors.neutral[600],
      },
      divider: '#333333', // User specific request "Subtle 1px borders"
      surface: {
        elevated: colors.neutral[800],
      },
    }
  }
  // Light mode - Premium "slatedness" preserved
  // Uses Slate-200 (#e2e8f0) as base to make glass panels pop
  // Per AI Studio Protocol: backgrounds become Slate-50 (now Slate-200 for premium feel)
  return {
    background: {
      default: '#e2e8f0', // Slate-200: Blue-tinted gray for premium look
      paper: '#f8fafc', // Slate-50: Slightly lighter for cards/panels
    },
    text: {
      primary: '#0f172a', // Slate-900
      secondary: '#475569', // Slate-600
      disabled: colors.neutral[400],
    },
    divider: 'rgba(0, 0, 0, 0.08)', // Subtle divider for light mode
    surface: {
      elevated: '#f1f5f9', // Slate-100
    },
  }
}

function createAppTheme(mode: ThemeMode): Theme {
  const modeColors = getModeColors(mode)

  const themeOptions: ThemeOptions = {
    /**
     * Tokenized spacing:
     * - MUI calls `theme.spacing(n)` for `sx` shorthands (p/m/gap) and Grid spacing.
     * - We map 1 unit to `--ob-space-050` (8px) so numeric spacing remains token-based.
     */
    spacing: (factor: number) => {
      if (factor === 0) return '0px'
      return `calc(${factor} * ${spacing['050']})`
    },
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
      borderRadius: 4, // Square Cyber-Minimalism: --ob-radius-sm (4px)
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: radii.xs, // 2px - Square Cyber-Minimalism
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
            borderRadius: radii.sm, // 4px - Square Cyber-Minimalism
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
            borderRadius: radii.xs, // 2px - Square Cyber-Minimalism (tags/chips)
          },
        },
      },
      // =========================================================================
      // SQUARE CYBER-MINIMALISM: Enforce sharp geometry across ALL MUI components
      // Radius scale: xs=2px (buttons/chips), sm=4px (cards/panels), md=6px (inputs), lg=8px (modals ONLY)
      // =========================================================================
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            borderRadius: radii.sm, // 4px - panels/cards
          },
          rounded: {
            borderRadius: radii.sm, // 4px
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: radii.lg, // 8px - modals/dialogs get lg
          },
        },
      },
      MuiDialogTitle: {
        styleOverrides: {
          root: {
            borderRadius: 0,
          },
        },
      },
      MuiMenu: {
        styleOverrides: {
          paper: {
            borderRadius: radii.sm, // 4px
          },
        },
      },
      MuiPopover: {
        styleOverrides: {
          paper: {
            borderRadius: radii.sm, // 4px
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: radii.sm, // 4px
          },
        },
      },
      MuiSnackbarContent: {
        styleOverrides: {
          root: {
            borderRadius: radii.sm, // 4px
          },
        },
      },
      MuiTabs: {
        styleOverrides: {
          root: {
            borderRadius: 0, // Tabs container - no radius
          },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            borderRadius: radii.xs, // 2px - tab items
          },
        },
      },
      MuiToggleButton: {
        styleOverrides: {
          root: {
            borderRadius: radii.xs, // 2px
          },
        },
      },
      MuiToggleButtonGroup: {
        styleOverrides: {
          root: {
            borderRadius: radii.xs, // 2px
          },
        },
      },
      MuiAccordion: {
        styleOverrides: {
          root: {
            borderRadius: radii.sm, // 4px
            '&:first-of-type': {
              borderTopLeftRadius: radii.sm,
              borderTopRightRadius: radii.sm,
            },
            '&:last-of-type': {
              borderBottomLeftRadius: radii.sm,
              borderBottomRightRadius: radii.sm,
            },
          },
        },
      },
      MuiSelect: {
        styleOverrides: {
          root: {
            borderRadius: radii.md, // 6px - inputs
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: radii.md, // 6px - inputs
          },
          notchedOutline: {
            borderRadius: radii.md, // 6px
          },
        },
      },
      MuiFilledInput: {
        styleOverrides: {
          root: {
            borderRadius: `${radii.md} ${radii.md} 0 0`, // 6px top only
          },
        },
      },
      MuiInputBase: {
        styleOverrides: {
          root: {
            borderRadius: radii.md, // 6px - inputs
          },
        },
      },
      MuiAutocomplete: {
        styleOverrides: {
          paper: {
            borderRadius: radii.sm, // 4px - dropdown
          },
          inputRoot: {
            borderRadius: radii.md, // 6px - input
          },
        },
      },
      MuiSlider: {
        styleOverrides: {
          thumb: {
            borderRadius: radii.xs, // 2px - square thumb
          },
          track: {
            borderRadius: radii.xs, // 2px
          },
          rail: {
            borderRadius: radii.xs, // 2px
          },
        },
      },
      MuiSwitch: {
        styleOverrides: {
          track: {
            borderRadius: radii.sm, // 4px - more square track
          },
        },
      },
      MuiAvatar: {
        styleOverrides: {
          root: {
            borderRadius: radii.sm, // 4px - square avatars (use pill for circular)
          },
          circular: {
            borderRadius: radii.pill, // Keep circular option
          },
        },
      },
      MuiBadge: {
        styleOverrides: {
          badge: {
            borderRadius: radii.xs, // 2px
          },
        },
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: radii.xs, // 2px
          },
        },
      },
      MuiMenuItem: {
        styleOverrides: {
          root: {
            borderRadius: radii.xs, // 2px
          },
        },
      },
      MuiSkeleton: {
        styleOverrides: {
          root: {
            borderRadius: radii.sm, // 4px
          },
          rectangular: {
            borderRadius: radii.sm, // 4px
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            borderRadius: radii.xs, // 2px
          },
          bar: {
            borderRadius: radii.xs, // 2px
          },
        },
      },
      MuiFab: {
        styleOverrides: {
          root: {
            borderRadius: radii.sm, // 4px - square FAB
          },
        },
      },
      MuiSpeedDial: {
        styleOverrides: {
          fab: {
            borderRadius: radii.sm, // 4px
          },
        },
      },
      MuiImageListItemBar: {
        styleOverrides: {
          root: {
            borderRadius: 0,
          },
        },
      },
      MuiBottomNavigation: {
        styleOverrides: {
          root: {
            borderRadius: 0,
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            borderRadius: 0,
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRadius: 0, // Drawers - no radius
          },
        },
      },
    },
  }

  return createTheme(themeOptions)
}

// Pre-create themes for performance
export const darkTheme = createAppTheme('dark')
export const lightTheme = createAppTheme('light')

// Default export for backward compatibility
export const theme = darkTheme

// Get theme by mode
export function getTheme(mode: ThemeMode): Theme {
  return mode === 'dark' ? darkTheme : lightTheme
}

// Deprecated exports for backward compatibility
/** @deprecated Use darkTheme instead */
export const yosaiDarkTheme = darkTheme
/** @deprecated Use lightTheme instead */
export const yosaiLightTheme = lightTheme
/** @deprecated Use theme instead */
export const yosaiTheme = theme
/** @deprecated Use getTheme instead */
export const getYosaiTheme = getTheme
