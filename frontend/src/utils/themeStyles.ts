/**
 * Shared Theme Style Utilities
 *
 * Canonical styling functions that use design tokens and provide consistent
 * theme-aware styles across all pages. These should be used instead of
 * inline hardcoded colors.
 *
 * Usage:
 *   const theme = useTheme()
 *   const isDarkMode = theme.palette.mode === 'dark'
 *   <GlassCard sx={getGlassCardSx(isDarkMode)}>
 */

import { type SxProps, type Theme } from '@mui/material'

/**
 * Check if current theme is dark mode
 */
export const isDarkMode = (theme: Theme): boolean =>
  theme.palette.mode === 'dark'

/**
 * GlassCard styling - premium glassmorphism effect
 * Uses CSS custom properties from tokens.css
 */
export const getGlassCardSx = (dark: boolean): SxProps<Theme> =>
  dark
    ? {
        bgcolor: 'var(--ob-surface-glass-1)',
        borderColor: 'var(--ob-border-glass)',
        color: 'var(--ob-color-text-primary)',
        boxShadow: 'var(--ob-shadow-sm)',
        p: 3,
      }
    : {
        bgcolor: 'var(--ob-surface-glass-1)',
        borderColor: 'var(--ob-border-glass-strong)',
        boxShadow: 'var(--ob-shadow-sm)',
        p: 3,
      }

/**
 * Section header styling
 */
export const getSectionHeaderSx = (dark: boolean): SxProps<Theme> =>
  dark
    ? {
        color: 'var(--ob-color-text-primary)',
      }
    : {
        color: 'var(--ob-color-text-primary)',
      }

/**
 * Secondary/muted text styling
 */
export const getSecondaryTextSx = (dark: boolean): SxProps<Theme> =>
  dark
    ? { color: 'var(--ob-color-text-secondary)' }
    : { color: 'var(--ob-color-text-subtle)' }

/**
 * Border color for dividers and separators
 */
export const getBorderColor = (dark: boolean): string =>
  dark ? 'var(--ob-border-glass)' : 'var(--ob-color-border-subtle)'

/**
 * Input field styling for forms
 */
export const getInputSx = (dark: boolean): SxProps<Theme> =>
  dark
    ? {
        '& .MuiOutlinedInput-root': {
          color: 'var(--ob-color-text-primary)',
          backgroundColor: 'rgba(var(--ob-color-text-primary-rgb), 0.04)',
          '& fieldset': { borderColor: 'var(--ob-border-glass)' },
          '&:hover fieldset': { borderColor: 'var(--ob-border-glass-strong)' },
          '&.Mui-focused fieldset': {
            borderColor: 'var(--ob-color-brand-primary)',
          },
        },
        '& .MuiOutlinedInput-input': { color: 'var(--ob-color-text-primary)' },
        '& .MuiInputLabel-root': { color: 'var(--ob-color-text-secondary)' },
        '& .MuiSvgIcon-root': { color: 'var(--ob-color-text-secondary)' },
      }
    : {}

/**
 * Table styling for data tables
 */
export const getTableSx = (dark: boolean): SxProps<Theme> =>
  dark
    ? {
        '& .MuiTableCell-root': {
          borderColor: 'var(--ob-border-glass)',
          color: 'var(--ob-color-text-primary)',
        },
        '& .MuiTableCell-head': {
          backgroundColor: 'var(--ob-color-bg-surface-elevated)',
          color: 'var(--ob-color-text-primary)',
          fontWeight: 'var(--ob-font-weight-semibold)',
        },
        '& .MuiTableRow-root:hover': {
          backgroundColor: 'var(--ob-color-action-hover)',
        },
      }
    : {}

/**
 * Card hover effect styling
 */
export const getCardHoverSx = (dark: boolean): SxProps<Theme> => ({
  transition:
    'transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: dark ? 'var(--ob-shadow-md)' : 'var(--ob-shadow-sm)',
    borderColor: dark
      ? 'var(--ob-border-glass-strong)'
      : 'var(--ob-color-brand-primary)',
  },
})

/**
 * Primary action button styling (gradient)
 */
