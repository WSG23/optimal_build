import { styled } from '@mui/material/styles'
import React from 'react'

const CardButton = styled('button')<{ selected?: boolean }>(({ selected }) => ({
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '16px 12px',
  gap: '8px',
  background: selected
    ? 'linear-gradient(135deg, rgba(6,182,212,0.15) 0%, rgba(59,130,246,0.15) 100%)'
    : 'rgba(255, 255, 255, 0.03)',
  border: selected ? '1px solid #06b6d4' : '1px solid rgba(255, 255, 255, 0.1)',
  borderRadius: '4px',
  cursor: 'pointer',
  transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
  backdropFilter: 'blur(10px)',
  overflow: 'hidden',
  color: selected ? '#06b6d4' : '#a1a1aa',

  // Neon Glow for Active State
  boxShadow: selected
    ? '0 0 20px rgba(6, 182, 212, 0.25), inset 0 0 0 1px rgba(6,182,212,0.1)'
    : 'none',

  '&:hover': {
    transform: 'translateY(-2px)',
    background: selected
      ? 'linear-gradient(135deg, rgba(6,182,212,0.2) 0%, rgba(59,130,246,0.2) 100%)'
      : 'rgba(255, 255, 255, 0.06)',
    borderColor: selected ? '#22d3ee' : 'rgba(255, 255, 255, 0.2)',
  },

  '&:active': {
    transform: 'scale(0.98)',
  },
}))

const CostBadge = styled('div')({
  position: 'absolute',
  top: '6px',
  right: '6px',
  fontSize: '0.625rem',
  fontWeight: 700,
  color: '#ef4444', // Red for cost
  background: 'rgba(239, 68, 68, 0.1)',
  padding: '2px 6px',
  borderRadius: '4px',
  border: '1px solid rgba(239, 68, 68, 0.2)',
  letterSpacing: '0.025em',
})

interface HolographicCardProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean
  label: string
  icon: React.ReactNode
  costImpact?: string // e.g. "+$15" or "$$$"
}

export function HolographicCard({
  selected,
  label,
  icon,
  costImpact,
  ...props
}: HolographicCardProps) {
  return (
    <CardButton selected={selected} type="button" {...props}>
      {costImpact && <CostBadge>{costImpact}</CostBadge>}

      {/* Icon Container with some 3D perspective hint */}
      <div
        style={{
          fontSize: '2rem',
          lineHeight: 1,
          filter: selected
            ? 'drop-shadow(0 0 8px rgba(6,182,212,0.6))'
            : 'grayscale(0.8)',
          transform: selected ? 'scale(1.1)' : 'scale(1)',
          transition: 'all 0.3s ease',
        }}
      >
        {icon}
      </div>

      <span
        style={{
          fontSize: '0.75rem',
          fontWeight: 600,
          textAlign: 'center',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginTop: 'auto',
        }}
      >
        {label}
      </span>

      {/* Shine Effect */}
      {selected && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            background:
              'linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.1) 40%, transparent 50%)',
            backgroundSize: '200% 100%',
            animation: 'holographic-shine 3s infinite linear',
            pointerEvents: 'none',
          }}
        />
      )}
      <style>
        {`@keyframes holographic-shine { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }`}
      </style>
    </CardButton>
  )
}
