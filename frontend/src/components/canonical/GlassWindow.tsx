import { Box, IconButton, Modal, Paper, Typography } from '@mui/material'
import { Close } from '@mui/icons-material'
import { ReactNode } from 'react'
import { GlassCard } from './GlassCard'

export interface GlassWindowProps {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: string
  children: ReactNode
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | number
  /**
   * If true, renders as a standalone panel in the page flow instead of a modal.
   */
  inline?: boolean
}

/**
 * GlassWindow - Standardized Content Container
 *
 * Can represent a floating Modal ("Window") or an inline Panel.
 * Enforces consistent header styling and content padding.
 */
export function GlassWindow({
  open,
  onClose,
  title,
  subtitle,
  children,
  maxWidth = 'md',
  inline = false,
}: GlassWindowProps) {
  const content = (
    <GlassCard
      variant="glass-heavy"
      className="glass-window animate-entrance"
      sx={{
        width: '100%',
        maxWidth: maxWidth,
        outline: 'none',
        display: 'flex',
        flexDirection: 'column',
        maxHeight: inline ? 'none' : '90vh',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 'var(--ob-space-150)', // 24px
          borderBottom: '1px solid var(--ob-color-border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          background: 'rgba(0,0,0,0.1)', // Subtle darken for header
        }}
      >
        <Box>
          <Typography
            variant="h5"
            sx={{
              color: 'var(--ob-color-text-primary)',
              fontWeight: 'var(--ob-font-weight-bold)',
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
                mt: 0.5,
              }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>
        <IconButton
          onClick={onClose}
          sx={{
            color: 'var(--ob-color-text-secondary)',
            '&:hover': {
              color: 'var(--ob-color-text-primary)',
              background: 'var(--ob-surface-glass-2)',
            },
          }}
        >
          <Close />
        </IconButton>
      </Box>

      {/* Content */}
      <Box
        sx={{
          p: 'var(--ob-space-150)', // 24px
          overflowY: 'auto',
          flex: 1,
        }}
      >
        {children}
      </Box>
    </GlassCard>
  )

  if (inline) {
    if (!open) return null
    return content
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        backdropFilter: 'blur(var(--ob-blur-sm))', // Extra blurred backdrop for focus
      }}
    >
      {/* Modal wrapper primarily for positioning, content handles the look */}
      <Box
        sx={{
          outline: 'none',
          width: '100%',
          maxWidth,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        {content}
      </Box>
    </Modal>
  )
}
