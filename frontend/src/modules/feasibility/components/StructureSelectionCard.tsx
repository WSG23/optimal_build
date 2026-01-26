import { Box, Typography, alpha, useTheme } from '@mui/material'

interface StructureSelectionCardProps {
  value: string
  label: string
  icon: string | React.ReactNode
  selected: boolean
  onClick: () => void
  costEstimate?: string // e.g. "$1,200/sqm"
}

export function StructureSelectionCard({
  value: _value,
  label,
  icon,
  selected,
  onClick,
  costEstimate,
}: StructureSelectionCardProps) {
  const theme = useTheme()

  return (
    <Box
      onClick={onClick}
      sx={{
        position: 'relative',
        cursor: 'pointer',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 2,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--ob-space-100)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        background: selected
          ? `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.primary.main, 0.05)} 100%)`
          : 'white',
        border: `1px solid ${selected ? theme.palette.primary.main : alpha(theme.palette.divider, 0.6)}`,
        boxShadow: selected
          ? `0 8px 16px ${alpha(theme.palette.primary.main, 0.2)}`
          : '0 2px 4px var(--ob-color-table-row-alt)',
        transform: selected ? 'translateY(-2px)' : 'none',
        '&:hover': {
          borderColor: theme.palette.primary.main,
          boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.15)}`,
          transform: 'translateY(-2px)',
        },
      }}
    >
      <Typography
        variant="h3"
        sx={{ fontSize: '2rem', lineHeight: 1, mb: 'var(--ob-space-50)' }}
      >
        {icon}
      </Typography>

      <Typography
        variant="body2"
        sx={{
          fontWeight: 600,
          textAlign: 'center',
          color: selected ? 'primary.main' : 'text.primary',
        }}
      >
        {label}
      </Typography>

      {/* Cost Badge */}
      {costEstimate && (
        <Box
          sx={{
            mt: 'var(--ob-space-100)',
            px: 'var(--ob-space-100)',
            py: '0',
            borderRadius: 'var(--ob-radius-sm)',
            bgcolor: alpha(theme.palette.success.main, 0.1),
            color: 'success.dark',
            fontSize: '0.65rem',
            fontWeight: 700,
            letterSpacing: '0.02em',
          }}
        >
          {costEstimate}
        </Box>
      )}

      {/* Selection Ring (Optional 3D effect enhancement) */}
      {selected && (
        <Box
          sx={{
            position: 'absolute',
            inset: -1,
            borderRadius: 'inherit',
            border: `2px solid ${theme.palette.primary.main}`,
            pointerEvents: 'none',
            zIndex: 1,
          }}
        />
      )}
    </Box>
  )
}
