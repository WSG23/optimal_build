/**
 * Massing Layers Panel Component
 *
 * Compact layer control panel for Development Preview.
 * Shows layer visibility toggles, height info, and focus controls.
 *
 * Design Principles:
 * - No allocation duplication (PreviewLayersTable handles that)
 * - Square Cyber-Minimalism: 4px radius cards, 2px radius buttons
 * - Functional Color Language: Cyan for focus state
 */

import { Box, IconButton, Typography, Stack } from '@mui/material'
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
} from '@mui/icons-material'

import { Button } from '../../../../components/canonical/Button'
import type { PreviewLayerMetadata } from '../previewMetadata'

export interface MassingLayersPanelProps {
  /** Layer metadata from preview job */
  layers: PreviewLayerMetadata[]
  /** Visibility state per layer ID */
  visibility: Record<string, boolean>
  /** Currently focused layer ID */
  focusLayerId: string | null
  /** Toggle layer visibility */
  onToggleVisibility: (layerId: string) => void
  /** Focus on a specific layer */
  onFocus: (layerId: string) => void
  /** Reset focus (show all) */
  onResetFocus: () => void
}

/**
 * Format height in meters for display
 */
function formatHeight(meters: number | null | undefined): string {
  if (meters == null) return '—'
  return `${meters.toFixed(1)}m`
}

export function MassingLayersPanel({
  layers,
  visibility,
  focusLayerId,
  onToggleVisibility,
  onFocus,
  onResetFocus,
}: MassingLayersPanelProps) {
  if (layers.length === 0) {
    return null
  }

  return (
    <Box
      className="massing-layers-panel"
      sx={{
        bgcolor: 'var(--ob-color-surface-elevated)',
        borderRadius: 'var(--ob-radius-sm)',
        border: '1px solid var(--ob-color-border-subtle)',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 'var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography
          variant="overline"
          sx={{
            fontWeight: 700,
            letterSpacing: '0.1em',
            color: 'text.secondary',
          }}
        >
          Massing Layers
        </Typography>
        {focusLayerId && (
          <Button variant="ghost" size="sm" onClick={onResetFocus}>
            Show All
          </Button>
        )}
      </Box>

      {/* Layer List */}
      <Stack spacing={0} sx={{ maxHeight: 300, overflowY: 'auto' }}>
        {layers.map((layer) => {
          const layerId = layer.id
          const isVisible = visibility[layerId] !== false
          const isFocused = focusLayerId === layerId
          const heightM = layer.metrics?.heightM ?? null

          return (
            <Box
              key={layerId}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-050)',
                p: 'var(--ob-space-075) var(--ob-space-100)',
                borderBottom: '1px solid var(--ob-color-border-subtle)',
                bgcolor: isFocused
                  ? 'color-mix(in srgb, var(--ob-color-neon-cyan) 10%, transparent)'
                  : 'transparent',
                transition: 'background 0.15s ease',
                '&:last-child': {
                  borderBottom: 'none',
                },
                '&:hover': {
                  bgcolor: isFocused
                    ? 'color-mix(in srgb, var(--ob-color-neon-cyan) 15%, transparent)'
                    : 'var(--ob-color-surface-hover)',
                },
              }}
            >
              {/* Visibility Toggle */}
              <IconButton
                size="small"
                onClick={() => onToggleVisibility(layerId)}
                sx={{
                  color: isVisible ? 'text.primary' : 'text.disabled',
                  p: 'var(--ob-space-025)',
                }}
              >
                {isVisible ? (
                  <VisibilityIcon sx={{ fontSize: 18 }} />
                ) : (
                  <VisibilityOffIcon sx={{ fontSize: 18 }} />
                )}
              </IconButton>

              {/* Layer Info */}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 600,
                    color: isVisible ? 'text.primary' : 'text.disabled',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {layer.name}
                </Typography>
                {heightM !== null && (
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'text.secondary',
                      fontSize: 'var(--ob-font-size-2xs)',
                    }}
                  >
                    Height: {formatHeight(heightM)}
                  </Typography>
                )}
              </Box>

              {/* Focus Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onFocus(layerId)}
                disabled={isFocused}
              >
                {isFocused ? 'Focused' : 'Focus'}
              </Button>
            </Box>
          )
        })}
      </Stack>
    </Box>
  )
}
