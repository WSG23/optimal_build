import {
  Box,
  IconButton,
  Modal,
  Typography,
  SxProps,
  Theme,
} from '@mui/material'
import { Close } from '@mui/icons-material'
import { ReactNode } from 'react'
import { Card } from './Card'

export interface WindowProps {
  /**
   * Control visibility
   */
  open: boolean
  /**
   * Close handler
   */
  onClose: () => void
  /**
   * Window title
   */
  title: string
  /**
   * Window subtitle (optional)
   */
  subtitle?: string
  /**
   * Window content
   */
  children: ReactNode
  /**
   * Maximum width
   */
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | number
  /**
   * Render as inline panel instead of modal
   */
  inline?: boolean
  /**
   * Hide close button
   */
  hideClose?: boolean
  /**
   * Footer content (actions, buttons)
   */
  footer?: ReactNode
  /**
   * Additional styles for the window container
   */
  sx?: SxProps<Theme>
}

const maxWidthMap = {
  sm: '480px',
  md: '640px',
  lg: '800px',
  xl: '1024px',
}

/**
 * Window - Modal/Panel Container
 *
 * Geometry: 8px border radius (--ob-radius-lg) - ONLY component with lg radius
 * Border: 1px fine line strong
 * Effects: Backdrop blur, entrance animation
 *
 * Can render as floating modal or inline panel.
 */
export function Window({
  open,
  onClose,
  title,
  subtitle,
  children,
  maxWidth = 'md',
  inline = false,
  hideClose = false,
  footer,
  sx = {},
}: WindowProps) {
  const resolvedMaxWidth =
    typeof maxWidth === 'number' ? `${maxWidth}px` : maxWidthMap[maxWidth]

  const content = (
    <Card
      variant="glass"
      hover="none"
      animated
      sx={{
        width: '100%',
        maxWidth: resolvedMaxWidth,
        borderRadius: 'var(--ob-radius-lg)', // 8px - Windows get larger radius
        border: 'var(--ob-border-fine-strong)',
        background: 'var(--ob-surface-glass-2)',
        backdropFilter: 'blur(var(--ob-blur-lg))',
        WebkitBackdropFilter: 'blur(var(--ob-blur-lg))',
        display: 'flex',
        flexDirection: 'column',
        maxHeight: inline ? 'none' : '90vh',
        outline: 'none',
        boxShadow: 'var(--ob-shadow-glass-lg)',
        ...sx,
      }}
    >
      {/* Header */}
      <Box
        sx={{
          px: 'var(--ob-space-150)',
          py: 'var(--ob-space-100)',
          borderBottom: 'var(--ob-divider-strong)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          background: 'rgba(0, 0, 0, 0.15)',
        }}
      >
        <Box sx={{ flex: 1, pr: hideClose ? 0 : 2 }}>
          <Typography
            variant="h5"
            sx={{
              color: 'var(--ob-color-text-primary)',
              fontWeight: 'var(--ob-font-weight-bold)',
              fontSize: 'var(--ob-font-size-xl)',
              lineHeight: 1.2,
              letterSpacing: '-0.01em',
            }}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography
              variant="body2"
              sx={{
                color: 'var(--ob-color-text-secondary)',
                mt: 'var(--ob-space-025)',
                fontSize: 'var(--ob-font-size-sm)',
              }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>
        {!hideClose && (
          <IconButton
            onClick={onClose}
            size="small"
            sx={{
              color: 'var(--ob-color-text-secondary)',
              borderRadius: 'var(--ob-radius-xs)', // 2px for buttons
              '&:hover': {
                color: 'var(--ob-color-text-primary)',
                background: 'var(--ob-surface-glass-1)',
              },
            }}
          >
            <Close fontSize="small" />
          </IconButton>
        )}
      </Box>

      {/* Content */}
      <Box
        sx={{
          p: 'var(--ob-space-150)',
          overflowY: 'auto',
          flex: 1,
        }}
      >
        {children}
      </Box>

      {/* Footer (optional) */}
      {footer && (
        <Box
          sx={{
            px: 'var(--ob-space-150)',
            py: 'var(--ob-space-100)',
            borderTop: 'var(--ob-divider-strong)',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 'var(--ob-space-075)',
            background: 'rgba(0, 0, 0, 0.1)',
          }}
        >
          {footer}
        </Box>
      )}
    </Card>
  )

  // Inline mode - render directly
  if (inline) {
    if (!open) return null
    return content
  }

  // Modal mode - wrap in Modal
  return (
    <Modal
      open={open}
      onClose={onClose}
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 'var(--ob-space-100)',
        backdropFilter: 'blur(var(--ob-blur-sm))',
      }}
    >
      <Box
        sx={{
          outline: 'none',
          width: '100%',
          maxWidth: resolvedMaxWidth,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        {content}
      </Box>
    </Modal>
  )
}
