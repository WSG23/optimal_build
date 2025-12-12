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
        backdropFilter: 'blur(16px) saturate(180%)',
        borderColor: 'var(--ob-border-glass)',
        color: 'var(--ob-color-text-primary)',
        boxShadow: 'var(--ob-shadow-glass)',
        p: 3,
      }
    : {
        // Light mode: premium glass surface
        bgcolor: 'rgba(255, 255, 255, 0.7)',
        backdropFilter: 'blur(16px)',
        borderColor: 'rgba(255, 255, 255, 0.6)',
        boxShadow: '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
        p: 3,
      }

/**
 * Section header styling - gradient text in dark mode
 */
export const getSectionHeaderSx = (dark: boolean): SxProps<Theme> =>
  dark
    ? {
        background:
          'linear-gradient(90deg, var(--ob-neutral-100), var(--ob-neutral-400))',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
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
          backgroundColor: 'rgba(255,255,255,0.04)',
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
          fontWeight: 600,
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
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: dark ? 'var(--ob-shadow-glass-lg)' : 'var(--ob-shadow-lg)',
    borderColor: dark
      ? 'var(--ob-border-glass-strong)'
      : 'var(--ob-color-brand-primary)',
  },
})

/**
 * Primary action button styling (gradient)
 */
export const getPrimaryButtonSx = (): SxProps<Theme> => ({
  background:
    'linear-gradient(135deg, var(--ob-brand-600), var(--ob-brand-500))',
  color: '#fff',
  fontWeight: 600,
  px: 3,
  py: 1.5,
  borderRadius: 'var(--ob-radius-xs)', // 2px - Square Cyber-Minimalism
  boxShadow: '0 4px 15px var(--ob-brand-glow)',
  transition: 'all 0.2s ease',
  '&:hover': {
    background:
      'linear-gradient(135deg, var(--ob-brand-700), var(--ob-brand-600))',
    transform: 'translateY(-2px)',
    boxShadow: '0 8px 25px var(--ob-brand-glow)',
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
  '&::after': {
    content: '""',
    position: 'absolute',
    inset: -4,
    borderRadius: 'inherit',
    border: '1px solid rgba(255,255,255,0.35)',
    animation: 'cta-pulse 2s ease-in-out infinite',
    pointerEvents: 'none',
  },
  '@keyframes cta-pulse': {
    '0%': { opacity: 0.6, transform: 'scale(0.98)' },
    '50%': { opacity: 0.2, transform: 'scale(1.04)' },
    '100%': { opacity: 0.6, transform: 'scale(0.98)' },
  },
})

/**
 * Shimmer background for loading tiles/cards
 */
export const getShimmerSx = (): SxProps<Theme> => ({
  position: 'relative',
  overflow: 'hidden',
  background:
    'linear-gradient(90deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.12) 50%, rgba(255,255,255,0.04) 100%)',
  backgroundSize: '200% 100%',
  animation: 'shimmer 1.6s ease-in-out infinite',
  '@keyframes shimmer': {
    '0%': { backgroundPosition: '-200% 0' },
    '100%': { backgroundPosition: '200% 0' },
  },
})

/**
 * Bouncing CTA button animation (for primary actions)
 */
export const getBouncingButtonSx = (): SxProps<Theme> => ({
  '@keyframes subtle-bounce': {
    '0%, 100%': { transform: 'translateY(0)' },
    '50%': { transform: 'translateY(-4px)' },
  },
  animation: 'subtle-bounce 2s ease-in-out infinite',
  '&:hover': {
    animationPlayState: 'paused',
  },
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
  backdropFilter: 'blur(8px)',
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
            'linear-gradient(to bottom, rgba(0,0,0,0.3), rgba(0,0,0,0.7))',
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
