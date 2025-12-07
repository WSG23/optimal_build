import { Slider } from '@mui/material'
import type { SliderProps } from '@mui/material'
import { styled } from '@mui/material/styles'
import React from 'react'

// Custom Styled Slider
const StyledSlider = styled(Slider)(() => ({
  height: 6,
  color: 'transparent', // We handle color via track background
  padding: '13px 0',
  '& .MuiSlider-thumb': {
    height: 24,
    width: 24,
    backgroundColor: '#fff',
    border: '2px solid currentColor',
    marginTop: 0,
    marginLeft: -12,
    boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
    transition: 'transform 0.1s cubic-bezier(0.175, 0.885, 0.32, 1.275)', // Spring effect
    '&:focus, &:hover, &.Mui-active': {
      boxShadow: '0 0 0 8px rgba(6, 182, 212, 0.16)', // Brand glow
      transform: 'scale(1.1)',
    },
    '&:before': {
      display: 'none',
    },
    zIndex: 1,
  },
  '& .MuiSlider-track': {
    height: 6,
    border: 'none',
    borderRadius: 3,
    background: 'linear-gradient(90deg, #3b82f6 0%, #06b6d4 50%, #f43f5e 100%)', // Blue -> Cyan -> Red (Safe to Aggressive)
    opacity: 1,
  },
  '& .MuiSlider-rail': {
    color: '#d8d8d8',
    opacity: 1,
    height: 6,
    borderRadius: 3,
    background: 'rgba(255,255,255,0.2)',
  },
  '& .MuiSlider-mark': {
    backgroundColor: '#bfbfbf',
    height: 8,
    width: 1,
    marginTop: -3,
  },
  '& .MuiSlider-markActive': {
    opacity: 1,
    backgroundColor: 'rgba(255,255,255,0.8)',
  },
}))

function ValueLabelComponent(props: {
  children: React.ReactElement
  value: number
  open?: boolean
}) {
  const { children, value, open } = props

  return (
    <div
      style={{
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Floating Bubble */}
      <div
        style={{
          position: 'absolute',
          top: -36,
          left: '50%',
          transform: `translateX(-50%) scale(${open ? 1 : 0})`,
          background: 'var(--ob-color-bg-surface-main, #1e1e24)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '6px',
          fontSize: '0.75rem',
          fontWeight: 700,
          whiteSpace: 'nowrap',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
          border: '1px solid rgba(255,255,255,0.1)',
          opacity: open ? 1 : 0,
          transition: 'transform 0.15s ease-out, opacity 0.15s ease-out',
          pointerEvents: 'none',
          zIndex: 2,
        }}
      >
        {value}
      </div>
      {children}
    </div>
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
