import { styled } from '@mui/material/styles'
import React from 'react'

const CardButton = styled('button')<{ selected?: boolean }>(({ selected }) => ({
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 'var(--ob-space-075) var(--ob-space-050)',
  gap: 'var(--ob-space-025)',
  background: selected
    ? `linear-gradient(135deg, rgba(var(--ob-color-brand-primary-emphasis-rgb), 0.15) 0%, rgba(var(--ob-color-brand-soft-rgb), 0.15) 100%), var(--ob-surface-glass-1)`
    : 'var(--ob-surface-glass-1)',
  border: selected
    ? '1px solid var(--ob-color-border-brand)'
    : '1px solid var(--ob-border-glass)',
  borderRadius: 'var(--ob-radius-sm)',
  cursor: 'pointer',
  transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
  backdropFilter: 'blur(var(--ob-blur-md))',
  overflow: 'hidden',
  color: selected
    ? 'var(--ob-color-brand-primary-emphasis)'
    : 'var(--ob-color-text-muted)',

  // Neon Glow for Active State
  boxShadow: selected
    ? 'var(--ob-glow-brand-medium), inset 0 0 0 1px rgba(var(--ob-color-brand-primary-emphasis-rgb), 0.1)'
    : 'none',

  '&:hover': {
    transform: 'translateY(-2px)',
    background: selected
      ? `linear-gradient(135deg, rgba(var(--ob-color-brand-primary-emphasis-rgb), 0.2) 0%, rgba(var(--ob-color-brand-soft-rgb), 0.2) 100%), var(--ob-surface-glass-1)`
      : 'var(--ob-surface-glass-2)',
    borderColor: selected
      ? 'var(--ob-color-border-focus)'
      : 'var(--ob-border-glass-strong)',
  },

  '&:active': {
    transform: 'scale(0.98)',
  },
}))

const CostBadge = styled('div')({
  position: 'absolute',
  top: 'var(--ob-space-035)',
  right: 'var(--ob-space-035)',
  fontSize: 'var(--ob-font-size-2xs)',
  fontWeight: 'var(--ob-font-weight-bold)',
  color: 'var(--ob-error-500)',
  background: 'var(--ob-color-error-soft)',
  padding: 'var(--ob-space-025) var(--ob-space-035)',
  borderRadius: 'var(--ob-radius-sm)',
  border: '1px solid rgba(var(--ob-color-error-strong-rgb), 0.25)',
  letterSpacing: 'var(--ob-letter-spacing-wider)',
})

const IconWrap = styled('div')<{ selected?: boolean }>(({ selected }) => ({
  fontSize: 'var(--ob-font-size-2xl)',
  lineHeight: 'var(--ob-line-height-none)',
  filter: selected
    ? `drop-shadow(0 0 var(--ob-space-050) rgba(var(--ob-color-brand-primary-emphasis-rgb), 0.6))`
    : 'grayscale(0.8)',
  transform: selected ? 'scale(1.1)' : 'scale(1)',
  transition: 'all 0.3s ease',
}))

const Label = styled('span')({
  fontSize: 'var(--ob-font-size-xs)',
  fontWeight: 'var(--ob-font-weight-semibold)',
  textAlign: 'center',
  textTransform: 'uppercase',
  letterSpacing: 'var(--ob-letter-spacing-widest)',
  marginTop: 'auto',
})

const Shine = styled('div')({
  position: 'absolute',
  top: '0',
  left: 0,
  width: '100%',
  height: '100%',
  background: `linear-gradient(120deg, transparent 30%, var(--ob-border-glass) 40%, transparent 50%)`,
  backgroundSize: '200% 100%',
  animation: 'holographic-shine 3s infinite linear',
  pointerEvents: 'none',
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
      <IconWrap selected={selected}>{icon}</IconWrap>

      <Label>{label}</Label>

      {/* Shine Effect */}
      {selected && <Shine />}
      <style>
        {`@keyframes holographic-shine { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }`}
      </style>
    </CardButton>
  )
}
