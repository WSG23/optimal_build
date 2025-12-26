import { Box, SxProps, Theme } from '@mui/material'
import { forwardRef, ReactNode } from 'react'

export interface CardProps {
  children: ReactNode
  /**
   * Visual variant:
   * - 'default': Solid surface background
   * - 'glass': Glassmorphism with backdrop blur
   * - 'ghost': Minimal, border only
   * - 'premium': Premium dark glass with stronger blur (cyber aesthetic)
   */
  variant?: 'default' | 'glass' | 'ghost' | 'premium'
  /**
   * Hover effect:
   * - 'none': No hover effect
   * - 'subtle': Slight border highlight
   * - 'lift': Lift with shadow
   * - 'glow': Neon cyan border glow (cyber aesthetic)
   */
  hover?: 'none' | 'subtle' | 'lift' | 'glow'
  /**
   * Show gradient accent border on top (cyber aesthetic)
   */
  accent?: boolean
  /**
   * Enable entrance animation
   */
  animated?: boolean
  /**
   * Click handler - makes card interactive
   */
  onClick?: () => void
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
  className?: string
}

/**
 * Card - Square Cyber-Minimalism Base Container
 *
 * Geometry: 4px border radius (--ob-radius-sm)
 * Border: 1px fine line at low opacity
 * Effects: Optional glassmorphism, lift on hover
 */
export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      variant = 'default',
      hover = 'subtle',
      accent = false,
      animated = false,
      onClick,
      sx = {},
      className,
    },
    ref,
  ) => {
    // Base styles - enforced square geometry
    const baseStyles: SxProps<Theme> = {
      borderRadius: 'var(--ob-radius-sm)', // 4px - ENFORCED
      border: 'var(--ob-border-fine)',
      overflow: 'hidden',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      cursor: onClick ? 'pointer' : 'default',
    }

    // Variant styles
    const variantStyles: Record<string, SxProps<Theme>> = {
      default: {
        background: 'var(--ob-color-bg-surface)',
      },
      glass: {
        background: 'var(--ob-surface-glass-1)',
        backdropFilter: 'blur(var(--ob-blur-md))',
        WebkitBackdropFilter: 'blur(var(--ob-blur-md))',
      },
      ghost: {
        background: 'transparent',
        border: 'var(--ob-border-fine-strong)',
      },
      premium: {
        background: 'var(--ob-surface-premium)',
        backdropFilter: 'blur(var(--ob-blur-xl))',
        WebkitBackdropFilter: 'blur(var(--ob-blur-xl))',
      },
    }

    // Hover styles
    const hoverStyles: Record<string, SxProps<Theme>> = {
      none: {},
      subtle: {
        '&:hover': {
          border: 'var(--ob-border-fine-hover)',
        },
      },
      lift: {
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 'var(--ob-shadow-md)',
          border: 'var(--ob-border-fine-hover)',
        },
      },
      glow: {
        '&:hover': {
          borderColor: 'var(--ob-color-neon-cyan)',
          boxShadow: 'var(--ob-glow-neon-cyan)',
        },
      },
    }

    // Accent styles (gradient top border)
    const accentStyles: SxProps<Theme> = accent
      ? {
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '2px',
            background: 'var(--ob-gradient-accent-fade)',
            borderRadius: 'var(--ob-radius-sm) var(--ob-radius-sm) 0 0',
          },
        }
      : {}

    // Animation styles
    const animationStyles: SxProps<Theme> = animated
      ? {
          animation: 'cardEntrance 0.4s ease-out',
          '@keyframes cardEntrance': {
            '0%': {
              opacity: 0,
              transform: 'translateY(8px)',
            },
            '100%': {
              opacity: 1,
              transform: 'translateY(0)',
            },
          },
        }
      : {}

    const resolvedSx = Array.isArray(sx) ? sx : [sx]

    return (
      <Box
        ref={ref}
        className={className}
        onClick={onClick}
        sx={[
          baseStyles,
          variantStyles[variant],
          hoverStyles[hover],
          accentStyles,
          animationStyles,
          ...resolvedSx,
        ]}
      >
        {children}
      </Box>
    )
  },
)

Card.displayName = 'Card'
