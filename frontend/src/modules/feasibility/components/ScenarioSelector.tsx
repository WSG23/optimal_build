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
      icon: <Business fontSize="small" />,
    },
    {
      value: 'Residential',
      label: 'Residential',
      icon: <HomeWork fontSize="small" />,
    },
    {
      value: 'Commercial',
      label: 'Commercial',
      icon: <Foundation fontSize="small" />,
    },
    {
      value: 'Raw Land',
      label: 'Raw Land',
      icon: <Landscape fontSize="small" />,
    },
  ]

  return (
    <div className="scenario-selector">
      {options.map((option) => {
        const isSelected = value === option.value
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`scenario-selector__option ${isSelected ? 'scenario-selector__option--selected' : ''}`}
            aria-pressed={isSelected}
          >
            <span className="scenario-selector__icon">{option.icon}</span>

            <Typography variant="body2" className="scenario-selector__label">
              {option.label}
            </Typography>
          </button>
        )
      })}
    </div>
  )
}
