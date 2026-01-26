import { Box, Typography } from '@mui/material'
import { BarChart } from '@mui/icons-material'

interface ChartPlaceholderProps {
  height?: number | string
  label?: string
  subLabel?: string
}

export function ChartPlaceholder({
  height = 300,
  label = 'No Data Available',
  subLabel = 'Connect data source to visualize trends',
}: ChartPlaceholderProps) {
  return (
    <Box
      sx={{
        height: height,
        width: '100%',
        position: 'relative',
        bgcolor: 'background.paper',
        borderRadius: 'var(--ob-radius-sm)',
        border: '1px dashed',
        borderColor: 'divider',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Wireframe Background */}
      <Box
        sx={{
          position: 'absolute',
          inset: 0,
          opacity: 0.05,
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-around',
          padding: 4,
          pointerEvents: 'none',
        }}
      >
        {[40, 70, 50, 90, 60, 80, 45].map((h, i) => (
          <Box
            key={i}
            sx={{
              width: '8%',
              height: `${h}%`,
              bgcolor: 'text.primary',
              borderRadius: '4px 4px 0 0',
            }}
          />
        ))}
      </Box>

      {/* Content Overlay */}
      <Box sx={{ textAlign: 'center', zIndex: 1, p: 'var(--ob-space-200)' }}>
        <Box
          sx={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            bgcolor: 'action.hover',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px auto',
            color: 'text.secondary',
          }}
        >
          <BarChart fontSize="large" />
        </Box>
        <Typography variant="h6" color="text.primary" gutterBottom>
          {label}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {subLabel}
        </Typography>
      </Box>
    </Box>
  )
}
