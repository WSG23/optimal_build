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
   * - 'primary': Solid brand background (main CTAs)
   * - 'secondary': Surface with border
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
}

type StyledButtonProps = Omit<MuiButtonProps, 'variant' | 'size'> & {
  obVariant: ObButtonVariant
  obSize: ObButtonSize
}

const StyledButton = styled(MuiButton, {
  shouldForwardProp: (prop) => prop !== 'obVariant' && prop !== 'obSize',
})<StyledButtonProps>(({ obVariant, obSize }) => {
  // Height mapping
  const heightMap = {
    sm: '32px',
    md: '40px',
    lg: '48px',
  }

  // Padding mapping - size-proportional for visual balance
  const paddingMap = {
    sm: '0 var(--ob-space-100)', // 16px - compact inline actions
    md: '0 var(--ob-space-150)', // 24px - standard actions
    lg: '0 var(--ob-space-175)', // 28px - hero CTAs
  }

  // Common base styles - ENFORCED 2px radius
  const common = {
    height: heightMap[obSize],
    borderRadius: 'var(--ob-radius-xs)', // 2px - ENFORCED
    textTransform: 'none' as const,
    fontWeight: 'var(--ob-font-weight-semibold)',
    letterSpacing: '0.1em', // Wide tracking for precision cyber aesthetic (AI Studio recommendation)
    padding: paddingMap[obSize],
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

  // Primary variant - solid brand color
  if (obVariant === 'primary') {
    return {
      ...common,
      background: 'var(--ob-color-brand-primary)',
      color: 'var(--ob-color-bg-root)',
      border: 'none',
      '&:hover': {
        background: 'var(--ob-color-brand-primary)',
        filter: 'brightness(1.1)',
        transform: 'translateY(-1px)',
      },
    }
  }

  // Secondary variant - surface with border
  if (obVariant === 'secondary') {
    return {
      ...common,
      background: 'var(--ob-color-bg-surface)',
      color: 'var(--ob-color-text-primary)',
      border: 'var(--ob-border-fine-strong)',
      '&:hover': {
        background: 'var(--ob-color-surface-strong)',
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
 * Button - Square Minimalism Action Component
 *
 * Geometry: 2px border radius (--ob-radius-xs)
 * Effects: Lift on hover
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', children, ...props }, ref) => {
    return (
      <StyledButton
        ref={ref}
        obVariant={variant}
        obSize={size}
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
