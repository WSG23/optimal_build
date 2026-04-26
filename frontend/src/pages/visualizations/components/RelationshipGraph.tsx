import React, { useEffect, useRef, useState, useCallback } from 'react'
import { Box, Typography } from '@mui/material'

interface Node {
  id: string
  label: string
  category: string
  weight: number
}

interface Link {
  source: string
  target: string
  strength: number
}

export interface RelationshipGraphProps {
  nodes: Node[]
  links: Link[]
  width?: number | string
  height?: number | string
  onNodeClick?: (nodeId: string) => void
}

interface SimPosition {
  x: number
  y: number
  vx: number
  vy: number
}

/** Force simulation that cools down after convergence */
function useForceSimulation(
  nodes: Node[],
  links: Link[],
  width: number,
  height: number,
) {
  const [positions, setPositions] = useState<
    Partial<Record<string, SimPosition>>
  >(() => {
    const initial: Partial<Record<string, SimPosition>> = {}
    nodes.forEach((node) => {
      initial[node.id] = {
        x: width / 2 + (Math.random() - 0.5) * 50,
        y: height / 2 + (Math.random() - 0.5) * 50,
        vx: 0,
        vy: 0,
      }
    })
    return initial
  })

  const requestRef = useRef<number>()
  const tickRef = useRef(0)

  useEffect(() => {
    tickRef.current = 0
    // Converge faster for small graphs, longer for large ones
    const maxTicks = Math.min(300, 50 + nodes.length * 10)

    const animate = () => {
      tickRef.current++
      if (tickRef.current > maxTicks) return

      setPositions((prev) => {
        const next: Partial<Record<string, SimPosition>> = {}
        for (const [k, v] of Object.entries(prev)) {
          if (v) next[k] = { ...v }
        }

        const REPULSION = 4000
        const SPRING = 0.05
        const DAMPING = 0.85
        const CENTER_PULL = 0.02

        const forces: Record<string, { fx: number; fy: number }> = {}
        nodes.forEach((n) => (forces[n.id] = { fx: 0, fy: 0 }))

        // Repulsion
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const pu = next[nodes[i].id]
            const pv = next[nodes[j].id]
            if (!pu || !pv) continue
            const dx = pu.x - pv.x
            const dy = pu.y - pv.y
            const distSq = dx * dx + dy * dy || 1
            const dist = Math.sqrt(distSq)
            const force = REPULSION / distSq
            const fx = (dx / dist) * force
            const fy = (dy / dist) * force
            forces[nodes[i].id].fx += fx
            forces[nodes[i].id].fy += fy
            forces[nodes[j].id].fx -= fx
            forces[nodes[j].id].fy -= fy
          }
        }

        // Spring
        links.forEach((link) => {
          const srcPos = next[link.source]
          const tgtPos = next[link.target]
          if (!srcPos || !tgtPos) return
          const dx = srcPos.x - tgtPos.x
          const dy = srcPos.y - tgtPos.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const targetLen = 100 / link.strength
          const displacement = dist - targetLen
          const fx = (dx / dist) * SPRING * displacement
          const fy = (dy / dist) * SPRING * displacement
          forces[link.source].fx -= fx
          forces[link.source].fy -= fy
          forces[link.target].fx += fx
          forces[link.target].fy += fy
        })

        // Center pull + Apply
        nodes.forEach((node) => {
          const p = next[node.id]
          if (!p) return
          const f = forces[node.id]
          p.vx = (p.vx + (f.fx - (p.x - width / 2) * CENTER_PULL)) * DAMPING
          p.vy = (p.vy + (f.fy - (p.y - height / 2) * CENTER_PULL)) * DAMPING
          p.x += p.vx
          p.y += p.vy
          const margin = 20
          if (p.x < margin) p.vx += 1
          if (p.x > width - margin) p.vx -= 1
          if (p.y < margin) p.vy += 1
          if (p.y > height - margin) p.vy -= 1
        })

        return next
      })
      requestRef.current = requestAnimationFrame(animate)
    }

    requestRef.current = requestAnimationFrame(animate)
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current)
    }
  }, [nodes, links, width, height])

  return positions
}

/** Category colors for CRE entity types, with neutral fallback */
const CATEGORY_COLORS: Record<string, { fill: string }> = {
  team: { fill: 'var(--ob-info-500)' },
  workflow: { fill: 'var(--ob-brand-500)' },
  partner: { fill: 'var(--ob-warning-500)' },
  property: { fill: 'var(--ob-success-500)' },
  deal: { fill: 'var(--ob-error-400)' },
}

const FALLBACK_COLOR = { fill: 'var(--ob-neutral-400)' }

function getCategoryColor(category: string): { fill: string } {
  return CATEGORY_COLORS[category.toLowerCase()] ?? FALLBACK_COLOR
}

/** SVG sizing constants (CSS custom properties don't resolve in SVG attributes) */
const SVG_LABEL_FONT_SIZE = '11px'
const SVG_LABEL_OFFSET = 14
const LEGEND_DOT_SIZE = 8

