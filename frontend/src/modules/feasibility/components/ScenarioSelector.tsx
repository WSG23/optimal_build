import { Business, Foundation, HomeWork, Landscape } from '@mui/icons-material'
import { Typography } from '@mui/material'

interface ScenarioSelectorProps {
  value: string
  onChange: (value: string) => void
}

export function ScenarioSelector({ value, onChange }: ScenarioSelectorProps) {
  const options = [
    {
      value: 'Mixed Use',
      label: 'Mixed Use',
      icon: <Business />,
      color: '#ec4899',
    }, // Pink/Magenta
    {
      value: 'Residential',
      label: 'Residential',
      icon: <HomeWork />,
      color: '#3b82f6',
    }, // Blue
    {
      value: 'Commercial',
      label: 'Commercial',
      icon: <Foundation />,
      color: '#10b981',
    }, // Emerald
    {
      value: 'Raw Land',
      label: 'Raw Land',
      icon: <Landscape />,
      color: '#f59e0b',
    }, // Amber
  ]

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '12px',
      }}
    >
      {options.map((option) => {
        const isSelected = value === option.value
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            style={{
              background: isSelected
                ? 'rgba(255, 255, 255, 0.1)'
                : 'rgba(255, 255, 255, 0.03)',
              border: `1px solid ${isSelected ? option.color : 'rgba(255, 255, 255, 0.1)'}`,
              borderRadius: '4px',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              cursor: 'pointer',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: isSelected
                ? `0 0 20px ${option.color}40, inset 0 0 10px ${option.color}20`
                : 'none',
              height: '100px',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Icon */}
            <div
              style={{
                color: isSelected ? option.color : 'rgba(255,255,255,0.7)',
                transform: isSelected ? 'scale(1.1)' : 'scale(1)',
                transition: 'transform 0.3s',
              }}
            >
              {option.icon}
            </div>

            {/* Label */}
            <Typography
              variant="body2"
              sx={{
                color: isSelected ? 'white' : 'rgba(255,255,255,0.6)',
                fontWeight: isSelected ? 600 : 400,
                fontSize: '0.8rem',
              }}
            >
              {option.label}
            </Typography>

            {/* Selection Glow */}
            {isSelected && (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  background: `radial-gradient(circle at center, ${option.color}15 0%, transparent 70%)`,
                }}
              />
            )}
          </button>
        )
      })}
    </div>
  )
}
