import { Slider } from '@mui/material'
import type { SliderProps } from '@mui/material'
import { styled } from '@mui/material/styles'
import React from 'react'

// Custom Styled Slider
const StyledSlider = styled(Slider)(() => ({
  height: 'var(--ob-radius-md)',
  color: 'var(--ob-color-brand-primary-emphasis)',
  padding: 'var(--ob-space-085) 0',
  '& .MuiSlider-thumb': {
    height: 'var(--ob-size-icon-sm)',
    width: 'var(--ob-size-icon-sm)',
    backgroundColor: 'var(--ob-color-text-primary)',
    border: '2px solid currentColor',
    marginTop: '0',
    marginLeft: 'calc(-1 * var(--ob-size-icon-sm) / 2)',
    boxShadow: 'var(--ob-shadow-md)',
    transition: 'transform 0.1s cubic-bezier(0.175, 0.885, 0.32, 1.275)', // Spring effect
    '&:focus, &:hover, &.Mui-active': {
      boxShadow: `0 0 0 var(--ob-space-050) rgba(var(--ob-color-brand-primary-emphasis-rgb), 0.16)`,
      transform: 'scale(1.1)',
    },
    '&:before': {
      display: 'none',
    },
    zIndex: 1,
  },
  '& .MuiSlider-track': {
    height: 'var(--ob-radius-md)',
    border: 'none',
    borderRadius: 'var(--ob-radius-xs)',
    background: `linear-gradient(90deg, var(--ob-color-brand-primary-emphasis) 0%, var(--ob-warning-500) 50%, var(--ob-error-500) 100%)`,
    opacity: 1,
  },
  '& .MuiSlider-rail': {
    opacity: 1,
    height: 'var(--ob-radius-md)',
    borderRadius: 'var(--ob-radius-xs)',
    background: 'rgba(var(--ob-color-text-primary-rgb), 0.2)',
  },
  '& .MuiSlider-mark': {
    backgroundColor: 'rgba(var(--ob-color-text-primary-rgb), 0.5)',
    height: 'var(--ob-space-050)',
    width: 1,
    marginTop: -3,
  },
  '& .MuiSlider-markActive': {
    opacity: 1,
    backgroundColor: 'rgba(var(--ob-color-text-primary-rgb), 0.8)',
  },
}))

const ValueLabelRoot = styled('div')({
  position: 'relative',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
})

const ValueBubble = styled('div')<{ open?: boolean }>(({ open }) => ({
  position: 'absolute',
  top: 'calc(-1 * var(--ob-space-200) - var(--ob-space-025))',
  left: '50%',
  transform: `translateX(-50%) scale(${open ? 1 : 0})`,
  background: 'var(--ob-color-bg-surface)',
  color: 'var(--ob-color-text-primary)',
  padding: 'var(--ob-space-025) var(--ob-space-050)',
  borderRadius: 'var(--ob-radius-md)',
  fontSize: 'var(--ob-font-size-xs)',
  fontWeight: 'var(--ob-font-weight-bold)',
  whiteSpace: 'nowrap',
  boxShadow: 'var(--ob-shadow-md)',
  border: '1px solid var(--ob-color-border-subtle)',
  opacity: open ? 1 : 0,
  transition: 'transform 0.15s ease-out, opacity 0.15s ease-out',
  pointerEvents: 'none',
  zIndex: 2,
}))

function ValueLabelComponent(props: {
  children: React.ReactElement
  value: number
  open?: boolean
}) {
  const { children, value, open } = props

  return (
    <ValueLabelRoot>
      {/* Floating Bubble */}
      <ValueBubble open={open}>{value}</ValueBubble>
      {children}
    </ValueLabelRoot>
  )
}

type TunerSliderProps = Omit<SliderProps, 'valueLabelDisplay'>

export function TunerSlider(props: TunerSliderProps) {
  return (
    <StyledSlider
      valueLabelDisplay="auto" // We handle custom visibility logic via components if needed, or rely on MUI default with our custom slot
      components={{
        ValueLabel: ValueLabelComponent,
      }}
      // Pass dragging state or just use active class
      {...props}
      sx={{
        // Overwrite track color specifically if dynamic logic is needed later
        ...props.sx,
      }}
    />
  )
}
