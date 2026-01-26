import {
  Box,
  Typography,
  useTheme,
  alpha,
  Fade,
  Paper,
  IconButton,
} from '@mui/material'
import { useState } from 'react'
import CloseIcon from '@mui/icons-material/Close'

export interface Correlation {
  id: string
  driver: string
  outcome: string
  coefficient: number // -1 to 1
  pValue: number
}

export interface CorrelationHeatmapProps {
  data: Correlation[]
}

export function CorrelationHeatmap({ data }: CorrelationHeatmapProps) {
  const theme = useTheme()
  const [selectedCorrelation, setSelectedCorrelation] =
    useState<Correlation | null>(null)

  // Unique factors for building full N x N matrix (future feature)
  // const drivers = Array.from(new Set(data.map(d => d.driver)));
  // const outcomes = Array.from(new Set(data.map(d => d.outcome)));

  // Simple 1D list view transformation to "Heatmap" style grid if possible,
  // but typically correlation matrices are symmetric N x N.
  // Assuming 'data' contains the significant pairs.
  // To allow for a nice "Grid", we'll just map the pairs into a flex-wrap layout
  // because a full N x N matrix might be sparse if only significant ones are passed.
  // The user request asked for a "Grid of colored squares".

  const getColor = (coeff: number) => {
    // -1 (Red) -> 0 ( Transparent/Grey) -> 1 (Blue)
    if (coeff > 0) return alpha(theme.palette.info.main, Math.abs(coeff))
    return alpha(theme.palette.error.main, Math.abs(coeff))
  }

  return (
    <Box
      display="flex"
      gap="var(--ob-space-200)"
      sx={{ position: 'relative', minHeight: 400 }}
    >
      {/* Heatmap Grid Area */}
      <Box flex={1}>
        <Typography
          variant="subtitle2"
          gutterBottom
          sx={{
            color: 'text.secondary',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
          }}
        >
          Correlation Matrix (Significant Pairs)
        </Typography>

        <Box display="flex" flexWrap="wrap" gap="var(--ob-space-100)">
          {data.map((item) => (
            <Box
              key={item.id}
              onClick={() => setSelectedCorrelation(item)}
              sx={{
                width: 60,
                height: 60,
                bgcolor: getColor(item.coefficient),
                borderRadius: 'var(--ob-radius-xs)', // Square Cyber-Minimalism: xs for small elements
                cursor: 'pointer',
                transition: 'transform 0.2s',
                border:
                  selectedCorrelation?.id === item.id
                    ? `2px solid ${theme.palette.primary.main}`
                    : '1px solid transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                '&:hover': {
                  transform: 'scale(1.1)',
                  zIndex: 10,
                  boxShadow: theme.shadows[4],
                },
              }}
            >
              <Typography
                variant="caption"
                fontWeight="bold"
                sx={{
                  color: 'var(--ob-color-text-inverse)',
                  textShadow: '0 1px 2px rgba(0 0 0 / 0.8)',
                }}
              >
                {item.coefficient.toFixed(1)}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>

      {/* Interaction Side Panel */}
      {selectedCorrelation && (
        <Fade in={!!selectedCorrelation}>
          <Paper
            elevation={6}
            sx={{
              width: 300,
              p: 'var(--ob-space-300)',
              borderRadius: 'var(--ob-radius-sm)', // Square Cyber-Minimalism: sm for panels
              bgcolor: alpha(theme.palette.background.paper, 0.8),
              backdropFilter: 'blur(var(--ob-blur-lg))',
              borderLeft: `4px solid ${getColor(selectedCorrelation.coefficient)}`,
            }}
          >
            <Box
              display="flex"
              justifyContent="space-between"
              mb="var(--ob-space-200)"
            >
              <Typography variant="h6" fontSize="1rem" fontWeight={700}>
                Correlation Detail
              </Typography>
              <IconButton
                size="small"
                onClick={() => setSelectedCorrelation(null)}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>

            <Typography variant="caption" color="text.secondary">
              DRIVER
            </Typography>
            <Typography variant="body1" fontWeight={600} gutterBottom>
              {selectedCorrelation.driver}
            </Typography>

            <Box my="var(--ob-space-200)" textAlign="center">
              <Typography
                variant="h4"
                fontWeight={800}
                sx={{
                  color: getColor(selectedCorrelation.coefficient),
                  filter: 'brightness(1.2)',
                }}
              >
                {selectedCorrelation.coefficient > 0 ? '+' : ''}
                {selectedCorrelation.coefficient.toFixed(2)}
              </Typography>
              <Typography variant="caption">Correlation Coefficient</Typography>
            </Box>

            <Typography variant="caption" color="text.secondary">
              AFFECTS
            </Typography>
            <Typography variant="body1" fontWeight={600} gutterBottom>
              {selectedCorrelation.outcome}
            </Typography>

            <Typography
              variant="body2"
              sx={{
                mt: 'var(--ob-space-200)',
                p: 'var(--ob-space-150)',
                bgcolor: alpha(theme.palette.action.hover, 0.05),
                borderRadius: 'var(--ob-radius-sm)', // Square Cyber-Minimalism: sm for panels
              }}
            >
              {selectedCorrelation.coefficient > 0
                ? 'Strong positive correlation. Increasing the driver likely increases the outcome.'
                : 'Negative correlation. Increasing the driver likely decreases the outcome.'}
            </Typography>
          </Paper>
        </Fade>
      )}
    </Box>
  )
}
