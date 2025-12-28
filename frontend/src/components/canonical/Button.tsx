import {
  Button as MuiButton,
  ButtonProps as MuiButtonProps,
  styled,
} from '@mui/material'
import { forwardRef } from 'react'

type ObButtonVariant = 'primary' | 'secondary' | 'ghost'
type ObButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends Omit<MuiButtonProps, 'variant' | 'size'> {
  /**
   * Button variant:
   * - 'primary': Gradient background with glow (main CTAs)
   * - 'secondary': Glass surface with border
   * - 'ghost': Transparent with hover effect
   */
  variant?: ObButtonVariant
  /**
   * Button size:
   * - 'sm': 32px height
   * - 'md': 40px height (default)
   * - 'lg': 48px height
   */
  size?: ObButtonSize
  /**
   * Disable shimmer animation on primary buttons
   */
  disableShimmer?: boolean
}

type StyledButtonProps = Omit<MuiButtonProps, 'variant' | 'size'> & {
  obVariant: ObButtonVariant
  obSize: ObButtonSize
  disableShimmer?: boolean
}

const StyledButton = styled(MuiButton, {
  shouldForwardProp: (prop) =>
    prop !== 'disableShimmer' && prop !== 'obVariant' && prop !== 'obSize',
})<StyledButtonProps>(({ obVariant, obSize, disableShimmer }) => {
  // Height mapping
  const heightMap = {
    sm: '32px',
    md: '40px',
    lg: '48px',
  }

  // Common base styles - ENFORCED 2px radius
  const common = {
    height: heightMap[obSize],
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

  // Primary variant - cyan gradient with shimmer (premium cyber aesthetic)
  if (obVariant === 'primary') {
    return {
      ...common,
      background:
        'linear-gradient(135deg, #0096cc 0%, var(--ob-color-neon-cyan) 100%)',
      color: '#0a1628', // Dark text for contrast on bright cyan
      border: 'none',
      boxShadow: 'var(--ob-glow-neon-cyan)',
      '&:hover': {
        background:
          'linear-gradient(135deg, var(--ob-color-neon-cyan) 0%, #0096cc 100%)',
        boxShadow: 'var(--ob-glow-neon-cyan-strong)',
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
  if (obVariant === 'secondary') {
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
  if (obVariant === 'ghost') {
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
        obVariant={variant}
        obSize={size}
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
