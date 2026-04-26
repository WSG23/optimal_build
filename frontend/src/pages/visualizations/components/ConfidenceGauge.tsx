import { Box, Typography, Tooltip } from '@mui/material'

export interface ConfidenceGaugeProps {
  label: string
  value: number // 0-100
  projection: number
  baseline?: number
}

/** Returns a design-token color based on confidence threshold */
function getConfidenceColor(value: number): string {
  if (value >= 70) return 'var(--ob-success-500)'
  if (value >= 50) return 'var(--ob-warning-500)'
  return 'var(--ob-error-500)'
}

export function ConfidenceGauge({
  label,
  value,
  projection,
  baseline,
}: ConfidenceGaugeProps) {
  const color = getConfidenceColor(value)
  const delta =
    baseline && baseline > 0
      ? `${(((projection - baseline) / baseline) * 100).toFixed(0)}% uplift`
      : undefined

  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="caption" sx={{ display: 'block' }}>
            Projection: {projection}
          </Typography>
          {delta && (
            <Typography variant="caption" sx={{ display: 'block' }}>
              {delta} vs baseline ({baseline})
            </Typography>
          )}
        </Box>
      }
      arrow
      placement="top"
    >
      <Box sx={{ py: 'var(--ob-space-075)', cursor: 'help' }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            mb: 'var(--ob-space-050)',
          }}
        >
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 'var(--ob-font-weight-semibold)',
              color: 'var(--ob-color-text-primary)',
            }}
          >
            {label}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 'var(--ob-font-weight-bold)',
              fontFamily: 'var(--ob-font-family-mono)',
              color,
            }}
          >
            {value}%
          </Typography>
        </Box>
        <Box
          sx={{
            height: 'var(--ob-space-050)',
            width: '100%',
            background: 'var(--ob-color-border-subtle)',
            borderRadius: 'var(--ob-radius-xs)',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* Fill bar using transform for GPU-accelerated animation */}
          <Box
            sx={{
              height: '100%',
              width: '100%',
              background: color,
              borderRadius: 'var(--ob-radius-xs)',
              transformOrigin: 'left',
              transform: `scaleX(${String(value / 100)})`,
              transition: 'transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          />
        </Box>
      </Box>
    </Tooltip>
  )
}
