import { AutoAwesome, CheckCircle } from '@mui/icons-material'
import {
  Card,
  CardActionArea,
  Typography,
  Grid,
  Box,
  Tooltip,
} from '@mui/material'
import type { GenerativeStrategy } from '../types'
import { GENERATIVE_OPTIONS } from '../types'

interface GenerativeDesignPanelProps {
  selectedStrategy: GenerativeStrategy | null
  onSelectStrategy: (strategy: GenerativeStrategy) => void
  loading?: boolean
}

// Isometric 3D building SVG icons for each strategy
const IsometricIcon = ({
  strategy,
  selected,
}: {
  strategy: GenerativeStrategy
  selected: boolean
}) => {
  const baseColor = selected ? '#06b6d4' : 'var(--ob-neutral-500)'
  const highlightColor = selected ? '#22d3ee' : 'var(--ob-neutral-400)'
  const shadowColor = selected
    ? 'var(--ob-color-neon-cyan-muted)'
    : 'rgba(100, 116, 139, 0.2)'
  const iconSize = 32

  switch (strategy) {
    case 'max_density':
      // Tall dense tower cluster
      return (
        <svg width={iconSize} height={iconSize} viewBox="0 0 48 48" fill="none">
          <defs>
            <filter
              id="glow-density"
              x="-50%"
              y="-50%"
              width="200%"
              height="200%"
            >
              <feGaussianBlur stdDeviation="2" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <g filter={selected ? 'url(#glow-density)' : undefined}>
            {/* Main tower */}
            <path d="M24 4L32 10V38L24 44L16 38V10L24 4Z" fill={baseColor} />
            <path
              d="M24 4L32 10V38L24 32V4Z"
              fill={highlightColor}
              opacity="0.7"
            />
            {/* Side tower left */}
            <path
              d="M12 14L18 18V40L12 44L6 40V18L12 14Z"
              fill={baseColor}
              opacity="0.8"
            />
            {/* Side tower right */}
            <path
              d="M36 14L42 18V40L36 44L30 40V18L36 14Z"
              fill={baseColor}
              opacity="0.8"
            />
            {/* Windows */}
            <rect x="21" y="12" width="6" height="2" fill={shadowColor} />
            <rect x="21" y="18" width="6" height="2" fill={shadowColor} />
            <rect x="21" y="24" width="6" height="2" fill={shadowColor} />
          </g>
        </svg>
      )

    case 'balanced':
      // Medium-height stepped building
      return (
        <svg width={iconSize} height={iconSize} viewBox="0 0 48 48" fill="none">
          <defs>
            <filter
              id="glow-balanced"
              x="-50%"
              y="-50%"
              width="200%"
              height="200%"
            >
              <feGaussianBlur stdDeviation="2" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <g filter={selected ? 'url(#glow-balanced)' : undefined}>
            {/* Base */}
            <path d="M8 32L24 24L40 32V44L24 52L8 44V32Z" fill={baseColor} />
            {/* Middle tier */}
            <path
              d="M12 24L24 18L36 24V36L24 42L12 36V24Z"
              fill={highlightColor}
              opacity="0.8"
            />
            {/* Top tier */}
            <path d="M16 16L24 12L32 16V28L24 32L16 28V16Z" fill={baseColor} />
            {/* Highlight */}
            <path
              d="M24 12L32 16V28L24 24V12Z"
              fill={highlightColor}
              opacity="0.5"
            />
            {/* Open space indicator */}
            <circle cx="24" cy="38" r="3" fill={shadowColor} />
          </g>
        </svg>
      )

    case 'iconic':
      // Distinctive curved/angular form
      return (
        <svg width={iconSize} height={iconSize} viewBox="0 0 48 48" fill="none">
          <defs>
            <filter
              id="glow-iconic"
              x="-50%"
              y="-50%"
              width="200%"
              height="200%"
            >
              <feGaussianBlur stdDeviation="2" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <g filter={selected ? 'url(#glow-iconic)' : undefined}>
            {/* Curved iconic tower */}
            <path
              d="M24 2C24 2 32 8 34 16C36 24 36 32 34 40L24 46L14 40C12 32 12 24 14 16C16 8 24 2 24 2Z"
              fill={baseColor}
            />
            <path
              d="M24 2C24 2 32 8 34 16C36 24 36 32 34 40L24 34V2Z"
              fill={highlightColor}
              opacity="0.6"
            />
            {/* Crown feature */}
            <path d="M20 6L24 2L28 6L24 10L20 6Z" fill={highlightColor} />
            {/* Decorative bands */}
            <ellipse cx="24" cy="20" rx="8" ry="2" fill={shadowColor} />
            <ellipse cx="24" cy="32" rx="8" ry="2" fill={shadowColor} />
          </g>
        </svg>
      )

    case 'green_focus':
      // Building with terraces/greenery
      return (
        <svg width={iconSize} height={iconSize} viewBox="0 0 48 48" fill="none">
          <defs>
            <filter
              id="glow-green"
              x="-50%"
              y="-50%"
              width="200%"
              height="200%"
            >
              <feGaussianBlur stdDeviation="2" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <g filter={selected ? 'url(#glow-green)' : undefined}>
            {/* Building base */}
            <path d="M10 28L24 20L38 28V44L24 52L10 44V28Z" fill={baseColor} />
            <path
              d="M24 20L38 28V44L24 36V20Z"
              fill={highlightColor}
              opacity="0.5"
            />
            {/* Green terraces */}
            <ellipse
              cx="16"
              cy="32"
              rx="4"
              ry="2"
              fill="#10b981"
              opacity="0.8"
            />
            <ellipse
              cx="32"
              cy="32"
              rx="4"
              ry="2"
              fill="#10b981"
              opacity="0.8"
            />
            <ellipse
              cx="24"
              cy="26"
              rx="5"
              ry="2"
              fill="#34d399"
              opacity="0.9"
            />
            {/* Trees/plants */}
            <circle cx="16" cy="30" r="2" fill="#059669" />
            <circle cx="32" cy="30" r="2" fill="#059669" />
            <circle cx="24" cy="24" r="2.5" fill="#10b981" />
            {/* Top garden */}
            <path
              d="M20 16L24 12L28 16C28 16 26 18 24 18C22 18 20 16 20 16Z"
              fill="#34d399"
            />
          </g>
        </svg>
      )

    default:
      return null
  }
}

