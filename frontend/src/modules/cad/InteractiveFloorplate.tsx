import { useMemo, useState } from 'react'
import { Box, useTheme, Fade } from '@mui/material'
import { keyframes } from '@emotion/react'
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

  const isEmpty = units.length === 0 || loading

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

          {isEmpty ? (
            // Empty State: "Living Blueprint" Wireframe
            <g transform="translate(400, 300)">
              {/* Rotating Outer Ring */}
              <g style={{ animation: `${rotate} 60s linear infinite` }}>
                <circle
                  r="200"
                  fill="none"
                  stroke="rgba(255, 255, 255, 0.05)"
                  strokeWidth="1"
                />
                <path
                  d="M -200 0 L 200 0 M 0 -200 L 0 200"
                  stroke="rgba(255,255,255,0.05)"
                  strokeDasharray="5 5"
                />
              </g>

              {/* Wireframe Building Placeholder */}
              <g transform="translate(-100, -140) scale(0.8)">
                {/* 3D loose Isometric-ish wireframe */}
                <path
                  d="M100 250 L250 180 L250 50 L100 120 Z"
                  fill="none"
                  stroke="rgba(6, 182, 212, 0.3)"
                  strokeWidth="2"
                />{' '}
                {/* Right Face */}
                <path
                  d="M100 250 L0 200 L0 70 L100 120 Z"
                  fill="none"
                  stroke="rgba(6, 182, 212, 0.3)"
                  strokeWidth="2"
                />{' '}
                {/* Left Face */}
                <path
                  d="M100 120 L250 50 L150 0 L0 70 Z"
                  fill="none"
                  stroke="rgba(6, 182, 212, 0.5)"
                  strokeWidth="2"
                />{' '}
                {/* Top Face */}
                {/* Internal Structure Lines */}
                <path
                  d="M100 120 L100 250"
                  stroke="rgba(6, 182, 212, 0.2)"
                  strokeDasharray="4 4"
                />
                <path
                  d="M0 200 L100 250 L250 180"
                  stroke="rgba(6, 182, 212, 0.2)"
                />
              </g>

              {/* Status Indicator */}
              <g transform="translate(0, 180)">
                <text
                  textAnchor="middle"
                  fill="var(--ob-brand-400)"
                  fontSize="14"
                  fontFamily="monospace"
                  letterSpacing="4"
                  style={{ textShadow: '0 0 10px rgba(6,182,212,0.8)' }}
                >
                  {loading ? 'SCANNING_SECTORS' : 'WAITING_FOR_CAD_INPUT'}
                </text>
                <rect
                  x="-10"
                  y="20"
                  width="20"
                  height="4"
                  fill="var(--ob-brand-400)"
                >
                  <animate
                    attributeName="opacity"
                    values="0;1;0"
                    dur="1s"
                    repeatCount="indefinite"
                  />
                </rect>
              </g>
            </g>
          ) : (
            // Units view remains same
            layout.map((unit) => {
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
            })
          )}
        </svg>
      </Fade>

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
