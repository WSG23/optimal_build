import { AutoAwesome } from '@mui/icons-material'
import { Card, CardActionArea, Typography, Grid, Box } from '@mui/material'
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
  const baseColor = selected ? '#06b6d4' : '#64748b'
  const highlightColor = selected ? '#22d3ee' : '#94a3b8'
  const shadowColor = selected
    ? 'rgba(6, 182, 212, 0.3)'
    : 'rgba(100, 116, 139, 0.2)'

  switch (strategy) {
    case 'max_density':
      // Tall dense tower cluster
      return (
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
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
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
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
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
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
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
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
          gap: '12px',
          marginBottom: '1rem',
        }}
      >
        <Box
          sx={{
            width: '32px',
            height: '32px',
            borderRadius: '4px',
            background:
              'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(59, 130, 246, 0.2))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <AutoAwesome sx={{ color: '#06b6d4', fontSize: '18px' }} />
        </Box>
        <div>
          <h2
            style={{
              margin: 0,
              fontSize: '1rem',
              fontWeight: 600,
              color: 'rgba(255,255,255,0.9)',
            }}
          >
            Generative Design
          </h2>
          <p
            style={{
              margin: 0,
              fontSize: '0.75rem',
              color: 'rgba(255,255,255,0.5)',
            }}
          >
            AI-optimized massing strategies
          </p>
        </div>
      </div>

      <Grid container spacing={1.5}>
        {GENERATIVE_OPTIONS.map((option) => {
          const isSelected = selectedStrategy === option.value
          return (
            <Grid item xs={6} key={option.value}>
              <Card
                variant="outlined"
                sx={{
                  height: '100%',
                  background: isSelected
                    ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(59, 130, 246, 0.1))'
                    : 'rgba(255, 255, 255, 0.03)',
                  borderColor: isSelected
                    ? '#06b6d4'
                    : 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '4px',
                  transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
                  '&:hover': {
                    borderColor: '#06b6d4',
                    transform: 'translateY(-4px) scale(1.02)',
                    boxShadow: '0 12px 32px -8px rgba(6, 182, 212, 0.4)',
                    background: 'rgba(6, 182, 212, 0.08)',
                  },
                  boxShadow: isSelected
                    ? '0 0 0 1px #06b6d4, 0 8px 24px -4px rgba(6, 182, 212, 0.3), inset 0 0 20px rgba(6, 182, 212, 0.1)'
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
                    padding: '16px 12px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  {/* Isometric Icon */}
                  <Box
                    sx={{
                      width: '56px',
                      height: '56px',
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
                      color: isSelected ? '#06b6d4' : 'rgba(255,255,255,0.9)',
                      textAlign: 'center',
                      fontSize: '0.8rem',
                    }}
                  >
                    {option.label}
                  </Typography>

                  <Typography
                    variant="caption"
                    sx={{
                      color: 'rgba(255,255,255,0.5)',
                      lineHeight: 1.3,
                      display: 'block',
                      textAlign: 'center',
                      fontSize: '0.7rem',
                    }}
                  >
                    {option.description}
                  </Typography>

                  {/* Selected indicator */}
                  {isSelected && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: '#06b6d4',
                        boxShadow: '0 0 8px #06b6d4',
                      }}
                    />
                  )}
                </CardActionArea>
              </Card>
            </Grid>
          )
        })}
      </Grid>
    </section>
  )
}
