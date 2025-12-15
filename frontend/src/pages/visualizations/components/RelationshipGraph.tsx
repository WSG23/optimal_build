import { useEffect, useRef, useState } from 'react'
import { Box, useTheme, alpha } from '@mui/material'

// Types
interface Node {
  id: string
  label: string
  category: 'Team' | 'Workflow'
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
}

// Simple Force Simulation Hooks
function useForceSimulation(
  nodes: Node[],
  links: Link[],
  width: number,
  height: number,
) {
  // Initialize positions randomly but centered
  const [positions, setPositions] = useState<
    Record<string, { x: number; y: number; vx: number; vy: number }>
  >(() => {
    const initial: Record<
      string,
      { x: number; y: number; vx: number; vy: number }
    > = {}
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

  useEffect(() => {
    const animate = () => {
      setPositions((prev) => {
        const next = { ...prev }
        // Constants (tuned for "Cyber-Zen" feel - floaty but stable)
        const REPULSION = 4000
        const SPRING = 0.05
        const DAMPING = 0.85
        const CENTER_PULL = 0.02

        // Reset forces
        const forces: Record<string, { fx: number; fy: number }> = {}
        nodes.forEach((n) => (forces[n.id] = { fx: 0, fy: 0 }))

        // 1. Repulsion (Nodes repel each other)
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const u = nodes[i].id
            const v = nodes[j].id
            const dx = next[u].x - next[v].x
            const dy = next[u].y - next[v].y
            const distSq = dx * dx + dy * dy || 1 // Avoid div by zero
            const dist = Math.sqrt(distSq)

            const force = REPULSION / distSq
            const fx = (dx / dist) * force
            const fy = (dy / dist) * force

            forces[u].fx += fx
            forces[u].fy += fy
            forces[v].fx -= fx
            forces[v].fy -= fy
          }
        }

        // 2. Spring (Links pull nodes together)
        links.forEach((link) => {
          const u = link.source
          const v = link.target
          if (!next[u] || !next[v]) return

          const dx = next[u].x - next[v].x
          const dy = next[u].y - next[v].y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1

          // Target content length
          const targetLen = 100 / link.strength
          const displacement = dist - targetLen

          const fx = (dx / dist) * SPRING * displacement
          const fy = (dy / dist) * SPRING * displacement

          forces[u].fx -= fx
          forces[u].fy -= fy
          forces[v].fx += fx
          forces[v].fy += fy
        })

        // 3. Center Pull (Keep graph centered)
        nodes.forEach((node) => {
          const u = node.id
          const dx = next[u].x - width / 2
          const dy = next[u].y - height / 2

          forces[u].fx -= dx * CENTER_PULL
          forces[u].fy -= dy * CENTER_PULL
        })

        // Apply forces to velocity and position
        nodes.forEach((node) => {
          const u = node.id
          next[u].vx = (next[u].vx + forces[u].fx) * DAMPING
          next[u].vy = (next[u].vy + forces[u].fy) * DAMPING

          next[u].x += next[u].vx
          next[u].y += next[u].vy

          // Bounds check (soft)
          const margin = 20
          if (next[u].x < margin) next[u].vx += 1
          if (next[u].x > width - margin) next[u].vx -= 1
          if (next[u].y < margin) next[u].vy += 1
          if (next[u].y > height - margin) next[u].vy -= 1
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

export function RelationshipGraph({
  nodes,
  links,
  width = '100%',
  height = 400,
}: RelationshipGraphProps) {
  const theme = useTheme()
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ w: 800, h: 400 })

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        w: containerRef.current.offsetWidth,
        h: containerRef.current.offsetHeight || 400,
      })
    }
  }, [])

  const positions = useForceSimulation(nodes, links, dimensions.w, dimensions.h)

  // Interaction State (dragNode reserved for future drag implementation)
  const [_dragNode, setDragNode] = useState<string | null>(null)

  const handleMouseDown = (id: string) => {
    setDragNode(id)
  }

  const handleMouseUp = () => {
    setDragNode(null)
  }

  // Note: Full drag is complex in this simple hook, for now we just allow 'grabbing' visual
  // Real drag would require updating position override in simulation loop.

  return (
    <Box
      ref={containerRef}
      sx={{
        width: width,
        height: height,
        bgcolor: alpha(theme.palette.background.paper, 0.4),
        borderRadius: '4px', // Square Cyber-Minimalism: sm for panels
        border: '1px solid',
        borderColor: alpha(theme.palette.divider, 0.1),
        position: 'relative',
        overflow: 'hidden',
        backdropFilter: 'blur(var(--ob-blur-md))',
      }}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${dimensions.w} ${dimensions.h}`}
      >
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Links */}
        {links.map((link, i) => {
          const start = positions[link.source]
          const end = positions[link.target]
          if (!start || !end) return null

          return (
            <line
              key={`link-${i}`}
              x1={start.x}
              y1={start.y}
              x2={end.x}
              y2={end.y}
              stroke={alpha(theme.palette.text.secondary, 0.2)}
              strokeWidth={link.strength * 3}
              strokeLinecap="round"
            />
          )
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const pos = positions[node.id]
          if (!pos) return null

          const isTeam = node.category === 'Team'
          const color = isTeam
            ? theme.palette.info.main
            : theme.palette.secondary.main
          const radius = 8 + node.weight * 5 // Size by weight

          return (
            <g
              key={node.id}
              transform={`translate(${pos.x}, ${pos.y})`}
              onMouseDown={() => handleMouseDown(node.id)}
              style={{ cursor: 'grab' }}
            >
              <circle
                r={radius}
                fill={alpha(color, 0.2)}
                stroke={color}
                strokeWidth={2}
                filter="url(#glow)"
              >
                <animate
                  attributeName="r"
                  values={`${radius};${radius + 2};${radius}`}
                  dur="3s"
                  repeatCount="indefinite"
                />
              </circle>
              <text
                dy={radius + 15}
                textAnchor="middle"
                fill={theme.palette.text.primary}
                fontSize="12px"
                fontWeight="500"
                style={{
                  pointerEvents: 'none',
                  textShadow: '0 2px 4px rgba(0,0,0,0.5)',
                }}
              >
                {node.label}
              </text>
            </g>
          )
        })}
      </svg>
    </Box>
  )
}
