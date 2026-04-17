import { useMemo, useState } from 'react'
import { Box, useTheme, Fade } from '@mui/material'
import { keyframes } from '@emotion/react'
import AutoFixHigh from '@mui/icons-material/AutoFixHigh'
import Autorenew from '@mui/icons-material/Autorenew'
import { DetectedUnit } from './types'

// Vertical Radar Sweep Animation
const radarSweep = keyframes`
  0% { transform: translateX(-100%); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateX(100%); opacity: 0; }
`

const pulse = keyframes`
  0% { opacity: 0.3; }
  50% { opacity: 0.6; }
  100% { opacity: 0.3; }
`

const rotate = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`

interface InteractiveFloorplateProps {
  units: DetectedUnit[]
  onUnitSelect?: (unit: DetectedUnit) => void
  loading?: boolean
}

export function InteractiveFloorplate({
  units,
  onUnitSelect,
  loading,
}: InteractiveFloorplateProps) {
  const theme = useTheme()
  const [hoveredUnitId, setHoveredUnitId] = useState<string | null>(null)

  // Procedural Layout Generation (Simple Grid)
  const layout = useMemo(() => {
    if (units.length === 0) return []
    const count = units.length
    const cols = Math.ceil(Math.sqrt(count))
    const rows = Math.ceil(count / cols)

    // Canvas size 800x600 logical units
    const width = 800
    const height = 600
    const padding = 40
    const gap = 10

    const cellW = (width - padding * 2 - (cols - 1) * gap) / cols
    const cellH = (height - padding * 2 - (rows - 1) * gap) / rows

    return units.map((unit, index) => {
      const col = index % cols
      const row = Math.floor(index / cols)
      return {
        ...unit,
        x: padding + col * (cellW + gap),
        y: padding + row * (cellH + gap),
        w: cellW,
        h: cellH,
      }
    })
  }, [units])

  const displayState = loading
    ? 'loading'
    : units.length === 0
      ? 'empty'
      : 'ready'

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        position: 'relative',
        background: 'var(--ob-neutral-950)', // Deep black/slate
        overflow: 'hidden',
        // Note: minHeight is enforced by parent container now
        // But we keep internal structure robust
      }}
    >
      {/* Technical Grid Background */}
      <svg
        width="100%"
        height="100%"
        style={{ position: 'absolute', opacity: 0.2, pointerEvents: 'none' }}
      >
        <defs>
          <pattern
            id="grid"
            width="40"
            height="40"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 40 0 L 0 0 0 40"
              fill="none"
              stroke={theme.palette.primary.main}
              strokeWidth="0.5"
            />
          </pattern>
        </defs>
        <rect
          width="100%"
          height="100%"
          fill="url(#grid)"
          style={{ animation: `${pulse} 4s infinite ease-in-out` }}
        />
      </svg>

      {/* Main Content */}
      {displayState === 'ready' ? (
        <Fade in={true} timeout={1000}>
          <svg
            viewBox="0 0 800 600"
            preserveAspectRatio="xMidYMid meet"
            style={{ width: '100%', height: '100%' }}
          >
            <defs>
              <linearGradient id="unitGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgba(59, 130, 246, 0.1)" />
                <stop offset="100%" stopColor="rgba(59, 130, 246, 0.3)" />
              </linearGradient>
              <linearGradient
                id="unitGradHover"
                x1="0%"
                y1="0%"
                x2="100%"
                y2="100%"
              >
                <stop offset="0%" stopColor="rgba(59, 130, 246, 0.3)" />
                <stop offset="100%" stopColor="rgba(59, 130, 246, 0.6)" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {layout.map((unit) => {
              const isHovered = hoveredUnitId === unit.id
              return (
                <g
                  key={unit.id}
                  onClick={() => onUnitSelect?.(unit)}
                  onMouseEnter={() => setHoveredUnitId(unit.id)}
                  onMouseLeave={() => setHoveredUnitId(null)}
                  style={{ cursor: 'pointer', transition: 'all 0.3s' }}
                >
                  <rect
                    x={unit.x}
                    y={unit.y}
                    width={unit.w}
                    height={unit.h}
                    fill={isHovered ? 'url(#unitGradHover)' : 'url(#unitGrad)'}
                    stroke={
                      isHovered
                        ? 'var(--ob-brand-400)'
                        : 'rgba(96, 165, 250, 0.5)'
                    }
                    strokeWidth={isHovered ? 2 : 1}
                    rx="4"
                    filter={isHovered ? 'url(#glow)' : ''}
                  />
                  {unit.w > 40 && unit.h > 20 && (
                    <text
                      x={unit.x + unit.w / 2}
                      y={unit.y + unit.h / 2}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="white"
                      fontSize="12"
                      fontWeight="bold"
                      pointerEvents="none"
                    >
                      {unit.unitLabel}
                    </text>
                  )}
                  {unit.severity && unit.severity !== 'none' && (
                    <circle
                      cx={unit.x + unit.w - 15}
                      cy={unit.y + 15}
                      r="4"
                      fill={
                        unit.severity === 'high'
                          ? 'var(--ob-error-500)'
                          : unit.severity === 'medium'
                            ? 'var(--ob-warning-500)'
                            : 'var(--ob-brand-500)'
                      }
                    />
                  )}
                </g>
              )
            })}
          </svg>
        </Fade>
      ) : (
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 4,
            zIndex: 5,
          }}
        >
          <Box
            sx={{
              width: 'min(480px, 100%)',
              borderRadius: 'var(--ob-radius-sm)',
              border: '1px solid var(--ob-border-fine)',
              background:
                'radial-gradient(circle at top, rgba(0, 214, 255, 0.14), transparent 65%), rgba(10, 22, 40, 0.82)',
              backdropFilter: 'blur(var(--ob-blur-md))',
              boxShadow: '0 0 36px rgba(0, 214, 255, 0.08)',
              textAlign: 'center',
              px: 4,
              py: 5,
            }}
          >
            <Box
              sx={{
                width: 72,
                height: 72,
                mx: 'auto',
                mb: 2,
                borderRadius: '50%',
                border: '1px solid rgba(0, 214, 255, 0.28)',
                background: 'rgba(0, 214, 255, 0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 24px rgba(0, 214, 255, 0.12)',
              }}
            >
              {displayState === 'loading' ? (
                <Autorenew
                  sx={{
                    color: 'var(--ob-brand-400)',
                    fontSize: 36,
                    animation: `${rotate} 2.4s linear infinite`,
                  }}
                />
              ) : (
                <AutoFixHigh
                  sx={{
                    color: 'var(--ob-brand-400)',
                    fontSize: 36,
                  }}
                />
              )}
            </Box>
            <Box
              sx={{
                color: 'var(--ob-brand-400)',
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 700,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                mb: 1.5,
              }}
            >
              {displayState === 'loading'
                ? 'Scanning sectors'
                : 'CAD detection ready'}
            </Box>
            <Box
              sx={{
                color: 'var(--ob-color-text-primary)',
                fontSize: 'var(--ob-font-size-xl)',
                fontWeight: 700,
                lineHeight: 1.2,
                mb: 1,
              }}
            >
              {displayState === 'loading'
                ? 'Preparing detection overlays'
                : 'Upload a CAD file to see detection results'}
            </Box>
            <Box
              sx={{
                color: 'var(--ob-color-text-secondary)',
                fontSize: 'var(--ob-font-size-sm)',
                maxWidth: 360,
                mx: 'auto',
              }}
            >
              {displayState === 'loading'
                ? 'We are mapping floors, unit boundaries, and review overlays before the interactive floorplate comes online.'
                : 'Detection layers, floor segmentation, and feasibility overlays will appear here once source plans are processed.'}
            </Box>
          </Box>
        </Box>
      )}

      {/* Vertical Green Radar Sweep */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          width: '4px',
          background:
            'linear-gradient(to bottom, transparent, var(--ob-success-500), transparent)', // Green
          boxShadow: '0 0 15px var(--ob-success-500)',
          animation: `${radarSweep} 3s linear infinite`, // Reverts to left-to-right but vertical line
          pointerEvents: 'none',
          opacity: 0.8,
          zIndex: 10,
        }}
      />

      {/* Corner UI Accents */}
      <Box
        sx={{
          position: 'absolute',
          top: 20,
          left: 20,
          width: 20,
          height: 20,
          borderTop: '2px solid rgba(255,255,255,0.3)',
          borderLeft: '2px solid rgba(255,255,255,0.3)',
          pointerEvents: 'none',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          top: 20,
          right: 20,
          width: 20,
          height: 20,
          borderTop: '2px solid rgba(255,255,255,0.3)',
          borderRight: '2px solid rgba(255,255,255,0.3)',
          pointerEvents: 'none',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: 20,
          left: 20,
          width: 20,
          height: 20,
          borderBottom: '2px solid rgba(255,255,255,0.3)',
          borderLeft: '2px solid rgba(255,255,255,0.3)',
          pointerEvents: 'none',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: 20,
          right: 20,
          width: 20,
          height: 20,
          borderBottom: '2px solid rgba(255,255,255,0.3)',
          borderRight: '2px solid rgba(255,255,255,0.3)',
          pointerEvents: 'none',
        }}
      />
    </Box>
  )
}
