import { Box, type SxProps, type Theme } from '@mui/material'

export interface SegmentedGaugeProps {
  label: string
  value: number
  valueLabel?: string
  segments?: number
  activeColor?: string
  trackColor?: string
  sx?: SxProps<Theme>
}

export function SegmentedGauge({
  label,
  value,
  valueLabel,
  segments = 8,
  activeColor = 'var(--ob-color-neon-cyan)',
  trackColor = 'var(--ob-color-border-subtle)',
  sx,
}: SegmentedGaugeProps) {
  const clampedValue = Math.max(0, Math.min(100, value))
  const activeSegments = Math.round((clampedValue / 100) * segments)

  return (
    <Box
      role="meter"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={clampedValue}
      sx={{
        padding: 'var(--ob-space-100)',
        background: 'var(--ob-color-surface-default)',
        borderRadius: 'var(--ob-radius-xs)',
        ...sx,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 'var(--ob-space-075)',
          gap: 'var(--ob-space-075)',
        }}
      >
        <Box
          component="span"
          sx={{
            fontSize: 'var(--ob-font-size-2xs)',
            fontWeight: 'var(--ob-font-weight-bold)',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            color: 'var(--ob-text-tertiary)',
          }}
        >
          {label}
        </Box>
        <Box
          component="span"
          sx={{
            fontFamily: 'var(--ob-font-family-mono)',
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 'var(--ob-font-weight-bold)',
            color: 'var(--ob-color-text-primary)',
          }}
        >
          {valueLabel ?? `${clampedValue}%`}
        </Box>
      </Box>

      <Box sx={{ display: 'flex', gap: 'var(--ob-space-025)' }}>
        {Array.from({ length: segments }).map((_, idx) => (
          <Box
            key={idx}
            sx={{
              flex: 1,
              height: 'var(--ob-space-050)',
              background: idx < activeSegments ? activeColor : trackColor,
              borderRadius: 'var(--ob-radius-xs)',
              transition: 'background 0.2s ease',
            }}
          />
        ))}
      </Box>
    </Box>
  )
}
