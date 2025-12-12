import { Box, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'

export interface DataBlockProps {
  /**
   * Table or data grid content
   */
  children: ReactNode
  /**
   * Header content (column headers, filters)
   */
  header?: ReactNode
  /**
   * Footer content (pagination, summary)
   */
  footer?: ReactNode
  /**
   * Maximum height for scrollable content
   */
  maxHeight?: string | number
  /**
   * Show outer border
   */
  bordered?: boolean
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

/**
 * DataBlock - Table/Grid Container
 *
 * Geometry: 0px border radius (--ob-radius-none) - HARD EDGES
 * Border: 1px fine lines for table structure
 *
 * Used for data tables, grids, and structured data displays.
 * Has NO border radius - pure geometric hard edges.
 */
export function DataBlock({
  children,
  header,
  footer,
  maxHeight,
  bordered = true,
  sx = {},
}: DataBlockProps) {
  return (
    <Box
      sx={{
        borderRadius: 'var(--ob-radius-none)', // 0px - ENFORCED
        border: bordered ? 'var(--ob-border-fine-strong)' : 'none',
        background: 'var(--ob-color-bg-surface)',
        overflow: 'hidden',
        ...sx,
      }}
    >
      {/* Header */}
      {header && (
        <Box
          sx={{
            px: 'var(--ob-space-100)',
            py: 'var(--ob-space-075)',
            borderBottom: 'var(--ob-divider-strong)',
            background: 'rgba(0, 0, 0, 0.1)',
          }}
        >
          {header}
        </Box>
      )}

      {/* Content - scrollable */}
      <Box
        sx={{
          maxHeight: maxHeight,
          overflowY: maxHeight ? 'auto' : 'visible',
          overflowX: 'auto',

          // Table styling within DataBlock
          '& table': {
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: 'var(--ob-font-size-sm)',
          },

          '& thead': {
            background: 'var(--ob-color-surface-strong)',
            position: 'sticky',
            top: 0,
            zIndex: 1,
          },

          '& th': {
            color: 'var(--ob-color-text-secondary)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            fontSize: 'var(--ob-font-size-xs)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            textAlign: 'left',
            padding: 'var(--ob-space-075) var(--ob-space-100)',
            borderBottom: 'var(--ob-divider-strong)',
            whiteSpace: 'nowrap',
          },

          '& td': {
            color: 'var(--ob-color-text-primary)',
            padding: 'var(--ob-space-075) var(--ob-space-100)',
            borderBottom: 'var(--ob-divider)',
            verticalAlign: 'middle',
          },

          '& tbody tr': {
            transition: 'background 0.15s ease',

            '&:hover': {
              background: 'var(--ob-color-action-hover)',
            },

            '&:last-child td': {
              borderBottom: 'none',
            },
          },

          // Scrollbar styling
          '&::-webkit-scrollbar': {
            width: 6,
            height: 6,
          },
          '&::-webkit-scrollbar-track': {
            background: 'transparent',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'var(--ob-color-border-subtle)',
            borderRadius: 'var(--ob-radius-xs)',
          },
        }}
      >
        {children}
      </Box>

      {/* Footer */}
      {footer && (
        <Box
          sx={{
            px: 'var(--ob-space-100)',
            py: 'var(--ob-space-075)',
            borderTop: 'var(--ob-divider-strong)',
            background: 'rgba(0, 0, 0, 0.05)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          {footer}
        </Box>
      )}
    </Box>
  )
}
