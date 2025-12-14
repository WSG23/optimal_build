import {
  Button as MuiButton,
  ButtonProps as MuiButtonProps,
  styled,
} from '@mui/material'
import { forwardRef } from 'react'

export interface ButtonProps extends Omit<MuiButtonProps, 'variant'> {
  /**
   * Button variant:
   * - 'primary': Gradient background with glow (main CTAs)
   * - 'secondary': Glass surface with border
   * - 'ghost': Transparent with hover effect
   */
  variant?: 'primary' | 'secondary' | 'ghost'
  /**
   * Button size:
   * - 'sm': 32px height
   * - 'md': 40px height (default)
   * - 'lg': 48px height
   */
  size?: 'sm' | 'md' | 'lg'
  /**
   * Disable shimmer animation on primary buttons
   */
  disableShimmer?: boolean
}

const StyledButton = styled(MuiButton, {
  shouldForwardProp: (prop) => prop !== 'disableShimmer',
})<ButtonProps & { disableShimmer?: boolean }>(({
  variant,
  size,
  disableShimmer,
}) => {
  // Height mapping
  const heightMap = {
    sm: '32px',
    md: '40px',
    lg: '48px',
  }

  // Common base styles - ENFORCED 2px radius
  const common = {
    height: heightMap[size || 'md'],
    borderRadius: 'var(--ob-radius-xs)', // 2px - ENFORCED
    textTransform: 'none' as const,
    fontWeight: 'var(--ob-font-weight-semibold)',
    letterSpacing: '0.02em',
    padding: '0 var(--ob-space-150)', // 24px horizontal
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    position: 'relative' as const,
    overflow: 'hidden' as const,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 'var(--ob-space-050)',
    whiteSpace: 'nowrap' as const,
    '&:active': {
      transform: 'scale(0.98)',
    },
  }

  // Primary variant - gradient with shimmer
  if (variant === 'primary') {
    return {
      ...common,
      background:
        'linear-gradient(135deg, var(--ob-brand-600) 0%, var(--ob-brand-500) 100%)',
      color: 'var(--ob-color-text-inverse)',
      border: 'none',
      boxShadow: 'var(--ob-glow-brand-subtle)',
      '&:hover': {
        background:
          'linear-gradient(135deg, var(--ob-brand-500) 0%, var(--ob-brand-400) 100%)',
        boxShadow: 'var(--ob-glow-brand-medium)',
        transform: 'translateY(-1px)',
      },
      // Shimmer effect overlay
      ...(!disableShimmer && {
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
      }),
    }
  }

  // Secondary variant - glass with border
  if (variant === 'secondary') {
    return {
      ...common,
      background: 'var(--ob-surface-glass-1)',
      color: 'var(--ob-color-text-primary)',
      border: 'var(--ob-border-fine-strong)',
      backdropFilter: 'blur(var(--ob-blur-xs))',
      '&:hover': {
        background: 'var(--ob-surface-glass-2)',
        border: 'var(--ob-border-fine-hover)',
        transform: 'translateY(-1px)',
      },
    }
  }

  // Ghost variant - transparent
  if (variant === 'ghost') {
    return {
      ...common,
      background: 'transparent',
      color: 'var(--ob-color-text-secondary)',
      border: 'none',
      padding: '0 var(--ob-space-100)',
      '&:hover': {
        color: 'var(--ob-color-text-primary)',
        background: 'var(--ob-color-action-hover)',
      },
    }
  }

  return common
})

/**
 * Button - Square Cyber-Minimalism Action Component
 *
 * Geometry: 2px border radius (--ob-radius-xs)
 * Effects: Shimmer animation on primary, lift on hover
 *
 * Preserves the "wow" factor with gradient backgrounds and glow effects.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      disableShimmer = false,
      children,
      ...props
    },
    ref,
  ) => {
    return (
      <StyledButton
        ref={ref}
        variant={variant}
        size={size}
        disableShimmer={disableShimmer}
        disableElevation
        disableRipple
        {...props}
      >
        {children}
      </StyledButton>
    )
  },
)

Button.displayName = 'Button'