export const getPrimaryButtonSx = (): SxProps<Theme> => ({
  background: 'var(--ob-brand-600)',
  color: 'var(--ob-neutral-50)',
  fontWeight: 'var(--ob-font-weight-semibold)',
  px: 3,
  py: 1.5,
  borderRadius: 'var(--ob-radius-xs)', // 2px - Square Cyber-Minimalism
  boxShadow: 'var(--ob-shadow-sm)',
  transition: 'background-color 0.2s ease, transform 0.2s ease',
  '&:hover': {
    background: 'var(--ob-brand-700)',
    transform: 'translateY(-1px)',
    boxShadow: 'var(--ob-shadow-md)',
  },
  '&:disabled': {
    background: 'var(--ob-neutral-700)',
    color: 'var(--ob-neutral-400)',
    boxShadow: 'none',
  },
})

/**
 * Primary action pulse (subtle attention grabber)
 */
export const getPulseButtonSx = (): SxProps<Theme> => ({
  position: 'relative',
  overflow: 'hidden',
  '&::after': { content: 'none' },
})

/**
 * Shimmer background for loading tiles/cards
 */
export const getShimmerSx = (): SxProps<Theme> => ({
  position: 'relative',
  overflow: 'hidden',
  backgroundColor: 'rgba(var(--ob-color-text-primary-rgb), 0.06)',
})

/**
 * Bouncing CTA button animation (for primary actions)
 */
export const getBouncingButtonSx = (): SxProps<Theme> => ({
  transform: 'none',
})

/**
 * Sticky header styling
 */
export const getStickyHeaderSx = (dark: boolean): SxProps<Theme> => ({
  position: 'sticky',
  top: 0,
  zIndex: 'var(--ob-z-sticky)',
  backgroundColor: dark
    ? 'var(--ob-color-bg-root)'
    : 'var(--ob-color-bg-surface)',
  borderBottom: `1px solid ${dark ? 'var(--ob-border-glass)' : 'var(--ob-color-border-subtle)'}`,
  py: 2,
  px: 3,
})

/**
 * Page background styling (for immersive pages)
 */
export const getPageBackgroundSx = (dark: boolean): SxProps<Theme> =>
  dark
    ? {
        bgcolor: 'var(--ob-color-bg-root)',
        minHeight: '100vh',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'fixed',
          inset: 0,
          background:
            'linear-gradient(to bottom, rgba(var(--ob-color-text-inverse-rgb), 0.06), rgba(var(--ob-color-text-inverse-rgb), 0.14))',
          pointerEvents: 'none',
          zIndex: 0,
        },
      }
    : {
        bgcolor: 'var(--ob-color-bg-root)',
        minHeight: '100vh',
      }

/**
 * Status badge styling
 */
export const getStatusBadgeSx = (
  status: 'success' | 'warning' | 'error' | 'info',
): SxProps<Theme> => ({
  px: 1,
  py: 0.25,
  borderRadius: 'var(--ob-radius-sm)',
  fontSize: 'var(--ob-font-size-xs)',
  fontWeight: 500,
  textTransform: 'uppercase',
  ...(status === 'success' && {
    backgroundColor: 'var(--ob-color-success-soft)',
    color: 'var(--ob-color-status-success-text)',
  }),
  ...(status === 'warning' && {
    backgroundColor: 'var(--ob-color-warning-soft)',
    color: 'var(--ob-color-status-warning-text)',
  }),
  ...(status === 'error' && {
    backgroundColor: 'var(--ob-color-error-soft)',
    color: 'var(--ob-color-status-error-text)',
  }),
  ...(status === 'info' && {
    backgroundColor: 'var(--ob-color-info-soft)',
    color: 'var(--ob-color-status-info-text)',
  }),
})

/**
 * Combine multiple sx objects
 */
export const combineSx = (
  ...sxArray: (SxProps<Theme> | undefined)[]
): SxProps<Theme> =>
  sxArray.filter(Boolean).reduce(
    (acc, sx) => ({
      ...acc,
      ...(sx as object),
    }),
    {},
  ) as SxProps<Theme>
