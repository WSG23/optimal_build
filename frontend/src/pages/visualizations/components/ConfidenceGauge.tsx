import { Box, Typography, Tooltip, Zoom, useTheme, alpha } from '@mui/material'

export interface ConfidenceGaugeProps {
  label: string
  value: number // 0-100
  projection: string
}

export function ConfidenceGauge({
  label,
  value,
  projection,
}: ConfidenceGaugeProps) {
  const theme = useTheme()

  // Color logic
  let color = theme.palette.error.main
  if (value >= 70)
    color = theme.palette.success.main // "Green/Teal"
  else if (value >= 50) color = theme.palette.warning.main // "Yellow/Orange"

  return (
    <Tooltip
      title={
        <Typography variant="caption">Projection: {projection}</Typography>
      }
      TransitionComponent={Zoom}
      arrow
      placement="top"
    >
      <Box sx={{ mb: 'var(--ob-space-200)', cursor: 'help' }}>
        <Box
          display="flex"
          justifyContent="space-between"
          mb="var(--ob-space-50)"
        >
          <Typography variant="body2" fontWeight={600}>
            {label}
          </Typography>
          <Typography variant="body2" fontWeight={700} color={color}>
            {value}%
          </Typography>
        </Box>
        <Box
          sx={{
            height: 8,
            width: '100%',
            bgcolor: alpha(theme.palette.text.disabled, 0.1),
            borderRadius: 'var(--ob-radius-sm)', // Square Cyber-Minimalism: sm for containers
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* Background dashed segments for "ruler" effect */}
          <Box
            sx={{
              position: 'absolute',
              top: '0',
              left: 0,
              right: 0,
              bottom: '0',
              backgroundImage: `linear-gradient(90deg, transparent 95%, ${theme.palette.background.paper} 95%)`,
              backgroundSize: '10% 100%',
              opacity: 0.3,
              zIndex: 1,
            }}
          />

          {/* Fill */}
          <Box
            sx={{
              height: '100%',
              width: `${value}%`,
              bgcolor: color,
              borderRadius: 'var(--ob-radius-sm)', // Square Cyber-Minimalism: sm for containers
              transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)',
              position: 'relative',
              zIndex: 2,
              boxShadow: `0 0 10px ${alpha(color, 0.5)}`, // Glow
            }}
          />
        </Box>
      </Box>
    </Tooltip>
  )
}