export function GenerativeDesignPanel({
  selectedStrategy,
  onSelectStrategy,
  loading = false,
}: GenerativeDesignPanelProps) {
  return (
    <section className="feasibility-generative">
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--ob-space-050)',
          marginBottom: 'var(--ob-space-075)',
        }}
      >
        <Box
          sx={{
            width: 'var(--ob-size-icon-md)',
            height: 'var(--ob-size-icon-md)',
            borderRadius: 'var(--ob-radius-sm)',
            background:
              'linear-gradient(135deg, var(--ob-color-brand-soft), var(--ob-color-action-selected))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <AutoAwesome
            sx={{
              color: 'var(--ob-color-brand-primary)',
              fontSize: 'var(--ob-size-icon-sm)',
            }}
          />
        </Box>
        <div>
          <h2
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-base)',
              fontWeight: 600,
              color: 'var(--ob-color-text-primary)',
            }}
          >
            Generative Design
          </h2>
          <p
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-xs)',
              color: 'var(--ob-color-text-muted)',
            }}
          >
            AI-optimized massing strategies
          </p>
        </div>
      </div>

      <Grid container spacing="var(--ob-space-100)">
        {GENERATIVE_OPTIONS.map((option) => {
          const isSelected = selectedStrategy === option.value
          return (
            <Grid item xs={6} sm={3} key={option.value}>
              <Tooltip
                title={
                  <Box sx={{ p: 'var(--ob-space-100)' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {option.label}
                    </Typography>
                    <Typography variant="caption" sx={{ display: 'block' }}>
                      {option.description}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{
                        display: 'block',
                        mt: 'var(--ob-space-50)',
                        color: 'var(--ob-color-brand-primary)',
                      }}
                    >
                      Efficiency: {option.efficiency}% | F2F: {option.f2f}m
                    </Typography>
                  </Box>
                }
                arrow
                placement="top"
              >
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    background: isSelected
                      ? 'linear-gradient(135deg, var(--ob-color-brand-soft), var(--ob-color-action-selected))'
                      : 'var(--ob-color-bg-surface)',
                    borderColor: isSelected
                      ? 'var(--ob-color-brand-primary)'
                      : 'var(--ob-color-border-subtle)',
                    borderRadius: 'var(--ob-radius-sm)',
                    transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
                    '&:hover': {
                      borderColor: 'var(--ob-color-brand-primary)',
                      transform: 'translateY(-4px) scale(1.02)',
                      boxShadow: 'var(--ob-glow-brand-medium)',
                      background: 'var(--ob-color-brand-soft)',
                    },
                    boxShadow: isSelected
                      ? 'var(--ob-glow-brand-strong)'
                      : 'none',
                  }}
                >
                  <CardActionArea
                    onClick={() => {
                      onSelectStrategy(option.value)
                    }}
                    disabled={loading}
                    sx={{
                      height: '100%',
                      padding: 'var(--ob-space-075)',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 'var(--ob-space-050)',
                    }}
                  >
                    {/* Isometric Icon */}
                    <Box
                      sx={{
                        width: 'var(--ob-size-icon-md)',
                        height: 'var(--ob-size-icon-md)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'transform 0.3s ease',
                        transform: isSelected ? 'scale(1.1)' : 'scale(1)',
                      }}
                    >
                      <IsometricIcon
                        strategy={option.value}
                        selected={isSelected}
                      />
                    </Box>

                    <Typography
                      variant="subtitle2"
                      sx={{
                        fontWeight: 600,
                        color: isSelected
                          ? 'var(--ob-color-brand-primary)'
                          : 'var(--ob-color-text-primary)',
                        textAlign: 'center',
                        fontSize: 'var(--ob-font-size-xs)',
                      }}
                    >
                      {option.label}
                    </Typography>

                    <Typography
                      variant="caption"
                      sx={{
                        color: 'var(--ob-color-text-muted)',
                        lineHeight: 1.3,
                        textAlign: 'center',
                        fontSize: 'var(--ob-font-size-2xs)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 'var(--ob-space-200)',
                        WebkitBoxOrient: 'vertical',
                      }}
                    >
                      {option.description}
                    </Typography>

                    {/* Selected indicator with checkmark */}
                    {isSelected && (
                      <Box
                        sx={{
                          position: 'absolute',
                          top: 'var(--ob-space-050)',
                          right: 'var(--ob-space-050)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <CheckCircle
                          sx={{
                            fontSize: 'var(--ob-size-icon-sm)',
                            color: 'var(--ob-color-brand-primary)',
                            filter:
                              'drop-shadow(0 0 4px var(--ob-color-brand-primary))',
                          }}
                        />
                      </Box>
                    )}
                  </CardActionArea>
                </Card>
              </Tooltip>
            </Grid>
          )
        })}
      </Grid>

      {/* Show selected strategy details */}
      {selectedStrategy && (
        <Box
          sx={{
            mt: 'var(--ob-space-075)',
            p: 'var(--ob-space-075)',
            borderRadius: 'var(--ob-radius-sm)',
            background: 'var(--ob-color-brand-soft)',
            border: '1px solid var(--ob-color-brand-primary)',
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: 'var(--ob-color-text-secondary)',
              display: 'block',
              mb: 'var(--ob-space-025)',
            }}
          >
            Applied Strategy
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              color: 'var(--ob-color-brand-primary)',
            }}
          >
            {
              GENERATIVE_OPTIONS.find((opt) => opt.value === selectedStrategy)
                ?.label
            }
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: 'var(--ob-color-text-muted)',
              display: 'block',
              mt: 'var(--ob-space-025)',
            }}
          >
            Preset values applied to assumptions
          </Typography>
        </Box>
      )}
    </section>
  )
}
