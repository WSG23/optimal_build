import { CheckCircle, Description } from '@mui/icons-material'
import type { ProfessionalPackType } from '../../../api/agents'

interface PackGridProps {
  value: ProfessionalPackType
  onChange: (value: ProfessionalPackType) => void
  options: Array<{
    value: ProfessionalPackType
    label: string
    description: string
  }>
}

export function PackGrid({ value, onChange, options }: PackGridProps) {
  return (
    <div className="pack-grid">
      {options.map((option) => {
        const isSelected = value === option.value
        return (
          <button
            key={option.value}
            type="button"
            className={`pack-card ${isSelected ? 'pack-card--selected' : ''}`}
            onClick={() => onChange(option.value)}
            aria-pressed={isSelected}
          >
            <div className="pack-card__icon">
              <Description />
            </div>
            <div className="pack-card__content">
              <span className="pack-card__title">{option.label}</span>
              <span className="pack-card__desc">{option.description}</span>
            </div>
            {isSelected && (
              <div className="pack-card__check">
                <CheckCircle sx={{ color: 'var(--ob-color-brand-primary)' }} />
              </div>
            )}
          </button>
        )
      })}
    </div>
  )
}
