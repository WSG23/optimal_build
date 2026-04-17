import { createTheme, ThemeOptions, Theme } from '@mui/material/styles'
import { colors, typography, radii, spacing } from '@ob/tokens'
import type { ThemeMode } from './ThemeContext'

/**
 * Theme Configuration
 * =============================================================================
 * Maps canonical design tokens from @ob/tokens to MUI's theme system.
 * Palette: Warm Stone & Slate Blue.
 * CSS variables in tokens.css are the SINGLE SOURCE OF TRUTH.
 * This theme uses the static JS values for MUI compatibility.
 * =============================================================================
 */

/**
 * Get mode-specific color values
 * Dark mode uses warm stone palette, light mode uses inverted warm stone
 */
function getModeColors(mode: ThemeMode) {
  if (mode === 'dark') {
    return {
      background: {
        default: colors.neutral[950], // #0c0a09 — Warm stone root
        paper: colors.neutral[900], // #151311 — Warm charcoal surface
      },
      text: {
        primary: colors.neutral[100], // #f5f5f4 — Warm off-white
        secondary: colors.neutral[400], // #a8a29e — Stone-400 labels
        disabled: colors.neutral[600], // #44403c — Ghost UI
      },
      divider: 'rgba(245, 235, 220, 0.10)', // Cream-tinted border
      surface: {
        elevated: colors.neutral[800], // #1c1917 — Stone-900
      },
    }
  }
  // Light mode — Clean whites with warm stone text hierarchy
  return {
    background: {
      default: '#ffffff', // Clean white page
      paper: colors.neutral[100], // #f5f5f4 — Stone-100 cards
    },
    text: {
      primary: '#1c1917', // Stone-900 — Near black
      secondary: '#44403c', // Stone-700
      disabled: colors.neutral[400], // #a8a29e — Stone-400
    },
    divider: 'rgba(28, 25, 23, 0.12)', // Warm black border
    surface: {
      elevated: colors.neutral[200], // #e7e5e3 — Stone-200
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
        main: colors.brand[500], // #3B7CB8 — Institutional Slate Blue
        light: colors.brand[400], // #5a9ad4
        dark: colors.brand[700], // #1e4f7a
        contrastText: '#fafaf9', // Light text on blue
      },
      secondary: {
        main: colors.accent[500],
        light: colors.accent[400],
        dark: colors.accent[600],
        contrastText: colors.neutral[950],
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
        fontFamily: typography.family.display,
        fontWeight: typography.weight.bold,
        fontSize: typography.size['2xl'],
        letterSpacing: '-0.02em',
        lineHeight: typography.lineHeight.tight,
        '@media (max-width: 600px)': {
          fontSize: typography.size.xl,
        },
      },
      h2: {
        fontFamily: typography.family.display,
        fontWeight: typography.weight.bold,
        fontSize: typography.size.xl,
        letterSpacing: '-0.01em',
        lineHeight: typography.lineHeight.tight,
        '@media (max-width: 600px)': {
          fontSize: typography.size.lg,
        },
      },
      h3: {
        fontFamily: typography.family.display,
        fontWeight: typography.weight.semibold,
        fontSize: typography.size.lg,
        lineHeight: typography.lineHeight.normal,
        '@media (max-width: 600px)': {
          fontSize: typography.size.base,
        },
      },
      h4: {
        fontFamily: typography.family.display,
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
              backgroundColor: colors.brand[600],
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
            scrollbarColor: `${colors.neutral[600]} ${colors.neutral[950]}`,
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
