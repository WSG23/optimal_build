import { Button, ButtonProps, styled, alpha } from '@mui/material'
import { forwardRef } from 'react'

export interface GlassButtonProps extends ButtonProps {
  /**
   * Variant of the button:
   * - 'primary': Strong gradient background with glass/glow effect
   * - 'secondary': Glass surface with border
   * - 'ghost': Transparent with hover effect
   */
  variant?:
    | 'text'
    | 'outlined'
    | 'contained'
    | 'primary'
    | 'secondary'
    | 'ghost'
  /**
   * Size of the button
   * - 'sm': 32px height
   * - 'md': 40px height (Standard)
   * - 'lg': 48px height
   */
  size?: 'small' | 'medium' | 'large'
  /**
   * Shape of the button
   */
  shape?: 'pill' | 'rounded'
}

const StyledButton = styled(Button, {
  shouldForwardProp: (prop) => prop !== 'variant' && prop !== 'shape',
})<GlassButtonProps>(({ theme, variant, size, shape }) => {
  // Map custom sizes to fixed heights
  const heightMap = {
    small: '32px',
    medium: '40px',
    large: '48px',
  }

  const radiusMap = {
    pill: '9999px',
    rounded: 'var(--ob-radius-md)',
  }

  // Common base styles
  const common = {
    height: heightMap[size || 'medium'],
    borderRadius: radiusMap[shape || 'pill'],
    textTransform: 'none',
    fontWeight: 'var(--ob-font-weight-semibold)',
    letterSpacing: 'var(--ob-letter-spacing-wider)',
    padding: '0 var(--ob-space-150)', // 24px horizontal
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

  // Variants
  if (variant === 'primary' || variant === 'contained') {
    return {
      ...common,
      background: 'var(--ob-gradient-brand)',
      color: 'var(--ob-color-text-inverse)',
      border: 'none',
      boxShadow: 'var(--ob-shadow-glow-brand)',
      '&:hover': {
        background: 'var(--ob-gradient-brand-hover)',
        boxShadow: 'var(--ob-shadow-glow-brand-strong)',
        transform: 'translateY(-1px)',
      },
      // Shimmer effect overlay
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
  }

  if (variant === 'secondary' || variant === 'outlined') {
    return {
      ...common,
      background: 'var(--ob-surface-glass-1)',
      color: 'var(--ob-color-text-primary)',
      border: '1px solid var(--ob-border-glass-strong)',
      backdropFilter: 'blur(8px)',
      '&:hover': {
        background: 'var(--ob-surface-glass-2)',
        borderColor: 'var(--ob-color-text-primary)',
        transform: 'translateY(-1px)',
        boxShadow: 'var(--ob-shadow-sm)',
      },
    }
  }

  if (variant === 'ghost' || variant === 'text') {
    return {
      ...common,
      background: 'transparent',
      color: 'var(--ob-color-text-secondary)',
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
 * GlassButton - Standardized Premium Action Component
 *
 * Implements the "Wow" factor with gradients, glows, and glass effects.
 * Enforces strict sizing (40px standard) and shape (pill/rounded).
 */
export const GlassButton = forwardRef<HTMLButtonElement, GlassButtonProps>(
  (
    {
      variant = 'primary',
      size = 'medium',
      shape = 'pill',
      children,
      ...props
    },
    ref,
  ) => {
    return (
      <StyledButton
        ref={ref}
        variant={variant as any} // MUI types compatibility
        size={size}
        shape={shape}
        disableElevation
        disableRipple // We handle active state via CSS transform
        {...props}
      >
        {children}
      </StyledButton>
    )
  },
)
