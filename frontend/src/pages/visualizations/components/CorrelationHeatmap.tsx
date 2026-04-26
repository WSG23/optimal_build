import { Box, Typography, IconButton, Tooltip } from '@mui/material'
import { useState, useMemo } from 'react'
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
  /** Minimum absolute coefficient to show (filter) */
  minStrength?: number
}

/** Returns a design-token-based color for correlation strength */
function getCellColor(coeff: number): string {
  const abs = Math.abs(coeff)
  if (coeff > 0) {
    if (abs > 0.6) return 'var(--ob-info-500)'
    if (abs > 0.3) return 'var(--ob-info-400)'
    return 'var(--ob-info-300)'
  }
  if (abs > 0.6) return 'var(--ob-error-500)'
  if (abs > 0.3) return 'var(--ob-error-400)'
  return 'var(--ob-error-300)'
}

function getSignificanceLabel(pValue: number): string {
  if (pValue < 0.01) return 'Highly significant'
  if (pValue < 0.05) return 'Significant'
  return 'Marginal'
}

export function CorrelationHeatmap({
  data,
  minStrength = 0,
}: CorrelationHeatmapProps) {
  const [selectedCorrelation, setSelectedCorrelation] =
    useState<Correlation | null>(null)

  const filteredData = useMemo(
    () => data.filter((d) => Math.abs(d.coefficient) >= minStrength),
    [data, minStrength],
  )

  // Sort by absolute coefficient descending for most important first
  const sortedData = useMemo(
    () =>
      [...filteredData].sort(
        (a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient),
      ),
    [filteredData],
  )

  return (
    <Box sx={{ position: 'relative', minHeight: 200 }}>
      {/* Correlation pairs as a structured list (more useful than colored squares) */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-050)',
        }}
      >
        {sortedData.map((item) => {
          const isSelected = selectedCorrelation?.id === item.id
          const color = getCellColor(item.coefficient)

          return (
            <Box
              key={item.id}
              onClick={() => {
                setSelectedCorrelation(isSelected ? null : item)
              }}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
                p: 'var(--ob-space-075)',
                borderRadius: 'var(--ob-radius-xs)',
                border: isSelected
                  ? 'var(--ob-border-fine-hover)'
                  : 'var(--ob-border-fine)',
                background: isSelected
                  ? 'var(--ob-color-surface-strong)'
                  : 'transparent',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                '&:hover': {
                  background: 'var(--ob-color-surface-strong)',
                },
              }}
            >
              {/* Coefficient badge */}
              <Box
                sx={{
                  minWidth: 48,
                  textAlign: 'center',
                  fontFamily: 'var(--ob-font-family-mono)',
                  fontSize: 'var(--ob-font-size-sm)',
                  fontWeight: 'var(--ob-font-weight-bold)',
                  color,
                }}
              >
                {item.coefficient > 0 ? '+' : ''}
                {item.coefficient.toFixed(2)}
              </Box>

              {/* Driver → Outcome */}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-sm)',
                    fontWeight: 'var(--ob-font-weight-medium)',
                    color: 'var(--ob-color-text-primary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {item.driver}
                </Typography>
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-xs)',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  → {item.outcome}
                </Typography>
              </Box>

              {/* p-value */}
              <Tooltip title={`p = ${item.pValue.toFixed(3)}`} arrow>
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-2xs)',
                    color: 'var(--ob-color-text-muted)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {getSignificanceLabel(item.pValue)}
                </Typography>
              </Tooltip>
            </Box>
          )
        })}
      </Box>

      {/* Detail panel */}
      {selectedCorrelation && (
        <Box
          sx={{
            mt: 'var(--ob-space-150)',
            p: 'var(--ob-space-150)',
            borderRadius: 'var(--ob-radius-sm)',
            background: 'var(--ob-color-bg-surface-elevated)',
            border: 'var(--ob-border-fine-strong)',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              mb: 'var(--ob-space-100)',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-base)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                color: 'var(--ob-color-text-primary)',
              }}
            >
              Correlation Detail
            </Typography>
            <IconButton
              size="small"
              onClick={() => {
                setSelectedCorrelation(null)
              }}
              sx={{ color: 'var(--ob-color-text-muted)' }}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>

          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-075)',
            }}
          >
            <Box>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-2xs)',
                  textTransform: 'uppercase',
                  letterSpacing: 'var(--ob-letter-spacing-wider)',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                Driver
              </Typography>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  color: 'var(--ob-color-text-primary)',
                }}
              >
                {selectedCorrelation.driver}
              </Typography>
            </Box>

            <Box sx={{ textAlign: 'center', py: 'var(--ob-space-075)' }}>
              <Typography
                sx={{
                  fontFamily: 'var(--ob-font-family-mono)',
                  fontSize: 'var(--ob-font-size-2xl)',
                  fontWeight: 'var(--ob-font-weight-bold)',
                  color: getCellColor(selectedCorrelation.coefficient),
                }}
              >
                {selectedCorrelation.coefficient > 0 ? '+' : ''}
                {selectedCorrelation.coefficient.toFixed(2)}
              </Typography>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                Correlation coefficient &middot; p ={' '}
                {selectedCorrelation.pValue.toFixed(3)}
              </Typography>
            </Box>

            <Box>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-2xs)',
                  textTransform: 'uppercase',
                  letterSpacing: 'var(--ob-letter-spacing-wider)',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                Affects
              </Typography>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  color: 'var(--ob-color-text-primary)',
                }}
              >
                {selectedCorrelation.outcome}
              </Typography>
            </Box>

            <Typography
              sx={{
                mt: 'var(--ob-space-075)',
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-secondary)',
                fontStyle: 'italic',
              }}
            >
              {selectedCorrelation.coefficient > 0
                ? 'Positive correlation — increasing the driver metric tends to increase the outcome.'
                : 'Negative correlation — increasing the driver metric tends to decrease the outcome.'}{' '}
              {getSignificanceLabel(selectedCorrelation.pValue)} at p ={' '}
              {selectedCorrelation.pValue.toFixed(3)}.
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  )
}