export function RelationshipGraph({
  nodes,
  links,
  width = '100%',
  height = 400,
  onNodeClick,
}: RelationshipGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ w: 800, h: 400 })
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)

  // Measure on mount + resize
  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const measure = () => {
      setDimensions({
        w: el.offsetWidth,
        h: el.offsetHeight || 400,
      })
    }
    measure()

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(measure)
      observer.observe(el)
      return () => {
        observer.disconnect()
      }
    }
    return undefined
  }, [])

  const positions = useForceSimulation(nodes, links, dimensions.w, dimensions.h)

  const handleNodeClick = useCallback(
    (id: string) => {
      onNodeClick?.(id)
    },
    [onNodeClick],
  )

  const handleNodeKeyDown = useCallback(
    (id: string, e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        onNodeClick?.(id)
      }
    },
    [onNodeClick],
  )

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
      }}
    >
      {/* Legend — derived from actual node categories */}
      <Box
        sx={{
          display: 'flex',
          gap: 'var(--ob-space-200)',
          px: 'var(--ob-space-100)',
        }}
      >
        {Array.from(new Set(nodes.map((n) => n.category))).map((category) => (
          <Box
            key={category}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-050)',
            }}
          >
            <Box
              sx={{
                width: LEGEND_DOT_SIZE,
                height: LEGEND_DOT_SIZE,
                borderRadius: 'var(--ob-radius-xs)',
                background: getCategoryColor(category).fill,
              }}
            />
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'var(--ob-color-text-muted)',
                fontWeight: 'var(--ob-font-weight-medium)',
                textTransform: 'capitalize',
              }}
            >
              {category}
            </Typography>
          </Box>
        ))}
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            color: 'var(--ob-color-text-muted)',
            ml: 'auto',
          }}
        >
          Node size = weight
          {onNodeClick ? <> &middot; Click to inspect</> : null}
        </Typography>
      </Box>

      {/* Graph */}
      <Box
        ref={containerRef}
        sx={{
          width,
          height,
          background: 'var(--ob-color-bg-surface)',
          borderRadius: 'var(--ob-radius-sm)',
          border: 'var(--ob-border-fine)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${String(dimensions.w)} ${String(dimensions.h)}`}
          role="img"
          aria-label="Relationship intelligence graph showing entity connections"
        >
          {/* Links */}
          {links.map((link, i) => {
            const start = positions[link.source]
            const end = positions[link.target]
            if (!start || !end) return null
            const isHovered =
              hoveredNode === link.source || hoveredNode === link.target

            return (
              <line
                key={`link-${String(i)}`}
                x1={start.x}
                y1={start.y}
                x2={end.x}
                y2={end.y}
                stroke="var(--ob-color-border-subtle)"
                strokeWidth={String(link.strength * 2)}
                strokeLinecap="round"
                opacity={isHovered ? 0.8 : 0.3}
                style={{ transition: 'opacity 0.15s ease' }}
              />
            )
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = positions[node.id]
            if (!pos) return null

            const colors = getCategoryColor(node.category)
            const radius = 6 + node.weight * 4
            const isHovered = hoveredNode === node.id

            return (
              <g
                key={node.id}
                transform={`translate(${String(pos.x)}, ${String(pos.y)})`}
                onMouseEnter={() => {
                  setHoveredNode(node.id)
                }}
                onMouseLeave={() => {
                  setHoveredNode(null)
                }}
                onFocus={() => {
                  setHoveredNode(node.id)
                }}
                onBlur={() => {
                  setHoveredNode(null)
                }}
                onClick={
                  onNodeClick
                    ? () => {
                        handleNodeClick(node.id)
                      }
                    : undefined
                }
                onKeyDown={
                  onNodeClick
                    ? (e: React.KeyboardEvent) => {
                        handleNodeKeyDown(node.id, e)
                      }
                    : undefined
                }
                role={onNodeClick ? 'button' : undefined}
                tabIndex={onNodeClick ? 0 : undefined}
                aria-label={`${node.label} (${node.category}, weight ${node.weight.toFixed(1)})`}
                style={{
                  cursor: onNodeClick ? 'pointer' : 'default',
                  outline: 'none',
                }}
              >
                <circle
                  r={radius}
                  fill={colors.fill}
                  opacity={isHovered ? 1 : 0.7}
                  style={{ transition: 'opacity 0.15s ease' }}
                />
                {/* Focus ring for keyboard navigation */}
                {isHovered && (
                  <circle
                    r={radius + 3}
                    fill="none"
                    stroke="var(--ob-color-brand-primary)"
                    strokeWidth="1.5"
                    opacity={0.6}
                  />
                )}
                <text
                  dy={radius + SVG_LABEL_OFFSET}
                  textAnchor="middle"
                  fill="var(--ob-color-text-secondary)"
                  fontSize={SVG_LABEL_FONT_SIZE}
                  fontWeight={isHovered ? '600' : '400'}
                  style={{ pointerEvents: 'none' }}
                >
                  {node.label}
                </text>
              </g>
            )
          })}
        </svg>
      </Box>
    </Box>
  )
}
