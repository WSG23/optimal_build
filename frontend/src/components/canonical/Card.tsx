import { Box, SxProps, Theme } from '@mui/material'
import { forwardRef, ReactNode } from 'react'

export interface CardProps {
  children: ReactNode
  /**
   * Visual variant:
   * - 'default': Solid surface background
   * - 'glass': Glassmorphism with backdrop blur
   * - 'ghost': Minimal, border only
   */
  variant?: 'default' | 'glass' | 'ghost'
  /**
   * Hover effect:
   * - 'none': No hover effect
   * - 'subtle': Slight border highlight
   * - 'lift': Lift with shadow
   */
  hover?: 'none' | 'subtle' | 'lift'
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
    }

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

    return (
      <Box
        ref={ref}
        className={className}
        onClick={onClick}
        sx={{
          ...baseStyles,
          ...variantStyles[variant],
          ...hoverStyles[hover],
          ...animationStyles,
          ...sx,
        }}
      >
        {children}
      </Box>
    )
  },
)

Card.displayName = 'Card'
