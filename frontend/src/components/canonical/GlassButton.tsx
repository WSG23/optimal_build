import {
  Button as MuiButton,
  type ButtonProps as MuiButtonProps,
  type SxProps,
  type Theme,
} from '@mui/material'
import { forwardRef } from 'react'

type ObVariant = 'primary' | 'secondary' | 'ghost'
type MuiVariant = NonNullable<MuiButtonProps['variant']>
type GlassButtonVariant = ObVariant | MuiVariant

export interface GlassButtonProps extends Omit<
  MuiButtonProps,
  'variant' | 'size' | 'sx'
> {
  variant?: GlassButtonVariant
  size?: 'small' | 'medium' | 'large'
  shape?: 'pill' | 'rounded'
  sx?: SxProps<Theme>
}

const heightMap = {
  small: '32px',
  medium: '40px',
  large: '48px',
} as const

const radiusMap = {
  pill: 'var(--ob-radius-pill)',
  rounded: 'var(--ob-radius-xs)',
} as const

export const GlassButton = forwardRef<HTMLButtonElement, GlassButtonProps>(
  (
    { variant = 'primary', size = 'medium', shape = 'pill', sx, ...props },
    ref,
  ) => {
    const muiVariant: MuiVariant =
      variant === 'primary'
        ? 'contained'
        : variant === 'secondary'
          ? 'outlined'
          : variant === 'ghost'
            ? 'text'
            : variant

    const commonSx: SxProps<Theme> = {
      height: heightMap[size],
      borderRadius: radiusMap[shape],
      textTransform: 'none',
      fontWeight: 'var(--ob-font-weight-semibold)',
      letterSpacing: 'var(--ob-letter-spacing-wider)',
      padding: '0 var(--ob-space-150)',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      position: 'relative',
      overflow: 'hidden',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 'var(--ob-space-050)',
      whiteSpace: 'nowrap',
      '&:active': {
        transform: 'scale(0.98)',
      },
    }

    const resolvedVariant: GlassButtonVariant = variant

    const variantSx: SxProps<Theme> =
      resolvedVariant === 'primary' || resolvedVariant === 'contained'
        ? {
            background: 'var(--ob-gradient-brand)',
            color: 'var(--ob-color-text-inverse)',
            border: 'none',
            boxShadow: 'var(--ob-shadow-glow-brand)',
            '&:hover': {
              background: 'var(--ob-gradient-brand-hover)',
              boxShadow: 'var(--ob-shadow-glow-brand-strong)',
              transform: 'translateY(-1px)',
            },
            '&::after': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: '-100%',
              width: '50%',
              height: '100%',
              background:
                'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
              transform: 'skewX(-20deg)',
              transition: 'none',
            },
            '&:hover::after': {
              left: '200%',
              transition: 'left 0.7s ease-in-out',
            },
          }
        : resolvedVariant === 'secondary' || resolvedVariant === 'outlined'
          ? {
              background: 'var(--ob-surface-glass-1)',
              color: 'var(--ob-color-text-primary)',
              border: '1px solid var(--ob-border-glass-strong)',
              backdropFilter: 'blur(var(--ob-blur-xs))',
              '&:hover': {
                background: 'var(--ob-surface-glass-2)',
                borderColor: 'var(--ob-color-text-primary)',
                transform: 'translateY(-1px)',
                boxShadow: 'var(--ob-shadow-sm)',
              },
            }
          : resolvedVariant === 'ghost' || resolvedVariant === 'text'
            ? {
                background: 'transparent',
                color: 'var(--ob-color-text-secondary)',
                padding: '0 var(--ob-space-100)',
                '&:hover': {
                  color: 'var(--ob-color-text-primary)',
                  background: 'var(--ob-color-action-hover)',
                },
              }
            : {}

    const resolvedSx = Array.isArray(sx) ? sx : sx ? [sx] : []

    return (
      <MuiButton
        ref={ref}
        variant={muiVariant}
        size={size}
        disableElevation
        disableRipple
        sx={[commonSx, variantSx, ...resolvedSx]}
        {...props}
      />
    )
  },
)

GlassButton.displayName = 'GlassButton'
