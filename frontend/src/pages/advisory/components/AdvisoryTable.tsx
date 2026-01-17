import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  alpha,
  useTheme,
} from '@mui/material'
import type { ReactNode } from 'react'

interface Column {
  id: string
  label: string
  align?: 'left' | 'right' | 'center'
  width?: string | number
}

interface AdvisoryTableProps {
  columns: Column[]
  children: ReactNode
}

export function AdvisoryTable({ columns, children }: AdvisoryTableProps) {
  const theme = useTheme()

  return (
    <TableContainer
      component={Paper}
      sx={{
        background: 'transparent',
        boxShadow: 'none',
        borderRadius: 0,
        overflow: 'hidden',
      }}
    >
      <Table size="small">
        <TableHead>
          <TableRow>
            {columns.map((col) => (
              <TableCell
                key={col.id}
                align={col.align || 'left'}
                sx={{
                  color: 'var(--ob-color-text-secondary)',
                  fontSize: 'var(--ob-font-size-xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                  height: 48,
                  width: col.width,
                  fontWeight: 600,
                  bgcolor: alpha(theme.palette.background.paper, 0.2),
                }}
              >
                {col.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody
          sx={{
            '& tr:last-child td': {
              borderBottom: 0,
            },
            '& td': {
              borderColor: alpha(theme.palette.divider, 0.05),
              color: 'var(--ob-color-text-primary)',
              fontSize: 'var(--ob-font-size-sm)',
              height: 44,
            },
          }}
        >
          {children}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
